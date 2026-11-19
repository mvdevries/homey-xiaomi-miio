from .application.bedside_lamp_service import BedsideLampService
from .application.humidifier_service import HumidifierService
from .application.pairing_service import PairingService
from .application.standing_fan_service import StandingFanService
from .domain.token import token_from_hex
from .infrastructure.transport import MiioTransport


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
