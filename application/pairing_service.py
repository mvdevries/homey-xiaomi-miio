from ..domain.pairing import build_pairing_device
from ..domain.token import token_from_hex
from .ports import TransportFactory

PROBE_RETRIES = 2


class PairingService:
    def __init__(self, *, transport_factory: TransportFactory) -> None:
        self._transport_factory = transport_factory

    async def validate_device(self, data: dict) -> dict:
        device = build_pairing_device(data)
        await self._verify_reachable(device["settings"])
        return device

    async def _verify_reachable(self, settings: dict) -> None:
        token = token_from_hex(settings["token"])
        transport = self._transport_factory(settings["address"], token)
        try:
            await transport.send("miIO.info", retries=PROBE_RETRIES)
        finally:
            transport.close()
