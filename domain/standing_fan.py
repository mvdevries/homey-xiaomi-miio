from dataclasses import dataclass
from typing import Any

from .properties import read_properties
from .token import token_from_hex
from .transport import MiioTransport
from .values import as_int, as_switch, is_on, led_is_on, nearest

VALID_ANGLES = (30, 60, 90, 120)
MAX_SPEED = 100
MIN_SPEED = 1
STATE_PROPERTIES = [
    "power",
    "angle",
    "angle_enable",
    "speed_level",
    "natural_level",
    "child_lock",
    "buzzer",
    "led_b",
]


@dataclass(frozen=True, slots=True)
class FanState:
    power: bool
    speed: int
    natural_mode: bool
    oscillating: bool
    angle: int
    child_lock: bool
    buzzer: bool
    led_brightness: int


def dim_to_speed(dim: float) -> int:
    return max(MIN_SPEED, min(MAX_SPEED, round(dim * MAX_SPEED)))


def speed_to_dim(speed: int) -> float:
    return max(0.0, min(1.0, speed / MAX_SPEED))


def parse_state(values: dict[str, Any]) -> FanState:
    natural_level = as_int(values["natural_level"])
    direct_level = as_int(values["speed_level"])
    natural_mode = direct_level == 0 and natural_level > 0
    return FanState(
        power=is_on(values["power"]),
        speed=natural_level if natural_mode else direct_level,
        natural_mode=natural_mode,
        oscillating=is_on(values["angle_enable"]),
        angle=nearest(as_int(values["angle"]), VALID_ANGLES),
        child_lock=is_on(values["child_lock"]),
        buzzer=is_on(values["buzzer"]),
        led_brightness=as_int(values["led_b"]),
    )


def state_to_capabilities(state: FanState) -> dict[str, bool | float | str]:
    return {
        "onoff": state.power,
        "dim": speed_to_dim(state.speed),
        "fan_oscillating": state.oscillating,
        "fan_angle": state.angle,
        "led_display": led_is_on(state.led_brightness),
        "buzzer_enabled": state.buzzer,
        "locked": state.child_lock,
    }


class StandingFan:
    def __init__(self, transport: MiioTransport) -> None:
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


def build_fan(address: str, token_hex: str) -> StandingFan:
    return StandingFan(MiioTransport(address, token_from_hex(token_hex)))
