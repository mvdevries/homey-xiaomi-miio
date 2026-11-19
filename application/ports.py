from collections.abc import Callable
from typing import Any, Protocol

from ..domain.discovery import DiscoveredDevice
from ..domain.xiaomi_account import CloudDevice, QrChallenge


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


class CloudSession(Protocol):
    async def list_devices(self, server: str) -> list[CloudDevice]: ...


class CloudAuthenticator(Protocol):
    async def request_qr(self) -> QrChallenge: ...

    async def wait_for_scan(self, challenge: QrChallenge) -> CloudSession: ...


type CloudAuthenticatorFactory = Callable[[], CloudAuthenticator]
