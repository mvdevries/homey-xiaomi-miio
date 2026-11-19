import hashlib

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ..domain.errors import InvalidTokenError
from ..domain.token import TOKEN_SIZE

BLOCK_SIZE_BITS = 128


def md5(data: bytes) -> bytes:
    return hashlib.md5(data, usedforsecurity=False).digest()


class MiioCipher:
    def __init__(self, token: bytes) -> None:
        if len(token) != TOKEN_SIZE:
            raise InvalidTokenError("token_invalid")
        self._key = md5(token)
        self._iv = md5(self._key + token)

    def encrypt(self, plaintext: bytes) -> bytes:
        padder = padding.PKCS7(BLOCK_SIZE_BITS).padder()
        padded = padder.update(plaintext) + padder.finalize()
        encryptor = self._cipher().encryptor()
        return encryptor.update(padded) + encryptor.finalize()

    def decrypt(self, ciphertext: bytes) -> bytes:
        decryptor = self._cipher().decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(BLOCK_SIZE_BITS).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    def _cipher(self) -> Cipher:
        return Cipher(algorithms.AES128(self._key), modes.CBC(self._iv))
