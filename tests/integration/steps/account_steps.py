from pytest_bdd import given, parsers, then, when

from tests.support import load_module
from tests.support.fake_miio_devices import DEVICE_TOKEN_HEX
from tests.support.loop_harness import wait_until


def account_driver(scenario):
    if scenario.account_driver is None:
        module = load_module("drivers.yeelink-light-bslamp2.driver")
        scenario.account_driver = module.homey_export()
    return scenario.account_driver


def record(scenario, action):
    scenario.account_error = None
    try:
        return scenario.call(action)
    except Exception as error:
        scenario.account_error = error
        return None


@given(
    parsers.parse('a Xiaomi account with a bedside lamp named "{name}" at {address}')
)
def an_account_with_a_bedside_lamp(scenario, name, address):
    scenario.cloud.add_device(
        "de",
        did="1001",
        name=name,
        model="yeelink.light.bslamp2",
        token=DEVICE_TOKEN_HEX,
        localip=address,
    )


@given(parsers.parse('the same Xiaomi account has a smart speaker named "{name}"'))
def the_account_has_a_speaker(scenario, name):
    scenario.cloud.add_device(
        "de",
        did="1002",
        name=name,
        model="xiaomi.wifispeaker.l09g",
        token="ff" * 16,
        localip="192.0.2.30",
    )


@given("the Xiaomi account does not hand out a service token")
def the_account_hands_out_no_token(scenario):
    scenario.cloud.refuse_service_token = True


@given("the Xiaomi cloud is down")
def the_cloud_is_down(scenario):
    scenario.cloud.login_status = 500


@given("I started logging in with the Xiaomi account")
@when("I start logging in with the Xiaomi account")
def i_start_logging_in(scenario):
    scenario.account_login = record(
        scenario, account_driver(scenario).start_account_login()
    )


@when("the user scans the QR code in the Mi Home app")
def i_scan_the_qr_code(scenario):
    scenario.cloud.scanned = True
    wait_until(lambda: login_state(scenario) in ("signed_in", "failed"))


@when("I ask for the devices of the account")
def i_ask_for_the_devices(scenario):
    scenario.account_devices = record(
        scenario, account_driver(scenario).account_devices()
    )


def login_state(scenario):
    return scenario.call(account_driver(scenario).account_login_status())["state"]


@then("I get a QR code to scan")
def i_get_a_qr_code(scenario):
    assert scenario.account_login["qrImage"].startswith("data:image/png;base64,")


@then("the login is waiting for the scan")
def the_login_is_waiting(scenario):
    assert login_state(scenario) == "pending"


@then("the login is complete")
def the_login_is_complete(scenario):
    assert login_state(scenario) == "signed_in"


@then("the login has failed")
def the_login_has_failed(scenario):
    assert login_state(scenario) == "failed"


@then(parsers.parse('I see only the device "{name}" at {address} with its token'))
def i_see_only_the_device(scenario, name, address):
    devices = scenario.call(account_driver(scenario).account_devices())
    assert [(d["name"], d["address"], d["token"]) for d in devices] == [
        (name, address, DEVICE_TOKEN_HEX)
    ]


@then(parsers.parse('the request is rejected with "{code}"'))
def the_request_is_rejected(scenario, code):
    assert str(scenario.account_error) == code
