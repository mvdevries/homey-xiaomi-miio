import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..domain.errors import (
    MalformedPacketError,
    MiioConnectionError,
    MiioDeviceError,
    MiioTimeoutError,
)
from .packet import PORT, build_hello, decode, encode

DEFAULT_TIMEOUT_SECONDS = 1.5
DEFAULT_RETRIES = 3
HANDSHAKE_MAX_AGE_SECONDS = 60.0
MAX_MESSAGE_ID = 10_000
RETRY_ID_STEP = 100
STAMP_MODULUS = 2**32


@dataclass(frozen=True, slots=True)
class Handshake:
    device_id: int
    stamp: int


class _DatagramHandler(asyncio.DatagramProtocol):
    def __init__(
        self,
        on_datagram: Callable[[bytes], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        self._on_datagram = on_datagram
        self._on_error = on_error

    def datagram_received(self, data: bytes, addr: Any) -> None:
        self._on_datagram(data)

    def error_received(self, exc: Exception) -> None:
        self._on_error(exc)


class MiioTransport:
    def __init__(
        self,
        address: str,
        token: bytes,
        *,
        port: int = PORT,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_RETRIES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._address = address
        self._token = token
        self._port = port
        self._timeout = timeout
        self._retries = retries
        self._clock = clock
        self._endpoint: asyncio.DatagramTransport | None = None
        self._device_id = 0
        self._device_stamp = 0
        self._stamp_received_at = 0.0
        self._last_handshake: float | None = None
        self._last_id = 0
        self._handshake_waiter: asyncio.Future[Handshake] | None = None
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._lock = asyncio.Lock()

    async def handshake(self) -> Handshake:
        async with self._lock:
            return await self._perform_handshake()

    async def send(
        self,
        method: str,
        params: list[Any] | None = None,
        *,
        retries: int | None = None,
    ) -> Any:
        attempts_left = self._retries if retries is None else retries
        async with self._lock:
            first_attempt = True
            while True:
                try:
                    if self._needs_handshake():
                        await self._perform_handshake()
                    request_id = self._next_id(first_attempt)
                    first_attempt = False
                    return await self._send_once(request_id, method, params or [])
                except (MiioTimeoutError, MiioDeviceError) as error:
                    if not _is_retryable(error) or attempts_left <= 0:
                        raise
                    attempts_left -= 1
                    if isinstance(error, MiioTimeoutError):
                        self._last_handshake = None
                        self._close_endpoint()

    def reset(self) -> None:
        self.close()
        self._device_stamp = 0
        self._stamp_received_at = 0.0
        self._last_handshake = None

    def close(self) -> None:
        error = MiioConnectionError("Transport closed")
        self._fail_waiters(error)
        self._close_endpoint()

    async def _perform_handshake(self) -> Handshake:
        endpoint = await self._ensure_endpoint()
        waiter = asyncio.get_running_loop().create_future()
        self._handshake_waiter = waiter
        endpoint.sendto(build_hello())
        try:
            return await asyncio.wait_for(waiter, self._timeout)
        except TimeoutError as error:
            raise MiioTimeoutError(
                f"Handshake timed out after {self._timeout}s"
            ) from error
        finally:
            self._handshake_waiter = None

    async def _send_once(self, request_id: int, method: str, params: list[Any]) -> Any:
        payload = {"id": request_id, "method": method, "params": params}
        packet = encode(self._device_id, self._current_stamp(), self._token, payload)
        endpoint = await self._ensure_endpoint()
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        endpoint.sendto(packet)
        try:
            return await asyncio.wait_for(future, self._timeout)
        except TimeoutError as error:
            raise MiioTimeoutError(
                f"Command '{method}' timed out after {self._timeout}s"
            ) from error
        finally:
            self._pending.pop(request_id, None)

    def _needs_handshake(self) -> bool:
        if self._last_handshake is None:
            return True
        return self._clock() - self._last_handshake > HANDSHAKE_MAX_AGE_SECONDS

    def _next_id(self, first_attempt: bool) -> int:
        candidate = self._last_id + (1 if first_attempt else RETRY_ID_STEP)
        self._last_id = 1 if candidate >= MAX_MESSAGE_ID else candidate
        return self._last_id

    def _current_stamp(self) -> int:
        elapsed = int(self._clock() - self._stamp_received_at)
        return (self._device_stamp + elapsed) % STAMP_MODULUS

    def _update_stamp(self, stamp: int) -> None:
        if stamp > 0:
            self._device_stamp = stamp
            self._stamp_received_at = self._clock()

    async def _ensure_endpoint(self) -> asyncio.DatagramTransport:
        if self._endpoint is not None:
            return self._endpoint
        try:
            endpoint, _ = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: _DatagramHandler(self._handle_datagram, self._handle_error),
                remote_addr=(self._address, self._port),
            )
        except OSError as error:
            raise MiioConnectionError(str(error)) from error
        self._endpoint = endpoint
        return endpoint

    def _close_endpoint(self) -> None:
        endpoint, self._endpoint = self._endpoint, None
        if endpoint is not None:
            endpoint.close()

    def _handle_error(self, error: Exception) -> None:
        self._close_endpoint()
        self._fail_waiters(MiioConnectionError(str(error)))

    def _fail_waiters(self, error: Exception) -> None:
        waiter = self._handshake_waiter
        if waiter is not None and not waiter.done():
            waiter.set_exception(error)
        for future in self._pending.values():
            if not future.done():
                future.set_exception(error)

    def _handle_datagram(self, data: bytes) -> None:
        try:
            decoded = decode(data, self._token)
        except MalformedPacketError as error:
            waiter = self._handshake_waiter
            if waiter is not None and not waiter.done():
                waiter.set_exception(error)
            return
        self._update_stamp(decoded.stamp)
        if decoded.payload is None:
            self._complete_handshake(decoded.device_id, decoded.stamp)
        else:
            self._complete_request(decoded.payload)

    def _complete_handshake(self, device_id: int, stamp: int) -> None:
        waiter = self._handshake_waiter
        if waiter is None or waiter.done():
            return
        self._device_id = device_id
        self._last_handshake = self._clock()
        waiter.set_result(Handshake(device_id, stamp))

    def _complete_request(self, payload: dict[str, Any]) -> None:
        future = self._pending.get(payload.get("id", -1))
        if future is None or future.done():
            return
        error = payload.get("error")
        if error:
            future.set_exception(
                MiioDeviceError(error.get("code", 0), error.get("message", ""))
            )
        else:
            future.set_result(payload.get("result"))


def _is_retryable(error: Exception) -> bool:
    if isinstance(error, MiioTimeoutError):
        return True
    return isinstance(error, MiioDeviceError) and error.recoverable
