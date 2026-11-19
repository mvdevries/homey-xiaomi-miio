from app.endpoints.pairing_driver import MiioDriver

from tests.support import load_module

driver_module = load_module("drivers.zhimi-fan-za4.driver")


class TestZhimiFanZa4Driver:
    def test_given_the_driver_module_when_loaded_then_it_exports_a_pairing_driver(
        self,
    ):
        exported = driver_module.homey_export

        assert issubclass(exported, MiioDriver)
