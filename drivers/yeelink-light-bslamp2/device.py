from homey.device import Device


class BedsideLamp2Device(Device):
    async def on_init(self) -> None:
        await self.set_unavailable("The miIO connection is not implemented yet")


homey_export = BedsideLamp2Device
