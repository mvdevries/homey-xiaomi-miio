import pytest
from app.domain.errors import (
    CloudRequestError,
    LoginFailedError,
    MiioTimeoutError,
    NotSignedInError,
)
from app.domain.pairing import InvalidPairingInputError
from app.endpoints import pairing_driver
from app.endpoints.pairing_driver import MiioDriver

VALID_TOKEN = "0123456789abcdef0123456789ABCDEF"


class FakePairingService:
    def __init__(self, error=None):
        self.error = error
        self.validated = []

    async def validate_device(self, data):
        self.validated.append(data)
        if self.error is not None:
            raise self.error
        return {"name": data["name"]}


def use_pairing_service(monkeypatch, service):
    monkeypatch.setattr(pairing_driver, "create_pairing_service", lambda: service)


class TestMiioDriverValidateDevice:
    async def test_given_a_valid_device_when_validated_then_the_device_is_returned(
        self, monkeypatch
    ):
        use_pairing_service(monkeypatch, FakePairingService())

        result = await MiioDriver().validate_device(
            {"name": "Lamp", "token": VALID_TOKEN}
        )

        assert result == {"name": "Lamp"}

    async def test_given_invalid_input_when_validated_then_the_error_code_is_reported(
        self, monkeypatch
    ):
        service = FakePairingService(error=InvalidPairingInputError("token_invalid"))
        use_pairing_service(monkeypatch, service)

        with pytest.raises(Exception, match="token_invalid"):
            await MiioDriver().validate_device({"name": "Lamp", "token": "no"})

    async def test_given_an_unreachable_device_when_validated_then_it_is_rejected(
        self, monkeypatch
    ):
        service = FakePairingService(error=MiioTimeoutError("timeout"))
        use_pairing_service(monkeypatch, service)

        with pytest.raises(Exception, match="device_unreachable"):
            await MiioDriver().validate_device({"name": "Lamp", "token": VALID_TOKEN})


class TestMiioDriverOnPair:
    async def test_given_a_pair_session_when_pairing_then_validate_handler_is_set(
        self,
    ):
        handlers = {}

        class FakeSession:
            def set_handler(self, event, handler):
                handlers[event] = handler

        await MiioDriver().on_pair(FakeSession())

        assert "validate_device" in handlers


class FakeDiscoveryService:
    def __init__(self, error=None):
        self.error = error

    async def discover_devices(self):
        if self.error is not None:
            raise self.error
        return [{"address": "192.0.2.10", "deviceId": "00001234"}]


class TestMiioDriverDiscoverDevices:
    async def test_given_devices_on_the_network_when_discovered_then_they_are_returned(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            pairing_driver, "create_discovery_service", FakeDiscoveryService
        )

        result = await MiioDriver().discover_devices()

        assert result == [{"address": "192.0.2.10", "deviceId": "00001234"}]

    async def test_given_a_network_failure_when_discovered_then_it_is_reported(
        self, monkeypatch
    ):
        service = FakeDiscoveryService(error=MiioTimeoutError("timeout"))
        monkeypatch.setattr(pairing_driver, "create_discovery_service", lambda: service)

        with pytest.raises(Exception, match="discovery_failed"):
            await MiioDriver().discover_devices()


class FakeAccountLoginService:
    def __init__(self, error=None):
        self.error = error
        self.models = None

    async def start(self):
        if self.error is not None:
            raise self.error
        return {"qrImage": "data:image/png;base64,AA=="}

    def status(self):
        return {"state": "pending"}

    async def devices(self, models):
        if self.error is not None:
            raise self.error
        self.models = models
        return [{"did": "1"}]


def use_account_login(monkeypatch, service):
    monkeypatch.setattr(pairing_driver, "create_account_login_service", lambda: service)


class FanDriver(MiioDriver):
    models = ("zhimi.fan.za4",)


class TestMiioDriverAccountLogin:
    async def test_given_the_cloud_when_a_login_is_started_then_the_qr_is_returned(
        self, monkeypatch
    ):
        use_account_login(monkeypatch, FakeAccountLoginService())

        result = await MiioDriver().start_account_login()

        assert result == {"qrImage": "data:image/png;base64,AA=="}

    async def test_given_an_unreachable_cloud_when_started_then_it_is_reported(
        self, monkeypatch
    ):
        service = FakeAccountLoginService(error=CloudRequestError("down"))
        use_account_login(monkeypatch, service)

        with pytest.raises(Exception, match="login_unavailable"):
            await MiioDriver().start_account_login()

    async def test_given_a_login_when_the_status_is_asked_then_it_is_returned(
        self, monkeypatch
    ):
        use_account_login(monkeypatch, FakeAccountLoginService())

        assert await MiioDriver().account_login_status() == {"state": "pending"}

    async def test_given_a_driver_with_models_when_devices_are_asked_then_it_filters(
        self, monkeypatch
    ):
        service = FakeAccountLoginService()
        use_account_login(monkeypatch, service)

        result = await FanDriver().account_devices()

        assert result == [{"did": "1"}]
        assert service.models == ("zhimi.fan.za4",)

    async def test_given_no_login_when_devices_are_asked_then_it_is_reported(
        self, monkeypatch
    ):
        service = FakeAccountLoginService(error=NotSignedInError("no"))
        use_account_login(monkeypatch, service)

        with pytest.raises(Exception, match="not_signed_in"):
            await MiioDriver().account_devices()

    async def test_given_a_failed_login_when_devices_are_asked_then_it_is_reported(
        self, monkeypatch
    ):
        service = FakeAccountLoginService(error=LoginFailedError("failed"))
        use_account_login(monkeypatch, service)

        with pytest.raises(Exception, match="login_unavailable"):
            await MiioDriver().account_devices()

    async def test_given_two_calls_when_the_service_is_needed_then_it_is_created_once(
        self, monkeypatch
    ):
        created = []

        def create():
            created.append(1)
            return FakeAccountLoginService()

        monkeypatch.setattr(pairing_driver, "create_account_login_service", create)
        driver = MiioDriver()

        await driver.account_login_status()
        await driver.account_login_status()

        assert len(created) == 1
