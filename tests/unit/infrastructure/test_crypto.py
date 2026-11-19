import hashlib

import pytest
from app.domain.errors import InvalidTokenError
from app.infrastructure.crypto import MiioCipher
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

TOKEN = bytes(range(16))


class TestMiioCipher:
    def test_given_encrypted_data_when_decrypted_then_the_original_is_returned(self):
        cipher = MiioCipher(TOKEN)

        decrypted = cipher.decrypt(cipher.encrypt(b'{"id":1}'))

        assert decrypted == b'{"id":1}'

    def test_given_a_token_when_encrypting_then_key_and_iv_are_derived_from_the_token(
        self,
    ):
        key = hashlib.md5(TOKEN).digest()
        iv = hashlib.md5(key + TOKEN).digest()
        decryptor = Cipher(algorithms.AES128(key), modes.CBC(iv)).decryptor()

        encrypted = MiioCipher(TOKEN).encrypt(b"hello")
        padded = decryptor.update(encrypted) + decryptor.finalize()

        assert padded == b"hello" + bytes([11]) * 11

    def test_given_17_bytes_when_encrypting_then_the_length_is_a_block_multiple(
        self,
    ):
        encrypted = MiioCipher(TOKEN).encrypt(b"x" * 17)

        assert len(encrypted) == 32

    @pytest.mark.parametrize("size", [0, 15, 17])
    def test_given_a_token_of_the_wrong_size_when_created_then_it_is_rejected(
        self, size
    ):
        with pytest.raises(InvalidTokenError):
            MiioCipher(bytes(size))

    def test_given_ciphertext_with_invalid_padding_when_decrypted_then_it_is_rejected(
        self,
    ):
        cipher = MiioCipher(TOKEN)

        with pytest.raises(ValueError, match="padding"):
            cipher.decrypt(bytes(16))
