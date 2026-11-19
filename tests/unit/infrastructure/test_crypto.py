import hashlib

import pytest
from app.miio.crypto import MiioCipher
from app.miio.errors import InvalidTokenError
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

TOKEN = bytes(range(16))


def test_round_trip():
    cipher = MiioCipher(TOKEN)

    assert cipher.decrypt(cipher.encrypt(b'{"id":1}')) == b'{"id":1}'


def test_key_and_iv_are_derived_from_the_token():
    key = hashlib.md5(TOKEN).digest()
    iv = hashlib.md5(key + TOKEN).digest()
    decryptor = Cipher(algorithms.AES128(key), modes.CBC(iv)).decryptor()

    encrypted = MiioCipher(TOKEN).encrypt(b"hello")
    padded = decryptor.update(encrypted) + decryptor.finalize()

    assert padded == b"hello" + bytes([11]) * 11


def test_encrypted_length_is_a_multiple_of_the_block_size():
    assert len(MiioCipher(TOKEN).encrypt(b"x" * 17)) == 32


@pytest.mark.parametrize("size", [0, 15, 17])
def test_rejects_tokens_of_the_wrong_size(size):
    with pytest.raises(InvalidTokenError):
        MiioCipher(bytes(size))


def test_rejects_ciphertext_with_invalid_padding():
    with pytest.raises(ValueError, match="padding"):
        MiioCipher(TOKEN).decrypt(bytes(16))
