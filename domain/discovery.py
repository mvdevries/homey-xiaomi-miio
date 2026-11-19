from dataclasses import dataclass

MODEL_SEPARATOR = "_"
PRODUCT_NAMES = {
    "yeelink.light.bslamp2": "Mi Bedside Lamp 2",
    "zhimi.fan.za4": "Mi Smart Standing Fan",
    "zhimi.humidifier.ca1": "Mi Smart Humidifier",
    "zhimi.humidifier.cb1": "Mi Smart Humidifier",
}


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

    @property
    def product_name(self) -> str:
        return PRODUCT_NAMES.get(self.model, "")

    def to_dict(self) -> dict:
        return {
            "address": self.address,
            "deviceId": f"{self.device_id:08x}",
            "name": self.name,
            "model": self.model,
            "productName": self.product_name,
        }


def short_hostname(hostname: str) -> str:
    return hostname.split(".", maxsplit=1)[0]
