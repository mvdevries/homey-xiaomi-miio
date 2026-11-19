import pytest
from app.domain.standing_fan import (
    FanState,
    dim_to_speed,
    parse_state,
    speed_to_dim,
    state_to_capabilities,
)

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


class TestParseState:
    def test_given_direct_mode_properties_when_parsed_then_the_state_is_returned(self):
        state = parse_state(PROPERTIES)

        assert state == FanState(True, 40, False, True, 120, False, True, 1)

    def test_given_a_natural_level_when_parsed_then_the_natural_mode_is_active(self):
        state = parse_state(PROPERTIES | {"speed_level": 0, "natural_level": 55})

        assert state.natural_mode is True
        assert state.speed == 55

    def test_given_no_values_when_parsed_then_the_defaults_are_used(self):
        values = dict.fromkeys(PROPERTIES)

        state = parse_state(values)

        assert state == FanState(False, 0, False, False, 30, False, False, 0)


class TestStateToCapabilities:
    def test_given_a_state_when_mapped_then_all_capabilities_are_returned(self):
        state = parse_state(PROPERTIES)

        capabilities = state_to_capabilities(state)

        assert capabilities == {
            "onoff": True,
            "dim": 0.4,
            "fan_oscillating": True,
            "fan_angle": 120,
            "led_display": True,
            "buzzer_enabled": True,
            "locked": False,
        }


class TestDimToSpeed:
    @pytest.mark.parametrize(
        ("dim", "speed"), [(0.0, 1), (0.004, 1), (0.5, 50), (1.0, 100), (3.0, 100)]
    )
    def test_given_a_dim_value_when_converted_then_the_speed_is_clamped(
        self, dim, speed
    ):
        result = dim_to_speed(dim)

        assert result == speed


class TestSpeedToDim:
    def test_given_a_speed_when_converted_then_the_dim_value_is_clamped(self):
        within_range = speed_to_dim(25)
        above_range = speed_to_dim(500)

        assert within_range == 0.25
        assert above_range == 1.0
