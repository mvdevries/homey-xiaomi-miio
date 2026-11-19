import base64
from dataclasses import dataclass

SERVERS = ("cn", "de", "us", "ru", "tw", "sg", "in", "i2")
DEFAULT_IMAGE_TYPE = "image/png"

STATE_PENDING = "pending"
STATE_SIGNED_IN = "signed_in"
STATE_EXPIRED = "expired"
STATE_FAILED = "failed"
STATE_IDLE = "idle"


@dataclass(frozen=True, slots=True)
class QrChallenge:
    image: bytes
    login_url: str
    polling_url: str
    timeout_seconds: int
    image_type: str = DEFAULT_IMAGE_TYPE

    @property
    def image_data_uri(self) -> str:
        encoded = base64.b64encode(self.image).decode()
        return f"data:{self.image_type};base64,{encoded}"


@dataclass(frozen=True, slots=True)
class CloudDevice:
    did: str
    name: str
    model: str
    token: str
    address: str
    server: str

    def to_dict(self) -> dict:
        return {
            "did": self.did,
            "name": self.name,
            "model": self.model,
            "token": self.token,
            "address": self.address,
            "server": self.server,
        }


def keep_supported(
    devices: list[CloudDevice], models: tuple[str, ...]
) -> list[CloudDevice]:
    if not models:
        return list(devices)
    return [device for device in devices if device.model in models]


def unique_by_id(devices: list[CloudDevice]) -> list[CloudDevice]:
    unique: dict[str, CloudDevice] = {}
    for device in devices:
        unique.setdefault(device.did, device)
    return list(unique.values())


def device_from_cloud(info: dict, server: str) -> CloudDevice | None:
    token = str(info.get("token") or "")
    model = str(info.get("model") or "")
    if not token or not model:
        return None
    return CloudDevice(
        did=str(info.get("did") or ""),
        name=str(info.get("name") or ""),
        model=model,
        token=token,
        address=str(info.get("localip") or ""),
        server=server,
    )
