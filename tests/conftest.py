import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def register_project_as_package() -> None:
    package = types.ModuleType("app")
    package.__path__ = [str(PROJECT_ROOT)]
    sys.modules["app"] = package


def register_homey_sdk_stub() -> None:
    homey_package = types.ModuleType("homey")
    modules = {
        "homey.app": ("App", type("App", (), {"log": lambda self, *a: None})),
        "homey.driver": ("Driver", type("Driver", (), {})),
        "homey.device": ("Device", type("Device", (), {})),
        "homey.pair_session": ("PairSession", object),
    }
    for module_name, (attribute, value) in modules.items():
        module = types.ModuleType(module_name)
        setattr(module, attribute, value)
        sys.modules[module_name] = module
        setattr(homey_package, module_name.split(".")[1], module)
    sys.modules["homey"] = homey_package


register_project_as_package()
register_homey_sdk_stub()


pytest_plugins = [
    "tests.integration.steps.scenario_context",
    "tests.integration.steps.device_steps",
    "tests.integration.steps.homey_steps",
    "tests.integration.steps.pairing_steps",
    "tests.integration.steps.discovery_steps",
    "tests.integration.steps.account_steps",
    "tests.e2e.steps.page_steps",
]


def pytest_collection_modifyitems(items):
    items.sort(key=lambda item: item.get_closest_marker("e2e") is not None)
