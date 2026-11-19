from collections.abc import Callable
from typing import Any, Protocol

from ..domain.discovery import DiscoveredDevice


class DeviceTransport(Protocol):
    async def send(
        self,
        method: str,
        params: list[Any] | None = None,
        *,
        retries: int | None = None,
    ) -> Any: ...

    def close(self) -> None: ...


type TransportFactory = Callable[[str, bytes], DeviceTransport]


class DeviceScanner(Protocol):
    async def scan(self) -> list[DiscoveredDevice]: ...
