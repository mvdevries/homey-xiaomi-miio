import asyncio
import struct
from collections.abc import Callable
from typing import Any

from app.domain.errors import MalformedPacketError
from app.infrastructure.packet import HEADER_SIZE, MAGIC, decode, encode

Responder = Callable[[dict[str, Any]], dict[str, Any] | None]


def echo_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {"id": payload["id"], "result": ["ok"]}


class FakeDevice(asyncio.DatagramProtocol):
    def __init__(
        self,
        token: bytes,
        responder: Responder = echo_result,
        device_id: int = 0x1234,
        stamp: int = 1000,
    ) -> None:
        self.token = token
        self.responder = responder
        self.device_id = device_id
        self.stamp = stamp
        self.hello_reply: bytes | None = None
        self.hellos = 0
        self.requests: list[dict[str, Any]] = []
        self.stamps: list[int] = []
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: Any) -> None:
        if len(data) == HEADER_SIZE:
            self.hellos += 1
            self._reply(self.hello_reply or self._hello_packet(), addr)
            return
        try:
            decoded = decode(data, self.token)
        except MalformedPacketError:
            return
        self.requests.append(decoded.payload)
        self.stamps.append(decoded.stamp)
        response = self.responder(decoded.payload)
        if response is not None:
            packet = encode(self.device_id, self.stamp, self.token, response)
            self._reply(packet, addr)

    def _reply(self, packet: bytes, addr: Any) -> None:
        if self.transport is not None:
            self.transport.sendto(packet, addr)

    def _hello_packet(self) -> bytes:
        return struct.pack(
            ">HHIII16s", MAGIC, HEADER_SIZE, 0, self.device_id, self.stamp, bytes(16)
        )

    def close(self) -> None:
        if self.transport is not None:
            self.transport.close()


async def start_fake_device(
    token: bytes, responder: Responder = echo_result, **options: Any
) -> tuple[FakeDevice, int]:
    device = FakeDevice(token, responder, **options)
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: device, local_addr=("127.0.0.1", 0)
    )
    return device, transport.get_extra_info("sockname")[1]
