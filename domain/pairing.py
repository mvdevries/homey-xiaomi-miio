import re

from .polling import polling_seconds

TOKEN_PATTERN = re.compile(r"[0-9a-fA-F]{32}")


class InvalidPairingInputError(Exception):
    pass


def build_pairing_device(data: dict) -> dict:
    name = str(data.get("name", "")).strip()
    address = str(data.get("address", "")).strip()
    token = str(data.get("token", "")).strip()
    if not name or not address:
        raise InvalidPairingInputError("name_and_address_required")
    if not TOKEN_PATTERN.fullmatch(token):
        raise InvalidPairingInputError("token_invalid")
    return {
        "name": name,
        "data": {"id": address},
        "settings": {
            "address": address,
            "token": token,
            "polling": polling_seconds(data.get("polling")),
        },
    }
