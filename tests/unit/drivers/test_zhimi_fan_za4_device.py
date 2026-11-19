import pytest
from app.domain.errors import MiioError
from app.domain.standing_fan import FanState
from app.endpoints.polling_device import MiioPollingDevice

from tests.support import load_module
from tests.support.fake_homey_device import FakeHomeyMixin

device_module = load_module("drivers.zhimi-fan-za4.device")


class FakeFan:
    def __init__(self, natural_mode=False):
        self.calls = []
        self.state = FanState(True, 40, natural_mode, True, 90, False, True, 1)

    async def get_state(self):
        return self.state

    async def set_power(self, on):
        self.calls.append(("power", on))

    async def set_speed(self, speed):
        self.calls.append(("speed", speed))

    async def set_natural_speed(self, speed):
        self.calls.append(("natural", speed))

    async def set_oscillating(self, on):
        self.calls.append(("oscillating", on))

    async def set_angle(self, angle):
        self.calls.append(("angle", angle))

    async def set_led_brightness(self, brightness):
        self.calls.append(("led", brightness))

    async def set_buzzer(self, on):
        self.calls.append(("buzzer", on))

    async def set_child_lock(self, on):
        self.calls.append(("lock", on))


class FakeHomeyDevice(FakeHomeyMixin, device_module.StandingFanDevice):
    def __init__(self, fan=None, capabilities=None):
        self.setup_fake(capabilities=capabilities)
        self._client = fan


class TestStandingFanDevice:
    def test_given_a_device_when_registering_then_all_listeners_are_set(
        self,
    ):
        device = FakeHomeyDevice()

        device.register_listeners()

        assert set(device.listeners) == {
            ("onoff", "dim"),
            "fan_oscillating",
            "fan_angle",
            "led_display",
            "buzzer_enabled",
            "locked",
        }

    def test_given_settings_when_creating_the_client_then_a_fan_is_created(
        self, monkeypatch
    ):
        created = []
        monkeypatch.setattr(
            device_module,
            "create_standing_fan",
            lambda address, token: created.append(address),
        )

        FakeHomeyDevice().create_client({"address": "192.0.2.10", "token": "00" * 16})

        assert created == ["192.0.2.10"]

    async def test_given_a_fan_when_reading_capabilities_then_the_state_is_mapped(self):
        fan = FakeFan()
        device = FakeHomeyDevice(fan)

        capabilities = await device.read_capabilities(fan)

        assert capabilities["dim"] == 0.4
        assert capabilities["fan_angle"] == 90
        assert device._natural_mode is False

    async def test_given_natural_mode_when_reading_capabilities_then_it_is_remembered(
        self,
    ):
        fan = FakeFan(natural_mode=True)
        device = FakeHomeyDevice(fan)

        await device.read_capabilities(fan)

        assert device._natural_mode is True

    async def test_given_a_fan_that_is_off_when_turned_on_then_power_is_sent(self):
        fan = FakeFan()
        device = FakeHomeyDevice(fan, {"onoff": False})

        await device._on_power_and_level({"onoff": True})

        assert fan.calls == [("power", True)]

    async def test_given_a_fan_that_is_on_when_dimmed_then_the_direct_speed_is_set(
        self,
    ):
        fan = FakeFan()
        device = FakeHomeyDevice(fan, {"onoff": True})

        await device._on_power_and_level({"dim": 0.6})

        assert fan.calls == [("speed", 60)]

    async def test_given_natural_mode_when_dimmed_then_the_natural_speed_is_set(self):
        fan = FakeFan()
        device = FakeHomeyDevice(fan, {"onoff": True})
        device._natural_mode = True

        await device._on_power_and_level({"dim": 0.6})

        assert fan.calls == [("natural", 60)]

    async def test_given_a_fan_that_is_on_when_dimmed_to_zero_then_it_is_turned_off(
        self,
    ):
        fan = FakeFan()
        device = FakeHomeyDevice(fan, {"onoff": True})

        await device._on_power_and_level({"dim": 0})

        assert fan.calls == [("power", False)]
        assert device.capabilities["onoff"] is False

    @pytest.mark.parametrize(
        ("capability", "value", "expected"),
        [
            ("fan_oscillating", True, ("oscillating", True)),
            ("fan_angle", 120.0, ("angle", 120)),
            ("led_display", False, ("led", 2)),
            ("led_display", True, ("led", 0)),
            ("buzzer_enabled", False, ("buzzer", False)),
            ("locked", True, ("lock", True)),
        ],
    )
    async def test_given_a_fan_when_a_capability_changes_then_the_command_is_sent(
        self, capability, value, expected
    ):
        fan = FakeFan()
        device = FakeHomeyDevice(fan)

        device.register_listeners()

        await device.listeners[capability](value)

        assert fan.calls == [expected]

    async def test_given_no_fan_when_a_command_is_sent_then_it_fails(self):
        with pytest.raises(MiioError):
            device = FakeHomeyDevice()
            device.register_listeners()
            await device.listeners["fan_oscillating"](True)

    def test_given_the_device_module_when_loaded_then_it_exports_a_polling_device(
        self,
    ):
        exported = device_module.homey_export

        assert issubclass(exported, MiioPollingDevice)
