import hashlib
import struct

import pytest
from app.miio import packet
from app.miio.crypto import MiioCipher
from app.miio.errors import MalformedPacketError, MiioDeviceError

TOKEN = bytes(range(16))
PAYLOAD = {"id": 7, "method": "get_prop", "params": ["power"]}


def test_hello_is_all_ones_except_magic_and_length():
    hello = packet.build_hello()

    assert hello[:4] == bytes([0x21, 0x31, 0x00, 0x20])
    assert hello[4:] == b"\xff" * 28


def test_encoded_header_fields():
    data = packet.encode(0xAABBCCDD, 1234, TOKEN, PAYLOAD)

    magic, length, unknown, device_id, stamp = struct.unpack_from(">HHIII", data)
    assert (magic, length, unknown, device_id, stamp) == (
        0x2131,
        len(data),
        0,
        0xAABBCCDD,
        1234,
    )


def test_encoded_checksum_covers_header_token_and_payload():
    data = packet.encode(1, 2, TOKEN, PAYLOAD)

    expected = hashlib.md5(data[:16] + TOKEN + data[32:]).digest()
    assert data[16:32] == expected


def test_decode_round_trip():
    data = packet.encode(0x11223344, 99, TOKEN, PAYLOAD)

    decoded = packet.decode(data, TOKEN)

    assert decoded == packet.DecodedPacket(0x11223344, 99, PAYLOAD)


def test_decode_hello_response_has_no_payload():
    response = bytearray(packet.build_hello())
    struct.pack_into(">II", response, 8, 0x01020304, 55)
    response[16:32] = TOKEN

    decoded = packet.decode(bytes(response), TOKEN)

    assert decoded == packet.DecodedPacket(0x01020304, 55, None)


def test_decode_ignores_trailing_zero_bytes_in_payload():
    body = MiioCipher(TOKEN).encrypt(b'{"id":1,"result":["ok"]}\x00')
    header = struct.pack(">HHIII", 0x2131, 32 + len(body), 0, 1, 1) + bytes(16)

    decoded = packet.decode(header + body, TOKEN)

    assert decoded.payload == {"id": 1, "result": ["ok"]}


def test_extract_token_from_hello_response():
    response = bytearray(packet.build_hello())
    response[16:32] = TOKEN

    assert packet.extract_token(bytes(response)) == TOKEN


@pytest.mark.parametrize("function", [packet.extract_token])
def test_extract_token_rejects_short_responses(function):
    with pytest.raises(MalformedPacketError):
        function(b"short")


def test_decode_rejects_short_packets():
    with pytest.raises(MalformedPacketError, match="too short"):
        packet.decode(b"\x21\x31", TOKEN)


def test_decode_rejects_wrong_magic():
    with pytest.raises(MalformedPacketError, match="magic"):
        packet.decode(bytes(32), TOKEN)


def test_decode_rejects_payload_encrypted_with_another_token():
    data = packet.encode(1, 1, bytes(16), PAYLOAD)

    with pytest.raises(MalformedPacketError):
        packet.decode(data, TOKEN)


def test_decode_rejects_payload_that_is_not_json():
    body = MiioCipher(TOKEN).encrypt(b"not json")
    header = struct.pack(">HHIII", 0x2131, 32 + len(body), 0, 1, 1) + bytes(16)

    with pytest.raises(MalformedPacketError):
        packet.decode(header + body, TOKEN)


def test_decode_rejects_payload_that_is_not_an_object():
    body = MiioCipher(TOKEN).encrypt(b"[1]")
    header = struct.pack(">HHIII", 0x2131, 32 + len(body), 0, 1, 1) + bytes(16)

    with pytest.raises(MalformedPacketError, match="object"):
        packet.decode(header + body, TOKEN)


@pytest.mark.parametrize(
    ("code", "recoverable"), [(-30001, True), (-9999, True), (-1, False)]
)
def test_device_error_recoverability(code, recoverable):
    error = MiioDeviceError(code, "boom")

    assert error.recoverable is recoverable
    assert str(error) == f"miIO error {code}: boom"
