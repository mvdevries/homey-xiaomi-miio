import asyncio
import logging

from ..domain.errors import (
    CloudError,
    CloudRequestError,
    LoginExpiredError,
    NotSignedInError,
)
from ..domain.xiaomi_account import (
    SERVERS,
    STATE_EXPIRED,
    STATE_FAILED,
    STATE_IDLE,
    STATE_PENDING,
    STATE_SIGNED_IN,
    CloudDevice,
    keep_supported,
    unique_by_id,
)
from .ports import CloudAuthenticator, CloudAuthenticatorFactory, CloudSession

LOGGER = logging.getLogger(__name__)


class AccountLoginService:
    def __init__(
        self,
        *,
        authenticator_factory: CloudAuthenticatorFactory,
        servers: tuple[str, ...] = SERVERS,
    ) -> None:
        self._authenticator_factory = authenticator_factory
        self._servers = servers
        self._task: asyncio.Task[None] | None = None
        self._session: CloudSession | None = None
        self._state = STATE_IDLE

    async def start(self) -> dict:
        self.close()
        self._session = None
        authenticator = self._authenticator_factory()
        challenge = await authenticator.request_qr()
        self._state = STATE_PENDING
        self._task = asyncio.create_task(self._wait_for_scan(authenticator, challenge))
        return {
            "qrImage": challenge.image_data_uri,
            "loginUrl": challenge.login_url,
            "timeoutSeconds": challenge.timeout_seconds,
        }

    def status(self) -> dict:
        return {"state": self._state}

    async def devices(self, models: tuple[str, ...] = ()) -> list[dict]:
        if self._session is None:
            raise NotSignedInError("not_signed_in")
        found = await self._collect(self._session)
        supported = keep_supported(unique_by_id(found), models)
        return [device.to_dict() for device in sorted(supported, key=_by_name)]

    def close(self) -> None:
        task, self._task = self._task, None
        if task is not None and not task.done():
            task.cancel()

    async def _wait_for_scan(
        self, authenticator: CloudAuthenticator, challenge
    ) -> None:
        try:
            self._session = await authenticator.wait_for_scan(challenge)
        except LoginExpiredError:
            LOGGER.warning("Login: the QR code expired")
            self._state = STATE_EXPIRED
        except CloudError as error:
            LOGGER.warning("Login failed: %s", error)
            self._state = STATE_FAILED
        else:
            LOGGER.warning("Login: signed in")
            self._state = STATE_SIGNED_IN

    async def _collect(self, session: CloudSession) -> list[CloudDevice]:
        results = await asyncio.gather(
            *(self._list_server(session, server) for server in self._servers)
        )
        if all(result is None for result in results):
            raise CloudRequestError("cloud_unreachable")
        return [device for result in results for device in result or []]

    async def _list_server(
        self, session: CloudSession, server: str
    ) -> list[CloudDevice] | None:
        try:
            listed = await session.list_devices(server)
        except CloudError as error:
            LOGGER.warning("Account %s: %s", server, error)
            return None
        LOGGER.warning("Account %s: %d devices", server, len(listed))
        return listed


def _by_name(device: CloudDevice) -> tuple[str, str]:
    return (device.name.lower(), device.did)
