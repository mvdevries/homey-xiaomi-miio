import pytest
from app.domain.values import (
    as_int,
    as_switch,
    is_on,
    led_is_on,
    led_level,
    nearest,
)


class TestIsOn:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [("on", True), (1, True), (2, True), ("off", False), (0, False), (None, False)],
    )
    def test_given_a_device_value_when_checked_then_it_is_read_as_on_or_off(
        self, value, expected
    ):
        result = is_on(value)

        assert result is expected


class TestAsSwitch:
    def test_given_a_boolean_when_converted_then_it_becomes_a_switch_word(self):
        on = as_switch(True)
        off = as_switch(False)

        assert on == "on"
        assert off == "off"


class TestNearest:
    def test_given_options_when_the_value_is_between_then_the_closest_is_picked(self):
        closest = nearest(118, (30, 60, 90, 120, 140))

        assert closest == 120

    def test_given_a_value_below_all_options_when_picked_then_the_lowest_is_returned(
        self,
    ):
        closest = nearest(0, (30, 60))

        assert closest == 30


class TestAsInt:
    @pytest.mark.parametrize(
        ("value", "expected"), [("5", 5), (7.9, 7), (None, 0), ("x", 0)]
    )
    def test_given_a_loose_value_when_converted_then_an_integer_is_returned(
        self, value, expected
    ):
        number = as_int(value)

        assert number == expected


class TestLedIsOn:
    @pytest.mark.parametrize(("level", "expected"), [(0, True), (1, True), (2, False)])
    def test_given_a_led_level_when_checked_then_only_the_off_level_is_off(
        self, level, expected
    ):
        result = led_is_on(level)

        assert result is expected


class TestLedLevel:
    def test_given_a_boolean_when_converted_then_it_becomes_a_led_level(self):
        on = led_level(True)
        off = led_level(False)

        assert on == 0
        assert off == 2
