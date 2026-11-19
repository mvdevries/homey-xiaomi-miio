import pytest
from app.infrastructure.rc4 import DISCARDED_BYTES, Rc4
from cryptography.hazmat.decrepit.ciphers.algorithms import ARC4
from cryptography.hazmat.primitives.ciphers import Cipher

KEY = bytes(range(16))


def reference_stream(key: bytes, data: bytes) -> bytes:
    encryptor = Cipher(ARC4(key), mode=None).encryptor()
    encryptor.update(bytes(DISCARDED_BYTES))
    return encryptor.update(data)


class TestRc4:
    @pytest.mark.parametrize("data", [b"", b"hello", bytes(range(256)) * 3])
    def test_given_data_when_processed_then_it_matches_the_reference(self, data):
        assert Rc4(KEY).process(data) == reference_stream(KEY, data)

    def test_given_encrypted_data_when_processed_again_then_it_is_restored(self):
        encrypted = Rc4(KEY).process(b"secret")

        assert Rc4(KEY).process(encrypted) == b"secret"

    def test_given_two_parts_when_processed_in_turn_then_the_stream_continues(self):
        cipher = Rc4(KEY)

        joined = cipher.process(b"ab") + cipher.process(b"cd")

        assert joined == reference_stream(KEY, b"abcd")
