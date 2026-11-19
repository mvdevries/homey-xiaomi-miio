import pytest
from app.miio.errors import InvalidTokenError
from app.miio.token import token_from_hex

VALID_TOKEN = "0123456789abcdef0123456789ABCDEF"


def test_converts_hex_to_bytes():
    assert token_from_hex(VALID_TOKEN) == bytes.fromhex(VALID_TOKEN)


@pytest.mark.parametrize(
    "value",
    ["", "xyz", VALID_TOKEN[:-1], VALID_TOKEN + "0", "g" * 32, " " + VALID_TOKEN],
)
def test_rejects_invalid_tokens(value):
    with pytest.raises(InvalidTokenError, match="token_invalid"):
        token_from_hex(value)
