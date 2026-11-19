import pytest
from app.application.standing_fan_service import StandingFanService
from app.domain import standing_fan

from tests.support.fake_transport import FakeTransport

PROPERTIES = {
    "power": "on",
    "angle": 118,
    "angle_enable": "on",
    "speed_level": 40,
    "natural_level": 0,
    "child_lock": "off",
    "buzzer": 2,
    "led_b": 1,
}


class TestStandingFanService:
    async def test_given_a_fan_when_the_state_is_requested_then_every_property_is_read(
        self,
    ):
        transport = FakeTransport(properties=PROPERTIES)

        state = await StandingFanService(transport).get_state()

        assert transport.calls == [("get_prop", standing_fan.STATE_PROPERTIES)]
        assert state.speed == 40

    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            (lambda fan: fan.set_power(True), ("set_power", ["on"])),
            (lambda fan: fan.set_power(False), ("set_power", ["off"])),
            (lambda fan: fan.set_speed(30), ("set_speed_level", [30])),
            (lambda fan: fan.set_natural_speed(30), ("set_natural_level", [30])),
            (lambda fan: fan.set_oscillating(True), ("set_angle_enable", ["on"])),
            (lambda fan: fan.set_angle(100), ("set_angle", [90])),
            (lambda fan: fan.set_led_brightness(2), ("set_led_b", [2])),
            (lambda fan: fan.set_buzzer(True), ("set_buzzer", [2])),
            (lambda fan: fan.set_buzzer(False), ("set_buzzer", [0])),
            (lambda fan: fan.set_child_lock(True), ("set_child_lock", ["on"])),
        ],
    )
    async def test_given_a_command_when_it_is_sent_then_the_matching_call_is_made(
        self, action, expected
    ):
        transport = FakeTransport()

        await action(StandingFanService(transport))

        assert transport.calls == [expected]

    def test_given_a_service_when_closed_then_the_transport_is_closed(self):
        transport = FakeTransport()

        StandingFanService(transport).close()

        assert transport.closed
