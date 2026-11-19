from homey.driver import Driver
from homey.pair_session import PairSession

from ..container import create_discovery_service, create_pairing_service
from ..domain.errors import MiioError
from ..domain.pairing import InvalidPairingInputError


class MiioDriver(Driver):
    async def on_pair(self, session: PairSession) -> None:
        session.set_handler("validate_device", self.validate_device)
        session.set_handler("discover_devices", self.discover_devices)

    async def discover_devices(self, data: dict | None = None) -> list[dict]:
        try:
            return await create_discovery_service().discover_devices()
        except MiioError as error:
            raise Exception("discovery_failed") from error

    async def validate_device(self, data: dict) -> dict:
        try:
            return await create_pairing_service().validate_device(data)
        except InvalidPairingInputError as error:
            raise Exception(str(error)) from error
        except MiioError as error:
            raise Exception("device_unreachable") from error
