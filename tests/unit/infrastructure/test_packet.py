import hashlib
import struct

import pytest
from app.domain.errors import MalformedPacketError, MiioDeviceError
from app.infrastructure import packet
from app.infrastructure.crypto import MiioCipher

TOKEN = bytes(range(16))
PAYLOAD = {"id": 7, "method": "get_prop", "params": ["power"]}


def build_packet(body: bytes) -> bytes:
    header = struct.pack(">HHIII", 0x2131, 32 + len(body), 0, 1, 1) + bytes(16)
    return header + body


class TestBuildHello:
    def test_given_no_input_when_built_then_all_bytes_are_ones_except_magic_and_length(
        self,
    ):
        hello = packet.build_hello()

        assert hello[:4] == bytes([0x21, 0x31, 0x00, 0x20])
        assert hello[4:] == b"\xff" * 28


class TestEncode:
    def test_given_a_payload_when_encoded_then_the_header_fields_are_set(self):
        data = packet.encode(0xAABBCCDD, 1234, TOKEN, PAYLOAD)

        magic, length, unknown, device_id, stamp = struct.unpack_from(">HHIII", data)

        assert (magic, length, unknown, device_id, stamp) == (
            0x2131,
            len(data),
            0,
            0xAABBCCDD,
            1234,
        )

    def test_given_a_payload_when_encoded_then_the_checksum_covers_everything(
        self,
    ):
        data = packet.encode(1, 2, TOKEN, PAYLOAD)

        expected = hashlib.md5(data[:16] + TOKEN + data[32:]).digest()

        assert data[16:32] == expected


class TestDecode:
    def test_given_an_encoded_packet_when_decoded_then_the_original_is_returned(self):
        data = packet.encode(0x11223344, 99, TOKEN, PAYLOAD)

        decoded = packet.decode(data, TOKEN)

        assert decoded == packet.DecodedPacket(0x11223344, 99, PAYLOAD)

    def test_given_a_hello_response_when_decoded_then_there_is_no_payload(self):
        response = bytearray(packet.build_hello())
        struct.pack_into(">II", response, 8, 0x01020304, 55)
        response[16:32] = TOKEN

        decoded = packet.decode(bytes(response), TOKEN)

        assert decoded == packet.DecodedPacket(0x01020304, 55, None)

    def test_given_trailing_zero_bytes_when_decoded_then_they_are_ignored(
        self,
    ):
        body = MiioCipher(TOKEN).encrypt(b'{"id":1,"result":["ok"]}\x00')

        decoded = packet.decode(build_packet(body), TOKEN)

        assert decoded.payload == {"id": 1, "result": ["ok"]}

    def test_given_a_short_packet_when_decoded_then_it_is_rejected(self):
        with pytest.raises(MalformedPacketError, match="too short"):
            packet.decode(b"\x21\x31", TOKEN)

    def test_given_the_wrong_magic_when_decoded_then_it_is_rejected(self):
        with pytest.raises(MalformedPacketError, match="magic"):
            packet.decode(bytes(32), TOKEN)

    def test_given_another_token_when_decoded_then_the_payload_is_rejected(
        self,
    ):
        data = packet.encode(1, 1, bytes(16), PAYLOAD)

        with pytest.raises(MalformedPacketError):
            packet.decode(data, TOKEN)

    def test_given_a_payload_that_is_not_json_when_decoded_then_it_is_rejected(self):
        body = MiioCipher(TOKEN).encrypt(b"not json")

        with pytest.raises(MalformedPacketError):
            packet.decode(build_packet(body), TOKEN)

    def test_given_a_payload_that_is_not_an_object_when_decoded_then_it_is_rejected(
        self,
    ):
        body = MiioCipher(TOKEN).encrypt(b"[1]")

        with pytest.raises(MalformedPacketError, match="object"):
            packet.decode(build_packet(body), TOKEN)


class TestExtractToken:
    def test_given_a_hello_response_when_extracted_then_the_token_is_returned(self):
        response = bytearray(packet.build_hello())
        response[16:32] = TOKEN

        token = packet.extract_token(bytes(response))

        assert token == TOKEN

    def test_given_a_short_response_when_extracted_then_it_is_rejected(self):
        with pytest.raises(MalformedPacketError):
            packet.extract_token(b"short")


class TestMiioDeviceError:
    @pytest.mark.parametrize(
        ("code", "recoverable"), [(-30001, True), (-9999, True), (-1, False)]
    )
    def test_given_an_error_code_when_created_then_recoverability_follows_the_code(
        self, code, recoverable
    ):
        error = MiioDeviceError(code, "boom")

        assert error.recoverable is recoverable
        assert str(error) == f"miIO error {code}: boom"
