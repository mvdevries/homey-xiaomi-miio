import base64
import hashlib
import os
from urllib.parse import urlsplit

from .rc4 import Rc4

NONCE_RANDOM_BYTES = 8
NONCE_MINUTE_MILLISECONDS = 60_000


def generate_nonce(milliseconds: int) -> str:
    minutes = int(milliseconds / NONCE_MINUTE_MILLISECONDS)
    raw = os.urandom(NONCE_RANDOM_BYTES) + minutes.to_bytes(4, byteorder="big")
    return base64.b64encode(raw).decode()


def signed_nonce(ssecurity: str, nonce: str) -> str:
    digest = hashlib.sha256(base64.b64decode(ssecurity) + base64.b64decode(nonce))
    return base64.b64encode(digest.digest()).decode()


def encrypt_payload(signed: str, payload: str) -> str:
    cipher = Rc4(base64.b64decode(signed))
    return base64.b64encode(cipher.process(payload.encode())).decode()


def decrypt_payload(signed: str, payload: str) -> str:
    cipher = Rc4(base64.b64decode(signed))
    return cipher.process(base64.b64decode(payload)).decode()


def signature(method: str, url: str, params: dict[str, str], signed: str) -> str:
    path = urlsplit(url).path.replace("/app/", "/")
    parts = [method.upper(), path]
    parts.extend(f"{key}={value}" for key, value in params.items())
    parts.append(signed)
    digest = hashlib.sha1("&".join(parts).encode()).digest()
    return base64.b64encode(digest).decode()


def encrypted_params(
    url: str,
    method: str,
    signed: str,
    nonce: str,
    params: dict[str, str],
    ssecurity: str,
) -> dict[str, str]:
    fields = dict(params)
    fields["rc4_hash__"] = signature(method, url, fields, signed)
    encrypted = {key: encrypt_payload(signed, value) for key, value in fields.items()}
    encrypted["signature"] = signature(method, url, encrypted, signed)
    encrypted["ssecurity"] = ssecurity
    encrypted["_nonce"] = nonce
    return encrypted
