import asyncio
import socket
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from ..domain.discovery import DiscoveredDevice, short_hostname
from ..domain.errors import MalformedPacketError, MiioConnectionError
from .packet import PORT, build_hello, decode

BROADCAST_ADDRESS = "255.255.255.255"
LISTEN_SECONDS = 3.0
HELLO_ROUNDS = 3
NO_TOKEN = bytes(16)
NAME_LOOKUP_SECONDS = 2.0

type NameResolver = Callable[[str], Awaitable[str]]


async def reverse_dns_name(address: str) -> str:
    loop = asyncio.get_running_loop()
    try:
        hostname, _, _ = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyaddr, address),
            NAME_LOOKUP_SECONDS,
        )
    except OSError, TimeoutError:
        return ""
    return short_hostname(hostname)


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
        name_resolver: NameResolver = reverse_dns_name,
    ) -> None:
        self._name_resolver = name_resolver
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
        return await self._add_names(list(found.values()))

    async def _add_names(
        self, devices: list[DiscoveredDevice]
    ) -> list[DiscoveredDevice]:
        names = await asyncio.gather(
            *(self._name_resolver(device.address) for device in devices)
        )
        return [
            replace(device, name=name)
            for device, name in zip(devices, names, strict=True)
        ]

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
