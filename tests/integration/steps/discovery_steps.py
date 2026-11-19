from app.endpoints.pairing_driver import MiioDriver
from app.infrastructure.discovery import UdpDeviceScanner
from pytest_bdd import parsers, then, when

from tests.support.loopback import LOOPBACK_ADDRESS, UNUSED_PORT

SCAN_SECONDS = 0.3


def search(scenario, monkeypatch, port):
    monkeypatch.setattr(
        "app.container.create_scanner",
        lambda: UdpDeviceScanner(
            targets=[(LOOPBACK_ADDRESS, port)], listen_seconds=SCAN_SECONDS
        ),
    )
    scenario.found_devices = scenario.call(MiioDriver().discover_devices())


@when("I search for devices on the network")
def i_search_for_devices(scenario, monkeypatch):
    search(scenario, monkeypatch, scenario.fake.port)


@when("I search for devices on an empty network")
def i_search_on_an_empty_network(scenario, monkeypatch):
    search(scenario, monkeypatch, UNUSED_PORT)


@then(parsers.parse("I find {count:d} device"))
@then(parsers.parse("I find {count:d} devices"))
def i_find_devices(scenario, count):
    assert len(scenario.found_devices) == count


@then("the found device has an address and an identifier")
def the_found_device_has_an_address_and_identifier(scenario):
    device = scenario.found_devices[0]
    assert device["address"] == LOOPBACK_ADDRESS
    assert device["deviceId"] == "00001234"
