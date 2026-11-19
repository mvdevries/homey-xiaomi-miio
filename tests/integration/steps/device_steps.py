from pytest_bdd import given, parsers, then, when

from tests.support.fake_miio_devices import (
    FakeBedsideLamp,
    FakeHumidifier,
    FakeStandingFan,
)

LEVEL_PROPERTIES = {"lamp": "bright", "fan": "speed_level"}
ON_VALUES = ("on", 1, 2)


def is_on(value):
    return value in ON_VALUES


def expected_switch(state):
    return state == "on"


@given(parsers.parse("a bedside lamp that is on at {brightness:d}% brightness"))
def a_bedside_lamp_that_is_on(scenario, brightness):
    lamp = FakeBedsideLamp()
    lamp.properties.update(power="on", bright=brightness)
    scenario.add_fake_device("lamp", lamp)


@given("a standing fan that is switched off")
def a_standing_fan_that_is_switched_off(scenario):
    scenario.add_fake_device("fan", FakeStandingFan())


@given(parsers.parse("a standing fan that blows natural wind at {speed:d}% speed"))
def a_standing_fan_with_natural_wind(scenario, speed):
    fan = FakeStandingFan()
    fan.properties.update(power="on", speed_level=0, natural_level=speed)
    scenario.add_fake_device("fan", fan)


@given("a humidifier that is switched off")
def a_humidifier_that_is_switched_off(scenario):
    scenario.add_fake_device("humidifier", FakeHumidifier())


@given("the device does not answer")
@when("the device does not answer anymore")
def the_device_does_not_answer(scenario):
    scenario.fake.silent = True


@when("the device answers again")
def the_device_answers_again(scenario):
    scenario.fake.silent = False


@when(parsers.parse("someone switches the device {state} at the device itself"))
def someone_switches_the_device(scenario, state):
    scenario.fake.properties["power"] = state


@then(parsers.parse("the device is switched {state}"))
def the_device_is_switched(scenario, state):
    assert is_on(scenario.fake.properties["power"]) is expected_switch(state)


@then(parsers.parse("the device has a level of {percent:d}%"))
def the_device_has_a_level(scenario, percent):
    assert scenario.fake.properties[LEVEL_PROPERTIES[scenario.kind]] == percent


@then(parsers.parse("the device has a colour temperature of {kelvin:d} kelvin"))
def the_device_has_a_colour_temperature(scenario, kelvin):
    assert scenario.fake.properties["ct"] == kelvin
    assert scenario.fake.properties["color_mode"] == 2


@then("the device shines in the colour red")
def the_device_shines_red(scenario):
    assert scenario.fake.properties["hue"] == 0
    assert scenario.fake.properties["sat"] == 100


@then(parsers.parse("the device blows natural wind at {speed:d}% speed"))
def the_device_blows_natural_wind(scenario, speed):
    assert scenario.fake.properties["natural_level"] == speed
    assert scenario.fake.properties["speed_level"] == 0


@then(parsers.parse("the device oscillates over {angle:d} degrees"))
def the_device_oscillates_over(scenario, angle):
    assert scenario.fake.properties["angle_enable"] == "on"
    assert scenario.fake.properties["angle"] == angle


@then(parsers.parse("the device is set to an angle of {angle:d} degrees"))
def the_device_is_set_to_an_angle(scenario, angle):
    assert scenario.fake.properties["angle"] == angle


@then("the device does not oscillate")
def the_device_does_not_oscillate(scenario):
    assert scenario.fake.properties["angle_enable"] == "off"


@then(parsers.parse("the device has its LED display switched {state}"))
def the_device_has_its_led_display(scenario, state):
    brightness = int(scenario.fake.properties["led_b"])
    assert (brightness != 2) is expected_switch(state)


@then(parsers.parse("the device has its buzzer switched {state}"))
def the_device_has_its_buzzer(scenario, state):
    assert is_on(scenario.fake.properties["buzzer"]) is expected_switch(state)


@then(parsers.parse("the device has its child lock switched {state}"))
def the_device_has_its_child_lock(scenario, state):
    assert is_on(scenario.fake.properties["child_lock"]) is expected_switch(state)


@then(parsers.parse('the device runs in the mode "{mode}"'))
def the_device_runs_in_the_mode(scenario, mode):
    assert scenario.fake.properties["mode"] == mode


@then(parsers.parse("the device aims for a humidity of {humidity:d}%"))
def the_device_aims_for_a_humidity(scenario, humidity):
    assert scenario.fake.properties["limit_hum"] == humidity


@then("the device has its dry mode switched on")
def the_device_has_its_dry_mode(scenario):
    assert scenario.fake.properties["dry"] == "on"
