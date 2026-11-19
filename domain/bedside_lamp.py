from dataclasses import dataclass
from typing import Any

from .errors import MalformedPacketError

MIN_COLOR_TEMPERATURE = 1700
MAX_COLOR_TEMPERATURE = 6500
MAX_HUE = 359
MAX_PERCENT = 100
MIN_BRIGHTNESS = 1
TRANSITION = ("smooth", 500)
STATE_PROPERTIES = ["power", "bright", "color_mode", "rgb", "hue", "sat", "ct"]
COLOR_MODE_TEMPERATURE = 2
LIGHT_MODE_COLOR = "color"
LIGHT_MODE_TEMPERATURE = "temperature"


@dataclass(frozen=True, slots=True)
class LampState:
    power: bool
    brightness: int
    light_mode: str
    hue: int
    saturation: int
    color_temperature: int


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def dim_to_brightness(dim: float) -> int:
    return int(clamp(round(dim * MAX_PERCENT), MIN_BRIGHTNESS, MAX_PERCENT))


def brightness_to_dim(brightness: int) -> float:
    return clamp(brightness / MAX_PERCENT, 0.0, 1.0)


def hue_to_degrees(hue: float) -> int:
    return int(clamp(round(hue * MAX_HUE), 0, MAX_HUE))


def degrees_to_hue(degrees: int) -> float:
    return clamp(degrees / MAX_HUE, 0.0, 1.0)


def saturation_to_percent(saturation: float) -> int:
    return int(clamp(round(saturation * MAX_PERCENT), 0, MAX_PERCENT))


def percent_to_saturation(percent: int) -> float:
    return clamp(percent / MAX_PERCENT, 0.0, 1.0)


def temperature_to_kelvin(temperature: float) -> int:
    span = MAX_COLOR_TEMPERATURE - MIN_COLOR_TEMPERATURE
    kelvin = MIN_COLOR_TEMPERATURE + (1 - temperature) * span
    return int(clamp(round(kelvin), MIN_COLOR_TEMPERATURE, MAX_COLOR_TEMPERATURE))


def kelvin_to_temperature(kelvin: int) -> float:
    span = MAX_COLOR_TEMPERATURE - MIN_COLOR_TEMPERATURE
    return clamp(1 - (kelvin - MIN_COLOR_TEMPERATURE) / span, 0.0, 1.0)


def parse_state(result: Any) -> LampState:
    if not isinstance(result, list) or len(result) != len(STATE_PROPERTIES):
        raise MalformedPacketError("Unexpected get_prop result")
    power, brightness, color_mode, _, hue, saturation, temperature = result
    return LampState(
        power=power == "on",
        brightness=int(brightness),
        light_mode=_light_mode(color_mode),
        hue=int(hue),
        saturation=int(saturation),
        color_temperature=int(temperature),
    )


def state_to_capabilities(state: LampState) -> dict[str, bool | float | str]:
    return {
        "onoff": state.power,
        "dim": brightness_to_dim(state.brightness),
        "light_hue": degrees_to_hue(state.hue),
        "light_saturation": percent_to_saturation(state.saturation),
        "light_temperature": kelvin_to_temperature(state.color_temperature),
        "light_mode": state.light_mode,
    }


def _light_mode(color_mode: Any) -> str:
    if color_mode == COLOR_MODE_TEMPERATURE:
        return LIGHT_MODE_TEMPERATURE
    return LIGHT_MODE_COLOR
