import asyncio
from collections.abc import Callable
from typing import Any

from ..domain.discovery import DiscoveredDevice
from ..domain.errors import MalformedPacketError, MiioConnectionError
from .packet import PORT, build_hello, decode

BROADCAST_ADDRESS = "255.255.255.255"
LISTEN_SECONDS = 3.0
HELLO_ROUNDS = 3
NO_TOKEN = bytes(16)


class _CollectingHandler(asyncio.DatagramProtocol):
    def __init__(self, on_device: Callable[[DiscoveredDevice], None]) -> None:
        self._on_device = on_device

    def datagram_received(self, data: bytes, addr: Any) -> None:
        try:
            decoded = decode(data, NO_TOKEN)
        except MalformedPacketError:
            return
        self._on_device(DiscoveredDevice(addr[0], decoded.device_id))


class UdpDeviceScanner:
    def __init__(
        self,
        *,
        targets: list[tuple[str, int]] | None = None,
        listen_seconds: float = LISTEN_SECONDS,
    ) -> None:
        self._targets = targets or [(BROADCAST_ADDRESS, PORT)]
        self._listen_seconds = listen_seconds

    async def scan(self) -> list[DiscoveredDevice]:
        found: dict[str, DiscoveredDevice] = {}
        endpoint = await self._open_endpoint(
            lambda device: found.setdefault(device.address, device)
        )
        try:
            await self._send_hellos(endpoint)
        finally:
            endpoint.close()
        return list(found.values())

    async def _open_endpoint(
        self, on_device: Callable[[DiscoveredDevice], None]
    ) -> asyncio.DatagramTransport:
        try:
            endpoint, _ = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: _CollectingHandler(on_device),
                local_addr=("0.0.0.0", 0),
                allow_broadcast=True,
            )
        except OSError as error:
            raise MiioConnectionError(str(error)) from error
        return endpoint

    async def _send_hellos(self, endpoint: asyncio.DatagramTransport) -> None:
        pause = self._listen_seconds / HELLO_ROUNDS
        for _ in range(HELLO_ROUNDS):
            for target in self._targets:
                endpoint.sendto(build_hello(), target)
            await asyncio.sleep(pause)
