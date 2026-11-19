import pytest
from app.application.account_login_service import AccountLoginService
from app.application.bedside_lamp_service import BedsideLampService
from app.application.discovery_service import DiscoveryService
from app.application.humidifier_service import HumidifierService
from app.application.pairing_service import PairingService
from app.application.standing_fan_service import StandingFanService
from app.container import (
    create_account_login_service,
    create_authenticator,
    create_bedside_lamp,
    create_discovery_service,
    create_humidifier,
    create_pairing_service,
    create_scanner,
    create_standing_fan,
)
from app.domain.errors import InvalidTokenError
from app.infrastructure.discovery import UdpDeviceScanner
from app.infrastructure.xiaomi_cloud import XiaomiCloudClient

ADDRESS = "192.0.2.1"
VALID_TOKEN = "00" * 16


class TestCreateBedsideLamp:
    def test_given_an_invalid_token_when_created_then_it_is_rejected(self):
        with pytest.raises(InvalidTokenError):
            create_bedside_lamp(ADDRESS, "nope")

    def test_given_a_valid_token_when_created_then_a_bedside_lamp_service_is_returned(
        self,
    ):
        lamp = create_bedside_lamp(ADDRESS, VALID_TOKEN)

        assert isinstance(lamp, BedsideLampService)
        lamp.close()


class TestCreateStandingFan:
    def test_given_an_invalid_token_when_created_then_it_is_rejected(self):
        with pytest.raises(InvalidTokenError):
            create_standing_fan(ADDRESS, "nope")

    def test_given_a_valid_token_when_created_then_a_standing_fan_service_is_returned(
        self,
    ):
        fan = create_standing_fan(ADDRESS, VALID_TOKEN)

        assert isinstance(fan, StandingFanService)
        fan.close()


class TestCreateHumidifier:
    def test_given_an_invalid_token_when_created_then_it_is_rejected(self):
        with pytest.raises(InvalidTokenError):
            create_humidifier(ADDRESS, "nope")

    def test_given_a_valid_token_when_created_then_a_humidifier_service_is_returned(
        self,
    ):
        humidifier = create_humidifier(ADDRESS, VALID_TOKEN)

        assert isinstance(humidifier, HumidifierService)
        humidifier.close()


class TestCreatePairingService:
    def test_given_nothing_when_created_then_a_pairing_service_is_returned(self):
        service = create_pairing_service()

        assert isinstance(service, PairingService)


class TestCreateDiscoveryService:
    def test_given_the_container_when_asked_then_a_discovery_service_is_returned(self):
        assert isinstance(create_discovery_service(), DiscoveryService)


class TestCreateAccountLoginService:
    def test_given_the_container_when_asked_then_an_account_login_service_is_returned(
        self,
    ):
        assert isinstance(create_account_login_service(), AccountLoginService)

    def test_given_the_container_when_an_authenticator_is_asked_then_a_client_is_made(
        self,
    ):
        assert isinstance(create_authenticator(), XiaomiCloudClient)

    def test_given_the_container_when_a_scanner_is_asked_then_a_udp_scanner_is_returned(
        self,
    ):
        assert isinstance(create_scanner(), UdpDeviceScanner)
