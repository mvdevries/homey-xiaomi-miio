from dataclasses import dataclass
from typing import Any

from .errors import MiioDeviceError
from .properties import read_properties
from .token import token_from_hex
from .transport import MiioTransport
from .values import as_int, as_switch, is_on, led_is_on, nearest

TARGET_HUMIDITIES = (30, 40, 50, 60, 70, 80)
DEVICE_POWERED_OFF_CODE = -6011
DEFAULT_MODE = "auto"
STATE_PROPERTIES = [
    "power",
    "mode",
    "humidity",
    "temp_dec",
    "temperature",
    "buzzer",
    "led_b",
    "child_lock",
    "limit_hum",
    "dry",
]
OPTIONAL_PROPERTIES = frozenset({"temp_dec", "temperature", "dry", "led_b"})


@dataclass(frozen=True, slots=True)
class HumidifierState:
    power: bool
    mode: str
    humidity: int
    temperature: float | None
    buzzer: bool
    led_brightness: int
    child_lock: bool
    target_humidity: int
    dry: bool


def parse_temperature(values: dict[str, Any]) -> float | None:
    if values["temp_dec"] is not None:
        return as_int(values["temp_dec"]) / 10
    if values["temperature"] is not None:
        return float(values["temperature"])
    return None


def parse_state(values: dict[str, Any]) -> HumidifierState:
    return HumidifierState(
        power=is_on(values["power"]),
        mode=str(values["mode"] or DEFAULT_MODE),
        humidity=as_int(values["humidity"]),
        temperature=parse_temperature(values),
        buzzer=is_on(values["buzzer"]),
        led_brightness=as_int(values["led_b"]),
        child_lock=is_on(values["child_lock"]),
        target_humidity=nearest(as_int(values["limit_hum"]), TARGET_HUMIDITIES),
        dry=is_on(values["dry"]),
    )


def state_to_capabilities(state: HumidifierState) -> dict[str, bool | float | str]:
    capabilities: dict[str, bool | float | str] = {
        "onoff": state.power,
        "humidifier_mode": state.mode,
        "humidifier_target_humidity": str(state.target_humidity),
        "humidifier_dry": state.dry,
        "measure_humidity": state.humidity,
        "led_display": led_is_on(state.led_brightness),
        "buzzer_enabled": state.buzzer,
        "locked": state.child_lock,
    }
    if state.temperature is not None:
        capabilities["measure_temperature"] = state.temperature
    return capabilities


class Humidifier:
    def __init__(self, transport: MiioTransport) -> None:
        self._transport = transport

    async def get_state(self) -> HumidifierState:
        values = await read_properties(
            self._transport, STATE_PROPERTIES, OPTIONAL_PROPERTIES
        )
        return parse_state(values)

    async def set_power(self, on: bool) -> None:
        await self._transport.send("set_power", [as_switch(on)])

    async def set_mode(self, mode: str) -> None:
        try:
            await self._transport.send("set_mode", [mode])
        except MiioDeviceError as error:
            if error.code != DEVICE_POWERED_OFF_CODE:
                raise
            await self.set_power(True)
            await self._transport.send("set_mode", [mode])

    async def set_target_humidity(self, humidity: int) -> None:
        target = nearest(humidity, TARGET_HUMIDITIES)
        await self._transport.send("set_limit_hum", [target])

    async def set_dry(self, on: bool) -> None:
        await self._transport.send("set_dry", [as_switch(on)])

    async def set_led_brightness(self, brightness: int) -> None:
        await self._transport.send("set_led_b", [str(brightness)])

    async def set_buzzer(self, on: bool) -> None:
        await self._transport.send("set_buzzer", [as_switch(on)])

    async def set_child_lock(self, on: bool) -> None:
        await self._transport.send("set_child_lock", [as_switch(on)])

    def close(self) -> None:
        self._transport.close()


def build_humidifier(address: str, token_hex: str) -> Humidifier:
    return Humidifier(MiioTransport(address, token_from_hex(token_hex)))
