import pytest
from app.domain.bedside_lamp import LampState
from app.domain.errors import MiioError
from app.endpoints.polling_device import MiioPollingDevice

from tests.support import load_module
from tests.support.fake_homey_device import FakeHomeyMixin

device_module = load_module("drivers.yeelink-light-bslamp2.device")

STATE = LampState(True, 50, "color", 180, 100, 4000)


class FakeLamp:
    def __init__(self):
        self.calls = []
        self.state = STATE

    async def get_state(self):
        return self.state

    async def set_power(self, on):
        self.calls.append(("power", on))

    async def set_brightness(self, brightness):
        self.calls.append(("brightness", brightness))

    async def set_hsv(self, hue, saturation):
        self.calls.append(("hsv", hue, saturation))

    async def set_color_temperature(self, kelvin):
        self.calls.append(("temperature", kelvin))


class FakeHomeyDevice(FakeHomeyMixin, device_module.BedsideLamp2Device):
    def __init__(self, lamp=None, capabilities=None):
        self.setup_fake(capabilities=capabilities)
        self._client = lamp


class TestBedsideLamp2Device:
    async def test_given_a_device_when_registering_then_all_listeners_are_set(
        self,
    ):
        device = FakeHomeyDevice()

        device.register_listeners()

        assert set(device.listeners) == {
            ("onoff", "dim"),
            ("light_temperature", "light_mode", "light_hue", "light_saturation"),
        }

    async def test_given_settings_when_creating_the_client_then_a_lamp_is_created(
        self, monkeypatch
    ):
        created = []
        monkeypatch.setattr(
            device_module,
            "create_bedside_lamp",
            lambda address, token: created.append(address),
        )

        FakeHomeyDevice().create_client({"address": "192.0.2.10", "token": "00" * 16})

        assert created == ["192.0.2.10"]

    async def test_given_a_lamp_when_reading_capabilities_then_the_state_is_mapped(
        self,
    ):
        lamp = FakeLamp()

        capabilities = await FakeHomeyDevice(lamp).read_capabilities(lamp)

        assert capabilities["onoff"] is True
        assert capabilities["dim"] == 0.5
        assert capabilities["light_mode"] == "color"

    async def test_given_a_lamp_that_is_off_when_turned_on_then_power_is_sent(self):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"onoff": False})

        await device._on_power_and_level({"onoff": True})

        assert lamp.calls == [("power", True)]
        assert device.capabilities["onoff"] is True

    async def test_given_a_lamp_that_is_on_when_turned_off_then_power_is_sent(self):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"onoff": True})

        await device._on_power_and_level({"onoff": False})

        assert lamp.calls == [("power", False)]

    async def test_given_a_lamp_that_is_on_when_turned_on_then_nothing_is_sent(self):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"onoff": True})

        await device._on_power_and_level({"onoff": True})

        assert lamp.calls == []

    async def test_given_a_lamp_that_is_on_when_dimmed_then_the_brightness_is_set(self):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"onoff": True})

        await device._on_power_and_level({"dim": 0.4})

        assert lamp.calls == [("brightness", 40)]

    async def test_given_a_lamp_that_is_off_when_dimmed_then_it_is_turned_on_first(
        self,
    ):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"onoff": False})

        await device._on_power_and_level({"dim": 0.8})

        assert lamp.calls == [("power", True), ("brightness", 80)]

    async def test_given_a_lamp_that_is_on_when_dimmed_to_zero_then_it_is_turned_off(
        self,
    ):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"onoff": True})

        await device._on_power_and_level({"dim": 0})

        assert lamp.calls == [("power", False)]
        assert device.capabilities["onoff"] is False

    async def test_given_temperature_mode_when_the_color_changes_then_kelvin_is_set(
        self,
    ):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp)

        await device._on_color({"light_mode": "temperature", "light_temperature": 0.0})

        assert lamp.calls == [("temperature", 6500)]

    async def test_given_a_stored_temperature_when_the_color_changes_then_it_is_used(
        self,
    ):
        lamp = FakeLamp()
        device = FakeHomeyDevice(
            lamp, {"light_mode": "temperature", "light_temperature": 1.0}
        )

        await device._on_color({})

        assert lamp.calls == [("temperature", 1700)]

    async def test_given_color_mode_when_the_color_changes_then_hsv_is_set(
        self,
    ):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp)

        await device._on_color(
            {"light_mode": "color", "light_hue": 1.0, "light_saturation": 0.5}
        )

        assert lamp.calls == [("hsv", 359, 50)]

    async def test_given_only_a_new_hue_when_the_color_changes_then_saturation_is_kept(
        self,
    ):
        lamp = FakeLamp()
        device = FakeHomeyDevice(lamp, {"light_hue": 0.5, "light_saturation": 0.25})

        await device._on_color({"light_hue": 0.0})

        assert lamp.calls == [("hsv", 0, 25)]

    async def test_given_no_lamp_when_a_command_is_sent_then_it_fails(self):
        with pytest.raises(MiioError):
            await FakeHomeyDevice()._on_power_and_level({"onoff": True})

    def test_given_the_device_module_when_loaded_then_it_exports_a_polling_device(
        self,
    ):
        exported = device_module.homey_export

        assert issubclass(exported, MiioPollingDevice)
