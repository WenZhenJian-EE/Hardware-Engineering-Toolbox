# filter_tabs_power.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from utils import render_formula

# ----------------- 辅助函数 -----------------
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
# Tab: EMI Filter
# ==============================================================================
class EmiFilterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Section 1: 差模滤波 ---
        dm_group = QGroupBox("1. 差模滤波 (DM Filter - Switching Noise)")
        dm_grid = QGridLayout()
        
        self.dm_mode = QComboBox()
        self.dm_mode.addItems(["计算电感 Ldm (已知 Cx, fc)", "计算电容 Cx (已知 Ldm, fc)", "计算截止频率 fc"])
        self.dm_mode.currentIndexChanged.connect(self.update_dm_inputs)
        dm_grid.addWidget(QLabel("计算目标:"), 0, 0); dm_grid.addWidget(self.dm_mode, 0, 1, 1, 2)
        
        self.dm_l = QLineEdit("10"); self.dm_l_unit = QComboBox(); self.dm_l_unit.addItems(["uH", "mH"])
        dm_grid.addWidget(QLabel("差模电感 (Ldm):"), 1, 0)
        w_ldm = QWidget(); l_ldm = QHBoxLayout(w_ldm); l_ldm.setContentsMargins(0,0,0,0); l_ldm.addWidget(self.dm_l); l_ldm.addWidget(self.dm_l_unit)
        dm_grid.addWidget(w_ldm, 1, 1)
        
        self.dm_c = QLineEdit("0.47"); self.dm_c_unit = QComboBox(); self.dm_c_unit.addItems(["uF", "nF"])
        dm_grid.addWidget(QLabel("X 电容 (Cx):"), 1, 2)
        w_cx = QWidget(); l_cx = QHBoxLayout(w_cx); l_cx.setContentsMargins(0,0,0,0); l_cx.addWidget(self.dm_c); l_cx.addWidget(self.dm_c_unit)
        dm_grid.addWidget(w_cx, 1, 3)
        
        self.dm_fc = QLineEdit("10"); self.dm_fc_unit = QComboBox(); self.dm_fc_unit.addItems(["kHz", "MHz"])
        dm_grid.addWidget(QLabel("截止频率 (fc):"), 2, 0)
        w_dfc = QWidget(); l_dfc = QHBoxLayout(w_dfc); l_dfc.setContentsMargins(0,0,0,0); l_dfc.addWidget(self.dm_fc); l_dfc.addWidget(self.dm_fc_unit)
        dm_grid.addWidget(w_dfc, 2, 1)
        
        self.dm_res_label = QLabel("结果: ---")
        self.dm_res_label.setStyleSheet("font-weight: bold; color: #2980b9;")
        dm_grid.addWidget(self.dm_res_label, 2, 2, 1, 2)
        
        btn_dm = QPushButton("计算 DM 参数")
        btn_dm.clicked.connect(self.calc_dm)
        dm_grid.addWidget(btn_dm, 3, 0, 1, 4)
        dm_group.setLayout(dm_grid)
        layout.addWidget(dm_group)
        
        # --- Section 2: 共模滤波 ---
        cm_group = QGroupBox("2. 共模滤波 (CM Filter - Line to Earth)")
        cm_grid = QGridLayout()
        
        self.cm_mode = QComboBox()
        self.cm_mode.addItems(["计算电感 Lcm (已知 Cy, fc)", "计算电容 Cy (已知 Lcm, fc)"])
        self.cm_mode.currentIndexChanged.connect(self.update_cm_inputs)
        cm_grid.addWidget(QLabel("计算目标:"), 0, 0); cm_grid.addWidget(self.cm_mode, 0, 1, 1, 2)
        
        self.cm_l = QLineEdit("10"); self.cm_l_unit = QComboBox(); self.cm_l_unit.addItems(["mH", "uH"])
        cm_grid.addWidget(QLabel("共模电感 (Lcm):"), 1, 0)
        w_lcm = QWidget(); l_lcm = QHBoxLayout(w_lcm); l_lcm.setContentsMargins(0,0,0,0); l_lcm.addWidget(self.cm_l); l_lcm.addWidget(self.cm_l_unit)
        cm_grid.addWidget(w_lcm, 1, 1)
        
        self.cm_c = QLineEdit("2.2"); self.cm_c_unit = QComboBox(); self.cm_c_unit.addItems(["nF", "pF"])
        cm_grid.addWidget(QLabel("Y 电容 (Cy):"), 1, 2)
        w_cy = QWidget(); l_cy = QHBoxLayout(w_cy); l_cy.setContentsMargins(0,0,0,0); l_cy.addWidget(self.cm_c); l_cy.addWidget(self.cm_c_unit)
        cm_grid.addWidget(w_cy, 1, 3)
        
        self.cm_fc = QLineEdit("150"); self.cm_fc_unit = QComboBox(); self.cm_fc_unit.addItems(["kHz", "MHz"])
        cm_grid.addWidget(QLabel("截止频率 (fc):"), 2, 0)
        w_cfc = QWidget(); l_cfc = QHBoxLayout(w_cfc); l_cfc.setContentsMargins(0,0,0,0); l_cfc.addWidget(self.cm_fc); l_cfc.addWidget(self.cm_fc_unit)
        cm_grid.addWidget(w_cfc, 2, 1)
        
        self.cm_res_label = QLabel("结果: ---")
        self.cm_res_label.setStyleSheet("font-weight: bold; color: #e67e22;")
        cm_grid.addWidget(self.cm_res_label, 2, 2, 1, 2)
        
        btn_cm = QPushButton("计算 CM 参数")
        btn_cm.clicked.connect(self.calc_cm)
        cm_grid.addWidget(btn_cm, 3, 0, 1, 4)
        cm_group.setLayout(cm_grid)
        layout.addWidget(cm_group)
        
        layout.addStretch()
        self.setLayout(layout)
        self.update_dm_inputs()
        self.update_cm_inputs()

    def update_dm_inputs(self):
        idx = self.dm_mode.currentIndex()
        self.dm_l.setReadOnly(False); self.dm_l.setStyleSheet("")
        self.dm_c.setReadOnly(False); self.dm_c.setStyleSheet("")
        self.dm_fc.setReadOnly(False); self.dm_fc.setStyleSheet("")
        style_dis = "background-color: #f0f0f0; color: #888;"
        
        if idx == 0: self.dm_l.setReadOnly(True); self.dm_l.setStyleSheet(style_dis); self.dm_l.setText("")
        elif idx == 1: self.dm_c.setReadOnly(True); self.dm_c.setStyleSheet(style_dis); self.dm_c.setText("")
        else: self.dm_fc.setReadOnly(True); self.dm_fc.setStyleSheet(style_dis); self.dm_fc.setText("")

    def update_cm_inputs(self):
        idx = self.cm_mode.currentIndex()
        self.cm_l.setReadOnly(False); self.cm_l.setStyleSheet("")
        self.cm_c.setReadOnly(False); self.cm_c.setStyleSheet("")
        style_dis = "background-color: #f0f0f0; color: #888;"
        
        if idx == 0: self.cm_l.setReadOnly(True); self.cm_l.setStyleSheet(style_dis); self.cm_l.setText("")
        else: self.cm_c.setReadOnly(True); self.cm_c.setStyleSheet(style_dis); self.cm_c.setText("")

    def calc_dm(self):
        try:
            idx = self.dm_mode.currentIndex()
            l_mult = 1e-6 if self.dm_l_unit.currentText()=="uH" else 1e-3
            c_mult = 1e-6 if self.dm_c_unit.currentText()=="uF" else 1e-9
            f_mult = 1e3 if self.dm_fc_unit.currentText()=="kHz" else 1e6
            l = float(self.dm_l.text()) * l_mult if self.dm_l.text() else 0
            c = float(self.dm_c.text()) * c_mult if self.dm_c.text() else 0
            fc = float(self.dm_fc.text()) * f_mult if self.dm_fc.text() else 0
            
            if idx == 0: 
                if c*fc == 0: return
                res = 1 / (c * (2 * math.pi * fc)**2)
                self.dm_res_label.setText(f"Ldm = {format_ind(res)}")
                self.dm_l.setText(f"{res/l_mult:.2f}")
            elif idx == 1:
                if l*fc == 0: return
                res = 1 / (l * (2 * math.pi * fc)**2)
                self.dm_res_label.setText(f"Cx = {format_cap(res)}")
                self.dm_c.setText(f"{res/c_mult:.2f}")
            else:
                if l*c == 0: return
                res = 1 / (2 * math.pi * math.sqrt(l*c))
                self.dm_res_label.setText(f"fc = {format_freq(res)}")
                self.dm_fc.setText(f"{res/f_mult:.2f}")
        except: pass

    def calc_cm(self):
        try:
            idx = self.cm_mode.currentIndex()
            l_mult = 1e-3 if self.cm_l_unit.currentText()=="mH" else 1e-6
            c_mult = 1e-9 if self.cm_c_unit.currentText()=="nF" else 1e-12
            f_mult = 1e3 if self.cm_fc_unit.currentText()=="kHz" else 1e6
            l = float(self.cm_l.text()) * l_mult if self.cm_l.text() else 0
            c = float(self.cm_c.text()) * c_mult if self.cm_c.text() else 0
            fc = float(self.cm_fc.text()) * f_mult if self.cm_fc.text() else 0
            
            if idx == 0:
                if c*fc == 0: return
                res = 1 / (c * (2 * math.pi * fc)**2)
                self.cm_res_label.setText(f"Lcm = {format_ind(res)}")
                self.cm_l.setText(f"{res/l_mult:.2f}")
            else:
                if l*fc == 0: return
                res = 1 / (l * (2 * math.pi * fc)**2)
                self.cm_res_label.setText(f"Cy = {format_cap(res)}")
                self.cm_c.setText(f"{res/c_mult:.2f}")
        except: pass

# ==============================================================================
# Tab: CMC Saturation Check
# ==============================================================================
class CmcSaturationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能：估算共模电感 (CMC) 在大电流差模工作下的漏感饱和风险。\n"
                      "虽然 CMC 主要抗共模，但漏感会承受全部差模电流 (Idm)。如果漏感产生的磁通导致磁芯饱和，共模滤波将瞬间失效。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #2c3e50; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 电感参数
        grp_cmc = QGroupBox("1. CMC 参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.cmc_l = QLineEdit("10"); self.cmc_l.setToolTip("标称共模电感量 (单路)")
        grid.addWidget(QLabel("共模电感量 Lcm [mH]:"), 0, 0); grid.addWidget(self.cmc_l, 0, 1)
        
        self.cmc_leak_ratio = QLineEdit("1.0"); self.cmc_leak_ratio.setToolTip("漏感比例，通常 0.5% ~ 2%")
        grid.addWidget(QLabel("漏感比例 Leakage [%]:"), 0, 2); grid.addWidget(self.cmc_leak_ratio, 0, 3)
        
        self.cmc_idm = QLineEdit("10"); self.cmc_idm.setToolTip("工作回路的差模电流峰值 (Line Current)")
        grid.addWidget(QLabel("工作电流 Idm_peak [A]:"), 1, 0); grid.addWidget(self.cmc_idm, 1, 1)
        
        self.cmc_n = QLineEdit("40"); grid.addWidget(QLabel("匝数 N [Ts]:"), 1, 2); grid.addWidget(self.cmc_n, 1, 3)
        
        grp_cmc.setLayout(grid)
        layout.addWidget(grp_cmc)
        
        # 2. 磁芯参数
        grp_core = QGroupBox("2. 磁芯参数 (Core Params)")
        g_core = QGridLayout()
        
        self.cmc_ae = QLineEdit("50"); g_core.addWidget(QLabel("有效截面积 Ae [mm²]:"), 0, 0); g_core.addWidget(self.cmc_ae, 0, 1)
        self.cmc_bsat = QLineEdit("0.35"); self.cmc_bsat.setToolTip("铁氧体 0.3~0.4T, 纳米晶 1.2T")
        g_core.addWidget(QLabel("饱和磁密 Bsat [T]:"), 0, 2); g_core.addWidget(self.cmc_bsat, 0, 3)
        
        grp_core.setLayout(g_core)
        layout.addWidget(grp_core)
        
        btn = QPushButton("计算漏感磁通 & 评估饱和")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_saturation)
        layout.addWidget(btn)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估结果")
        r_grid = QGridLayout()
        
        self.res_lk = QLineEdit()
        self.res_b_lk = QLineEdit()
        self.res_status = QLineEdit()
        
        r_grid.addWidget(QLabel("估算漏感 L_leak [uH]:"), 0, 0); r_grid.addWidget(self.res_lk, 0, 1)
        r_grid.addWidget(QLabel("漏感磁通密度 B_leak [T]:"), 1, 0); r_grid.addWidget(self.res_b_lk, 1, 1)
        
        l_form = QLabel()
        l_form.setPixmap(render_formula(r'B_{leak} \approx \frac{L_{leak} \cdot I_{dm}}{N \cdot A_e}'))
        r_grid.addWidget(l_form, 0, 2, 2, 1)
        
        r_grid.addWidget(QLabel("饱和风险评估:"), 2, 0); r_grid.addWidget(self.res_status, 2, 1, 1, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        self.res_lk.setReadOnly(True); self.res_lk.setStyleSheet(style)
        self.res_b_lk.setReadOnly(True); self.res_b_lk.setStyleSheet(style)
        self.res_status.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)

    def calc_saturation(self):
        try:
            lcm_mh = float(self.cmc_l.text())
            leak_pct = float(self.cmc_leak_ratio.text())
            idm = float(self.cmc_idm.text())
            n = float(self.cmc_n.text())
            ae_mm2 = float(self.cmc_ae.text())
            bsat = float(self.cmc_bsat.text())
            
            if ae_mm2 <= 0 or n <= 0: raise ValueError
            
            l_leak_uh = lcm_mh * 1000 * (leak_pct / 100.0)
            l_leak_h = l_leak_uh * 1e-6
            ae_m2 = ae_mm2 * 1e-6
            
            # B = L * I / (N * Ae)
            b_leak = (l_leak_h * idm) / (n * ae_m2)
            
            self.res_lk.setText(f"{l_leak_uh:.2f} uH")
            self.res_b_lk.setText(f"{b_leak:.3f} T")
            
            if b_leak > bsat:
                self.res_status.setText(f"危险！严重饱和 (>{bsat}T)")
                self.res_status.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
            elif b_leak > bsat * 0.7:
                self.res_status.setText("警告：接近饱和 (裕量<30%)")
                self.res_status.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold;")
            else:
                self.res_status.setText("安全 (Pass)")
                self.res_status.setStyleSheet("background-color: #d4edda; color: green; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

# ==============================================================================
# Tab: SPWM Inverter Filter
# ==============================================================================
class SpwmFilterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Input Parameters
        grp_in = QGroupBox("1. 逆变器参数 (Inverter Parameters)")
        grid_in = QGridLayout()
        grid_in.setVerticalSpacing(12)
        
        self.spwm_type = QComboBox()
        self.spwm_type.addItems(["LC 滤波器 (离网/独立逆变)", "LCL 滤波器 (并网逆变)"])
        self.spwm_type.currentIndexChanged.connect(self.update_spwm_visibility)
        grid_in.addWidget(QLabel("滤波器类型:"), 0, 0); grid_in.addWidget(self.spwm_type, 0, 1)
        
        self.spwm_vdc = QLineEdit("700"); grid_in.addWidget(QLabel("直流母线电压 Vdc [V]:"), 1, 0); grid_in.addWidget(self.spwm_vdc, 1, 1)
        self.spwm_vac = QLineEdit("380"); grid_in.addWidget(QLabel("输出线电压 Vac_rms [V]:"), 1, 2); grid_in.addWidget(self.spwm_vac, 1, 3)
        self.spwm_p_rate = QLineEdit("10"); grid_in.addWidget(QLabel("额定功率 P_rate [kW]:"), 2, 0); grid_in.addWidget(self.spwm_p_rate, 2, 1)
        self.spwm_fsw = QLineEdit("10"); grid_in.addWidget(QLabel("开关频率 fsw [kHz]:"), 2, 2); grid_in.addWidget(self.spwm_fsw, 2, 3)
        self.spwm_fout = QLineEdit("50"); grid_in.addWidget(QLabel("基波频率 fout [Hz]:"), 3, 0); grid_in.addWidget(self.spwm_fout, 3, 1)
        self.spwm_ripple = QLineEdit("20"); grid_in.addWidget(QLabel("允许纹波电流 ΔIL [%]:"), 3, 2); grid_in.addWidget(self.spwm_ripple, 3, 3)
        
        grp_in.setLayout(grid_in)
        layout.addWidget(grp_in)
        
        btn_calc = QPushButton("计算滤波器参数")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_spwm)
        layout.addWidget(btn_calc)
        
        # 2. Results
        grp_res = QGroupBox("2. 推荐参数 (Design Recommendation)")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        
        self.res_spwm_l1 = QLineEdit()
        res_grid.addWidget(QLabel("逆变侧电感 L1 (Inverter Side):"), 0, 0); res_grid.addWidget(self.res_spwm_l1, 0, 1)
        l_l1 = QLabel(); l_l1.setPixmap(render_formula(r'L_1 \geq \frac{V_{dc}}{8 f_{sw} \Delta I_{ripple}}'))
        res_grid.addWidget(l_l1, 0, 2)
        
        self.res_spwm_cf = QLineEdit()
        res_grid.addWidget(QLabel("滤波电容 Cf (Filter Cap):"), 1, 0); res_grid.addWidget(self.res_spwm_cf, 1, 1)
        l_cf = QLabel(); l_cf.setPixmap(render_formula(r'C_f \approx 5\% \times \frac{P_{rate}}{3 \cdot 2\pi f_{out} \cdot V_{ph}^2}'))
        res_grid.addWidget(l_cf, 1, 2)
        
        self.lbl_spwm_l2 = QLabel("网侧电感 L2 (Grid Side):")
        self.res_spwm_l2 = QLineEdit()
        self.lbl_spwm_l2_desc = QLabel("通常取 L2 ≈ 0.4 ~ 0.8 * L1")
        res_grid.addWidget(self.lbl_spwm_l2, 2, 0); res_grid.addWidget(self.res_spwm_l2, 2, 1)
        res_grid.addWidget(self.lbl_spwm_l2_desc, 2, 2)
        
        self.res_spwm_fres = QLineEdit()
        res_grid.addWidget(QLabel("谐振频率 f_res (Check):"), 3, 0); res_grid.addWidget(self.res_spwm_fres, 3, 1)
        self.lbl_spwm_fres_formula = QLabel()
        self.lbl_spwm_fres_formula.setPixmap(render_formula(r'f_{res} = \frac{1}{2\pi} \sqrt{\frac{L_1+L_2}{L_1 L_2 C_f}}'))
        res_grid.addWidget(self.lbl_spwm_fres_formula, 3, 2)
        
        self.lbl_spwm_check = QLabel("Criteria: 10*fout < fres < 0.5*fsw")
        self.lbl_spwm_check.setStyleSheet("color: gray; font-weight: bold;")
        res_grid.addWidget(self.lbl_spwm_check, 4, 0, 1, 3)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_spwm_l1, self.res_spwm_cf, self.res_spwm_l2, self.res_spwm_fres]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)
        self.update_spwm_visibility()

    def update_spwm_visibility(self):
        is_lcl = (self.spwm_type.currentIndex() == 1)
        self.lbl_spwm_l2.setVisible(is_lcl)
        self.res_spwm_l2.setVisible(is_lcl)
        self.lbl_spwm_l2_desc.setVisible(is_lcl)
        if is_lcl:
            self.lbl_spwm_fres_formula.setPixmap(render_formula(r'f_{res} = \frac{1}{2\pi} \sqrt{\frac{L_1+L_2}{L_1 L_2 C_f}}'))
        else:
            self.lbl_spwm_fres_formula.setPixmap(render_formula(r'f_{res} = \frac{1}{2\pi \sqrt{L_1 C_f}}'))

    def calc_spwm(self):
        try:
            vdc = float(self.spwm_vdc.text())
            vac_ll = float(self.spwm_vac.text())
            p_rate = float(self.spwm_p_rate.text()) * 1000
            fsw = float(self.spwm_fsw.text()) * 1000
            fout = float(self.spwm_fout.text())
            ripple_percent = float(self.spwm_ripple.text()) / 100.0
            is_lcl = (self.spwm_type.currentIndex() == 1)
            
            v_ph = vac_ll / math.sqrt(3)
            i_rate = p_rate / (math.sqrt(3) * vac_ll)
            delta_i_max = i_rate * ripple_percent
            
            l1 = vdc / (8 * fsw * delta_i_max)
            w_out = 2 * math.pi * fout
            cf_max = (0.05 * p_rate) / (3 * (v_ph**2) * w_out)
            cf = cf_max
            l2 = 0; f_res = 0
            
            if is_lcl:
                l2 = 0.6 * l1 
                w_res = math.sqrt( (l1+l2) / (l1*l2*cf) )
                f_res = w_res / (2 * math.pi)
                self.res_spwm_l2.setText(f"{l2*1000:.3f} mH")
            else:
                w_res = 1.0 / math.sqrt(l1 * cf)
                f_res = w_res / (2 * math.pi)
                self.res_spwm_l2.setText("---")
            
            self.res_spwm_l1.setText(f"{l1*1000:.3f} mH")
            self.res_spwm_cf.setText(f"{cf*1e6:.2f} uF")
            self.res_spwm_fres.setText(f"{f_res/1000:.2f} kHz")
            
            cond1 = 10 * fout
            cond2 = 0.5 * fsw
            if cond1 < f_res < cond2:
                self.lbl_spwm_check.setText(f"Pass! ({cond1:.0f} < {f_res:.0f} < {cond2:.0f})")
                self.lbl_spwm_check.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.lbl_spwm_check.setText(f"Warning! Fres out of range ({cond1:.0f}~{cond2:.0f})")
                self.lbl_spwm_check.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

# ==============================================================================
# Tab: Ferrite Bead Selection
# ==============================================================================
class FerriteBeadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        grp_damp = QGroupBox("1. 磁珠 LC 振铃抑制计算 (Damping)")
        d_grid = QGridLayout()
        d_grid.setVerticalSpacing(12)
        
        self.bead_l = QLineEdit("0.6"); d_grid.addWidget(QLabel("磁珠等效电感 L_bead [µH]:"), 0, 0); d_grid.addWidget(self.bead_l, 0, 1)
        self.bead_c = QLineEdit("10"); d_grid.addWidget(QLabel("去耦电容 C_dec [µF]:"), 0, 2); d_grid.addWidget(self.bead_c, 0, 3)
        
        btn_damp = QPushButton("计算阻尼电阻 (Series R)")
        btn_damp.setFixedHeight(40)
        btn_damp.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn_damp.clicked.connect(self.calc_bead_damping)
        d_grid.addWidget(btn_damp, 1, 0, 1, 4)

        self.res_bead_freq = QLineEdit(); d_grid.addWidget(QLabel("LC 谐振频率 f_res:"), 2, 0); d_grid.addWidget(self.res_bead_freq, 2, 1)
        self.res_bead_z0 = QLineEdit(); d_grid.addWidget(QLabel("特征阻抗 Zo (√(L/C)):"), 2, 2); d_grid.addWidget(self.res_bead_z0, 2, 3)
        
        self.res_bead_rd = QLineEdit()
        self.res_bead_rd.setReadOnly(True)
        self.res_bead_rd.setStyleSheet("background-color: #fdedec; font-weight: bold; color: #c0392b; font-size: 15px;")
        d_grid.addWidget(QLabel("建议串联阻尼电阻 R_series:"), 3, 0); d_grid.addWidget(self.res_bead_rd, 3, 1, 1, 3)
        
        l_form_rd = QLabel()
        l_form_rd.setPixmap(render_formula(r'R_{critical} = 2 \sqrt{L/C}, \quad R_{optimal} \approx \sqrt{L/C}'))
        d_grid.addWidget(l_form_rd, 4, 0, 1, 4)
        
        grp_damp.setLayout(d_grid)
        layout.addWidget(grp_damp)

        grp_dc = QGroupBox("2. 磁珠直流偏置估算 (DC Bias Derating)")
        dc_grid = QGridLayout()
        dc_grid.setVerticalSpacing(12)

        self.bead_i_rate = QLineEdit("2000"); dc_grid.addWidget(QLabel("额定电流 I_rated [mA]:"), 0, 0); dc_grid.addWidget(self.bead_i_rate, 0, 1)
        self.bead_i_op = QLineEdit("1000"); dc_grid.addWidget(QLabel("实际工作电流 I_op [mA]:"), 0, 2); dc_grid.addWidget(self.bead_i_op, 0, 3)
        self.bead_z_nom = QLineEdit("1000"); dc_grid.addWidget(QLabel("标称阻抗 Z_nom (@0A) [Ω]:"), 1, 0); dc_grid.addWidget(self.bead_z_nom, 1, 1)

        btn_bias = QPushButton("估算实际阻抗 (Estimate Z_eff)")
        btn_bias.clicked.connect(self.calc_bead_bias)
        btn_bias.setStyleSheet("background-color: #e67e22; color: white;")
        dc_grid.addWidget(btn_bias, 1, 2, 1, 2)

        self.res_bead_z_eff = QLineEdit()
        self.res_bead_z_eff.setReadOnly(True)
        self.res_bead_z_eff.setStyleSheet("background-color: #fcf3cf; color: #d35400; font-weight: bold;")
        dc_grid.addWidget(QLabel("估算有效阻抗 Z_eff:"), 2, 0); dc_grid.addWidget(self.res_bead_z_eff, 2, 1)
        
        self.res_bead_warn = QLabel("注：仅为基于平方律的粗略估算。部分磁珠在50%额定电流时阻抗可能下降>60%。")
        self.res_bead_warn.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        dc_grid.addWidget(self.res_bead_warn, 2, 2, 1, 2)

        grp_dc.setLayout(dc_grid)
        layout.addWidget(grp_dc)
        layout.addStretch()
        self.setLayout(layout)

    def calc_bead_damping(self):
        try:
            l_uh = float(self.bead_l.text())
            c_uf = float(self.bead_c.text())
            if l_uh <= 0 or c_uf <= 0: return
            l = l_uh * 1e-6
            c = c_uf * 1e-6
            f_res = 1 / (2 * math.pi * math.sqrt(l * c))
            z0 = math.sqrt(l / c)
            r_crit = 2 * z0; r_opt = 1.0 * z0
            
            if f_res > 1e6: self.res_bead_freq.setText(f"{f_res/1e6:.2f} MHz")
            else: self.res_bead_freq.setText(f"{f_res/1e3:.2f} kHz")
            self.res_bead_z0.setText(f"{z0:.2f} Ω")
            self.res_bead_rd.setText(f"{r_opt:.2f} Ω (Q=1) ~ {r_crit:.2f} Ω (Q=0.5)")
        except Exception:
            QMessageBox.warning(self, "错误", "请输入有效的 L 和 C 数值")

    def calc_bead_bias(self):
        try:
            i_rate = float(self.bead_i_rate.text())
            i_op = float(self.bead_i_op.text())
            z_nom = float(self.bead_z_nom.text())
            if i_rate <= 0: return
            ratio = i_op / i_rate
            if ratio > 1.0:
                self.res_bead_z_eff.setText("饱和 (Saturated)!")
                return
            degrade = math.pow(ratio, 1.5)
            z_eff = z_nom * (1 - degrade)
            if z_eff < 0: z_eff = 0
            percent = (z_eff / z_nom) * 100
            self.res_bead_z_eff.setText(f"{z_eff:.1f} Ω (剩 {percent:.0f}%)")
        except Exception: pass

# ==============================================================================
# Tab: Input Filter Stability (New Feature)
# ==============================================================================
class InputFilterStabilityTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：基于 Middlebrook 判据，设计 DC-DC 输入滤波器的阻尼电路，防止电源震荡。\n"
                      "当 LC 滤波器与恒功率负载(DC-DC)级联时，若滤波器输出阻抗峰值 > 转换器输入阻抗，系统将不稳定。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 输入参数
        grp_sys = QGroupBox("1. 系统与滤波器参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.inp_vin = QLineEdit("24"); grid.addWidget(QLabel("输入电压 Vin [V]:"), 0, 0); grid.addWidget(self.inp_vin, 0, 1)
        self.inp_pout = QLineEdit("50"); grid.addWidget(QLabel("负载功率 P_load [W]:"), 0, 2); grid.addWidget(self.inp_pout, 0, 3)
        
        self.inp_l = QLineEdit("10"); self.inp_l.setToolTip("输入滤波电感")
        grid.addWidget(QLabel("滤波电感 L [uH]:"), 1, 0); grid.addWidget(self.inp_l, 1, 1)
        
        self.inp_c = QLineEdit("10"); self.inp_c.setToolTip("输入滤波电容 (陶瓷)")
        grid.addWidget(QLabel("滤波电容 C [uF]:"), 1, 2); grid.addWidget(self.inp_c, 1, 3)
        
        grp_sys.setLayout(grid)
        layout.addWidget(grp_sys)
        
        btn = QPushButton("计算阻尼电阻 (Damping Resistor)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_damping)
        layout.addWidget(btn)
        
        # 2. 结果
        grp_res = QGroupBox("2. 设计结果 (Parallel R-C Damping)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_zin = QLineEdit() # 转换器输入阻抗绝对值
        self.res_zout_peak = QLineEdit() # LC 未阻尼峰值
        self.res_rd = QLineEdit() # 推荐阻尼电阻
        self.res_cd = QLineEdit() # 推荐隔直电容
        
        # Row 1
        r_grid.addWidget(QLabel("转换器负阻抗 |Z_in|:"), 0, 0)
        r_grid.addWidget(self.res_zin, 0, 1)
        l_zin = QLabel(); l_zin.setPixmap(render_formula(r'|Z_{in}| = V_{in}^2 / P_{load}'))
        r_grid.addWidget(l_zin, 0, 2)
        
        # Row 2
        r_grid.addWidget(QLabel("LC 特征阻抗 Zo:"), 1, 0)
        r_grid.addWidget(self.res_zout_peak, 1, 1)
        l_zo = QLabel(); l_zo.setPixmap(render_formula(r'Z_o = \sqrt{L/C}'))
        r_grid.addWidget(l_zo, 1, 2)
        
        # Row 3
        r_grid.addWidget(QLabel("推荐阻尼电阻 Rd:"), 2, 0)
        r_grid.addWidget(self.res_rd, 2, 1)
        l_rd = QLabel(); l_rd.setPixmap(render_formula(r'R_d \approx Z_o \quad (\text{and } R_d < |Z_{in}|)'))
        r_grid.addWidget(l_rd, 2, 2)
        
        # Row 4
        r_grid.addWidget(QLabel("推荐隔直电容 Cd:"), 3, 0)
        r_grid.addWidget(self.res_cd, 3, 1)
        l_cd = QLabel(); l_cd.setPixmap(render_formula(r'C_d \geq 4 \times C_{filter}'))
        r_grid.addWidget(l_cd, 3, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_zin, self.res_zout_peak, self.res_rd, self.res_cd]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addWidget(QLabel("注：阻尼电路是由 Rd 和 Cd 串联后，再并联在输入滤波电容 C 两端。Cd 用于阻隔直流，防止 Rd 消耗功率。"))
        layout.addStretch()
        self.setLayout(layout)

    def calc_damping(self):
        try:
            vin = float(self.inp_vin.text())
            p = float(self.inp_pout.text())
            l = float(self.inp_l.text()) * 1e-6
            c = float(self.inp_c.text()) * 1e-6
            
            if p <= 0 or c <= 0 or l <= 0: raise ValueError
            
            # 1. Converter Input Impedance (Negative Resistor)
            # |Zin| = Vin^2 / P
            z_in_mag = (vin**2) / p
            
            # 2. Filter Characteristic Impedance
            z_o = math.sqrt(l/c)
            
            # Check basic stability condition without damping
            # Theoretically, if Zo << Zin, it might be marginally stable depending on Q.
            # But we always recommend damping for high Q ceramic capacitors.
            
            # 3. Design Damping
            # Optimal Rd = Zo (Middlebrook suggestion for parallel damping)
            # And we need Rd < |Zin| for stability. 
            # Ideally Rd should be significantly smaller than |Zin| (e.g. 1/2 or 1/3) to ensure Z_out_filter < Z_in_converter
            
            r_d = z_o
            
            # 4. Blocking Capacitor Cd
            # Cd should be large enough so that at resonant frequency, the branch impedance is dominated by Rd.
            # Typically Cd >= 3~5 * C
            c_d = 4 * c
            
            self.res_zin.setText(f"{z_in_mag:.2f} Ω")
            self.res_zout_peak.setText(f"{z_o:.2f} Ω")
            self.res_rd.setText(f"{r_d:.2f} Ω")
            
            if c_d < 1e-6:
                self.res_cd.setText(f"{c_d*1e6:.2f} uF")
            else:
                self.res_cd.setText(f"{c_d*1e6:.1f} uF")
            
            # Stability Warning
            if r_d >= z_in_mag:
                QMessageBox.warning(self, "不稳定风险", 
                    f"特征阻抗 Zo ({z_o:.1f}Ω) 大于或接近电源输入阻抗 Zin ({z_in_mag:.1f}Ω)。\n"
                    "仅仅加阻尼可能不够，建议增大输入电容 C 或减小电感 L，以降低 Zo。")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")