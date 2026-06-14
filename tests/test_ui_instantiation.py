# tests/test_ui_instantiation.py

import os
import sys
import matplotlib
matplotlib.use('Agg')
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# 添加路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
for folder in ['magnetics', 'power', 'control', 'signal', 'physical']:
    sys.path.insert(0, os.path.join(root_dir, 'modules', folder))

from PyQt5.QtWidgets import QApplication
from modules import get_all_modules

_APP = None


def get_app():
    global _APP
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    _APP = app
    return app


def instantiate_all_modules(verbose=False):
    get_app()
    registry = get_all_modules()
    if verbose:
        print(f"检测到注册模块数量: {len(registry)}", flush=True)

    success_count = 0
    fail_count = 0
    failures = []
    windows = []

    for win_id, win_cls in registry.items():
        try:
            if verbose:
                print(f"正在测试实例化: {win_cls.__name__} (ID: {win_id})...", end="", flush=True)
            w = win_cls()
            windows.append(w)
            assert w.window_id == win_id
            assert hasattr(w, 'category')
            assert hasattr(w, 'display_name')
            success_count += 1
            if verbose:
                print(" [OK]", flush=True)
        except Exception as e:
            fail_count += 1
            failures.append((win_id, win_cls.__name__, str(e)))
            if verbose:
                print(f" [FAILED] 错误: {e}", flush=True)

    return registry, success_count, fail_count, failures


def test_all_registered_modules_can_be_instantiated():
    registry, success_count, fail_count, failures = instantiate_all_modules(verbose=False)
    assert len(registry) >= 30
    assert fail_count == 0, failures
    assert success_count == len(registry)


def run_instantiation_test():
    registry, success_count, fail_count, failures = instantiate_all_modules(verbose=True)

    print("\n=========================================================")
    print(f"测试完毕。成功: {success_count}/{len(registry)}, 失败: {fail_count}")
    print("=========================================================")

    if fail_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    run_instantiation_test()
