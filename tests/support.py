import importlib
from types import ModuleType


def load_module(module_path: str) -> ModuleType:
    return importlib.import_module(f"app.{module_path}")
