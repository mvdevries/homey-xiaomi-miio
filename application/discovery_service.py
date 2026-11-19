from ..domain.discovery import DiscoveredDevice
from .ports import DeviceScanner


class DiscoveryService:
    def __init__(self, *, scanner: DeviceScanner) -> None:
        self._scanner = scanner

    async def discover_devices(self) -> list[dict]:
        devices = await self._scanner.scan()
        return [device.to_dict() for device in sort_by_address(devices)]


def sort_by_address(devices: list[DiscoveredDevice]) -> list[DiscoveredDevice]:
    return sorted(devices, key=lambda device: _address_key(device.address))


def _address_key(address: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in address.split("."))
    except ValueError:
        return (999,)
