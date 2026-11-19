import pytest
from app.domain import pairing
from app.domain.polling import DEFAULT_POLLING_SECONDS, MIN_POLLING_SECONDS

VALID_TOKEN = "0123456789abcdef0123456789ABCDEF"


def pairing_input(**overrides):
    base = {
        "name": "Lamp",
        "address": "192.0.2.10",
        "token": VALID_TOKEN,
        "polling": 10,
    }
    return base | overrides


class TestBuildPairingDevice:
    def test_given_valid_input_when_built_then_the_device_is_returned(self):
        device = pairing.build_pairing_device(pairing_input())

        assert device["name"] == "Lamp"
        assert device["data"] == {"id": "192.0.2.10"}
        assert device["settings"] == {
            "address": "192.0.2.10",
            "token": VALID_TOKEN,
            "polling": 10,
        }

    def test_given_whitespace_around_input_when_built_then_it_is_stripped(self):
        device = pairing.build_pairing_device(
            pairing_input(name=" Lamp ", address=" 192.0.2.10 ")
        )

        assert device["name"] == "Lamp"
        assert device["settings"]["address"] == "192.0.2.10"

    def test_given_a_too_low_polling_when_built_then_it_is_raised_to_the_minimum(self):
        device = pairing.build_pairing_device(pairing_input(polling=1))

        assert device["settings"]["polling"] == MIN_POLLING_SECONDS

    def test_given_no_polling_when_built_then_the_default_is_used(self):
        device = pairing.build_pairing_device(pairing_input(polling=None))

        assert device["settings"]["polling"] == DEFAULT_POLLING_SECONDS

    @pytest.mark.parametrize("field", ["name", "address"])
    def test_given_a_blank_name_or_address_when_built_then_it_is_rejected(self, field):
        with pytest.raises(
            pairing.InvalidPairingInputError, match="name_and_address_required"
        ):
            pairing.build_pairing_device(pairing_input(**{field: " "}))

    @pytest.mark.parametrize("token", ["", "xyz", VALID_TOKEN[:-1], VALID_TOKEN + "0"])
    def test_given_an_invalid_token_when_built_then_it_is_rejected(self, token):
        with pytest.raises(pairing.InvalidPairingInputError, match="token_invalid"):
            pairing.build_pairing_device(pairing_input(token=token))
