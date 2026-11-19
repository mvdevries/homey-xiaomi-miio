import asyncio
from typing import Any

from homey.device import Device

from .errors import InvalidTokenError, MiioError
from .polling import polling_seconds

FAILURES_BEFORE_UNAVAILABLE = 3
UNREACHABLE_MESSAGE = "Device unreachable"
INVALID_TOKEN_MESSAGE = "The device token is invalid"


class MiioPollingDevice(Device):
    _client: Any = None
    _poll_task: asyncio.Task | None = None
    _failures = 0
    _connected = False

    def create_client(self, settings: Any) -> Any:
        raise NotImplementedError

    async def read_capabilities(self, client: Any) -> dict[str, Any]:
        raise NotImplementedError

    def register_listeners(self) -> None:
        raise NotImplementedError

    async def on_init(self) -> None:
        self.register_listeners()
        try:
            self._client = self.create_client(self.get_settings())
        except InvalidTokenError:
            await self.set_unavailable(INVALID_TOKEN_MESSAGE)
            return
        self._start_polling()

    async def on_settings(
        self,
        old_settings: dict[str, Any],
        new_settings: dict[str, Any],
        changed_keys: tuple[str, ...],
    ) -> str | None:
        try:
            client = self.create_client(new_settings)
        except InvalidTokenError as error:
            raise Exception("token_invalid") from error
        self._replace_client(client)
        self._start_polling()
        return None

    async def on_uninit(self) -> None:
        self._stop()

    async def on_deleted(self) -> None:
        self._stop()

    def _replace_client(self, client: Any) -> None:
        previous, self._client = self._client, client
        if previous is not None:
            previous.close()
        self._failures = 0
        self._connected = False

    def _start_polling(self) -> None:
        if self._poll_task is None or self._poll_task.done():
            self._poll_task = asyncio.create_task(self._poll_forever())

    def _stop(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            self._poll_task = None
        if self._client is not None:
            self._client.close()
            self._client = None

    async def _poll_forever(self) -> None:
        while True:
            await self._poll_once()
            await asyncio.sleep(polling_seconds(self.get_setting("polling")))

    async def _poll_once(self) -> None:
        client = self._client
        if client is None:
            return
        try:
            capabilities = await self.read_capabilities(client)
        except MiioError as error:
            await self._handle_failure(error)
            return
        await self._handle_success(capabilities)

    async def _handle_success(self, capabilities: dict[str, Any]) -> None:
        for capability, value in capabilities.items():
            await self.set_capability_value(capability, value)
        self._failures = 0
        self._connected = True
        if not self.get_available():
            await self.set_available()

    async def _handle_failure(self, error: MiioError) -> None:
        self._failures += 1
        self.error(f"Polling failed ({self._failures}): {error}")
        if self._failures >= self._failure_limit() and self.get_available():
            await self.set_unavailable(UNREACHABLE_MESSAGE)

    def _failure_limit(self) -> int:
        return FAILURES_BEFORE_UNAVAILABLE if self._connected else 1

    def _require_client(self) -> Any:
        if self._client is None:
            raise MiioError("The device is not connected")
        return self._client

    def _current(self, capability: str, default: Any) -> Any:
        value = self.get_capability_value(capability)
        return default if value is None else value
