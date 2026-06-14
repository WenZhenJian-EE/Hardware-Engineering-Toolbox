# pcb_signal_integrity.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QComboBox,
                             QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

# ==============================================================================
# Helper: Elliptic Integral Calculations for CPW
# ==============================================================================
def calc_ellip_ratio(k):
    """
    计算椭圆积分比率 K(k)/K'(k)
    Reference: IPC-2141 / Waddell / Ghione
    K'(k) = K(k') where k' = sqrt(1 - k^2)
    Returns K(k)/K(k')
    """
    if k >= 1.0: return 1e9 # Avoid division by zero (infinite)
    if k <= 0.0: return 0.0
    
    kp = math.sqrt(1 - k**2) # k'
    
    # 当 0 <= k <= 0.707 (1/sqrt(2))
    if k <= 0.70710678:
        # term = ln( 2 * (1+sqrt(k')) / (1-sqrt(k')) )
        num = 1 + math.sqrt(kp)
        den = 1 - math.sqrt(kp)
        if den == 0: return 0
        return math.pi / math.log(2 * num / den)
    else:
        # 当 0.707 < k <= 1
        # term = ln( 2 * (1+sqrt(k)) / (1-sqrt(k)) )
        num = 1 + math.sqrt(k)
        den = 1 - math.sqrt(k)
        if den == 0: return 1e9
        return (1 / math.pi) * math.log(2 * num / den)

# ==============================================================================
# 1. 特性阻抗评估 (Impedance - Microstrip/Stripline/CPW)
# ==============================================================================
class ImpedanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 结构选择
        grp_stack = QGroupBox("1. 叠层结构与模式")
        grid_stack = QGridLayout()
        grid_stack.setVerticalSpacing(12)
        
        # 结构类型
        self.imp_struct = QComboBox()
        self.imp_struct.addItems([
            "外层微带线 (Microstrip)", 
            "内层带状线 (Stripline)",
            "共面波导 (CPW - 无地平面)",
            "接地共面波导 (CPW-G - 有地平面)"
        ])
        self.imp_struct.currentIndexChanged.connect(self.update_imp_ui)
        grid_stack.addWidget(QLabel("传输线结构:"), 0, 0); grid_stack.addWidget(self.imp_struct, 0, 1)
        
        # 模式选择 (单端/差分)
        self.rb_single = QRadioButton("单端 (Single-Ended)")
        self.rb_diff = QRadioButton("差分 (Differential)")
        self.rb_single.setChecked(True)
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.rb_single)
        self.mode_group.addButton(self.rb_diff)
        self.mode_group.buttonClicked.connect(self.update_imp_ui)
        
        h_mode = QHBoxLayout(); h_mode.addWidget(self.rb_single); h_mode.addWidget(self.rb_diff)
        grid_stack.addWidget(QLabel("信号模式:"), 0, 2); grid_stack.addLayout(h_mode, 0, 3)

        # 介电常数
        self.imp_er = QLineEdit("4.2")
        self.imp_er_combo = QComboBox()
        self.imp_er_combo.addItems(["自定义", "FR-4 (4.2)", "Rogers 4350B (3.66)", "Rogers 4003C (3.38)", "Polyimide (4.1)"])
        self.imp_er_combo.setCurrentIndex(1)
        self.imp_er_combo.currentIndexChanged.connect(self.on_er_combo_changed)
        
        h_er = QHBoxLayout(); h_er.addWidget(self.imp_er); h_er.addWidget(self.imp_er_combo)
        grid_stack.addWidget(QLabel("介电常数 (Er):"), 1, 0); grid_stack.addLayout(h_er, 1, 1)
        
        grp_stack.setLayout(grid_stack)
        layout.addWidget(grp_stack)
        
        # 2. 几何参数
        grp_geo = QGroupBox("2. 几何尺寸输入")
        grid_geo = QGridLayout()
        grid_geo.setVerticalSpacing(15)
        
        # 线宽 W
        self.imp_w = QLineEdit("10"); self.imp_w_unit = QComboBox(); self.imp_w_unit.addItems(["mil", "mm"])
        h_w = QHBoxLayout(); h_w.addWidget(self.imp_w); h_w.addWidget(self.imp_w_unit); h_w.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(QLabel("线宽 (W):"), 0, 0); grid_geo.addLayout(h_w, 0, 1)
        
        # 包地间距 G (CPW Only)
        self.imp_g_label = QLabel("包地间距 (G):")
        self.imp_g = QLineEdit("6"); self.imp_g_unit = QComboBox(); self.imp_g_unit.addItems(["mil", "mm"])
        self.h_g = QHBoxLayout(); self.h_g.addWidget(self.imp_g); self.h_g.addWidget(self.imp_g_unit); self.h_g.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(self.imp_g_label, 0, 2); grid_geo.addLayout(self.h_g, 0, 3)
        
        # 介质厚度 H
        self.imp_h_label = QLabel("介质厚度 (H):")
        self.imp_h = QLineEdit("6"); self.imp_h_unit = QComboBox(); self.imp_h_unit.addItems(["mil", "mm"])
        h_h = QHBoxLayout(); h_h.addWidget(self.imp_h); h_h.addWidget(self.imp_h_unit); h_h.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(self.imp_h_label, 1, 0); grid_geo.addLayout(h_h, 1, 1)
        
        # 铜厚 T
        self.imp_t = QLineEdit("1.0"); self.imp_t_unit = QComboBox(); self.imp_t_unit.addItems(["oz", "mil", "mm"])
        h_t = QHBoxLayout(); h_t.addWidget(self.imp_t); h_t.addWidget(self.imp_t_unit); h_t.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(QLabel("铜箔厚度 (T):"), 1, 2); grid_geo.addLayout(h_t, 1, 3)
        
        # 线间距 S (仅差分)
        self.imp_s_label = QLabel("差分线距 (S):")
        self.imp_s = QLineEdit("6"); self.imp_s_unit = QComboBox(); self.imp_s_unit.addItems(["mil", "mm"])
        self.h_s = QHBoxLayout(); self.h_s.addWidget(self.imp_s); self.h_s.addWidget(self.imp_s_unit); self.h_s.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(self.imp_s_label, 2, 0); grid_geo.addLayout(self.h_s, 2, 1)
        
        grp_geo.setLayout(grid_geo)
        layout.addWidget(grp_geo)
        
        btn = QPushButton("计算阻抗 (Calculate)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_impedance)
        layout.addWidget(btn)
        
        # 3. 结果
        grp_res = QGroupBox("3. 计算结果")
        r_grid = QGridLayout()
        self.imp_z0_label = QLabel("单端阻抗 (Zo):")
        self.imp_z0 = QLineEdit()
        self.imp_z0.setReadOnly(True)
        self.imp_z0.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 16px;")
        
        r_grid.addWidget(self.imp_z0_label, 0, 0); r_grid.addWidget(self.imp_z0, 0, 1)
        
        self.imp_formula_label = QLabel()
        r_grid.addWidget(self.imp_formula_label, 1, 0, 1, 2)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 提示
        tips = QLabel("注：\n"
                      "1. Microstrip/Stripline 基于 IPC-2141 近似公式。\n"
                      "2. CPW/CPW-G 基于椭圆积分 (Elliptic Integral) 计算，适用于宽频设计。\n"
                      "3. 差分阻抗为近似值，高精度请使用 2D 场求解器。")
        tips.setStyleSheet("color: #7f8c8d; font-style: italic;")
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        layout.addStretch()
        self.setLayout(layout)
        self.update_imp_ui()

    def update_imp_ui(self):
        idx = self.imp_struct.currentIndex()
        is_stripline = (idx == 1)
        is_cpw = (idx >= 2)
        is_diff = self.rb_diff.isChecked()
        
        # CPW Gap Visibility
        self.imp_g_label.setVisible(is_cpw)
        for i in range(self.h_g.count()): 
            w = self.h_g.itemAt(i).widget()
            if w: w.setVisible(is_cpw)
            
        # Update Labels
        if is_stripline:
            self.imp_h_label.setText("地平面间距 (B):")
            if self.imp_h.text() == "6": self.imp_h.setText("20") 
        else:
            self.imp_h_label.setText("介质厚度 (H):")
            if self.imp_h.text() == "20": self.imp_h.setText("6")
            
        # Visibility of Diff Spacing S
        self.imp_s_label.setVisible(is_diff)
        for i in range(self.h_s.count()):
            w = self.h_s.itemAt(i).widget()
            if w: w.setVisible(is_diff)
        
        # Update Formula Preview and Result Label
        if not is_diff:
            self.imp_z0_label.setText("特性阻抗 (Zo):")
            if idx == 0: # Microstrip
                self.imp_formula_label.setPixmap(render_formula(r'Z_0 = \frac{87}{\sqrt{E_r + 1.41}} \ln\left(\frac{5.98H}{0.8W + T}\right)'))
            elif idx == 1: # Stripline
                self.imp_formula_label.setPixmap(render_formula(r'Z_0 = \frac{60}{\sqrt{E_r}} \ln\left(\frac{1.9 B}{0.8W + T}\right)'))
            elif idx == 2: # CPW
                self.imp_formula_label.setPixmap(render_formula(r'CPW: Z_0 \propto \frac{1}{\sqrt{E_{eff}}} \frac{K(k\')}{K(k)}, \quad k = \frac{W}{W+2G}'))
            elif idx == 3: # CPW-G
                self.imp_formula_label.setPixmap(render_formula(r'CPW-G: Z_0 \approx \frac{60\pi}{\sqrt{E_{eff}}} \frac{1}{ K(k)/K(k\') + K(k_1)/K(k_1\') }'))
        else:
            self.imp_z0_label.setText("差分阻抗 (Zdiff):")
            if is_cpw:
                self.imp_formula_label.setText("Diff CPW 暂使用 Microstrip 耦合系数近似: 2*Z0*(1 - Coupling)")
            else:
                self.imp_formula_label.setPixmap(render_formula(r'Z_{diff} \approx 2 Z_0 \left(1 - \alpha e^{-\beta S/H}\right)'))

    def on_er_combo_changed(self):
        txt = self.imp_er_combo.currentText()
        if "FR-4" in txt: self.imp_er.setText("4.2")
        elif "4350B" in txt: self.imp_er.setText("3.66")
        elif "4003C" in txt: self.imp_er.setText("3.38")
        elif "Polyimide" in txt: self.imp_er.setText("4.1")

    def get_val_in_mil(self, widget, unit_widget):
        val = float(widget.text())
        unit = unit_widget.currentText()
        if unit == "mm": return val / 0.0254
        if unit == "oz": return val * 1.378
        return val

    def calc_impedance(self):
        try:
            er = float(self.imp_er.text())
            w = self.get_val_in_mil(self.imp_w, self.imp_w_unit)
            h = self.get_val_in_mil(self.imp_h, self.imp_h_unit) # H or B
            t = self.get_val_in_mil(self.imp_t, self.imp_t_unit)
            
            struct_idx = self.imp_struct.currentIndex()
            is_diff = self.rb_diff.isChecked()
            
            if w <= 0 or h <= 0 or er <= 0: raise ValueError
            
            z0 = 0.0
            
            # --- 1. Microstrip ---
            if struct_idx == 0: 
                term = (5.98 * h) / (0.8 * w + t)
                z0 = (87.0 / math.sqrt(er + 1.41)) * math.log(term)

            # --- 2. Stripline ---
            elif struct_idx == 1:
                term = (1.9 * h) / (0.8 * w + t)
                z0 = (60.0 / math.sqrt(er)) * math.log(term)

            # --- 3. CPW (Coplanar Waveguide) ---
            elif struct_idx == 2:
                g = self.get_val_in_mil(self.imp_g, self.imp_g_unit)
                if g <= 0: raise ValueError("CPW 间距 G 必须 > 0")
                
                # Effective Dielectric Constant
                eeff = (er + 1) / 2
                
                # Modulus k
                k = w / (w + 2*g)
                # Function calc_ellip_ratio returns K(k)/K(k')
                ratio = calc_ellip_ratio(k) 
                
                # Z0 = (30 * pi / sqrt(eeff)) * (K'(k)/K(k))
                # My calc_ellip_ratio returns K/K'. So need 1/ratio.
                z0 = (30 * math.pi / math.sqrt(eeff)) * (1.0 / ratio)

            # --- 4. CPW-G (Grounded Coplanar Waveguide) ---
            elif struct_idx == 3:
                g = self.get_val_in_mil(self.imp_g, self.imp_g_unit)
                if g <= 0: raise ValueError("CPW 间距 G 必须 > 0")
                
                k = w / (w + 2*g)
                
                # Hyperbolic functions arguments for finite H
                arg1 = (math.pi * w) / (4 * h)
                arg2 = (math.pi * (w + 2*g)) / (4 * h)
                k1 = math.tanh(arg1) / math.tanh(arg2)
                
                # Algorithm:
                r_k = calc_ellip_ratio(k)   # K(k)/K(k')
                r_k1 = calc_ellip_ratio(k1) # K(k1)/K(k1')
                
                # Approximation for Eeff in CPW-G
                q = r_k1 / r_k
                eeff = (1 + er * q) / (1 + q)
                
                # Z0 Calculation
                z0 = (60 * math.pi / math.sqrt(eeff)) * (1.0 / r_k1) # Behaves like Microstrip/CPW hybrid
                
            # --- Result Output ---
            if is_diff:
                s = self.get_val_in_mil(self.imp_s, self.imp_s_unit)
                if s <= 0: raise ValueError("差分线间距 S 必须大于 0")
                
                # Coupling factor approximation
                if struct_idx == 0: # Microstrip
                    factor = 1.0 - 0.48 * math.exp(-0.96 * s / h)
                elif struct_idx == 1: # Stripline
                    factor = 1.0 - 0.347 * math.exp(-2.9 * s / h)
                else: # CPW
                    # CPW coupling is weaker than MS for same S.
                    # Using MS formula as conservative estimate
                    factor = 1.0 - 0.48 * math.exp(-0.96 * s / h)
                    
                z_final = 2 * z0 * factor
                self.imp_z0.setText(f"{z_final:.2f} Ω")
            else:
                self.imp_z0.setText(f"{z0:.2f} Ω")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

# ==============================================================================
# 2. 寄生参数估算 (Parasitics)
# ==============================================================================
class ParasiticTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_trace = QGroupBox("1. PCB 走线寄生电感 (Trace Inductance)")
        grid_t = QGridLayout()
        grid_t.setVerticalSpacing(12)
        
        self.p_len = QLineEdit("10"); grid_t.addWidget(QLabel("长度 L [mm]:"), 0, 0); grid_t.addWidget(self.p_len, 0, 1)
        self.p_width = QLineEdit("0.5"); grid_t.addWidget(QLabel("宽度 W [mm]:"), 0, 2); grid_t.addWidget(self.p_width, 0, 3)
        self.p_thick = QLineEdit("0.035"); grid_t.addWidget(QLabel("厚度 T [mm]:"), 1, 0); grid_t.addWidget(self.p_thick, 1, 1)
        self.p_res_trace = QLineEdit(); self.p_res_trace.setReadOnly(True); self.p_res_trace.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
        grid_t.addWidget(QLabel("走线电感:"), 1, 2); grid_t.addWidget(self.p_res_trace, 1, 3)
        grp_trace.setLayout(grid_t)
        layout.addWidget(grp_trace)
        
        grp_via = QGroupBox("2. 过孔寄生电感 (Via Inductance)")
        grid_v = QGridLayout()
        grid_v.setVerticalSpacing(12)
        
        self.p_via_h = QLineEdit("1.6"); grid_v.addWidget(QLabel("过孔长度 h [mm]:"), 0, 0); grid_v.addWidget(self.p_via_h, 0, 1)
        self.p_via_d = QLineEdit("0.3"); grid_v.addWidget(QLabel("过孔直径 d [mm]:"), 0, 2); grid_v.addWidget(self.p_via_d, 0, 3)
        self.p_res_via = QLineEdit(); self.p_res_via.setReadOnly(True); self.p_res_via.setStyleSheet("background-color: #fdedec; font-weight: bold; color: #c0392b;")
        grid_v.addWidget(QLabel("单孔电感:"), 1, 2); grid_v.addWidget(self.p_res_via, 1, 3)
        grp_via.setLayout(grid_v)
        layout.addWidget(grp_via)
        
        btn = QPushButton("计算寄生电感 (Calculate)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_parasitic)
        layout.addWidget(btn)
        
        form_layout = QVBoxLayout()
        form_layout.setAlignment(Qt.AlignCenter)
        l1 = QLabel(); l1.setPixmap(render_formula(r'L_{trace} \approx 0.2 L [\ln(\frac{2L}{W+H}) + 0.22 \frac{W+H}{L} + 0.5] \text{ nH}'))
        l2 = QLabel(); l2.setPixmap(render_formula(r'L_{via} \approx 0.2 h [1 + \ln(\frac{4h}{d})] \text{ nH}'))
        form_layout.addWidget(l1)
        form_layout.addWidget(l2)
        layout.addLayout(form_layout)
        layout.addStretch()
        self.setLayout(layout)

    def calc_parasitic(self):
        try:
            l = float(self.p_len.text()); w = float(self.p_width.text()); t = float(self.p_thick.text())
            if l>0 and w>0 and t>0:
                term = (w + t)
                l_trace = 0.2 * l * (math.log((2 * l) / term) + 0.2235 * (term / l) + 0.5)
                self.p_res_trace.setText(f"{l_trace:.2f} nH")
            
            h = float(self.p_via_h.text()); d = float(self.p_via_d.text())
            if h>0 and d>0:
                l_via = 0.2 * h * (1 + math.log((4 * h) / d))
                self.p_res_via.setText(f"{l_via:.2f} nH")
        except: QMessageBox.warning(self, "错误", "输入数值无效")

# ==============================================================================
# 3. PCB 平面电容计算 (Planar Capacitance)
# ==============================================================================
class PlanarCapacitanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：计算 PCB 两个平面层（如 Power 和 GND）之间的寄生电容。\n"
                      "该电容可作为极高频的去耦电容。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. 参数输入
        grp_in = QGroupBox("1. 平面参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        # 面积计算
        self.pc_len = QLineEdit("50"); self.pc_len.setPlaceholderText("长 L")
        self.pc_wid = QLineEdit("20"); self.pc_wid.setPlaceholderText("宽 W")
        hbox_dim = QHBoxLayout(); hbox_dim.addWidget(self.pc_len); hbox_dim.addWidget(QLabel("x")); hbox_dim.addWidget(self.pc_wid)
        grid.addWidget(QLabel("重叠区域尺寸 [mm]:"), 0, 0); grid.addLayout(hbox_dim, 0, 1)
        
        self.pc_area = QLineEdit("1000"); 
        grid.addWidget(QLabel("或 直接输入面积 [mm²]:"), 1, 0); grid.addWidget(self.pc_area, 1, 1)
        
        self.pc_len.textChanged.connect(self.update_area_from_dim)
        self.pc_wid.textChanged.connect(self.update_area_from_dim)
        
        # 介质厚度
        self.pc_dist = QLineEdit("0.1"); self.pc_dist.setToolTip("层间介质厚度 (Prepreg Thickness)")
        self.pc_dist_unit = QComboBox(); self.pc_dist_unit.addItems(["mm", "mil"])
        hbox_d = QHBoxLayout(); hbox_d.addWidget(self.pc_dist); hbox_d.addWidget(self.pc_dist_unit)
        grid.addWidget(QLabel("介质厚度 d:"), 2, 0); grid.addLayout(hbox_d, 2, 1)
        
        # 介电常数
        self.pc_dk = QComboBox()
        self.pc_dk.addItem("FR-4 (Standard)", 4.4)
        self.pc_dk.addItem("Polyimide (FPC)", 3.5)
        self.pc_dk.addItem("Rogers 4350B", 3.66)
        self.pc_dk.addItem("Rogers 4003C", 3.55)
        self.pc_dk.addItem("自定义", 1.0)
        self.pc_dk.setEditable(True)
        grid.addWidget(QLabel("介电常数 Dk (εr):"), 3, 0); grid.addWidget(self.pc_dk, 3, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn_calc = QPushButton("计算平面电容")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_capacitance)
        layout.addWidget(btn_calc)
        
        # 2. 结果
        grp_res = QGroupBox("2. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_cap_pf = QLineEdit()
        self.res_cap_nf = QLineEdit()
        self.res_xc = QLineEdit()
        
        r_grid.addWidget(QLabel("平面电容 C_plane:"), 0, 0); r_grid.addWidget(self.res_cap_pf, 0, 1); r_grid.addWidget(QLabel("pF"), 0, 2)
        r_grid.addWidget(QLabel(""), 1, 0); r_grid.addWidget(self.res_cap_nf, 1, 1); r_grid.addWidget(QLabel("nF"), 1, 2)
        
        l_form = QLabel()
        l_form.setPixmap(render_formula(r'C \approx \frac{0.225 \cdot D_k \cdot Area}{d} \text{ pF}'))
        r_grid.addWidget(l_form, 2, 0, 1, 3)
        
        h_imp = QHBoxLayout()
        self.pc_freq = QLineEdit("100"); self.pc_freq.setPlaceholderText("MHz")
        h_imp.addWidget(QLabel("在频率 [MHz]:")); h_imp.addWidget(self.pc_freq)
        h_imp.addWidget(QLabel("下的容抗 Xc [Ω]:")); h_imp.addWidget(self.res_xc)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        self.res_cap_pf.setReadOnly(True); self.res_cap_pf.setStyleSheet(style)
        self.res_cap_nf.setReadOnly(True); self.res_cap_nf.setStyleSheet(style)
        self.res_xc.setReadOnly(True); self.res_xc.setStyleSheet("background-color: #f0f0f0; font-weight: bold;")
        
        layout.addWidget(grp_res)
        layout.addLayout(h_imp)
        layout.addStretch()
        self.setLayout(layout)

    def update_area_from_dim(self):
        try:
            l = float(self.pc_len.text())
            w = float(self.pc_wid.text())
            self.pc_area.setText(f"{l*w:.2f}")
        except: pass

    def calc_capacitance(self):
        try:
            area_mm2 = float(self.pc_area.text())
            d_val = float(self.pc_dist.text())
            is_mil = self.pc_dist_unit.currentText() == "mil"
            
            try:
                dk = float(self.pc_dk.currentText()) 
            except:
                dk = self.pc_dk.currentData() 
            
            if area_mm2 <= 0 or d_val <= 0 or dk <= 0: raise ValueError
            
            d_mm = d_val * 0.0254 if is_mil else d_val
            
            c_pf = 0.008854 * dk * area_mm2 / d_mm
            c_nf = c_pf / 1000.0
            
            self.res_cap_pf.setText(f"{c_pf:.2f}")
            self.res_cap_nf.setText(f"{c_nf:.4f}")
            
            try:
                f_mhz = float(self.pc_freq.text())
                if f_mhz > 0:
                    f = f_mhz * 1e6
                    c = c_pf * 1e-12
                    xc = 1.0 / (2 * math.pi * f * c)
                    self.res_xc.setText(f"{xc:.4f}")
            except: pass
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")