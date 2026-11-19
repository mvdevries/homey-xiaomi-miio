from ..domain.standing_fan import STATE_PROPERTIES, VALID_ANGLES, FanState, parse_state
from ..domain.values import as_switch, nearest
from .ports import DeviceTransport
from .properties import read_properties


class StandingFanService:
    def __init__(self, transport: DeviceTransport) -> None:
        self._transport = transport

    async def get_state(self) -> FanState:
        return parse_state(await read_properties(self._transport, STATE_PROPERTIES))

    async def set_power(self, on: bool) -> None:
        await self._transport.send("set_power", [as_switch(on)])

    async def set_speed(self, speed: int) -> None:
        await self._transport.send("set_speed_level", [speed])

    async def set_natural_speed(self, speed: int) -> None:
        await self._transport.send("set_natural_level", [speed])

    async def set_oscillating(self, on: bool) -> None:
        await self._transport.send("set_angle_enable", [as_switch(on)])

    async def set_angle(self, angle: int) -> None:
        await self._transport.send("set_angle", [nearest(angle, VALID_ANGLES)])

    async def set_led_brightness(self, brightness: int) -> None:
        await self._transport.send("set_led_b", [brightness])

    async def set_buzzer(self, on: bool) -> None:
        await self._transport.send("set_buzzer", [2 if on else 0])

    async def set_child_lock(self, on: bool) -> None:
        await self._transport.send("set_child_lock", [as_switch(on)])

    def close(self) -> None:
        self._transport.close()
