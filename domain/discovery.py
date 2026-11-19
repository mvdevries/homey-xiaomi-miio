from dataclasses import dataclass

MODEL_SEPARATOR = "_"


@dataclass(frozen=True, slots=True)
class DiscoveredDevice:
    address: str
    device_id: int
    name: str = ""

    @property
    def model(self) -> str:
        if MODEL_SEPARATOR not in self.name:
            return ""
        return self.name.split(MODEL_SEPARATOR)[0].replace("-", ".")

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "deviceId": f"{self.device_id:08x}",
            "name": self.name,
            "model": self.model,
        }


def short_hostname(hostname: str) -> str:
    return hostname.split(".", maxsplit=1)[0]
