import pytest
from app.domain.errors import InvalidTokenError
from app.domain.token import token_from_hex

VALID_TOKEN = "0123456789abcdef0123456789ABCDEF"


class TestTokenFromHex:
    def test_given_a_valid_hex_token_when_converted_then_the_bytes_are_returned(self):
        token = token_from_hex(VALID_TOKEN)

        assert token == bytes.fromhex(VALID_TOKEN)

    @pytest.mark.parametrize(
        "value",
        ["", "xyz", VALID_TOKEN[:-1], VALID_TOKEN + "0", "g" * 32, " " + VALID_TOKEN],
    )
    def test_given_an_invalid_token_when_converted_then_it_is_rejected(self, value):
        with pytest.raises(InvalidTokenError, match="token_invalid"):
            token_from_hex(value)
