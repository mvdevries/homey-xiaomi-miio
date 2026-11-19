import pytest
from app.application.humidifier_service import HumidifierService
from app.domain import humidifier
from app.domain.errors import MiioDeviceError

from tests.support.fake_transport import FakeTransport

PROPERTIES = {
    "power": "on",
    "mode": "high",
    "humidity": 44,
    "temp_dec": 213,
    "temperature": None,
    "buzzer": "off",
    "led_b": "1",
    "child_lock": "on",
    "limit_hum": 47,
    "dry": "off",
}


class TestHumidifierService:
    async def test_given_a_humidifier_when_state_is_read_then_every_property_is_asked(
        self,
    ):
        transport = FakeTransport(properties=PROPERTIES)

        state = await HumidifierService(transport).get_state()

        assert transport.calls == [("get_prop", humidifier.STATE_PROPERTIES)]
        assert state.humidity == 44

    async def test_given_an_unsupported_optional_property_when_read_then_it_is_none(
        self,
    ):
        transport = FakeTransport(properties=PROPERTIES, failing={"dry": -1})

        state = await HumidifierService(transport).get_state()

        assert state.dry is False

    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            (lambda device: device.set_power(True), ("set_power", ["on"])),
            (lambda device: device.set_power(False), ("set_power", ["off"])),
            (lambda device: device.set_mode("auto"), ("set_mode", ["auto"])),
            (lambda device: device.set_target_humidity(44), ("set_limit_hum", [40])),
            (lambda device: device.set_dry(True), ("set_dry", ["on"])),
            (lambda device: device.set_led_brightness(2), ("set_led_b", ["2"])),
            (lambda device: device.set_buzzer(False), ("set_buzzer", ["off"])),
            (lambda device: device.set_child_lock(True), ("set_child_lock", ["on"])),
        ],
    )
    async def test_given_a_command_when_it_is_sent_then_the_matching_call_is_made(
        self, action, expected
    ):
        transport = FakeTransport()

        await action(HumidifierService(transport))

        assert transport.calls == [expected]

    async def test_given_a_device_that_is_off_when_mode_is_set_then_it_powers_on_first(
        self,
    ):
        transport = FakeTransport(failing_methods={"set_mode": [-6011]})

        await HumidifierService(transport).set_mode("high")

        assert [call[0] for call in transport.calls] == [
            "set_mode",
            "set_power",
            "set_mode",
        ]

    async def test_given_another_device_error_when_the_mode_is_set_then_it_is_raised(
        self,
    ):
        transport = FakeTransport(failing_methods={"set_mode": [-1]})

        with pytest.raises(MiioDeviceError):
            await HumidifierService(transport).set_mode("high")

    def test_given_a_service_when_closed_then_the_transport_is_closed(self):
        transport = FakeTransport()

        HumidifierService(transport).close()

        assert transport.closed
