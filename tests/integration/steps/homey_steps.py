from pytest_bdd import given, parsers, then, when

from tests.support.homey_devices import set_capability_from_homey
from tests.support.loop_harness import wait_until

PERCENT = 100
TOLERANCE = 0.005


def homey_sets(scenario, capability, value):
    scenario.call(set_capability_from_homey(scenario.homey_device, capability, value))


def homey_shows(scenario, capability, expected):
    wait_until(lambda: scenario.homey_device.capabilities.get(capability) == expected)


def switch_value(state):
    return state == "on"


@given("the device is added to Homey")
@when("the device is added to Homey")
def the_device_is_added_to_homey(scenario):
    scenario.add_device_to_homey()


@when(parsers.parse("I turn the device {state} in Homey"))
def i_turn_the_device(scenario, state):
    homey_sets(scenario, "onoff", switch_value(state))


@when(parsers.parse("I dim the device to {percent:d}% in Homey"))
def i_dim_the_device(scenario, percent):
    homey_sets(scenario, "dim", percent / PERCENT)


@when("I choose the warmest light in Homey")
def i_choose_the_warmest_light(scenario):
    homey_sets(scenario, "light_mode", "temperature")
    homey_sets(scenario, "light_temperature", 1.0)


@when("I choose the colour red in Homey")
def i_choose_the_colour_red(scenario):
    homey_sets(scenario, "light_mode", "color")
    homey_sets(scenario, "light_hue", 0.0)
    homey_sets(scenario, "light_saturation", 1.0)


@when(parsers.parse("I turn the oscillation {state} in Homey"))
def i_turn_the_oscillation(scenario, state):
    homey_sets(scenario, "fan_oscillating", switch_value(state))


@when(parsers.parse("I set the oscillation angle to {angle:d} degrees in Homey"))
def i_set_the_oscillation_angle(scenario, angle):
    homey_sets(scenario, "fan_angle", float(angle))


@when(parsers.parse("I turn the LED display {state} in Homey"))
def i_turn_the_led_display(scenario, state):
    homey_sets(scenario, "led_display", switch_value(state))


@when(parsers.parse("I turn the buzzer {state} in Homey"))
def i_turn_the_buzzer(scenario, state):
    homey_sets(scenario, "buzzer_enabled", switch_value(state))


@when(parsers.parse("I turn the child lock {state} in Homey"))
def i_turn_the_child_lock(scenario, state):
    homey_sets(scenario, "locked", switch_value(state))


@when(parsers.parse('I choose the mode "{mode}" in Homey'))
def i_choose_the_mode(scenario, mode):
    homey_sets(scenario, "humidifier_mode", mode)


@when(parsers.parse("I set the target humidity to {humidity:d}% in Homey"))
def i_set_the_target_humidity(scenario, humidity):
    homey_sets(scenario, "humidifier_target_humidity", str(humidity))


@when(parsers.parse("I turn the dry mode {state} in Homey"))
def i_turn_the_dry_mode(scenario, state):
    homey_sets(scenario, "humidifier_dry", switch_value(state))


@then(parsers.parse("Homey shows the device as {state}"))
def homey_shows_the_device(scenario, state):
    homey_shows(scenario, "onoff", switch_value(state))


@then(parsers.parse("Homey shows a level of {percent:d}%"))
def homey_shows_a_level(scenario, percent):
    wait_until(
        lambda: (
            abs(scenario.homey_device.capabilities.get("dim", -1) - percent / PERCENT)
            < TOLERANCE
        )
    )


@then(parsers.parse("Homey shows the oscillation as {state}"))
def homey_shows_the_oscillation(scenario, state):
    homey_shows(scenario, "fan_oscillating", switch_value(state))


@then(parsers.parse("Homey shows an oscillation angle of {angle:d} degrees"))
def homey_shows_an_oscillation_angle(scenario, angle):
    homey_shows(scenario, "fan_angle", angle)


@then(parsers.parse("Homey shows the LED display as {state}"))
def homey_shows_the_led_display(scenario, state):
    homey_shows(scenario, "led_display", switch_value(state))


@then(parsers.parse("Homey shows the buzzer as {state}"))
def homey_shows_the_buzzer(scenario, state):
    homey_shows(scenario, "buzzer_enabled", switch_value(state))


@then(parsers.parse("Homey shows the child lock as {state}"))
def homey_shows_the_child_lock(scenario, state):
    homey_shows(scenario, "locked", switch_value(state))


@then(parsers.parse("Homey shows a humidity of {humidity:d}%"))
def homey_shows_a_humidity(scenario, humidity):
    homey_shows(scenario, "measure_humidity", humidity)


@then(parsers.parse("Homey shows a temperature of {temperature:f} degrees"))
def homey_shows_a_temperature(scenario, temperature):
    homey_shows(scenario, "measure_temperature", temperature)


@then(parsers.parse('Homey shows the mode "{mode}"'))
def homey_shows_the_mode(scenario, mode):
    homey_shows(scenario, "humidifier_mode", mode)


@then(parsers.parse("Homey shows a target humidity of {humidity:d}%"))
def homey_shows_a_target_humidity(scenario, humidity):
    homey_shows(scenario, "humidifier_target_humidity", str(humidity))


@then("Homey marks the device as unavailable")
def homey_marks_the_device_as_unavailable(scenario):
    wait_until(lambda: not scenario.homey_device.available)


@then("Homey marks the device as available")
def homey_marks_the_device_as_available(scenario):
    wait_until(lambda: scenario.homey_device.available)
