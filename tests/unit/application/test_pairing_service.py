import pytest
from app.application import pairing_service
from app.application.pairing_service import PROBE_RETRIES, PairingService
from app.domain.errors import InvalidTokenError, MiioTimeoutError
from app.domain.pairing import InvalidPairingInputError

from tests.support.fake_transport import FakeTransport

VALID_TOKEN = "0123456789abcdef0123456789ABCDEF"


def pairing_input(**overrides):
    base = {
        "name": "Lamp",
        "address": "192.0.2.10",
        "token": VALID_TOKEN,
        "polling": 10,
    }
    return base | overrides


class RecordingFactory:
    def __init__(self, transport):
        self.transport = transport
        self.created = []

    def __call__(self, address, token):
        self.created.append((address, token))
        return self.transport


class SilentTransport(FakeTransport):
    async def send(self, method, params=None, *, retries=None):
        self.calls.append((method, params, retries))
        raise MiioTimeoutError("timeout")


class TestPairingService:
    async def test_given_a_reachable_device_when_validated_then_the_device_is_returned(
        self,
    ):
        factory = RecordingFactory(FakeTransport())

        device = await PairingService(transport_factory=factory).validate_device(
            pairing_input()
        )

        assert device["data"] == {"id": "192.0.2.10"}

    async def test_given_valid_input_when_validated_then_it_probes_and_closes_transport(
        self,
    ):
        transport = FakeTransport()
        factory = RecordingFactory(transport)

        await PairingService(transport_factory=factory).validate_device(pairing_input())

        assert factory.created == [("192.0.2.10", bytes.fromhex(VALID_TOKEN))]
        assert transport.calls == [("miIO.info", None)]
        assert transport.closed

    async def test_given_invalid_input_when_validated_then_it_is_rejected_unprobed(
        self,
    ):
        factory = RecordingFactory(FakeTransport())

        with pytest.raises(InvalidPairingInputError, match="token_invalid"):
            await PairingService(transport_factory=factory).validate_device(
                pairing_input(token="no")
            )

        assert factory.created == []

    async def test_given_a_silent_device_when_validated_then_the_transport_is_closed(
        self,
    ):
        transport = SilentTransport()
        factory = RecordingFactory(transport)

        with pytest.raises(MiioTimeoutError):
            await PairingService(transport_factory=factory).validate_device(
                pairing_input()
            )

        assert transport.calls == [("miIO.info", None, PROBE_RETRIES)]
        assert transport.closed

    async def test_given_an_undecodable_token_when_validated_then_it_is_rejected(
        self, monkeypatch
    ):
        def fail(value):
            raise InvalidTokenError("token_invalid")

        monkeypatch.setattr(pairing_service, "token_from_hex", fail)

        with pytest.raises(InvalidTokenError):
            await PairingService(
                transport_factory=RecordingFactory(FakeTransport())
            ).validate_device(pairing_input())
