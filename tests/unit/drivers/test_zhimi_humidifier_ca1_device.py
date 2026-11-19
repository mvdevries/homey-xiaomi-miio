import pytest
from app.domain.errors import MiioError
from app.domain.humidifier import HumidifierState
from app.endpoints.polling_device import MiioPollingDevice

from tests.support import load_module
from tests.support.fake_homey_device import FakeHomeyMixin

device_module = load_module("drivers.zhimi-humidifier-ca1.device")


class FakeHumidifier:
    def __init__(self):
        self.calls = []
        self.state = HumidifierState(True, "auto", 44, 21.0, False, 1, True, 50, False)

    async def get_state(self):
        return self.state

    async def set_power(self, on):
        self.calls.append(("power", on))

    async def set_mode(self, mode):
        self.calls.append(("mode", mode))

    async def set_target_humidity(self, humidity):
        self.calls.append(("target", humidity))

    async def set_dry(self, on):
        self.calls.append(("dry", on))

    async def set_led_brightness(self, brightness):
        self.calls.append(("led", brightness))

    async def set_buzzer(self, on):
        self.calls.append(("buzzer", on))

    async def set_child_lock(self, on):
        self.calls.append(("lock", on))


class FakeHomeyDevice(FakeHomeyMixin, device_module.HumidifierDevice):
    def __init__(self, humidifier=None):
        self.setup_fake()
        self._client = humidifier


class TestHumidifierDevice:
    def test_given_a_device_when_registering_then_all_listeners_are_set(
        self,
    ):
        device = FakeHomeyDevice()

        device.register_listeners()

        assert set(device.listeners) == {
            "onoff",
            "humidifier_mode",
            "humidifier_target_humidity",
            "humidifier_dry",
            "led_display",
            "buzzer_enabled",
            "locked",
        }

    def test_given_settings_when_creating_the_client_then_a_humidifier_is_created(
        self, monkeypatch
    ):
        created = []
        monkeypatch.setattr(
            device_module,
            "create_humidifier",
            lambda address, token: created.append(address),
        )

        FakeHomeyDevice().create_client({"address": "192.0.2.10", "token": "00" * 16})

        assert created == ["192.0.2.10"]

    async def test_given_a_humidifier_when_reading_then_the_state_is_mapped(
        self,
    ):
        humidifier = FakeHumidifier()

        capabilities = await FakeHomeyDevice(humidifier).read_capabilities(humidifier)

        assert capabilities["measure_humidity"] == 44
        assert capabilities["humidifier_target_humidity"] == "50"

    @pytest.mark.parametrize(
        ("handler", "value", "expected"),
        [
            ("_on_power", True, ("power", True)),
            ("_on_mode", "high", ("mode", "high")),
            ("_on_target_humidity", "60", ("target", 60)),
            ("_on_dry", True, ("dry", True)),
            ("_on_led_display", True, ("led", 0)),
            ("_on_led_display", False, ("led", 2)),
            ("_on_buzzer", True, ("buzzer", True)),
            ("_on_child_lock", False, ("lock", False)),
        ],
    )
    async def test_given_a_humidifier_when_a_capability_changes_then_a_command_is_sent(
        self, handler, value, expected
    ):
        humidifier = FakeHumidifier()
        device = FakeHomeyDevice(humidifier)

        await getattr(device, handler)(value)

        assert humidifier.calls == [expected]

    async def test_given_no_humidifier_when_a_command_is_sent_then_it_fails(self):
        with pytest.raises(MiioError):
            await FakeHomeyDevice()._on_power(True)

    def test_given_the_device_module_when_loaded_then_it_exports_a_polling_device(
        self,
    ):
        exported = device_module.homey_export

        assert issubclass(exported, MiioPollingDevice)
