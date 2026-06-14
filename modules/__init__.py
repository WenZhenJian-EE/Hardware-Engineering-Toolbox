# modules/__init__.py

import importlib
import inspect
import os
import traceback

from modules.base_module import BaseModule


SKIP_FILES = {"base_module.py", "static_registry.py"}


def _iter_module_names():
    current_dir = os.path.dirname(__file__)
    for root, _, files in os.walk(current_dir):
        for file_name in files:
            if not file_name.endswith(".py") or file_name.startswith("__") or file_name in SKIP_FILES:
                continue
            relative_path = os.path.relpath(os.path.join(root, file_name), current_dir)
            module_parts = relative_path[:-3].replace(os.path.sep, ".")
            yield f"modules.{module_parts}"


def _discover_modules():
    registry = {}
    for module_name in sorted(_iter_module_names()):
        try:
            mod = importlib.import_module(module_name)
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if obj.__module__ != mod.__name__:
                    continue
                if issubclass(obj, BaseModule) and obj is not BaseModule and obj.window_id:
                    registry[obj.window_id] = obj
        except Exception as exc:
            print(f"[modules] Failed to load {module_name}: {exc}")
    return dict(sorted(registry.items()))


def get_all_modules(force_dynamic=False):
    """
    Return all registered calculator windows.

    Normal app and packaged runs use modules/static_registry.py for deterministic
    imports. Tests and tools can pass force_dynamic=True to scan source files.
    """
    if not force_dynamic:
        try:
            from modules import static_registry
            if hasattr(static_registry, "REGISTRY"):
                return dict(sorted(static_registry.REGISTRY.items()))
        except ImportError as exc:
            if exc.name not in ("modules.static_registry", "static_registry", "modules"):
                print("[modules] Static registry import failed because of an internal dependency error:")
                traceback.print_exc()

    return _discover_modules()
