import pytest

from tests.support import load_module

driver = load_module("drivers/yeelink-light-bslamp2/driver.py", "bslamp2_driver")

VALID_TOKEN = "0123456789abcdef0123456789ABCDEF"


def pairing_input(**overrides):
    base = {
        "name": "Lamp",
        "address": "192.0.2.10",
        "token": VALID_TOKEN,
        "polling": 10,
    }
    return base | overrides


def test_builds_device_from_valid_input():
    device = driver.build_pairing_device(pairing_input())

    assert device["name"] == "Lamp"
    assert device["data"] == {"id": "192.0.2.10"}
    assert device["settings"] == {
        "address": "192.0.2.10",
        "token": VALID_TOKEN,
        "polling": 10,
    }


def test_strips_whitespace_around_input():
    device = driver.build_pairing_device(
        pairing_input(name=" Lamp ", address=" 192.0.2.10 ")
    )

    assert device["name"] == "Lamp"
    assert device["settings"]["address"] == "192.0.2.10"


def test_raises_polling_to_the_minimum():
    device = driver.build_pairing_device(pairing_input(polling=1))

    assert device["settings"]["polling"] == driver.MIN_POLLING_SECONDS


def test_uses_default_polling_when_missing():
    device = driver.build_pairing_device(pairing_input(polling=None))

    assert device["settings"]["polling"] == driver.DEFAULT_POLLING_SECONDS


@pytest.mark.parametrize("field", ["name", "address"])
def test_rejects_missing_name_or_address(field):
    with pytest.raises(
        driver.InvalidPairingInputError, match="name_and_address_required"
    ):
        driver.build_pairing_device(pairing_input(**{field: " "}))


@pytest.mark.parametrize("token", ["", "xyz", VALID_TOKEN[:-1], VALID_TOKEN + "0"])
def test_rejects_invalid_token(token):
    with pytest.raises(driver.InvalidPairingInputError, match="token_invalid"):
        driver.build_pairing_device(pairing_input(token=token))


async def test_validate_device_returns_the_device():
    result = await driver.BedsideLamp2Driver().validate_device(pairing_input())

    assert result["data"] == {"id": "192.0.2.10"}


async def test_validate_device_reports_the_error_code():
    with pytest.raises(Exception, match="token_invalid"):
        await driver.BedsideLamp2Driver().validate_device(pairing_input(token="no"))


async def test_on_pair_registers_the_validate_handler():
    handlers = {}

    class FakeSession:
        def set_handler(self, event, handler):
            handlers[event] = handler

    await driver.BedsideLamp2Driver().on_pair(FakeSession())

    assert "validate_device" in handlers
