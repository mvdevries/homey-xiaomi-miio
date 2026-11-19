import asyncio

import pytest
from app.domain.errors import MiioConnectionError
from app.infrastructure.discovery import UdpDeviceScanner

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
