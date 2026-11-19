from dataclasses import dataclass
from typing import Any

from .values import as_int, is_on, led_is_on, nearest

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
