import asyncio
from typing import ClassVar

import pytest
from app.domain.errors import InvalidTokenError, MiioError, MiioTimeoutError
from app.endpoints.polling_device import (
    INVALID_TOKEN_MESSAGE,
    UNREACHABLE_MESSAGE,
    Command,
    MiioPollingDevice,
)

from tests.support.fake_homey_device import FakeHomeyMixin

SETTINGS = {"address": "192.0.2.10", "token": "00" * 16, "polling": 5}


class FakeClient:
    def __init__(self):
        self.closed = False
        self.error = None
        self.capabilities = {"onoff": True}

    def close(self):
        self.closed = True


class SampleDevice(FakeHomeyMixin, MiioPollingDevice):
    def __init__(self, client=None, **kwargs):
        self.setup_fake(**kwargs)
        self.next_client = client or FakeClient()
        self.registered = False
        self._client = None

    def register_listeners(self):
        self.registered = True

    def create_client(self, settings):
        if isinstance(self.next_client, Exception):
            raise self.next_client
        return self.next_client

    async def read_capabilities(self, client):
        if client.error is not None:
            raise client.error
        return client.capabilities


async def connected_device(**kwargs):
    device = SampleDevice(**kwargs)
    device._client = device.next_client
    return device


class TestMiioPollingDeviceOnInit:
    async def test_given_a_device_when_initialised_then_listeners_and_polling_start(
        self,
    ):
        device = SampleDevice()

        await device.on_init()
        await asyncio.sleep(0)
        registered = device.registered
        capabilities = dict(device.capabilities)
        await device.on_uninit()

        assert registered
        assert capabilities == {"onoff": True}
        assert device.next_client.closed

    async def test_given_an_invalid_token_when_initialised_then_it_is_unavailable(
        self,
    ):
        device = SampleDevice(client=InvalidTokenError("token_invalid"))

        await device.on_init()

        assert device.unavailable_messages == [INVALID_TOKEN_MESSAGE]
        assert device._poll_task is None


class TestMiioPollingDevicePollOnce:
    async def test_given_a_connected_device_when_polled_then_capabilities_are_applied(
        self,
    ):
        device = await connected_device()

        await device._poll_once()

        assert device.capabilities == {"onoff": True}

    async def test_given_an_unavailable_device_when_polled_then_it_becomes_available(
        self,
    ):
        device = await connected_device()
        device.available = False

        await device._poll_once()

        assert device.available

    async def test_given_a_failing_first_poll_when_polled_then_it_becomes_unavailable(
        self,
    ):
        device = await connected_device()
        device._client.error = MiioTimeoutError("timeout")

        await device._poll_once()

        assert device.unavailable_messages == [UNREACHABLE_MESSAGE]
        assert len(device.errors) == 1

    async def test_given_a_connected_device_when_polls_fail_then_a_few_are_tolerated(
        self,
    ):
        device = await connected_device()
        await device._poll_once()
        device._client.error = MiioTimeoutError("timeout")

        await device._poll_once()
        await device._poll_once()
        available_after_two_failures = device.available
        await device._poll_once()

        assert available_after_two_failures
        assert not device.available

    async def test_given_repeated_failures_when_polled_then_it_is_reported_once(
        self,
    ):
        device = await connected_device()
        device._client.error = MiioTimeoutError("timeout")

        await device._poll_once()
        await device._poll_once()

        assert len(device.unavailable_messages) == 1

    async def test_given_no_client_when_polled_then_nothing_happens(self):
        device = SampleDevice()

        await device._poll_once()

        assert device.capabilities == {}


class TestMiioPollingDeviceOnSettings:
    async def test_given_changed_settings_when_applied_then_the_client_is_replaced(
        self,
    ):
        old = FakeClient()
        device = await connected_device(client=old)
        device.next_client = FakeClient()
        device._failures = 2
        device._connected = True

        result = await device.on_settings({}, SETTINGS, ("address",))
        await device.on_uninit()

        assert result is None
        assert old.closed
        assert device._failures == 0
        assert device._connected is False

    async def test_given_an_invalid_token_when_settings_change_then_it_is_rejected(
        self,
    ):
        device = await connected_device()
        device.next_client = InvalidTokenError("token_invalid")

        with pytest.raises(Exception, match="token_invalid"):
            await device.on_settings({}, SETTINGS, ("token",))


class TestMiioPollingDeviceOnDeleted:
    async def test_given_a_polling_device_when_deleted_then_it_stops_and_closes(
        self,
    ):
        device = SampleDevice()
        await device.on_init()

        await device.on_deleted()

        assert device.next_client.closed
        assert device._poll_task is None


class TestMiioPollingDeviceRequireClient:
    async def test_given_no_client_when_required_then_it_fails(self):
        device = SampleDevice()

        with pytest.raises(MiioError):
            device._require_client()


class TestMiioPollingDeviceCurrent:
    async def test_given_stored_and_missing_values_when_read_then_default_applies(
        self,
    ):
        device = SampleDevice(capabilities={"dim": 0.3})

        stored = device._current("dim", 1)
        fallback = device._current("other", 1)

        assert stored == 0.3
        assert fallback == 1


class RecordingClient:
    def __init__(self):
        self.calls = []

    async def set_x(self, value):
        self.calls.append(("x", value))

    async def set_power(self, on):
        self.calls.append(("power", on))


class CommandDevice(FakeHomeyMixin, MiioPollingDevice):
    commands: ClassVar[dict[str, Command]] = {"x_capability": Command("set_x", int)}

    def __init__(self, client=None, capabilities=None):
        self.setup_fake(capabilities=capabilities)
        self._client = client

    async def set_level(self, client, dim):
        client.calls.append(("level", dim))


class TestMiioPollingDeviceRegisterListeners:
    def test_given_commands_when_registering_then_each_capability_has_a_listener(
        self,
    ):
        device = CommandDevice()

        device.register_listeners()

        assert set(device.listeners) == {"x_capability"}

    async def test_given_a_command_when_it_changes_then_the_converted_value_is_sent(
        self,
    ):
        client = RecordingClient()
        device = CommandDevice(client)
        device.register_listeners()

        await device.listeners["x_capability"]("7")

        assert client.calls == [("x", 7)]

    async def test_given_no_client_when_a_command_arrives_then_it_fails(self):
        device = CommandDevice()
        device.register_listeners()

        with pytest.raises(MiioError):
            await device.listeners["x_capability"]("7")

    def test_given_power_and_level_when_registering_then_one_listener_covers_both(
        self,
    ):
        device = CommandDevice()

        device.register_power_and_level()

        assert set(device.listeners) == {("onoff", "dim")}

    async def test_given_no_level_support_when_the_level_is_set_then_it_fails(
        self,
    ):
        with pytest.raises(NotImplementedError):
            await SampleDevice().set_level(None, 0.5)


class TestMiioPollingDevicePowerAndLevel:
    async def test_given_a_device_that_is_off_when_turned_on_then_power_is_sent(self):
        client = RecordingClient()
        device = CommandDevice(client, {"onoff": False})

        await device._on_power_and_level({"onoff": True})

        assert client.calls == [("power", True)]
        assert device.capabilities["onoff"] is True

    async def test_given_a_device_that_is_on_when_turned_on_then_nothing_is_sent(self):
        client = RecordingClient()
        device = CommandDevice(client, {"onoff": True})

        await device._on_power_and_level({"onoff": True})

        assert client.calls == []

    async def test_given_a_device_that_is_on_when_dimmed_then_only_the_level_is_set(
        self,
    ):
        client = RecordingClient()
        device = CommandDevice(client, {"onoff": True})

        await device._on_power_and_level({"dim": 0.4})

        assert client.calls == [("level", 0.4)]

    async def test_given_a_device_that_is_off_when_dimmed_then_it_turns_on_first(
        self,
    ):
        client = RecordingClient()
        device = CommandDevice(client, {"onoff": False})

        await device._on_power_and_level({"dim": 0.8})

        assert client.calls == [("power", True), ("level", 0.8)]

    async def test_given_a_device_that_is_on_when_dimmed_to_zero_then_it_turns_off(
        self,
    ):
        client = RecordingClient()
        device = CommandDevice(client, {"onoff": True})

        await device._on_power_and_level({"dim": 0})

        assert client.calls == [("power", False)]
        assert device.capabilities["onoff"] is False
