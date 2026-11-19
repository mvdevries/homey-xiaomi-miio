import pytest
from app.application.bedside_lamp_service import BedsideLampService
from app.domain import bedside_lamp

from tests.support.fake_transport import FakeTransport


class TestBedsideLampService:
    async def test_given_a_lamp_when_state_is_read_then_all_properties_are_asked(
        self,
    ):
        transport = FakeTransport(["on", 80, 3, 0, 120, 90, 4000])

        state = await BedsideLampService(transport).get_state()

        assert transport.calls == [("get_prop", bedside_lamp.STATE_PROPERTIES)]
        assert state.brightness == 80

    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            (lambda lamp: lamp.set_power(True), ("set_power", ["on", "smooth", 500])),
            (lambda lamp: lamp.set_power(False), ("set_power", ["off", "smooth", 500])),
            (lambda lamp: lamp.set_brightness(40), ("set_bright", [40, "smooth", 500])),
            (lambda lamp: lamp.set_hsv(10, 20), ("set_hsv", [10, 20, "smooth", 500])),
            (
                lambda lamp: lamp.set_color_temperature(3000),
                ("set_ct_abx", [3000, "smooth", 500]),
            ),
        ],
    )
    async def test_given_a_command_when_it_is_sent_then_a_smooth_transition_is_used(
        self, action, expected
    ):
        transport = FakeTransport()

        await action(BedsideLampService(transport))

        assert transport.calls == [expected]

    def test_given_a_service_when_closed_then_the_transport_is_closed(self):
        transport = FakeTransport()

        BedsideLampService(transport).close()

        assert transport.closed
