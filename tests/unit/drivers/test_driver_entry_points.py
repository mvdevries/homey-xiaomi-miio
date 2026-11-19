import pytest
from app.endpoints.pairing_driver import MiioDriver

from tests.support import load_module

DRIVER_MODELS = {
    "yeelink-light-bslamp2": ("yeelink.light.bslamp2",),
    "zhimi-fan-za4": ("zhimi.fan.za4",),
    "zhimi-humidifier-ca1": ("zhimi.humidifier.ca1", "zhimi.humidifier.cb1"),
}


class TestDriverEntryPoint:
    @pytest.mark.parametrize("driver_id", DRIVER_MODELS)
    def test_given_a_driver_module_when_loaded_then_it_exports_a_pairing_driver(
        self, driver_id
    ):
        module = load_module(f"drivers.{driver_id}.driver")

        assert issubclass(module.homey_export, MiioDriver)

    @pytest.mark.parametrize(("driver_id", "models"), DRIVER_MODELS.items())
    def test_given_a_driver_module_when_loaded_then_it_lists_its_models(
        self, driver_id, models
    ):
        module = load_module(f"drivers.{driver_id}.driver")

        assert module.homey_export.models == models
