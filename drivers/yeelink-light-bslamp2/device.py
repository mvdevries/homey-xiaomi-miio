from typing import Any

from app.application.bedside_lamp_service import BedsideLampService
from app.container import create_bedside_lamp
from app.domain.bedside_lamp import (
    LIGHT_MODE_TEMPERATURE,
    dim_to_brightness,
    hue_to_degrees,
    saturation_to_percent,
    state_to_capabilities,
    temperature_to_kelvin,
)
from app.endpoints.polling_device import DEBOUNCE_MILLISECONDS, MiioPollingDevice

COLOR_CAPABILITIES = [
    "light_temperature",
    "light_mode",
    "light_hue",
    "light_saturation",
]


class BedsideLamp2Device(MiioPollingDevice):
    def register_listeners(self) -> None:
        super().register_listeners()
        self.register_power_and_level()
        self.register_multiple_capability_listener(
            COLOR_CAPABILITIES, self._on_color, DEBOUNCE_MILLISECONDS
        )

    def create_client(self, settings: Any) -> BedsideLampService:
        return create_bedside_lamp(str(settings["address"]), str(settings["token"]))

    async def read_capabilities(self, client: BedsideLampService) -> dict[str, Any]:
        return state_to_capabilities(await client.get_state())

    async def set_level(self, client: BedsideLampService, dim: float) -> None:
        await client.set_brightness(dim_to_brightness(dim))

    async def _on_color(self, values: dict[str, Any], **options: Any) -> None:
        lamp = self._require_client()
        mode = values.get("light_mode", self._current("light_mode", "color"))
        if mode == LIGHT_MODE_TEMPERATURE:
            temperature = values.get(
                "light_temperature", self._current("light_temperature", 0.5)
            )
            await lamp.set_color_temperature(temperature_to_kelvin(temperature))
            return
        hue = values.get("light_hue", self._current("light_hue", 0.0))
        saturation = values.get(
            "light_saturation", self._current("light_saturation", 1.0)
        )
        await lamp.set_hsv(hue_to_degrees(hue), saturation_to_percent(saturation))


homey_export = BedsideLamp2Device
