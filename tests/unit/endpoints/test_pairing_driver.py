import pytest
from app.domain.errors import MiioTimeoutError
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
