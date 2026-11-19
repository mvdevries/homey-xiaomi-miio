from ..domain.errors import MiioDeviceError
from ..domain.humidifier import (
    DEVICE_POWERED_OFF_CODE,
    OPTIONAL_PROPERTIES,
    STATE_PROPERTIES,
    TARGET_HUMIDITIES,
    HumidifierState,
    parse_state,
)
from ..domain.values import nearest
from .device_service import MiioService
from .properties import read_properties


class HumidifierService(MiioService):
    async def get_state(self) -> HumidifierState:
        values = await read_properties(
            self._transport, STATE_PROPERTIES, OPTIONAL_PROPERTIES
        )
        return parse_state(values)

    async def set_power(self, on: bool) -> None:
        await self._switch("set_power", on)

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
        await self._switch("set_dry", on)

    async def set_led_brightness(self, brightness: int) -> None:
        await self._transport.send("set_led_b", [str(brightness)])

    async def set_buzzer(self, on: bool) -> None:
        await self._switch("set_buzzer", on)

    async def set_child_lock(self, on: bool) -> None:
        await self._switch("set_child_lock", on)
