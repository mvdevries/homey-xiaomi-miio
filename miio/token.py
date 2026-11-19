import re

from .errors import InvalidTokenError

TOKEN_HEX_PATTERN = re.compile(r"[0-9a-fA-F]{32}")
TOKEN_SIZE = 16


def token_from_hex(value: str) -> bytes:
    if not TOKEN_HEX_PATTERN.fullmatch(value):
        raise InvalidTokenError("token_invalid")
    return bytes.fromhex(value)
