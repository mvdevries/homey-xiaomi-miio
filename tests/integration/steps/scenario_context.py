from dataclasses import dataclass, field
from typing import Any

import pytest

from tests.support.fake_miio_devices import (
    DEVICE_ADDRESS,
    DEVICE_TOKEN_HEX,
    FakeMiioDevice,
)
from tests.support.homey_devices import make_homey_device
from tests.support.loop_harness import LoopHarness, wait_until
from tests.support.loopback import install_loopback_transport

DRIVER_IDS = {
    "lamp": "yeelink-light-bslamp2",
    "fan": "zhimi-fan-za4",
    "humidifier": "zhimi-humidifier-ca1",
}


@dataclass
class ScenarioContext:
    harness: LoopHarness
    ports: dict[str, int] = field(default_factory=dict)
    kind: str = ""
    fake: FakeMiioDevice | None = None
    homey_device: Any = None
    pairing_result: dict[str, Any] | None = None
    pairing_error: Exception | None = None

    def call(self, coroutine: Any) -> Any:
        return self.harness.call(coroutine)

    def add_fake_device(self, kind: str, fake: FakeMiioDevice) -> None:
        self.call(fake.start())
        self.kind = kind
        self.fake = fake
        self.ports[DEVICE_ADDRESS] = fake.port

    def add_device_to_homey(self) -> None:
        self.homey_device = make_homey_device(
            DRIVER_IDS[self.kind], DEVICE_ADDRESS, DEVICE_TOKEN_HEX
        )
        self.call(self.homey_device.on_init())
        wait_until(self.homey_has_answered)

    def homey_has_answered(self) -> bool:
        device = self.homey_device
        return bool(device.capabilities) or not device.available

    def stop_everything(self) -> None:
        if self.homey_device is not None:
            self.call(self.homey_device.on_uninit())
        if self.fake is not None:
            self.fake.stop()


@pytest.fixture
def scenario(monkeypatch):
    harness = LoopHarness()
    harness.start()
    context = ScenarioContext(harness=harness)
    install_loopback_transport(monkeypatch, context.ports)
    yield context
    context.stop_everything()
    harness.stop()
