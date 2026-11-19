from ..domain.bedside_lamp import (
    STATE_PROPERTIES,
    TRANSITION,
    LampState,
    parse_state,
)
from .device_service import MiioService


class BedsideLampService(MiioService):
    async def get_state(self) -> LampState:
        return parse_state(await self._transport.send("get_prop", STATE_PROPERTIES))

    async def set_power(self, on: bool) -> None:
        await self._transport.send("set_power", ["on" if on else "off", *TRANSITION])

    async def set_brightness(self, brightness: int) -> None:
        await self._transport.send("set_bright", [brightness, *TRANSITION])

    async def set_hsv(self, hue: int, saturation: int) -> None:
        await self._transport.send("set_hsv", [hue, saturation, *TRANSITION])

    async def set_color_temperature(self, kelvin: int) -> None:
        await self._transport.send("set_ct_abx", [kelvin, *TRANSITION])
