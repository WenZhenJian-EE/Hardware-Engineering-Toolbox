# main.py

import os
import sys

import matplotlib

matplotlib.use("Agg")


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LEGACY_MODULE_DIRS = ["magnetics", "power", "control", "signal", "physical"]


def configure_import_paths():
    """Keep compatibility with older modules that still use flat imports."""
    paths = [ROOT_DIR]
    paths.extend(os.path.join(ROOT_DIR, "modules", folder) for folder in LEGACY_MODULE_DIRS)
    for path in reversed(paths):
        if path not in sys.path:
            sys.path.insert(0, path)


configure_import_paths()

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.styles import STYLESHEET
from modules import get_all_modules


ORDER_WEIGHTS = {
    "mag_transformer": 10,
    "mag_inductor": 20,
    "power_topology": 30,
    "power_dcdc": 40,
    "power_dclink": 50,
    "power_ac_3ph": 60,
    "power_dpt": 10,
    "power_budget": 20,
    "power_waveform": 30,
    "power_device": 40,
    "safe_tvs": 50,
    "power_relay": 60,
    "battery_pack": 70,
    "power_snubber": 80,
    "thermal_heatsink": 90,
    "safe_fuse": 100,
    "safe_creepage": 110,
    "power_ldo_th": 120,
    "control_loop": 10,
    "control_digital": 20,
    "filter_passive": 30,
    "emc_calc": 40,
    "power_transient": 50,
    "analog_adc": 10,
    "analog_opamp": 20,
    "sense_ct": 30,
    "sense_ntc": 40,
    "analog_pwm": 50,
    "digital_bus": 60,
    "comm_powercomm": 70,
    "pcb_tool": 10,
    "phy_wire": 20,
    "phy_rc": 30,
    "comp_cap": 40,
    "comp_r_tool": 50,
    "theory_lc": 60,
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hardware Engineering Toolbox (Pro v10.4 Modular) - By: sakana (2260799319@qq.com)")
        self.setGeometry(100, 100, 1350, 950)
        self.child_windows = {}
        self.window_mapping = get_all_modules()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(STYLESHEET)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        content_widget = QWidget()
        scroll.setWidget(content_widget)

        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        categories = {}
        for win_id, win_cls in self.window_mapping.items():
            cat_name = getattr(win_cls, "category", "6. 其他 (Other Tools)")
            categories.setdefault(cat_name, []).append((win_cls.display_name, win_cls.description, win_id))

        for group_name in sorted(categories.keys()):
            group_lbl = QLabel(group_name)
            group_lbl.setObjectName("GroupTitle")
            main_layout.addWidget(group_lbl)

            grid = QGridLayout()
            grid.setSpacing(12)
            grid.setContentsMargins(5, 0, 5, 10)

            module_list = categories[group_name]
            module_list.sort(key=lambda item: (ORDER_WEIGHTS.get(item[2], 999), item[0]))

            for i, (main_text, sub_text, win_id) in enumerate(module_list):
                btn = QPushButton(f"{main_text}\n({sub_text})")
                btn.setObjectName("ToolButton")
                btn.setCursor(Qt.PointingHandCursor)
                btn.setMinimumHeight(60)
                btn.clicked.connect(lambda checked, wid=win_id: self.open_window(wid))

                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(8)
                shadow.setColor(QColor(0, 0, 0, 20))
                shadow.setOffset(1, 2)
                btn.setGraphicsEffect(shadow)

                grid.addWidget(btn, i // 4, i % 4)

            main_layout.addLayout(grid)

        main_layout.addStretch()

        footer = QLabel("System Ready. | 硬件工程助手 Pro v10.4 (动态模块化架构)")
        footer.setStyleSheet("color: #95a5a6; font-size: 11px; margin-left: 5px; margin-top: 10px;")
        main_layout.addWidget(footer)

    def open_window(self, window_name):
        if window_name in self.child_windows:
            window = self.child_windows[window_name]
            if window.isVisible():
                window.raise_()
                window.activateWindow()
            else:
                window.show()
            return

        win_cls = self.window_mapping.get(window_name)
        if win_cls is None:
            QMessageBox.warning(self, "未找到工具", f"未找到窗口: {window_name}")
            return

        try:
            window = win_cls()
            current_size = window.size()
            if current_size.width() > 0 and current_size.height() > 0:
                window.resize(int(current_size.width() * 1.5), int(current_size.height() * 1.5))

            self.child_windows[window_name] = window
            window.show()
        except Exception as exc:
            QMessageBox.critical(self, "运行错误", f"打开窗口失败: {exc}")


def main():
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 9))

    main_win = MainWindow()
    main_win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
