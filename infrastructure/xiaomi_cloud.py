import asyncio
import json
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from ..domain.errors import (
    CloudRequestError,
    CloudTimeoutError,
    LoginExpiredError,
    LoginFailedError,
)
from ..domain.xiaomi_account import (
    CloudDevice,
    QrChallenge,
    device_from_cloud,
)
from .http import START_MARKER, HttpResponse
from .xiaomi_signing import (
    decrypt_payload,
    encrypted_params,
    generate_nonce,
    signed_nonce,
)

LOGGER = logging.getLogger(__name__)
LOGIN_URL = "https://account.xiaomi.com/longPolling/loginUrl"
SERVICE_ID = "xiaomiio"
POLL_TIMEOUT_SECONDS = 10.0
POLL_RETRY_SECONDS = 1.0
CLIENT_VERSION = "APP/com.xiaomi.mihome APPV/10.5.201"
HOMES_PATH = "/v2/homeroom/gethome"
DEVICES_PATH = "/v2/home/home_device_list"
SHARED_PATH = "/v2/user/get_device_cnt"
HOMES_DATA = json.dumps(
    {
        "fg": True,
        "fetch_share": True,
        "fetch_share_dev": True,
        "limit": 300,
        "app_ver": 7,
    }
)
SHARED_DATA = json.dumps({"fetch_own": True, "fetch_share": True})


class Http(Protocol):
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        timeout_seconds: float = ...,
    ) -> HttpResponse: ...

    def cookie(self, name: str) -> str | None: ...


def parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text.replace(START_MARKER, ""))
    except ValueError as error:
        raise CloudRequestError("Response is not JSON") from error


def build_agent() -> str:
    letters = "".join(chr(random.randint(97, 122)) for _ in range(18))
    capitals = "".join(chr(random.randint(65, 69)) for _ in range(13))
    return f"{letters}-{capitals} {CLIENT_VERSION}"


def api_url(server: str, path: str) -> str:
    prefix = "" if server == "cn" else f"{server}."
    return f"https://{prefix}api.io.mi.com/app{path}"


class XiaomiCloudSession:
    def __init__(
        self,
        http: Http,
        *,
        user_id: str,
        ssecurity: str,
        service_token: str,
        agent: str,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._http = http
        self._user_id = user_id
        self._ssecurity = ssecurity
        self._service_token = service_token
        self._agent = agent
        self._clock = clock

    async def list_devices(self, server: str) -> list[CloudDevice]:
        devices: list[CloudDevice] = []
        for home in await self._homes(server):
            for info in await self._home_devices(server, home):
                device = device_from_cloud(info, server)
                if device is not None:
                    devices.append(device)
        return devices

    async def _homes(self, server: str) -> list[dict[str, Any]]:
        homes: list[dict[str, Any]] = []
        own = await self._call(server, HOMES_PATH, HOMES_DATA)
        for home in _nested(own, "result", "homelist") or []:
            homes.append({"home_id": home["id"], "home_owner": self._user_id})
        shared = await self._call(server, SHARED_PATH, SHARED_DATA)
        for home in _nested(shared, "result", "share", "share_family") or []:
            homes.append({"home_id": home["home_id"], "home_owner": home["home_owner"]})
        return homes

    async def _home_devices(
        self, server: str, home: dict[str, Any]
    ) -> list[dict[str, Any]]:
        data = json.dumps(
            {
                "home_owner": home["home_owner"],
                "home_id": home["home_id"],
                "limit": 200,
                "get_split_device": True,
                "support_smart_home": True,
            }
        )
        response = await self._call(server, DEVICES_PATH, data)
        return _nested(response, "result", "device_info") or []

    async def _call(self, server: str, path: str, data: str) -> dict[str, Any]:
        url = api_url(server, path)
        nonce = generate_nonce(round(self._clock() * 1000))
        signed = signed_nonce(self._ssecurity, nonce)
        fields = encrypted_params(
            url, "POST", signed, nonce, {"data": data}, self._ssecurity
        )
        response = await self._http.request(
            "POST",
            url,
            params=fields,
            headers=self._headers(),
            cookies=self._cookies(),
        )
        if response.status != 200:
            raise CloudRequestError(f"Cloud answered {response.status}")
        decrypted = decrypt_payload(
            signed_nonce(self._ssecurity, fields["_nonce"]), response.text
        )
        return parse_json(decrypted)

    def _headers(self) -> dict[str, str]:
        return {
            "Accept-Encoding": "identity",
            "User-Agent": self._agent,
            "Content-Type": "application/x-www-form-urlencoded",
            "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
            "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        }

    def _cookies(self) -> dict[str, str]:
        return {
            "userId": self._user_id,
            "yetAnotherServiceToken": self._service_token,
            "serviceToken": self._service_token,
            "locale": "en_GB",
            "timezone": "GMT+02:00",
            "is_daylight": "1",
            "dst_offset": "3600000",
            "channel": "MI_APP_STORE",
        }


def _nested(data: dict[str, Any] | None, *keys: str) -> Any:
    node: Any = data
    for key in keys:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return node


class XiaomiCloudClient:
    def __init__(
        self,
        http: Http,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._http = http
        self._clock = clock
        self._sleep = sleep
        self._agent = build_agent()

    async def request_qr(self) -> QrChallenge:
        response = await self._http.request(
            "GET", LOGIN_URL, params=self._login_parameters()
        )
        if response.status != 200:
            raise CloudRequestError(f"Cloud answered {response.status}")
        data = parse_json(response.text)
        if "qr" not in data:
            raise CloudRequestError("Cloud sent no QR code")
        image = await self._http.request("GET", data["qr"])
        if image.status != 200:
            raise CloudRequestError(f"Cloud answered {image.status} for the QR code")
        return QrChallenge(
            image=image.body,
            login_url=data["loginUrl"],
            polling_url=data["lp"],
            timeout_seconds=int(data["timeout"]),
            image_type=_image_type(image.content_type),
        )

    async def wait_for_scan(self, challenge: QrChallenge) -> XiaomiCloudSession:
        answer = await self._poll(challenge)
        LOGGER.warning("Login poll: the QR code was scanned")
        service_token = await self._service_token(answer["location"])
        LOGGER.warning("Login: the service token was received")
        return XiaomiCloudSession(
            self._http,
            user_id=str(answer["userId"]),
            ssecurity=answer["ssecurity"],
            service_token=service_token,
            agent=self._agent,
        )

    async def _poll(self, challenge: QrChallenge) -> dict[str, Any]:
        deadline = self._clock() + challenge.timeout_seconds
        while self._clock() < deadline:
            try:
                response = await self._http.request(
                    "GET", challenge.polling_url, timeout_seconds=POLL_TIMEOUT_SECONDS
                )
            except CloudTimeoutError:
                LOGGER.warning("Login poll: no answer yet")
                continue
            LOGGER.warning("Login poll: status %s", response.status)
            if response.status == 200:
                return _login_answer(parse_json(response.text))
            await self._sleep(POLL_RETRY_SECONDS)
        raise LoginExpiredError("The QR code expired")

    async def _service_token(self, location: str) -> str:
        response = await self._http.request(
            "GET",
            location,
            headers={"content-type": "application/x-www-form-urlencoded"},
        )
        token = self._http.cookie("serviceToken")
        if response.status != 200 or not token:
            raise LoginFailedError("The cloud sent no service token")
        return token

    @staticmethod
    def _login_parameters() -> dict[str, str]:
        return {
            "_qrsize": "480",
            "qs": f"%3Fsid%3D{SERVICE_ID}%26_json%3Dtrue",
            "callback": "https://sts.api.io.mi.com/sts",
            "_hasLogo": "false",
            "sid": SERVICE_ID,
            "serviceParam": "",
            "_locale": "en_GB",
            "_dc": str(int(time.time() * 1000)),
        }


def _login_answer(data: dict[str, Any]) -> dict[str, Any]:
    if not all(key in data for key in ("userId", "ssecurity", "location")):
        raise LoginFailedError("The login answer is incomplete")
    return data


def _image_type(content_type: str) -> str:
    media_type = content_type.split(";", maxsplit=1)[0].strip()
    return media_type if media_type.startswith("image/") else "image/png"
