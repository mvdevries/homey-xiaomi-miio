import asyncio
import time

import pytest
from app.domain.errors import MiioConnectionError
from app.infrastructure import discovery
from app.infrastructure.discovery import UdpDeviceScanner, reverse_dns_name

from tests.support.fake_device import start_fake_device

TOKEN = bytes(range(16))
SCAN_SECONDS = 0.3


class TestUdpDeviceScanner:
    async def test_given_a_device_when_scanned_then_it_is_found_once(self):
        device, port = await start_fake_device(TOKEN, device_id=0xABCD)
        scanner = UdpDeviceScanner(
            targets=[("127.0.0.1", port)], listen_seconds=SCAN_SECONDS
        )

        found = await scanner.scan()
        device.close()

        assert [(item.address, item.device_id) for item in found] == [
            ("127.0.0.1", 0xABCD)
        ]
        assert device.hellos >= 2

    async def test_given_a_name_resolver_when_scanned_then_the_name_is_added(self):
        async def resolve(address):
            return "zhimi-fan-za4_mibt0FE4"

        device, port = await start_fake_device(TOKEN)
        scanner = UdpDeviceScanner(
            targets=[("127.0.0.1", port)],
            listen_seconds=SCAN_SECONDS,
            name_resolver=resolve,
        )

        found = await scanner.scan()
        device.close()

        assert found[0].name == "zhimi-fan-za4_mibt0FE4"

    async def test_given_no_device_when_scanned_then_nothing_is_found(self):
        scanner = UdpDeviceScanner(targets=[("127.0.0.1", 9)], listen_seconds=0.1)

        found = await scanner.scan()

        assert found == []

    async def test_given_a_device_that_sends_garbage_when_scanned_then_it_is_ignored(
        self,
    ):
        device, port = await start_fake_device(TOKEN)
        device.hello_reply = b"not a miio packet at all, just some bytes....."
        scanner = UdpDeviceScanner(
            targets=[("127.0.0.1", port)], listen_seconds=SCAN_SECONDS
        )

        found = await scanner.scan()
        device.close()

        assert found == []

    async def test_given_a_socket_that_cannot_open_when_scanned_then_it_fails(
        self, monkeypatch
    ):
        async def refuse(*args, **kwargs):
            raise OSError("no network")

        loop = asyncio.get_running_loop()
        monkeypatch.setattr(loop, "create_datagram_endpoint", refuse)

        with pytest.raises(MiioConnectionError):
            await UdpDeviceScanner(listen_seconds=0.1).scan()


class TestReverseDnsName:
    async def test_given_a_known_address_when_resolved_then_the_short_name_is_returned(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            discovery.socket,
            "gethostbyaddr",
            lambda address: ("lamp_mibt1.home.example", [], [address]),
        )

        assert await reverse_dns_name("192.0.2.10") == "lamp_mibt1"

    async def test_given_an_unknown_address_when_resolved_then_the_name_is_empty(
        self, monkeypatch
    ):
        def fail(address):
            raise OSError("unknown")

        monkeypatch.setattr(discovery.socket, "gethostbyaddr", fail)

        assert await reverse_dns_name("192.0.2.10") == ""

    async def test_given_a_slow_lookup_when_resolved_then_the_name_is_empty(
        self, monkeypatch
    ):
        def slow(address):
            time.sleep(0.3)
            return ("late", [], [address])

        monkeypatch.setattr(discovery.socket, "gethostbyaddr", slow)
        monkeypatch.setattr(discovery, "NAME_LOOKUP_SECONDS", 0.05)

        assert await reverse_dns_name("192.0.2.10") == ""
