from app.application.discovery_service import DiscoveryService
from app.domain.discovery import DiscoveredDevice


class FakeScanner:
    def __init__(self, devices):
        self.devices = devices

    async def scan(self):
        return self.devices


class TestDiscoveryService:
    async def test_given_found_devices_when_discovered_then_they_are_sorted_by_address(
        self,
    ):
        scanner = FakeScanner(
            [
                DiscoveredDevice("192.0.2.100", 2),
                DiscoveredDevice("192.0.2.9", 1),
            ]
        )

        devices = await DiscoveryService(scanner=scanner).discover_devices()

        assert [device["address"] for device in devices] == ["192.0.2.9", "192.0.2.100"]

    async def test_given_no_devices_when_discovered_then_the_list_is_empty(self):
        devices = await DiscoveryService(scanner=FakeScanner([])).discover_devices()

        assert devices == []

    async def test_given_an_unusual_address_when_discovered_then_it_is_listed_last(
        self,
    ):
        scanner = FakeScanner(
            [DiscoveredDevice("fe80::1", 2), DiscoveredDevice("192.0.2.9", 1)]
        )

        devices = await DiscoveryService(scanner=scanner).discover_devices()

        assert [device["address"] for device in devices] == ["192.0.2.9", "fe80::1"]
