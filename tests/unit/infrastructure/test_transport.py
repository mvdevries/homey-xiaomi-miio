import asyncio

import pytest
from app.domain.errors import (
    MalformedPacketError,
    MiioConnectionError,
    MiioDeviceError,
    MiioTimeoutError,
)
from app.infrastructure.transport import HANDSHAKE_MAX_AGE_SECONDS, MiioTransport

from tests.support.fake_device import start_fake_device

TOKEN = bytes(range(16))


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
async def transports():
    created = []
    yield created
    for transport in created:
        transport.close()


async def make_transport(transports, clock, port, **options):
    transport = MiioTransport(
        "127.0.0.1",
        TOKEN,
        port=port,
        timeout=options.pop("timeout", 0.2),
        retries=options.pop("retries", 2),
        clock=clock,
        **options,
    )
    transports.append(transport)
    return transport


class TestMiioTransportHandshake:
    async def test_given_a_device_when_handshaking_then_id_and_stamp_are_returned(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, device_id=77, stamp=5000)
        transport = await make_transport(transports, clock, port)

        handshake = await transport.handshake()

        assert (handshake.device_id, handshake.stamp) == (77, 5000)
        device.close()

    async def test_given_a_malformed_reply_when_handshaking_then_it_is_rejected(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        device.hello_reply = b"x" * 40
        transport = await make_transport(transports, clock, port)

        with pytest.raises(MalformedPacketError):
            await transport.handshake()

        device.close()

    async def test_given_an_unreachable_host_when_handshaking_then_it_fails(
        self, transports, clock
    ):
        transport = MiioTransport("256.256.256.256", TOKEN, timeout=0.05, clock=clock)
        transports.append(transport)

        with pytest.raises(MiioConnectionError):
            await transport.handshake()

    async def test_given_nobody_listening_when_sending_then_the_handshake_fails(
        self, transports, clock
    ):
        _, port = await start_fake_device(TOKEN)
        transport = await make_transport(
            transports, clock, port, timeout=0.05, retries=0
        )
        transport._port = port + 1 if port < 65535 else port - 1

        with pytest.raises((MiioTimeoutError, MiioConnectionError)):
            await transport.send("a")

    async def test_given_a_fresh_handshake_when_sending_again_then_it_is_reused(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)

        await transport.send("a")
        clock.now += HANDSHAKE_MAX_AGE_SECONDS - 1
        await transport.send("b")

        assert device.hellos == 1
        device.close()

    async def test_given_a_stale_handshake_when_sending_again_then_it_is_repeated(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)

        await transport.send("a")
        clock.now += HANDSHAKE_MAX_AGE_SECONDS + 1
        await transport.send("b")

        assert device.hellos == 2
        device.close()

    async def test_given_an_unsolicited_handshake_when_received_then_it_is_ignored(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)

        transport._handle_datagram(device._hello_packet())

        assert transport._last_handshake is None
        device.close()


class TestMiioTransportSend:
    async def test_given_a_device_when_sending_then_the_result_is_returned(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)

        result = await transport.send("get_prop", ["power"])

        assert result == ["ok"]
        assert device.requests[0]["method"] == "get_prop"
        assert device.requests[0]["params"] == ["power"]
        device.close()

    async def test_given_no_params_when_sending_then_empty_params_are_sent(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)

        await transport.send("miIO.info")

        assert device.requests[0]["params"] == []
        device.close()

    async def test_given_two_sends_when_sent_then_the_message_ids_increase(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)

        await transport.send("a")
        await transport.send("b")

        assert [request["id"] for request in device.requests] == [1, 2]
        device.close()

    async def test_given_the_last_id_at_the_limit_when_sending_then_the_id_wraps_around(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)
        transport._last_id = 9_999

        await transport.send("a")

        assert device.requests[0]["id"] == 1
        device.close()

    async def test_given_a_moving_clock_when_sending_then_the_stamp_advances_with_it(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, stamp=1000)
        transport = await make_transport(transports, clock, port)

        await transport.send("a")
        clock.now += 5
        await transport.send("b")

        assert device.stamps == [1000, 1005]
        device.close()

    async def test_given_a_silent_device_when_sending_then_it_times_out_after_retries(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, responder=lambda payload: None)
        transport = await make_transport(
            transports, clock, port, timeout=0.05, retries=1
        )

        with pytest.raises(MiioTimeoutError):
            await transport.send("a")

        assert len(device.requests) == 2
        device.close()

    async def test_given_a_silent_device_when_retrying_then_a_new_message_id_is_used(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, responder=lambda payload: None)
        transport = await make_transport(
            transports, clock, port, timeout=0.05, retries=1
        )

        with pytest.raises(MiioTimeoutError):
            await transport.send("a")

        assert [request["id"] for request in device.requests] == [1, 101]
        device.close()

    async def test_given_retries_overridden_when_sending_then_the_override_is_used(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, responder=lambda payload: None)
        transport = await make_transport(
            transports, clock, port, timeout=0.05, retries=5
        )

        with pytest.raises(MiioTimeoutError):
            await transport.send("a", retries=0)

        assert len(device.requests) == 1
        device.close()

    async def test_given_a_device_error_when_sending_then_it_is_raised_without_retry(
        self, transports, clock
    ):
        device, port = await start_fake_device(
            TOKEN,
            responder=lambda payload: {
                "id": payload["id"],
                "error": {"code": -1, "message": "bad"},
            },
        )
        transport = await make_transport(transports, clock, port)

        with pytest.raises(MiioDeviceError) as raised:
            await transport.send("a")

        assert raised.value.code == -1
        assert len(device.requests) == 1
        device.close()

    async def test_given_a_recoverable_device_error_when_sending_then_it_is_retried(
        self, transports, clock
    ):
        calls = []

        def responder(payload):
            calls.append(payload["id"])
            if len(calls) == 1:
                return {
                    "id": payload["id"],
                    "error": {"code": -30001, "message": "busy"},
                }
            return {"id": payload["id"], "result": ["ok"]}

        device, port = await start_fake_device(TOKEN, responder=responder)
        transport = await make_transport(transports, clock, port)

        result = await transport.send("a")

        assert result == ["ok"]
        assert len(calls) == 2
        device.close()

    async def test_given_responses_with_unknown_ids_when_sending_then_they_are_ignored(
        self, transports, clock
    ):
        def responder(payload):
            return {"id": payload["id"] + 500, "result": ["other"]}

        device, port = await start_fake_device(TOKEN, responder=responder)
        transport = await make_transport(
            transports, clock, port, timeout=0.05, retries=0
        )

        with pytest.raises(MiioTimeoutError):
            await transport.send("a")

        device.close()

    async def test_given_a_pending_request_when_the_socket_fails_then_it_fails(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, responder=lambda payload: None)
        transport = await make_transport(transports, clock, port, timeout=5, retries=0)
        task = asyncio.create_task(transport.send("a"))
        await asyncio.sleep(0.1)

        transport._handle_error(OSError("unreachable"))

        with pytest.raises(MiioConnectionError, match="unreachable"):
            await task

        device.close()


class TestMiioTransportClose:
    async def test_given_a_pending_request_when_closed_then_the_request_fails(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN, responder=lambda payload: None)
        transport = await make_transport(transports, clock, port, timeout=5, retries=0)
        task = asyncio.create_task(transport.send("a"))
        await asyncio.sleep(0.1)

        transport.close()

        with pytest.raises(MiioConnectionError):
            await task

        device.close()


class TestMiioTransportReset:
    async def test_given_a_fresh_handshake_when_reset_then_a_new_handshake_is_made(
        self, transports, clock
    ):
        device, port = await start_fake_device(TOKEN)
        transport = await make_transport(transports, clock, port)
        await transport.send("a")

        transport.reset()
        await transport.send("b")

        assert device.hellos == 2
        device.close()
