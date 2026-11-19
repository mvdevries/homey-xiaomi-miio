from ..domain.values import as_switch
from .ports import DeviceTransport


class MiioService:
    def __init__(self, transport: DeviceTransport) -> None:
        self._transport = transport

    async def _switch(self, method: str, on: bool) -> None:
        await self._transport.send(method, [as_switch(on)])

    def close(self) -> None:
        self._transport.close()
