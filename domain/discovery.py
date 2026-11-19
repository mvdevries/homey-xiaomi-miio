from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiscoveredDevice:
    address: str
    device_id: int

    def to_dict(self) -> dict:
        return {"address": self.address, "deviceId": f"{self.device_id:08x}"}
