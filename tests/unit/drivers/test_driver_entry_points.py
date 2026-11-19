import pytest
from app.endpoints.pairing_driver import MiioDriver

from tests.support import load_module

DRIVER_IDS = ["yeelink-light-bslamp2", "zhimi-fan-za4", "zhimi-humidifier-ca1"]


class TestDriverEntryPoint:
    @pytest.mark.parametrize("driver_id", DRIVER_IDS)
    def test_given_a_driver_module_when_loaded_then_it_exports_the_pairing_driver(
        self, driver_id
    ):
        module = load_module(f"drivers.{driver_id}.driver")

        assert module.homey_export is MiioDriver
