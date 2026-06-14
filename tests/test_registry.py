import os
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
for folder in ["magnetics", "power", "control", "signal", "physical"]:
    path = os.path.join(ROOT_DIR, "modules", folder)
    if path not in sys.path:
        sys.path.insert(0, path)


def test_static_registry_matches_dynamic_discovery():
    from modules import get_all_modules

    static_registry = get_all_modules()
    dynamic_registry = get_all_modules(force_dynamic=True)

    assert set(static_registry) == set(dynamic_registry)
    for window_id in static_registry:
        assert static_registry[window_id].__name__ == dynamic_registry[window_id].__name__
        assert static_registry[window_id].__module__ == dynamic_registry[window_id].__module__
