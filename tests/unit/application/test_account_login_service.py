import asyncio

import pytest
from app.application.account_login_service import AccountLoginService
from app.domain.errors import (
    CloudError,
    CloudRequestError,
    LoginExpiredError,
    LoginFailedError,
    NotSignedInError,
)
from app.domain.xiaomi_account import CloudDevice, QrChallenge

CHALLENGE = QrChallenge(b"qr", "https://login.example", "poll", 300)


def device(did, name, model="zhimi.fan.za4", server="de"):
    return CloudDevice(did, name, model, "aa" * 16, "192.0.2.10", server)


class FakeSession:
    def __init__(self, by_server):
        self.by_server = by_server

    async def list_devices(self, server):
        result = self.by_server.get(server, [])
        if isinstance(result, Exception):
            raise result
        return result


class FakeAuthenticator:
    def __init__(self, session=None, error=None, gate=None):
        self.session = session
        self.error = error
        self.gate = gate or asyncio.Event()
        self.requested = 0

    async def request_qr(self):
        self.requested += 1
        return CHALLENGE

    async def wait_for_scan(self, challenge):
        await self.gate.wait()
        if self.error is not None:
            raise self.error
        return self.session


def make_service(authenticator, servers=("de", "us")):
    return AccountLoginService(
        authenticator_factory=lambda: authenticator, servers=servers
    )


async def settle():
    await asyncio.sleep(0)
    await asyncio.sleep(0)


class TestAccountLoginServiceStart:
    async def test_given_a_new_login_when_started_then_the_qr_is_returned(self):
        service = make_service(FakeAuthenticator())

        login = await service.start()
        service.close()

        assert login == {
            "qrImage": CHALLENGE.image_data_uri,
            "loginUrl": "https://login.example",
            "timeoutSeconds": 300,
        }

    async def test_given_a_started_login_when_asked_then_it_is_pending(self):
        service = make_service(FakeAuthenticator())

        await service.start()
        status = service.status()
        service.close()

        assert status == {"state": "pending"}

    async def test_given_no_login_when_asked_then_it_is_idle(self):
        assert make_service(FakeAuthenticator()).status() == {"state": "idle"}

    async def test_given_a_scan_when_it_completes_then_the_state_is_signed_in(self):
        authenticator = FakeAuthenticator(session=FakeSession({}))
        service = make_service(authenticator)
        await service.start()

        authenticator.gate.set()
        await settle()

        assert service.status() == {"state": "signed_in"}

    async def test_given_an_expired_code_when_waited_then_the_state_is_expired(self):
        authenticator = FakeAuthenticator(error=LoginExpiredError("expired"))
        service = make_service(authenticator)
        await service.start()

        authenticator.gate.set()
        await settle()

        assert service.status() == {"state": "expired"}

    async def test_given_a_failed_login_when_waited_then_the_state_is_failed(self):
        authenticator = FakeAuthenticator(error=LoginFailedError("failed"))
        service = make_service(authenticator)
        await service.start()

        authenticator.gate.set()
        await settle()

        assert service.status() == {"state": "failed"}

    async def test_given_a_login_in_progress_when_started_again_then_the_first_stops(
        self,
    ):
        first = FakeAuthenticator()
        service = make_service(first)
        await service.start()
        task = service._task

        await service.start()
        await settle()
        service.close()

        assert task.cancelled()

    async def test_given_a_new_login_when_started_then_the_old_session_is_dropped(
        self,
    ):
        authenticator = FakeAuthenticator(session=FakeSession({}))
        service = make_service(authenticator)
        await service.start()
        authenticator.gate.set()
        await settle()

        await service.start()
        service.close()

        with pytest.raises(NotSignedInError):
            await service.devices()


class TestAccountLoginServiceDevices:
    async def signed_in(self, by_server, servers=("de", "us")):
        authenticator = FakeAuthenticator(session=FakeSession(by_server))
        service = make_service(authenticator, servers)
        await service.start()
        authenticator.gate.set()
        await settle()
        return service

    async def test_given_no_login_when_devices_are_asked_then_it_fails(self):
        with pytest.raises(NotSignedInError):
            await make_service(FakeAuthenticator()).devices()

    async def test_given_devices_on_servers_when_asked_then_supported_ones_are_sorted(
        self,
    ):
        service = await self.signed_in(
            {
                "de": [device("2", "Zeta"), device("3", "Other", model="x.y.z")],
                "us": [device("1", "alpha", server="us")],
            }
        )

        devices = await service.devices(("zhimi.fan.za4",))

        assert [item["name"] for item in devices] == ["alpha", "Zeta"]

    async def test_given_a_device_on_two_servers_when_asked_then_it_is_listed_once(
        self,
    ):
        service = await self.signed_in(
            {"de": [device("1", "Fan")], "us": [device("1", "Fan", server="us")]}
        )

        assert len(await service.devices()) == 1

    async def test_given_a_failing_server_when_asked_then_the_others_still_count(
        self,
    ):
        service = await self.signed_in(
            {"de": CloudRequestError("down"), "us": [device("1", "Fan")]}
        )

        assert len(await service.devices()) == 1

    async def test_given_failing_servers_when_asked_then_the_list_is_empty(self):
        service = await self.signed_in(
            {"de": CloudError("down"), "us": CloudError("down")}
        )

        assert await service.devices() == []
