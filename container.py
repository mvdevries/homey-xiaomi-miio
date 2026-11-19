from .application.account_login_service import AccountLoginService
from .application.bedside_lamp_service import BedsideLampService
from .application.discovery_service import DiscoveryService
from .application.humidifier_service import HumidifierService
from .application.pairing_service import PairingService
from .application.standing_fan_service import StandingFanService
from .domain.token import token_from_hex
from .infrastructure.discovery import UdpDeviceScanner
from .infrastructure.http import HttpClient
from .infrastructure.transport import MiioTransport
from .infrastructure.xiaomi_cloud import XiaomiCloudClient


def create_transport(address: str, token: bytes) -> MiioTransport:
    return MiioTransport(address, token)


def create_bedside_lamp(address: str, token_hex: str) -> BedsideLampService:
    return BedsideLampService(create_transport(address, token_from_hex(token_hex)))


def create_standing_fan(address: str, token_hex: str) -> StandingFanService:
    return StandingFanService(create_transport(address, token_from_hex(token_hex)))


def create_humidifier(address: str, token_hex: str) -> HumidifierService:
    return HumidifierService(create_transport(address, token_from_hex(token_hex)))


def create_pairing_service() -> PairingService:
    return PairingService(transport_factory=create_transport)


def create_scanner() -> UdpDeviceScanner:
    return UdpDeviceScanner()


def create_discovery_service() -> DiscoveryService:
    return DiscoveryService(scanner=create_scanner())


def create_authenticator() -> XiaomiCloudClient:
    return XiaomiCloudClient(HttpClient())


def create_account_login_service() -> AccountLoginService:
    return AccountLoginService(authenticator_factory=create_authenticator)
