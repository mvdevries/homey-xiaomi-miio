from homey.driver import Driver
from homey.pair_session import PairSession

from ..container import (
    create_account_login_service,
    create_discovery_service,
    create_pairing_service,
)
from ..domain.errors import (
    CloudError,
    MiioError,
    NotSignedInError,
)
from ..domain.pairing import InvalidPairingInputError


class MiioDriver(Driver):
    models: tuple[str, ...] = ()
    _account_login = None

    async def on_pair(self, session: PairSession) -> None:
        session.set_handler("validate_device", self.validate_device)
        session.set_handler("discover_devices", self.discover_devices)
        session.set_handler("start_account_login", self.start_account_login)
        session.set_handler("account_login_status", self.account_login_status)
        session.set_handler("account_devices", self.account_devices)

    def _account_login_service(self):
        if self._account_login is None:
            self._account_login = create_account_login_service()
        return self._account_login

    async def start_account_login(self, data: dict | None = None) -> dict:
        try:
            return await self._account_login_service().start()
        except CloudError as error:
            raise Exception("login_unavailable") from error

    async def account_login_status(self, data: dict | None = None) -> dict:
        return self._account_login_service().status()

    async def account_devices(self, data: dict | None = None) -> list[dict]:
        try:
            return await self._account_login_service().devices(self.models)
        except NotSignedInError as error:
            raise Exception("not_signed_in") from error
        except CloudError as error:
            raise Exception("login_unavailable") from error

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
