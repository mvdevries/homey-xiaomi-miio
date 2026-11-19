from typing import Any

from app.application.humidifier_service import HumidifierService
from app.container import create_humidifier
from app.domain.humidifier import state_to_capabilities
from app.domain.values import led_level
from app.endpoints.polling_device import MiioPollingDevice


class HumidifierDevice(MiioPollingDevice):
    def register_listeners(self) -> None:
        self.register_capability_listener("onoff", self._on_power)
        self.register_capability_listener("humidifier_mode", self._on_mode)
        self.register_capability_listener(
            "humidifier_target_humidity", self._on_target_humidity
        )
        self.register_capability_listener("humidifier_dry", self._on_dry)
        self.register_capability_listener("led_display", self._on_led_display)
        self.register_capability_listener("buzzer_enabled", self._on_buzzer)
        self.register_capability_listener("locked", self._on_child_lock)

    def create_client(self, settings: Any) -> HumidifierService:
        return create_humidifier(str(settings["address"]), str(settings["token"]))

    async def read_capabilities(self, client: HumidifierService) -> dict[str, Any]:
        return state_to_capabilities(await client.get_state())

    async def _on_power(self, value: bool, **options: Any) -> None:
        await self._require_client().set_power(value)

    async def _on_mode(self, value: str, **options: Any) -> None:
        await self._require_client().set_mode(value)

    async def _on_target_humidity(self, value: str, **options: Any) -> None:
        await self._require_client().set_target_humidity(int(value))

    async def _on_dry(self, value: bool, **options: Any) -> None:
        await self._require_client().set_dry(value)

    async def _on_led_display(self, value: bool, **options: Any) -> None:
        await self._require_client().set_led_brightness(led_level(value))

    async def _on_buzzer(self, value: bool, **options: Any) -> None:
        await self._require_client().set_buzzer(value)

    async def _on_child_lock(self, value: bool, **options: Any) -> None:
        await self._require_client().set_child_lock(value)


homey_export = HumidifierDevice
