from typing import Any, ClassVar

from app.application.humidifier_service import HumidifierService
from app.container import create_humidifier
from app.domain.humidifier import state_to_capabilities
from app.domain.values import led_level
from app.endpoints.polling_device import Command, MiioPollingDevice


class HumidifierDevice(MiioPollingDevice):
    commands: ClassVar[dict[str, Command]] = {
        "onoff": Command("set_power"),
        "humidifier_mode": Command("set_mode"),
        "humidifier_target_humidity": Command("set_target_humidity", int),
        "humidifier_dry": Command("set_dry"),
        "led_display": Command("set_led_brightness", led_level),
        "buzzer_enabled": Command("set_buzzer"),
        "locked": Command("set_child_lock"),
    }

    def create_client(self, settings: Any) -> HumidifierService:
        return create_humidifier(str(settings["address"]), str(settings["token"]))

    async def read_capabilities(self, client: HumidifierService) -> dict[str, Any]:
        return state_to_capabilities(await client.get_state())


homey_export = HumidifierDevice
