import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QComboBox)
from PyQt5.QtCore import Qt
from utils import render_formula

# ----------------- 辅助函数 -----------------
def get_val(widget, unit_widget):
    try:
        val = float(widget.text())
        u = unit_widget.currentText()
        if u == "kΩ": return val * 1e3
        if u == "MΩ": return val * 1e6
        if u == "uF": return val * 1e-6
        if u == "nF": return val * 1e-9
        if u == "pF": return val * 1e-12
        if u == "uH": return val * 1e-6
        if u == "mH": return val * 1e-3
        if u == "kHz": return val * 1e3
        if u == "MHz": return val * 1e6
        return val
    except:
        return 0

def format_freq(val):
    if val >= 1e6: return f"{val/1e6:.3f} MHz"
    if val >= 1e3: return f"{val/1e3:.3f} kHz"
    return f"{val:.3f} Hz"

def format_res(val):
    if val >= 1e6: return f"{val/1e6:.3f} MΩ"
    if val >= 1e3: return f"{val/1e3:.3f} kΩ"
    return f"{val:.3f} Ω"

def format_cap(val):
    if val < 1e-9: return f"{val*1e12:.3f} pF"
    if val < 1e-6: return f"{val*1e9:.3f} nF"
    return f"{val*1e6:.3f} uF"

def format_ind(val):
    if val < 1e-3: return f"{val*1e6:.3f} uH"
    return f"{val*1e3:.3f} mH"

# ==============================================================================
# Tab 1: RC Filter
# ==============================================================================
class RcFilterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("计算目标:"))
        self.rc_mode = QComboBox()
        self.rc_mode.addItems(["计算截止频率 fc (已知 R, C)", "计算电阻 R (已知 fc, C)", "计算电容 C (已知 fc, R)"])
        self.rc_mode.currentIndexChanged.connect(self.update_rc_inputs)
        mode_layout.addWidget(self.rc_mode)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        grp = QGroupBox("参数设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.rc_r_label = QLabel("电阻 (R):")
        self.rc_r_val = QLineEdit("10")
        self.rc_r_unit = QComboBox(); self.rc_r_unit.addItems(["kΩ", "Ω", "MΩ"])
        w_r = QWidget(); l_r = QHBoxLayout(w_r); l_r.setContentsMargins(0,0,0,0); l_r.addWidget(self.rc_r_val); l_r.addWidget(self.rc_r_unit)
        grid.addWidget(self.rc_r_label, 0, 0); grid.addWidget(w_r, 0, 1)
        
        self.rc_c_label = QLabel("电容 (C):")
        self.rc_c_val = QLineEdit("100")
        self.rc_c_unit = QComboBox(); self.rc_c_unit.addItems(["nF", "pF", "uF"])
        w_c = QWidget(); l_c = QHBoxLayout(w_c); l_c.setContentsMargins(0,0,0,0); l_c.addWidget(self.rc_c_val); l_c.addWidget(self.rc_c_unit)
        grid.addWidget(self.rc_c_label, 1, 0); grid.addWidget(w_c, 1, 1)
        
        self.rc_fc_label = QLabel("截止频率 (fc):")
        self.rc_fc_val = QLineEdit()
        self.rc_fc_unit = QComboBox(); self.rc_fc_unit.addItems(["kHz", "Hz", "MHz"])
        w_f = QWidget(); l_f = QHBoxLayout(w_f); l_f.setContentsMargins(0,0,0,0); l_f.addWidget(self.rc_fc_val); l_f.addWidget(self.rc_fc_unit)
        grid.addWidget(self.rc_fc_label, 2, 0); grid.addWidget(w_f, 2, 1)
        
        grp.setLayout(grid)
        layout.addWidget(grp)
        
        btn = QPushButton("计算")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_rc)
        layout.addWidget(btn)
        
        res_grp = QGroupBox("计算结果")
        res_layout = QHBoxLayout()
        self.rc_result = QLabel("结果将显示在这里")
        self.rc_result.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        
        self.rc_formula = QLabel()
        self.rc_formula.setPixmap(render_formula(r'f_c = \frac{1}{2\pi R C}'))
        
        res_layout.addWidget(self.rc_result)
        res_layout.addStretch()
        res_layout.addWidget(self.rc_formula)
        res_grp.setLayout(res_layout)
        layout.addWidget(res_grp)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_rc_inputs()

    def update_rc_inputs(self):
        idx = self.rc_mode.currentIndex()
        self.rc_r_val.setReadOnly(False); self.rc_r_val.setStyleSheet("")
        self.rc_c_val.setReadOnly(False); self.rc_c_val.setStyleSheet("")
        self.rc_fc_val.setReadOnly(False); self.rc_fc_val.setStyleSheet("")
        style_dis = "background-color: #f0f0f0; color: #888;"
        
        if idx == 0:
            self.rc_fc_val.setReadOnly(True); self.rc_fc_val.setStyleSheet(style_dis); self.rc_fc_val.setText("")
            self.rc_formula.setPixmap(render_formula(r'f_c = \frac{1}{2\pi R C}'))
        elif idx == 1:
            self.rc_r_val.setReadOnly(True); self.rc_r_val.setStyleSheet(style_dis); self.rc_r_val.setText("")
            self.rc_formula.setPixmap(render_formula(r'R = \frac{1}{2\pi f_c C}'))
        else:
            self.rc_c_val.setReadOnly(True); self.rc_c_val.setStyleSheet(style_dis); self.rc_c_val.setText("")
            self.rc_formula.setPixmap(render_formula(r'C = \frac{1}{2\pi R f_c}'))

    def calc_rc(self):
        try:
            idx = self.rc_mode.currentIndex()
            if idx == 0:
                r = get_val(self.rc_r_val, self.rc_r_unit)
                c = get_val(self.rc_c_val, self.rc_c_unit)
                if r*c == 0: raise ValueError
                fc = 1 / (2 * math.pi * r * c)
                self.rc_result.setText(f"截止频率 fc = {format_freq(fc)}")
                self.rc_fc_val.setText(f"{fc/1000:.3f}") 
            elif idx == 1:
                fc = get_val(self.rc_fc_val, self.rc_fc_unit)
                c = get_val(self.rc_c_val, self.rc_c_unit)
                if fc*c == 0: raise ValueError
                r = 1 / (2 * math.pi * fc * c)
                self.rc_result.setText(f"所需电阻 R = {format_res(r)}")
                self.rc_r_val.setText(f"{r/1000:.3f}") 
            else:
                fc = get_val(self.rc_fc_val, self.rc_fc_unit)
                r = get_val(self.rc_r_val, self.rc_r_unit)
                if fc*r == 0: raise ValueError
                c = 1 / (2 * math.pi * fc * r)
                self.rc_result.setText(f"所需电容 C = {format_cap(c)}")
                self.rc_c_val.setText(f"{c*1e9:.3f}")
        except:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# Tab 2: LC Filter
# ==============================================================================
class LcFilterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("计算目标:"))
        self.lc_mode = QComboBox()
        self.lc_mode.addItems(["计算截止频率 fc (已知 L, C)", "计算电感 L (已知 fc, C)", "计算电容 C (已知 fc, L)"])
        self.lc_mode.currentIndexChanged.connect(self.update_lc_inputs)
        mode_layout.addWidget(self.lc_mode)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        grp = QGroupBox("参数设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.lc_l_label = QLabel("电感 (L):")
        self.lc_l_val = QLineEdit("10")
        self.lc_l_unit = QComboBox(); self.lc_l_unit.addItems(["uH", "mH", "H"])
        w_l = QWidget(); l_l = QHBoxLayout(w_l); l_l.setContentsMargins(0,0,0,0); l_l.addWidget(self.lc_l_val); l_l.addWidget(self.lc_l_unit)
        grid.addWidget(self.lc_l_label, 0, 0); grid.addWidget(w_l, 0, 1)
        
        self.lc_c_label = QLabel("电容 (C):")
        self.lc_c_val = QLineEdit("100")
        self.lc_c_unit = QComboBox(); self.lc_c_unit.addItems(["uF", "nF", "pF"])
        w_c = QWidget(); l_c = QHBoxLayout(w_c); l_c.setContentsMargins(0,0,0,0); l_c.addWidget(self.lc_c_val); l_c.addWidget(self.lc_c_unit)
        grid.addWidget(self.lc_c_label, 1, 0); grid.addWidget(w_c, 1, 1)
        
        self.lc_fc_label = QLabel("截止/谐振频率 (fc):")
        self.lc_fc_val = QLineEdit()
        self.lc_fc_unit = QComboBox(); self.lc_fc_unit.addItems(["kHz", "Hz", "MHz"])
        w_f = QWidget(); l_f = QHBoxLayout(w_f); l_f.setContentsMargins(0,0,0,0); l_f.addWidget(self.lc_fc_val); l_f.addWidget(self.lc_fc_unit)
        grid.addWidget(self.lc_fc_label, 2, 0); grid.addWidget(w_f, 2, 1)
        
        grp.setLayout(grid)
        layout.addWidget(grp)
        
        btn = QPushButton("计算")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_lc)
        layout.addWidget(btn)
        
        res_grp = QGroupBox("计算结果")
        res_layout = QGridLayout()
        
        self.lc_result = QLabel("---")
        self.lc_result.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        res_layout.addWidget(self.lc_result, 0, 0, 1, 2)
        
        self.lc_z0 = QLabel("特征阻抗 Zo: ---")
        self.lc_z0.setStyleSheet("color: #2980b9; font-weight: bold;")
        res_layout.addWidget(self.lc_z0, 1, 0)
        
        self.lc_formula = QLabel()
        self.lc_formula.setPixmap(render_formula(r'f_c = \frac{1}{2\pi \sqrt{LC}}'))
        res_layout.addWidget(self.lc_formula, 1, 1)
        
        res_grp.setLayout(res_layout)
        layout.addWidget(res_grp)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_lc_inputs()

    def update_lc_inputs(self):
        idx = self.lc_mode.currentIndex()
        self.lc_l_val.setReadOnly(False); self.lc_l_val.setStyleSheet("")
        self.lc_c_val.setReadOnly(False); self.lc_c_val.setStyleSheet("")
        self.lc_fc_val.setReadOnly(False); self.lc_fc_val.setStyleSheet("")
        style_dis = "background-color: #f0f0f0; color: #888;"
        
        if idx == 0:
            self.lc_fc_val.setReadOnly(True); self.lc_fc_val.setStyleSheet(style_dis); self.lc_fc_val.setText("")
            self.lc_formula.setPixmap(render_formula(r'f_c = \frac{1}{2\pi \sqrt{LC}}, \quad Z_0 = \sqrt{\frac{L}{C}}'))
        elif idx == 1:
            self.lc_l_val.setReadOnly(True); self.lc_l_val.setStyleSheet(style_dis); self.lc_l_val.setText("")
            self.lc_formula.setPixmap(render_formula(r'L = \frac{1}{C (2\pi f_c)^2}'))
        else:
            self.lc_c_val.setReadOnly(True); self.lc_c_val.setStyleSheet(style_dis); self.lc_c_val.setText("")
            self.lc_formula.setPixmap(render_formula(r'C = \frac{1}{L (2\pi f_c)^2}'))

    def calc_lc(self):
        try:
            idx = self.lc_mode.currentIndex()
            l = 0; c = 0; fc = 0
            
            if idx == 0:
                l = get_val(self.lc_l_val, self.lc_l_unit)
                c = get_val(self.lc_c_val, self.lc_c_unit)
                if l*c <= 0: raise ValueError
                fc = 1 / (2 * math.pi * math.sqrt(l*c))
                self.lc_result.setText(f"截止频率 fc = {format_freq(fc)}")
                self.lc_fc_val.setText(f"{fc/1000:.3f}")
            elif idx == 1:
                fc = get_val(self.lc_fc_val, self.lc_fc_unit)
                c = get_val(self.lc_c_val, self.lc_c_unit)
                if fc*c <= 0: raise ValueError
                l = 1 / (c * (2 * math.pi * fc)**2)
                self.lc_result.setText(f"所需电感 L = {format_ind(l)}")
                self.lc_l_val.setText(f"{l*1e6:.3f}")
            else:
                fc = get_val(self.lc_fc_val, self.lc_fc_unit)
                l = get_val(self.lc_l_val, self.lc_l_unit)
                if fc*l <= 0: raise ValueError
                c = 1 / (l * (2 * math.pi * fc)**2)
                self.lc_result.setText(f"所需电容 C = {format_cap(c)}")
                self.lc_c_val.setText(f"{c*1e6:.3f}")
            
            if idx != 0:
                if l == 0: l = get_val(self.lc_l_val, self.lc_l_unit)
                if c == 0: c = get_val(self.lc_c_val, self.lc_c_unit)
            
            if l > 0 and c > 0:
                z0 = math.sqrt(l/c)
                self.lc_z0.setText(f"特征阻抗 Zo = {z0:.2f} Ω")
        except:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# Tab 3: RL Filter
# ==============================================================================
class RlFilterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("计算目标:"))
        self.rl_mode = QComboBox()
        self.rl_mode.addItems(["计算截止频率 fc (已知 R, L)", "计算电阻 R (已知 fc, L)", "计算电感 L (已知 fc, R)"])
        self.rl_mode.currentIndexChanged.connect(self.update_rl_inputs)
        mode_layout.addWidget(self.rl_mode)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        grp = QGroupBox("参数设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.rl_r_label = QLabel("电阻 (R):")
        self.rl_r_val = QLineEdit("10")
        self.rl_r_unit = QComboBox(); self.rl_r_unit.addItems(["kΩ", "Ω", "MΩ"])
        w_r = QWidget(); l_r = QHBoxLayout(w_r); l_r.setContentsMargins(0,0,0,0); l_r.addWidget(self.rl_r_val); l_r.addWidget(self.rl_r_unit)
        grid.addWidget(self.rl_r_label, 0, 0); grid.addWidget(w_r, 0, 1)
        
        self.rl_l_label = QLabel("电感 (L):")
        self.rl_l_val = QLineEdit("100")
        self.rl_l_unit = QComboBox(); self.rl_l_unit.addItems(["uH", "mH", "H"])
        w_l = QWidget(); l_l = QHBoxLayout(w_l); l_l.setContentsMargins(0,0,0,0); l_l.addWidget(self.rl_l_val); l_l.addWidget(self.rl_l_unit)
        grid.addWidget(self.rl_l_label, 1, 0); grid.addWidget(w_l, 1, 1)
        
        self.rl_fc_label = QLabel("截止频率 (fc):")
        self.rl_fc_val = QLineEdit()
        self.rl_fc_unit = QComboBox(); self.rl_fc_unit.addItems(["kHz", "Hz", "MHz"])
        w_f = QWidget(); l_f = QHBoxLayout(w_f); l_f.setContentsMargins(0,0,0,0); l_f.addWidget(self.rl_fc_val); l_f.addWidget(self.rl_fc_unit)
        grid.addWidget(self.rl_fc_label, 2, 0); grid.addWidget(w_f, 2, 1)
        
        grp.setLayout(grid)
        layout.addWidget(grp)
        
        btn = QPushButton("计算")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_rl)
        layout.addWidget(btn)
        
        res_grp = QGroupBox("计算结果")
        res_layout = QHBoxLayout()
        self.rl_result = QLabel("结果将显示在这里")
        self.rl_result.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        
        self.rl_formula = QLabel()
        self.rl_formula.setPixmap(render_formula(r'f_c = \frac{R}{2\pi L}'))
        
        res_layout.addWidget(self.rl_result)
        res_layout.addStretch()
        res_layout.addWidget(self.rl_formula)
        res_grp.setLayout(res_layout)
        layout.addWidget(res_grp)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_rl_inputs()

    def update_rl_inputs(self):
        idx = self.rl_mode.currentIndex()
        self.rl_r_val.setReadOnly(False); self.rl_r_val.setStyleSheet("")
        self.rl_l_val.setReadOnly(False); self.rl_l_val.setStyleSheet("")
        self.rl_fc_val.setReadOnly(False); self.rl_fc_val.setStyleSheet("")
        style_dis = "background-color: #f0f0f0; color: #888;"
        
        if idx == 0:
            self.rl_fc_val.setReadOnly(True); self.rl_fc_val.setStyleSheet(style_dis); self.rl_fc_val.setText("")
            self.rl_formula.setPixmap(render_formula(r'f_c = \frac{R}{2\pi L}'))
        elif idx == 1:
            self.rl_r_val.setReadOnly(True); self.rl_r_val.setStyleSheet(style_dis); self.rl_r_val.setText("")
            self.rl_formula.setPixmap(render_formula(r'R = 2\pi f_c L'))
        else:
            self.rl_l_val.setReadOnly(True); self.rl_l_val.setStyleSheet(style_dis); self.rl_l_val.setText("")
            self.rl_formula.setPixmap(render_formula(r'L = \frac{R}{2\pi f_c}'))

    def calc_rl(self):
        try:
            idx = self.rl_mode.currentIndex()
            if idx == 0:
                r = get_val(self.rl_r_val, self.rl_r_unit)
                l = get_val(self.rl_l_val, self.rl_l_unit)
                if l == 0: raise ValueError
                fc = r / (2 * math.pi * l)
                self.rl_result.setText(f"截止频率 fc = {format_freq(fc)}")
                self.rl_fc_val.setText(f"{fc/1000:.3f}")
            elif idx == 1:
                fc = get_val(self.rl_fc_val, self.rl_fc_unit)
                l = get_val(self.rl_l_val, self.rl_l_unit)
                r = 2 * math.pi * fc * l
                self.rl_result.setText(f"所需电阻 R = {format_res(r)}")
                self.rl_r_val.setText(f"{r/1000:.3f}")
            else:
                fc = get_val(self.rl_fc_val, self.rl_fc_unit)
                r = get_val(self.rl_r_val, self.rl_r_unit)
                if fc == 0: raise ValueError
                l = r / (2 * math.pi * fc)
                self.rl_result.setText(f"所需电感 L = {format_ind(l)}")
                self.rl_l_val.setText(f"{l*1e6:.3f}")
        except:
            QMessageBox.warning(self, "错误", "输入无效")