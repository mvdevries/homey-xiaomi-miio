from typing import Any, ClassVar

from app.application.standing_fan_service import StandingFanService
from app.container import create_standing_fan
from app.domain.standing_fan import dim_to_speed, state_to_capabilities
from app.domain.values import led_level
from app.endpoints.polling_device import Command, MiioPollingDevice


class StandingFanDevice(MiioPollingDevice):
    commands: ClassVar[dict[str, Command]] = {
        "fan_oscillating": Command("set_oscillating"),
        "fan_angle": Command("set_angle", int),
        "led_display": Command("set_led_brightness", led_level),
        "buzzer_enabled": Command("set_buzzer"),
        "locked": Command("set_child_lock"),
    }
    _natural_mode = False

    def register_listeners(self) -> None:
        super().register_listeners()
        self.register_power_and_level()

    def create_client(self, settings: Any) -> StandingFanService:
        return create_standing_fan(str(settings["address"]), str(settings["token"]))

    async def read_capabilities(self, client: StandingFanService) -> dict[str, Any]:
        state = await client.get_state()
        self._natural_mode = state.natural_mode
        return state_to_capabilities(state)

    async def set_level(self, client: StandingFanService, dim: float) -> None:
        speed = dim_to_speed(dim)
        if self._natural_mode:
            await client.set_natural_speed(speed)
        else:
            await client.set_speed(speed)


homey_export = StandingFanDevice
