from app.endpoints.pairing_driver import MiioDriver
from pytest_bdd import parsers, then, when

from tests.support.fake_miio_devices import DEVICE_ADDRESS, DEVICE_TOKEN_HEX


def pair(scenario, **overrides):
    data = {
        "name": "Test device",
        "address": DEVICE_ADDRESS,
        "token": DEVICE_TOKEN_HEX,
        "polling": 10,
    } | overrides
    scenario.pairing_result = None
    scenario.pairing_error = None
    try:
        scenario.pairing_result = scenario.call(MiioDriver().validate_device(data))
    except Exception as error:
        scenario.pairing_error = error


@when(parsers.parse('I pair the device named "{name}" with its address and token'))
def i_pair_the_device_with_its_details(scenario, name):
    pair(scenario, name=name)


@when(parsers.parse('I pair the device with the token "{token}"'))
def i_pair_the_device_with_a_token(scenario, token):
    pair(scenario, token=token)


@when("I pair a device without a name")
def i_pair_a_device_without_a_name(scenario):
    pair(scenario, name="")


@when(parsers.parse("I pair the device with a polling interval of {seconds:d} seconds"))
def i_pair_the_device_with_a_polling_interval(scenario, seconds):
    pair(scenario, polling=seconds)


@then("the pairing is accepted")
def the_pairing_is_accepted(scenario):
    assert scenario.pairing_error is None
    assert scenario.pairing_result is not None


@then(parsers.parse('the pairing is rejected with "{code}"'))
def the_pairing_is_rejected(scenario, code):
    assert scenario.pairing_result is None
    assert str(scenario.pairing_error) == code


@then(parsers.parse('the paired device is called "{name}"'))
def the_paired_device_is_called(scenario, name):
    assert scenario.pairing_result["name"] == name


@then(parsers.parse("the paired device is polled every {seconds:d} seconds"))
def the_paired_device_is_polled_every(scenario, seconds):
    assert scenario.pairing_result["settings"]["polling"] == seconds
