import re

from homey.driver import Driver
from homey.pair_session import PairSession

from .errors import MiioError
from .polling import polling_seconds
from .probe import probe_device

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


class MiioDriver(Driver):
    async def on_pair(self, session: PairSession) -> None:
        session.set_handler("validate_device", self.validate_device)

    async def validate_device(self, data: dict) -> dict:
        try:
            device = build_pairing_device(data)
        except InvalidPairingInputError as error:
            raise Exception(str(error)) from error
        await self.verify_reachable(device["settings"])
        return device

    async def verify_reachable(self, settings: dict) -> None:
        try:
            await probe_device(settings["address"], settings["token"])
        except MiioError as error:
            raise Exception("device_unreachable") from error
