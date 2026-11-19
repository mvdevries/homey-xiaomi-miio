from typing import Any

from tests.support.fake_device import FakeDevice, start_fake_device

DEVICE_TOKEN_HEX = "00112233445566778899aabbccddeeff"
DEVICE_TOKEN = bytes.fromhex(DEVICE_TOKEN_HEX)
DEVICE_ADDRESS = "192.0.2.10"
DEVICE_POWERED_OFF_CODE = -6011
INVALID_ARGUMENT_CODE = -5001
UNKNOWN_METHOD_CODE = -32601


def ok(payload: dict[str, Any], result: Any = None) -> dict[str, Any]:
    return {"id": payload["id"], "result": ["ok"] if result is None else result}


def failure(payload: dict[str, Any], code: int, message: str) -> dict[str, Any]:
    return {"id": payload["id"], "error": {"code": code, "message": message}}


class FakeMiioDevice:
    model = "generic.device"
    properties: dict[str, Any]

    def __init__(self) -> None:
        self.silent = False
        self.port = 0
        self.requests: list[dict[str, Any]] = []
        self._device: FakeDevice | None = None

    async def start(self) -> None:
        self._device, self.port = await start_fake_device(
            DEVICE_TOKEN, responder=self.respond
        )

    def stop(self) -> None:
        if self._device is not None:
            self._device.close()

    def respond(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if self.silent:
            return None
        self.requests.append(payload)
        handler = getattr(
            self, f"handle_{payload['method'].replace('.', '_').lower()}", None
        )
        if handler is None:
            return failure(payload, UNKNOWN_METHOD_CODE, "method not supported")
        return handler(payload)

    def handle_miio_info(self, payload: dict[str, Any]) -> dict[str, Any]:
        return ok(payload, {"model": self.model, "token": DEVICE_TOKEN_HEX})

    def handle_get_prop(self, payload: dict[str, Any]) -> dict[str, Any]:
        names = payload["params"]
        return ok(payload, [self.properties.get(name) for name in names])

    def switch(self, payload: dict[str, Any], name: str) -> dict[str, Any]:
        self.properties[name] = payload["params"][0]
        return ok(payload)

    def received(self, method: str) -> list[dict[str, Any]]:
        return [request for request in self.requests if request["method"] == method]


class FakeBedsideLamp(FakeMiioDevice):
    model = "yeelink.light.bslamp2"

    def __init__(self) -> None:
        super().__init__()
        self.properties = {
            "power": "on",
            "bright": 50,
            "color_mode": 3,
            "rgb": 0,
            "hue": 120,
            "sat": 80,
            "ct": 4000,
        }

    def handle_set_power(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "power")

    def handle_set_bright(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "bright")

    def handle_set_hsv(self, payload: dict[str, Any]) -> dict[str, Any]:
        hue, saturation = payload["params"][:2]
        self.properties.update(hue=hue, sat=saturation, color_mode=3)
        return ok(payload)

    def handle_set_ct_abx(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.properties.update(ct=payload["params"][0], color_mode=2)
        return ok(payload)


class FakeStandingFan(FakeMiioDevice):
    model = "zhimi.fan.za4"
    valid_angles = (30, 60, 90, 120)

    def __init__(self) -> None:
        super().__init__()
        self.properties = {
            "power": "off",
            "angle": 90,
            "angle_enable": "off",
            "speed_level": 40,
            "natural_level": 0,
            "child_lock": "off",
            "buzzer": 0,
            "led_b": 0,
        }

    def handle_set_power(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "power")

    def handle_set_speed_level(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.properties.update(speed_level=payload["params"][0], natural_level=0)
        return ok(payload)

    def handle_set_natural_level(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.properties.update(natural_level=payload["params"][0], speed_level=0)
        return ok(payload)

    def handle_set_angle_enable(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "angle_enable")

    def handle_set_angle(self, payload: dict[str, Any]) -> dict[str, Any]:
        angle = payload["params"][0]
        if angle not in self.valid_angles:
            return failure(payload, INVALID_ARGUMENT_CODE, "invalid arg")
        self.properties["angle"] = angle
        return ok(payload)

    def handle_set_led_b(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "led_b")

    def handle_set_buzzer(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "buzzer")

    def handle_set_child_lock(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "child_lock")


class FakeHumidifier(FakeMiioDevice):
    model = "zhimi.humidifier.ca1"

    def __init__(self) -> None:
        super().__init__()
        self.properties = {
            "power": "off",
            "mode": "auto",
            "humidity": 41,
            "temp_dec": 215,
            "buzzer": "off",
            "led_b": "0",
            "child_lock": "off",
            "limit_hum": 50,
            "dry": "off",
        }

    def handle_set_power(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "power")

    def handle_set_mode(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.properties["power"] != "on":
            return failure(payload, DEVICE_POWERED_OFF_CODE, "device_poweroff")
        return self.switch(payload, "mode")

    def handle_set_limit_hum(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "limit_hum")

    def handle_set_dry(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "dry")

    def handle_set_led_b(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "led_b")

    def handle_set_buzzer(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "buzzer")

    def handle_set_child_lock(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.switch(payload, "child_lock")
