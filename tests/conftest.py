import sys
import types


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


register_homey_sdk_stub()
