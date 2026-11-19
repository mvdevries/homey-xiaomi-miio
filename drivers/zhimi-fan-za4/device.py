from typing import Any

from app.application.standing_fan_service import StandingFanService
from app.container import create_standing_fan
from app.domain.standing_fan import dim_to_speed, state_to_capabilities
from app.domain.values import led_level
from app.endpoints.polling_device import MiioPollingDevice

DEBOUNCE_MILLISECONDS = 50
POWER_CAPABILITIES = ["onoff", "dim"]


class StandingFanDevice(MiioPollingDevice):
    _natural_mode = False

    def register_listeners(self) -> None:
        self.register_multiple_capability_listener(
            POWER_CAPABILITIES, self._on_power_and_speed, DEBOUNCE_MILLISECONDS
        )
        self.register_capability_listener("fan_oscillating", self._on_oscillating)
        self.register_capability_listener("fan_angle", self._on_angle)
        self.register_capability_listener("led_display", self._on_led_display)
        self.register_capability_listener("buzzer_enabled", self._on_buzzer)
        self.register_capability_listener("locked", self._on_child_lock)

    def create_client(self, settings: Any) -> StandingFanService:
        return create_standing_fan(str(settings["address"]), str(settings["token"]))

    async def read_capabilities(self, client: StandingFanService) -> dict[str, Any]:
        state = await client.get_state()
        self._natural_mode = state.natural_mode
        return state_to_capabilities(state)

    async def _on_power_and_speed(self, values: dict[str, Any], **options: Any) -> None:
        fan = self._require_client()
        current_power = bool(self._current("onoff", False))
        power = values.get("onoff", current_power)
        if "dim" in values:
            power = values["dim"] > 0
        if power != current_power:
            await fan.set_power(power)
            await self.set_capability_value("onoff", power)
        if "dim" in values and power:
            await self._set_speed(fan, dim_to_speed(values["dim"]))

    async def _set_speed(self, fan: StandingFanService, speed: int) -> None:
        if self._natural_mode:
            await fan.set_natural_speed(speed)
        else:
            await fan.set_speed(speed)

    async def _on_oscillating(self, value: bool, **options: Any) -> None:
        await self._require_client().set_oscillating(value)

    async def _on_angle(self, value: float, **options: Any) -> None:
        await self._require_client().set_angle(int(value))

    async def _on_led_display(self, value: bool, **options: Any) -> None:
        await self._require_client().set_led_brightness(led_level(value))

    async def _on_buzzer(self, value: bool, **options: Any) -> None:
        await self._require_client().set_buzzer(value)

    async def _on_child_lock(self, value: bool, **options: Any) -> None:
        await self._require_client().set_child_lock(value)


homey_export = StandingFanDevice
