import re

from homey.driver import Driver
from homey.pair_session import PairSession

TOKEN_PATTERN = re.compile(r"[0-9a-fA-F]{32}")
DEFAULT_POLLING_SECONDS = 10
MIN_POLLING_SECONDS = 5


class InvalidPairingInputError(Exception):
    pass


def build_pairing_device(data: dict) -> dict:
    name = str(data.get("name", "")).strip()
    address = str(data.get("address", "")).strip()
    token = str(data.get("token", "")).strip()
    polling = int(data.get("polling") or DEFAULT_POLLING_SECONDS)
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
            "polling": max(polling, MIN_POLLING_SECONDS),
        },
    }


class BedsideLamp2Driver(Driver):
    async def on_pair(self, session: PairSession) -> None:
        session.set_handler("validate_device", self.validate_device)

    async def validate_device(self, data: dict) -> dict:
        try:
            return build_pairing_device(data)
        except InvalidPairingInputError as error:
            raise Exception(str(error)) from error


homey_export = BedsideLamp2Driver
