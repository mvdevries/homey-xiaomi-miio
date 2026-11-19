from collections.abc import Iterable
from typing import Any

ON_VALUES = frozenset({"on", 1, 2})


def is_on(value: Any) -> bool:
    return value in ON_VALUES


def as_switch(value: bool) -> str:
    return "on" if value else "off"


def nearest(value: float, options: Iterable[int]) -> int:
    return min(options, key=lambda option: abs(option - value))


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except TypeError, ValueError:
        return default


LED_BRIGHT = 0
LED_OFF = 2


def led_is_on(brightness: int) -> bool:
    return brightness != LED_OFF


def led_level(on: bool) -> int:
    return LED_BRIGHT if on else LED_OFF
