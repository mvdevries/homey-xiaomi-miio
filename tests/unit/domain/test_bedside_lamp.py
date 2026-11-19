import pytest
from app.domain.bedside_lamp import (
    LampState,
    brightness_to_dim,
    degrees_to_hue,
    dim_to_brightness,
    hue_to_degrees,
    kelvin_to_temperature,
    parse_state,
    percent_to_saturation,
    saturation_to_percent,
    state_to_capabilities,
    temperature_to_kelvin,
)
from app.domain.errors import MalformedPacketError


class TestDimToBrightness:
    @pytest.mark.parametrize(
        ("dim", "brightness"), [(0.0, 1), (0.004, 1), (0.5, 50), (1.0, 100), (2.0, 100)]
    )
    def test_given_a_dim_value_when_converted_then_the_brightness_is_clamped(
        self, dim, brightness
    ):
        result = dim_to_brightness(dim)

        assert result == brightness


class TestBrightnessToDim:
    def test_given_a_brightness_when_converted_then_the_dim_value_is_clamped(self):
        within_range = brightness_to_dim(50)
        above_range = brightness_to_dim(500)

        assert within_range == 0.5
        assert above_range == 1.0


class TestHueConversion:
    def test_given_hue_values_when_converted_then_degrees_are_clamped(self):
        top = hue_to_degrees(1.0)
        below = hue_to_degrees(-1)

        assert top == 359
        assert below == 0

    def test_given_degrees_when_converted_then_the_hue_is_returned(self):
        hue = degrees_to_hue(359)

        assert hue == 1.0

    def test_given_degrees_when_round_tripped_then_they_are_unchanged(self):
        degrees = hue_to_degrees(degrees_to_hue(180))

        assert degrees == 180


class TestSaturationConversion:
    def test_given_saturation_values_when_converted_then_percent_is_clamped(self):
        within_range = saturation_to_percent(0.5)
        above_range = saturation_to_percent(3)

        assert within_range == 50
        assert above_range == 100

    def test_given_a_percentage_when_converted_then_the_saturation_is_returned(self):
        saturation = percent_to_saturation(25)

        assert saturation == 0.25


class TestTemperatureConversion:
    def test_given_temperature_values_when_converted_then_kelvin_covers_the_range(
        self,
    ):
        coldest = temperature_to_kelvin(0.0)
        warmest = temperature_to_kelvin(1.0)
        beyond = temperature_to_kelvin(5)

        assert coldest == 6500
        assert warmest == 1700
        assert beyond == 1700

    def test_given_kelvin_values_when_converted_then_the_temperature_is_clamped(self):
        warmest = kelvin_to_temperature(1700)
        coldest = kelvin_to_temperature(6500)
        beyond = kelvin_to_temperature(9000)

        assert warmest == 1.0
        assert coldest == 0.0
        assert beyond == 0.0


class TestParseState:
    def test_given_a_color_mode_result_when_parsed_then_the_state_is_returned(self):
        state = parse_state(["on", 80, 3, 16711680, 120, 90, 4000])

        assert state == LampState(True, 80, "color", 120, 90, 4000)

    def test_given_a_temperature_mode_result_when_parsed_then_the_mode_is_temperature(
        self,
    ):
        state = parse_state(["off", 10, 2, 0, 0, 0, 2700])

        assert state.power is False
        assert state.light_mode == "temperature"

    @pytest.mark.parametrize("result", [None, [], ["on"], "on"])
    def test_given_an_unexpected_result_when_parsed_then_it_is_rejected(self, result):
        with pytest.raises(MalformedPacketError):
            parse_state(result)


class TestStateToCapabilities:
    def test_given_a_state_when_mapped_then_all_capabilities_are_returned(self):
        state = LampState(True, 50, "color", 359, 100, 1700)

        capabilities = state_to_capabilities(state)

        assert capabilities == {
            "onoff": True,
            "dim": 0.5,
            "light_hue": 1.0,
            "light_saturation": 1.0,
            "light_temperature": 1.0,
            "light_mode": "color",
        }
