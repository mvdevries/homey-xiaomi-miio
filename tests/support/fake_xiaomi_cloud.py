import asyncio
import base64
import json
from typing import Any
from urllib.parse import urlsplit

from app.domain.errors import CloudTimeoutError
from app.infrastructure.http import HttpResponse
from app.infrastructure.xiaomi_cloud import LOGIN_URL
from app.infrastructure.xiaomi_signing import (
    decrypt_payload,
    encrypt_payload,
    signature,
    signed_nonce,
)

QR_URL = "https://account.xiaomi.com/qr/image.png"
POLLING_URL = "https://account.xiaomi.com/longPolling/wait"
LOCATION_URL = "https://sts.api.io.mi.com/sts/token"
QR_IMAGE = b"\x89PNG fake qr image"
USER_ID = "10001"
SSECURITY = base64.b64encode(bytes(range(16))).decode()
SERVICE_TOKEN = "fake-service-token"
POLL_PAUSE_SECONDS = 0.02


class FakeXiaomiCloud:
    def __init__(self) -> None:
        self.scanned = False
        self.homes: dict[str, list[dict[str, Any]]] = {}
        self.devices: dict[str, list[dict[str, Any]]] = {}
        self.shared_homes: dict[str, list[dict[str, Any]]] = {}
        self.broken_servers: set[str] = set()
        self.login_status = 200
        self.polling_status = 200
        self.refuse_service_token = False
        self.api_delay_seconds = 0.0
        self.requests: list[tuple[str, str]] = []
        self._cookies: dict[str, str] = {}

    def add_device(self, server: str, **info: Any) -> None:
        self.homes.setdefault(server, [{"id": 1}])
        self.devices.setdefault(server, []).append(info)

    def cookie(self, name: str) -> str | None:
        return self._cookies.get(name)

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> HttpResponse:
        self.requests.append((method, url))
        if url == LOGIN_URL:
            return self._login()
        if url == QR_URL:
            return HttpResponse(200, QR_IMAGE, "image/png")
        if url == POLLING_URL:
            return await self._poll()
        if url == LOCATION_URL:
            if not self.refuse_service_token:
                self._cookies["serviceToken"] = SERVICE_TOKEN
            return HttpResponse(200, b"ok")
        await asyncio.sleep(self.api_delay_seconds)
        return self._api(url, params or {}, cookies or {})

    def _login(self) -> HttpResponse:
        body = {
            "qr": QR_URL,
            "loginUrl": "https://account.xiaomi.com/login",
            "lp": POLLING_URL,
            "timeout": 300,
        }
        return HttpResponse(self.login_status, _wrapped(body))

    async def _poll(self) -> HttpResponse:
        if self.polling_status != 200:
            return HttpResponse(self.polling_status, b"")
        if not self.scanned:
            await asyncio.sleep(POLL_PAUSE_SECONDS)
            raise CloudTimeoutError("no scan yet")
        body = {
            "userId": USER_ID,
            "ssecurity": SSECURITY,
            "cUserId": "c-user",
            "passToken": "pass-token",
            "location": LOCATION_URL,
        }
        return HttpResponse(200, _wrapped(body))

    def _api(
        self, url: str, params: dict[str, str], cookies: dict[str, str]
    ) -> HttpResponse:
        server = urlsplit(url).hostname.split(".")[0]
        server = "cn" if server == "api" else server
        if server in self.broken_servers or cookies.get("userId") != USER_ID:
            return HttpResponse(500, b"")
        signed = signed_nonce(SSECURITY, params["_nonce"])
        received = {
            key: value
            for key, value in params.items()
            if key not in ("signature", "ssecurity", "_nonce")
        }
        if params["signature"] != signature("POST", url, received, signed):
            return HttpResponse(403, b"bad signature")
        request = json.loads(decrypt_payload(signed, params["data"]))
        answer = self._answer(server, urlsplit(url).path, request)
        return HttpResponse(200, encrypt_payload(signed, json.dumps(answer)).encode())

    def _answer(self, server: str, path: str, request: dict[str, Any]) -> dict:
        if path.endswith("/v2/homeroom/gethome"):
            return {"result": {"homelist": self.homes.get(server, [])}}
        if path.endswith("/v2/user/get_device_cnt"):
            families = self.shared_homes.get(server, [])
            return {"result": {"share": {"share_family": families}}}
        return {
            "result": {"device_info": self.devices.get(server, []) if request else None}
        }


def _wrapped(body: dict[str, Any]) -> bytes:
    return ("&&&START&&&" + json.dumps(body)).encode()
