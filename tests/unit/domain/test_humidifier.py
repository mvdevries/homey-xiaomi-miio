from app.domain.humidifier import HumidifierState, parse_state, state_to_capabilities

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


class TestParseState:
    def test_given_device_properties_when_parsed_then_the_state_is_returned(self):
        state = parse_state(PROPERTIES)

        assert state == HumidifierState(
            True, "high", 44, 21.3, False, 1, True, 50, False
        )

    def test_given_the_temperature_property_when_parsed_then_it_is_used(self):
        state = parse_state(PROPERTIES | {"temp_dec": None, "temperature": 19})

        assert state.temperature == 19.0

    def test_given_no_temperature_when_parsed_then_the_temperature_is_none(self):
        state = parse_state(PROPERTIES | {"temp_dec": None})

        assert state.temperature is None

    def test_given_no_mode_when_parsed_then_the_mode_defaults_to_auto(self):
        state = parse_state(PROPERTIES | {"mode": None})

        assert state.mode == "auto"


class TestStateToCapabilities:
    def test_given_a_state_when_mapped_then_all_capabilities_are_returned(self):
        state = parse_state(PROPERTIES)

        capabilities = state_to_capabilities(state)

        assert capabilities == {
            "onoff": True,
            "humidifier_mode": "high",
            "humidifier_target_humidity": "50",
            "humidifier_dry": False,
            "measure_humidity": 44,
            "measure_temperature": 21.3,
            "led_display": True,
            "buzzer_enabled": False,
            "locked": True,
        }

    def test_given_no_temperature_when_mapped_then_the_temperature_is_omitted(self):
        state = parse_state(PROPERTIES | {"temp_dec": None})

        capabilities = state_to_capabilities(state)

        assert "measure_temperature" not in capabilities
