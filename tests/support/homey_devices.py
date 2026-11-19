from typing import Any

from tests.support import load_module
from tests.support.fake_homey_device import FakeHomeyMixin

HOMEY_DEVICE_SETTINGS = {"polling": 10}


def make_homey_device(driver_id: str, address: str, token_hex: str) -> Any:
    module = load_module(f"drivers.{driver_id}.device")
    device_class = type("HomeyDevice", (FakeHomeyMixin, module.homey_export), {})
    device = device_class()
    device.setup_fake(
        settings=HOMEY_DEVICE_SETTINGS | {"address": address, "token": token_hex}
    )
    return device


async def set_capability_from_homey(device: Any, capability: str, value: Any) -> None:
    for key, listener in device.listeners.items():
        if isinstance(key, tuple) and capability in key:
            await listener({capability: value})
            break
        if key == capability:
            await listener(value)
            break
    else:
        raise LookupError(capability)
    device.capabilities[capability] = value
