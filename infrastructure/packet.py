import json
import struct
from dataclasses import dataclass
from typing import Any

from ..domain.errors import MalformedPacketError
from .crypto import MiioCipher, md5

MAGIC = 0x2131
HEADER_SIZE = 32
PORT = 54321
HELLO_FILL = 0xFF
CHECKSUM_OFFSET = 16
HEADER_FORMAT = ">HHIII"


@dataclass(frozen=True, slots=True)
class DecodedPacket:
    device_id: int
    stamp: int
    payload: dict[str, Any] | None


def build_hello() -> bytes:
    header = bytearray([HELLO_FILL] * HEADER_SIZE)
    struct.pack_into(">HH", header, 0, MAGIC, HEADER_SIZE)
    return bytes(header)


def encode(device_id: int, stamp: int, token: bytes, payload: dict[str, Any]) -> bytes:
    body = json.dumps(payload, separators=(",", ":")).encode()
    encrypted = MiioCipher(token).encrypt(body)
    header = bytearray(HEADER_SIZE)
    struct.pack_into(
        HEADER_FORMAT,
        header,
        0,
        MAGIC,
        HEADER_SIZE + len(encrypted),
        0,
        device_id,
        stamp,
    )
    header[CHECKSUM_OFFSET:HEADER_SIZE] = token
    checksum = md5(bytes(header) + encrypted)
    header[CHECKSUM_OFFSET:HEADER_SIZE] = checksum
    return bytes(header) + encrypted


def decode(data: bytes, token: bytes) -> DecodedPacket:
    if len(data) < HEADER_SIZE:
        raise MalformedPacketError(f"Packet too short: {len(data)} bytes")
    magic, length, _, device_id, stamp = struct.unpack_from(HEADER_FORMAT, data)
    if magic != MAGIC:
        raise MalformedPacketError(f"Invalid magic: {magic:#x}")
    if length == HEADER_SIZE:
        return DecodedPacket(device_id, stamp, None)
    return DecodedPacket(
        device_id, stamp, _decode_payload(data[HEADER_SIZE:length], token)
    )


def _decode_payload(encrypted: bytes, token: bytes) -> dict[str, Any]:
    try:
        decrypted = MiioCipher(token).decrypt(encrypted)
        payload = json.loads(decrypted.rstrip(b"\x00").decode())
    except (ValueError, UnicodeDecodeError) as error:
        raise MalformedPacketError("Payload cannot be decoded") from error
    if not isinstance(payload, dict):
        raise MalformedPacketError("Payload is not an object")
    return payload
