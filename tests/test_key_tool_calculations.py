import os
import sys

import matplotlib
matplotlib.use("Agg")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
for folder in ["magnetics", "power", "control", "signal", "physical"]:
    path = os.path.join(ROOT_DIR, "modules", folder)
    if path not in sys.path:
        sys.path.insert(0, path)


from PyQt5.QtWidgets import QApplication

_APP = None


def get_app():
    global _APP
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    _APP = app
    return app


def test_new_high_frequency_tools_calculate_with_defaults():
    get_app()

    from modules.control.emc_filter_radiated import EmcCalculatorWindow
    from modules.physical.comp_capacitor_life import CapacitorToolWindow
    from modules.power.dcdc_basic import DcdcCalculatorWindow
    from modules.power.power_device_driver import DeviceCompareTab
    from modules.signal.analog_adc_afe import AdcCalibrationWindow

    device = DeviceCompareTab()
    device.calc_compare()
    assert "Rank by total estimated loss" in device.cmp_summary.toPlainText()

    dcdc = DcdcCalculatorWindow()
    dcdc.calc_flyback_detail()
    assert dcdc.fbd_res["lm"].text().endswith("uH")
    assert dcdc.fbd_res["vds"].text().endswith("V")

    adc = AdcCalibrationWindow()
    adc.calc_sampling_budget()
    assert adc.sb_res["fc"].text().endswith("kHz")
    assert "LSB" in adc.sb_res["lsb"].text()

    emc = EmcCalculatorWindow()
    emc.calc_conducted_fix()
    assert emc.fix_res["need"].text().endswith("dB")
    assert "nF" in emc.fix_res["cy"].text()

    cap = CapacitorToolWindow()
    cap.calc_topology_rms()
    assert cap.topo_res_rms.text().endswith("A")
    assert cap.topo_res_loss.text().endswith("W")
