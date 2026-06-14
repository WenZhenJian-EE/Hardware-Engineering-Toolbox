# modules/power/dcdc_basic.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from modules.base_module import BaseModule
from core.formula_dcdc import (
    calc_buck_converter, calc_boost_converter, calc_inverting_buck_boost,
    calc_flyback_converter, calc_ldo_thermal
)

class DcdcCalculatorWindow(BaseModule):
    """
    DC-DC (Buck/Boost/Inv/Flyback) & LDO 计算工具
    """
    category = "1. 磁性元件与电源拓扑 (Magnetics & Topology)"
    display_name = "DC-DC 基础"
    description = "Buck / Boost / 负压 / 反激 / LDO"
    window_id = "power_dcdc"

    def init_module_ui(self):
        self.setWindowTitle('DC-DC (Buck/Boost/Inv/Flyback) & LDO & 动态响应')
        self.setGeometry(350, 350, 1100, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计原理与公式说明")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(200)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # Tab 容器
        self.tabs = QTabWidget()

        self.tab_buck = QWidget()
        self.tab_boost = QWidget()
        self.tab_inv = QWidget()
        self.tab_flyback = QWidget()
        self.tab_flyback_detail = QWidget()
        self.tab_ldo = QWidget()

        self.init_buck_ui(self.tab_buck)
        self.init_boost_ui(self.tab_boost)
        self.init_inv_ui(self.tab_inv)
        self.init_flyback_ui(self.tab_flyback)
        self.init_flyback_detail_ui(self.tab_flyback_detail)
        self.init_ldo_ui(self.tab_ldo)

        self.tabs.addTab(self.tab_buck, "Buck 降压")
        self.tabs.addTab(self.tab_boost, "Boost 升压")
        self.tabs.addTab(self.tab_inv, "负压 Inverting")
        self.tabs.addTab(self.tab_flyback, "Flyback 反激")
        self.tabs.addTab(self.tab_flyback_detail, "Flyback 详细设计")
        self.tabs.addTab(self.tab_ldo, "LDO 线性稳压")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: Buck Converter
    # ==============================================================================
    def init_buck_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入区
        input_group = QGroupBox("输入参数")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        self.bk_vin = QLineEdit("12")
        self.bk_vout = QLineEdit("5")
        self.bk_iout = QLineEdit("2")
        self.bk_fsw = QLineEdit("500")
        self.bk_k_ind = QLineEdit("30")
        self.bk_k_out = QLineEdit("1")
        
        inputs = [
            ("输入电压 (Vin) [V]:", self.bk_vin),
            ("输出电压 (Vout) [V]:", self.bk_vout),
            ("最大输出电流 (Iout) [A]:", self.bk_iout),
            ("开关频率 (fsw) [kHz]:", self.bk_fsw),
            ("电感纹波率 (LIR) [%]:", self.bk_k_ind),
            ("输出电压纹波 [%]:", self.bk_k_out)
        ]
        
        for i, (txt, w) in enumerate(inputs):
            r, c = i//2, (i%2)*2
            input_layout.addWidget(QLabel(txt), r, c)
            input_layout.addWidget(w, r, c+1)
            
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算 Buck 参数")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_buck)
        layout.addWidget(btn)
        
        # 结果区
        out_group = QGroupBox("计算结果")
        out_grid = QGridLayout()
        out_grid.setVerticalSpacing(12)
        
        self.bk_d = QLineEdit()
        self.bk_l = QLineEdit()
        self.bk_c = QLineEdit()
        self.bk_ipeak = QLineEdit()
        self.bk_cin_rms = QLineEdit()
        self.bk_cout_rms = QLineEdit()
        
        res_list = [
            ("占空比 (Duty):", self.bk_d, r'D = V_{out} / V_{in}'),
            ("最小电感 (L_min):", self.bk_l, r'L = \frac{V_{out}(V_{in}-V_{out})}{V_{in} \cdot f_{sw} \cdot \Delta I_L}'),
            ("最小输出电容 (C_min):", self.bk_c, r'C_{out} = \frac{\Delta I_L}{8 \cdot f_{sw} \cdot \Delta V_{out}}'),
            ("电感峰值电流 (I_pk):", self.bk_ipeak, r'I_{pk} = I_{out} + \Delta I_L / 2'),
            ("输入电容纹波 (I_Cin_rms):", self.bk_cin_rms, r'I_{Cin} = I_{out}\sqrt{D(1-D)}'),
            ("输出电容纹波 (I_Cout_rms):", self.bk_cout_rms, r'I_{Cout} \approx \Delta I_L / \sqrt{12}')
        ]
        
        for i, (label, widget, formula) in enumerate(res_list):
            out_grid.addWidget(QLabel(label), i, 0)
            widget.setReadOnly(True)
            out_grid.addWidget(widget, i, 1)
            l_form = QLabel(); l_form.setPixmap(self.render_formula(formula))
            out_grid.addWidget(l_form, i, 2)
            
        out_group.setLayout(out_grid)
        layout.addWidget(out_group)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_buck(self):
        try:
            vin = float(self.bk_vin.text())
            vout = float(self.bk_vout.text())
            iout = float(self.bk_iout.text())
            fsw_khz = float(self.bk_fsw.text())
            lir_pct = float(self.bk_k_ind.text())
            v_rip_pct = float(self.bk_k_out.text())
            
            res = calc_buck_converter(vin, vout, iout, fsw_khz, lir_pct, v_rip_pct)
            
            self.bk_d.setText(f"{res['duty']:.4f}")
            self.bk_l.setText(f"{res['l_min_h']*1e6:.2f} uH")
            self.bk_c.setText(f"{res['c_min_f']*1e6:.2f} uF")
            self.bk_ipeak.setText(f"{res['i_peak_a']:.3f} A")
            self.bk_cin_rms.setText(f"{res['cin_rms_a']:.3f} A")
            self.bk_cout_rms.setText(f"{res['cout_rms_a']:.3f} A")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    # ==============================================================================
    # Tab 2: Boost Converter
    # ==============================================================================
    def init_boost_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入区
        input_group = QGroupBox("输入参数")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        self.bst_vin = QLineEdit("3.3"); input_layout.addWidget(QLabel("输入电压 (Vin) [V]:"), 0, 0); input_layout.addWidget(self.bst_vin, 0, 1)
        self.bst_vout = QLineEdit("12"); input_layout.addWidget(QLabel("输出电压 (Vout) [V]:"), 0, 2); input_layout.addWidget(self.bst_vout, 0, 3)
        self.bst_iout = QLineEdit("1.0"); input_layout.addWidget(QLabel("输出电流 (Iout) [A]:"), 1, 0); input_layout.addWidget(self.bst_iout, 1, 1)
        self.bst_fsw = QLineEdit("500"); input_layout.addWidget(QLabel("开关频率 (fsw) [kHz]:"), 1, 2); input_layout.addWidget(self.bst_fsw, 1, 3)
        self.bst_lir = QLineEdit("40"); input_layout.addWidget(QLabel("纹波率 (LIR) [%]:"), 2, 0); input_layout.addWidget(self.bst_lir, 2, 1)
        self.bst_vf = QLineEdit("0.5"); input_layout.addWidget(QLabel("二极管压降 (Vf) [V]:"), 2, 2); input_layout.addWidget(self.bst_vf, 2, 3)
        
        tip = QLabel("说明：Boost 电路因右半平面零点(RHPZ)限制，LIR通常取 30%~50%，比 Buck 稍大以减小电感体积。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic;")
        input_layout.addWidget(tip, 3, 0, 1, 4)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算 Boost 参数")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_boost)
        layout.addWidget(btn)
        
        # 结果区
        out_group = QGroupBox("计算结果")
        out_grid = QGridLayout()
        out_grid.setVerticalSpacing(12)
        
        self.bst_d = QLineEdit()
        self.bst_l = QLineEdit()
        self.bst_ipeak = QLineEdit()
        self.bst_rhpz = QLineEdit()
        self.bst_ploss = QLineEdit()
        self.bst_cin_rms = QLineEdit()
        self.bst_cout_rms = QLineEdit()
        
        res_list = [
            ("占空比 (Duty):", self.bst_d, r'D = 1 - \frac{V_{in}}{V_{out}}'),
            ("所需电感 (L):", self.bst_l, r'L = \frac{V_{in} \cdot D}{f_{sw} \cdot \Delta I_L}'),
            ("电感峰值电流 (I_pk):", self.bst_ipeak, r'I_{pk} = \frac{I_{out}}{1-D} + \frac{\Delta I_L}{2}'),
            ("右半平面零点 (RHPZ):", self.bst_rhpz, r'f_{RHPZ} = \frac{R_L (1-D)^2}{2\pi L}'),
            ("二极管损耗 (P_diode):", self.bst_ploss, r'P_{diode} \approx V_F \cdot I_{out}'),
            ("输入电容纹波 (I_Cin_rms):", self.bst_cin_rms, r'I_{Cin} \approx \Delta I_L / \sqrt{12}'),
            ("输出电容纹波 (I_Cout_rms):", self.bst_cout_rms, r'I_{Cout} = I_{out}\sqrt{\frac{D}{1-D}}')
        ]
        
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400;"
        
        for i, (label, widget, formula) in enumerate(res_list):
            out_grid.addWidget(QLabel(label), i, 0)
            widget.setReadOnly(True)
            if "RHPZ" in label: 
                widget.setStyleSheet(style_warn)
            out_grid.addWidget(widget, i, 1)
            l_form = QLabel(); l_form.setPixmap(self.render_formula(formula))
            out_grid.addWidget(l_form, i, 2)
            
        out_group.setLayout(out_grid)
        layout.addWidget(out_group)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_boost(self):
        try:
            vin = float(self.bst_vin.text())
            vout = float(self.bst_vout.text())
            iout = float(self.bst_iout.text())
            fsw_khz = float(self.bst_fsw.text())
            lir_pct = float(self.bst_lir.text())
            vf = float(self.bst_vf.text())
            
            res = calc_boost_converter(vin, vout, iout, fsw_khz, lir_pct, vf)
            
            self.bst_d.setText(f"{res['duty']:.4f}")
            self.bst_l.setText(f"{res['l_h']*1e6:.2f} uH")
            self.bst_ipeak.setText(f"{res['i_peak_a']:.3f} A")
            self.bst_rhpz.setText(f"{res['f_rhpz_hz']/1000:.2f} kHz")
            self.bst_ploss.setText(f"{res['p_diode_w']:.2f} W")
            self.bst_cin_rms.setText(f"{res['cin_rms_a']:.3f} A")
            self.bst_cout_rms.setText(f"{res['cout_rms_a']:.3f} A")
            
            bandwidth_limit = res['f_rhpz_hz'] / 3.0
            self.bst_rhpz.setToolTip(f"环路带宽建议限制在 {bandwidth_limit/1000:.1f} kHz 以内")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    # ==============================================================================
    # Tab 3: Inverting Buck-Boost
    # ==============================================================================
    def init_inv_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 说明
        desc_box = QGroupBox("应用场景说明")
        desc_layout = QVBoxLayout()
        desc_lbl = QLabel("适用：运放负电源 (如 -5V, -12V) 或 GaN 驱动负偏置 (如 -3V)。\n方法：使用普通 Buck 芯片，将 Vout 接地，GND 接负输出。")
        desc_lbl.setStyleSheet("color: #2980b9; font-style: italic;")
        desc_layout.addWidget(desc_lbl)
        desc_box.setLayout(desc_layout)
        layout.addWidget(desc_box)

        # 输入
        input_group = QGroupBox("输入参数 (Input)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.inv_vin = QLineEdit("12"); grid.addWidget(QLabel("输入电压 (Vin) [V]:"), 0, 0); grid.addWidget(self.inv_vin, 0, 1)
        self.inv_vout = QLineEdit("-5"); self.inv_vout.setPlaceholderText("例如 -5"); grid.addWidget(QLabel("目标负电压 (Vout) [V]:"), 0, 2); grid.addWidget(self.inv_vout, 0, 3)
        self.inv_iout = QLineEdit("0.5"); grid.addWidget(QLabel("最大负载电流 (Iout) [A]:"), 1, 0); grid.addWidget(self.inv_iout, 1, 1)
        self.inv_fsw = QLineEdit("300"); grid.addWidget(QLabel("开关频率 (fsw) [kHz]:"), 1, 2); grid.addWidget(self.inv_fsw, 1, 3)
        self.inv_lir = QLineEdit("40"); grid.addWidget(QLabel("电感纹波率 (LIR) [%]:"), 2, 0); grid.addWidget(self.inv_lir, 2, 1)
        self.inv_vf = QLineEdit("0.5"); grid.addWidget(QLabel("二极管压降 (Vf) [V]:"), 2, 2); grid.addWidget(self.inv_vf, 2, 3)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算负压电路参数")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.setStyleSheet("background-color: #8e44ad; color: white;")
        btn.clicked.connect(self.calc_inv)
        layout.addWidget(btn)
        
        # 结果
        res_group = QGroupBox("关键设计指标 (Key Specs)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.inv_d = QLineEdit()
        self.inv_vsw = QLineEdit()
        self.inv_l = QLineEdit()
        self.inv_ipk = QLineEdit()
        self.inv_cin_rms = QLineEdit()
        self.inv_cout_rms = QLineEdit()
        
        # Duty
        r_grid.addWidget(QLabel("占空比 (Duty):"), 0, 0)
        r_grid.addWidget(self.inv_d, 0, 1)
        l_d = QLabel(); l_d.setPixmap(self.render_formula(r'D = \frac{|V_{out}|}{V_{in} + |V_{out}|}'))
        r_grid.addWidget(l_d, 0, 2)
        
        # Voltage Stress
        r_grid.addWidget(QLabel("开关管承受电压 (V_sw):"), 1, 0)
        r_grid.addWidget(self.inv_vsw, 1, 1)
        l_v = QLabel(); l_v.setPixmap(self.render_formula(r'V_{sw} = V_{in} + |V_{out}|'))
        r_grid.addWidget(l_v, 1, 2)
        
        # Inductor
        r_grid.addWidget(QLabel("最小电感 (L_min):"), 2, 0)
        r_grid.addWidget(self.inv_l, 2, 1)
        l_l = QLabel(); l_l.setPixmap(self.render_formula(r'L = \frac{V_{in} \cdot D}{f_{sw} \cdot \Delta I_L}'))
        r_grid.addWidget(l_l, 2, 2)
        
        # Peak Current
        r_grid.addWidget(QLabel("电感/开关峰值电流 (I_pk):"), 3, 0)
        r_grid.addWidget(self.inv_ipk, 3, 1)
        l_i = QLabel(); l_i.setPixmap(self.render_formula(r'I_{pk} = \frac{I_{out}}{1-D} + \frac{\Delta I_L}{2}'))
        r_grid.addWidget(l_i, 3, 2)

        # Cin RMS
        r_grid.addWidget(QLabel("输入电容纹波 (I_Cin_rms):"), 4, 0)
        r_grid.addWidget(self.inv_cin_rms, 4, 1)
        l_cin = QLabel(); l_cin.setPixmap(self.render_formula(r'I_{Cin} \approx I_{in\_avg}\sqrt{\frac{1-D}{D}}'))
        r_grid.addWidget(l_cin, 4, 2)

        # Cout RMS
        r_grid.addWidget(QLabel("输出电容纹波 (I_Cout_rms):"), 5, 0)
        r_grid.addWidget(self.inv_cout_rms, 5, 1)
        l_cout = QLabel(); l_cout.setPixmap(self.render_formula(r'I_{Cout} = I_{out}\sqrt{\frac{D}{1-D}}'))
        r_grid.addWidget(l_cout, 5, 2)
        
        style_alert = "background-color: #fff5f5; font-weight: bold; color: #c0392b;" # Red for voltage stress warning
        
        for w in [self.inv_d, self.inv_l, self.inv_ipk, self.inv_cin_rms, self.inv_cout_rms]:
            w.setReadOnly(True)
        
        self.inv_vsw.setReadOnly(True); self.inv_vsw.setStyleSheet(style_alert)
        self.inv_vsw.setToolTip("注意！在 Buck-Boost 拓扑中，芯片承受的电压是 Vin+|Vout|，\n而不仅仅是 Vin。请务必核对芯片的 Max Input Voltage。")
        
        res_group.setLayout(r_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_inv(self):
        try:
            vin = float(self.inv_vin.text())
            vout_raw = float(self.inv_vout.text())
            iout = float(self.inv_iout.text())
            fsw_khz = float(self.inv_fsw.text())
            lir_pct = float(self.inv_lir.text())
            vf = float(self.inv_vf.text())
            
            res = calc_inverting_buck_boost(vin, vout_raw, iout, fsw_khz, lir_pct, vf)
            
            self.inv_d.setText(f"{res['duty']:.4f}")
            self.inv_vsw.setText(f"{res['v_stress_v']:.2f} V")
            self.inv_l.setText(f"{res['l_min_h']*1e6:.2f} uH")
            self.inv_ipk.setText(f"{res['i_peak_a']:.3f} A")
            self.inv_cin_rms.setText(f"{res['cin_rms_a']:.3f} A")
            self.inv_cout_rms.setText(f"{res['cout_rms_a']:.3f} A")
            
            if res['v_stress_v'] > 40 and vin < 40:
                QMessageBox.warning(self, "耐压警告", f"计算出的开关管应力为 {res['v_stress_v']:.1f}V。\n如果使用普通 40V 耐压的 Buck 芯片，可能处于危险边缘！")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数值无效: {e}")

    # ==============================================================================
    # Tab 4: Flyback Calculator
    # ==============================================================================
    def init_flyback_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入参数
        input_group = QGroupBox("输入参数 (DCM/CCM Boundary)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.fly_vin = QLineEdit("85"); grid.addWidget(QLabel("最小输入电压 Vin_min [V]:"), 0, 0); grid.addWidget(self.fly_vin, 0, 1)
        self.fly_vor = QLineEdit("80"); grid.addWidget(QLabel("反射电压 Vor [V]:"), 0, 2); grid.addWidget(self.fly_vor, 0, 3)
        self.fly_vout = QLineEdit("12"); grid.addWidget(QLabel("输出电压 Vout [V]:"), 1, 0); grid.addWidget(self.fly_vout, 1, 1)
        self.fly_iout = QLineEdit("2"); grid.addWidget(QLabel("输出电流 Iout [A]:"), 1, 2); grid.addWidget(self.fly_iout, 1, 3)
        self.fly_fsw = QLineEdit("65"); grid.addWidget(QLabel("开关频率 fsw [kHz]:"), 2, 0); grid.addWidget(self.fly_fsw, 2, 1)
        
        self.fly_krf = QLineEdit("0.4")
        self.fly_krf.setToolTip("纹波系数 Krf = dI / I_edc。Krf < 1 为 CCM，Krf = 2 为 BCM/DCM。")
        grid.addWidget(QLabel("纹波系数 Krf (0.3~0.5):"), 2, 2); grid.addWidget(self.fly_krf, 2, 3)
        
        self.fly_bmax = QLineEdit("0.25"); grid.addWidget(QLabel("最大磁通密度 Bmax [T]:"), 3, 0); grid.addWidget(self.fly_bmax, 3, 1)
        self.fly_ae = QLineEdit("23"); self.fly_ae.setToolTip("磁芯有效截面积 Ae")
        grid.addWidget(QLabel("磁芯 Ae [mm²]:"), 3, 2); grid.addWidget(self.fly_ae, 3, 3)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算反激变压器参数")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_flyback)
        layout.addWidget(btn)
        
        # 结果
        res_group = QGroupBox("计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.fly_lp = QLineEdit()
        self.fly_np = QLineEdit()
        self.fly_gap = QLineEdit()
        self.fly_ipk = QLineEdit()
        self.fly_cin_rms = QLineEdit()
        self.fly_cout_rms = QLineEdit()
        
        r_grid.addWidget(QLabel("原边电感 Lp [uH]:"), 0, 0); r_grid.addWidget(self.fly_lp, 0, 1)
        r_grid.addWidget(QLabel("原边匝数 Np [T]:"), 1, 0); r_grid.addWidget(self.fly_np, 1, 1)
        r_grid.addWidget(QLabel("气隙长度 lg [mm]:"), 2, 0); r_grid.addWidget(self.fly_gap, 2, 1)
        r_grid.addWidget(QLabel("原边峰值电流 I_pk [A]:"), 3, 0); r_grid.addWidget(self.fly_ipk, 3, 1)
        r_grid.addWidget(QLabel("输入电容纹波 (I_Cin_rms):"), 4, 0); r_grid.addWidget(self.fly_cin_rms, 4, 1)
        r_grid.addWidget(QLabel("输出电容纹波 (I_Cout_rms):"), 5, 0); r_grid.addWidget(self.fly_cout_rms, 5, 1)
        
        for w in [self.fly_lp, self.fly_np, self.fly_gap, self.fly_ipk, self.fly_cin_rms, self.fly_cout_rms]:
            w.setReadOnly(True)
            
        res_group.setLayout(r_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_flyback(self):
        try:
            vin_min = float(self.fly_vin.text())
            vor = float(self.fly_vor.text())
            vout = float(self.fly_vout.text())
            iout = float(self.fly_iout.text())
            fsw_khz = float(self.fly_fsw.text())
            krf = float(self.fly_krf.text())
            bmax = float(self.fly_bmax.text())
            ae = float(self.fly_ae.text())
            
            res = calc_flyback_converter(vin_min, vor, vout, iout, fsw_khz, krf, bmax, ae)
            
            self.fly_lp.setText(f"{res['lp_h']*1e6:.1f}")
            self.fly_np.setText(f"{res['np_turns']}")
            self.fly_gap.setText(f"{res['lg_m']*1000:.3f}")
            self.fly_ipk.setText(f"{res['ipk_a']:.2f}")
            self.fly_cin_rms.setText(f"{res['cin_rms_a']:.3f} A")
            self.fly_cout_rms.setText(f"{res['cout_rms_a']:.3f} A")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {e}")

    # ==============================================================================
    # Tab 4B: Detailed Flyback Design Helper
    # ==============================================================================
    def init_flyback_detail_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            "Detailed flyback first-pass design: turns ratio, Lm, peak current, air gap, "
            "MOSFET/rectifier stress, RCD/TVS clamp and CCM/DCM boundary."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #566573; font-style: italic;")
        layout.addWidget(info)

        grp = QGroupBox("1. Input and transformer target")
        g = QGridLayout()
        self.fbd_vin_min = QLineEdit("90")
        self.fbd_vin_max = QLineEdit("375")
        self.fbd_vout = QLineEdit("12")
        self.fbd_iout = QLineEdit("3")
        self.fbd_eff = QLineEdit("0.85")
        self.fbd_fsw = QLineEdit("65")
        self.fbd_dmax = QLineEdit("45")
        self.fbd_vf = QLineEdit("0.6")
        self.fbd_bmax = QLineEdit("0.22")
        self.fbd_ae = QLineEdit("80")
        self.fbd_leak = QLineEdit("2")
        self.fbd_clamp_margin = QLineEdit("30")

        fields = [
            ("Vin min [Vdc]:", self.fbd_vin_min),
            ("Vin max [Vdc]:", self.fbd_vin_max),
            ("Vout [V]:", self.fbd_vout),
            ("Iout [A]:", self.fbd_iout),
            ("Efficiency eta:", self.fbd_eff),
            ("fsw [kHz]:", self.fbd_fsw),
            ("Max duty [%]:", self.fbd_dmax),
            ("Secondary diode drop [V]:", self.fbd_vf),
            ("Bmax [T]:", self.fbd_bmax),
            ("Core Ae [mm2]:", self.fbd_ae),
            ("Leakage ratio [% of Lm]:", self.fbd_leak),
            ("Clamp margin above Vor [%]:", self.fbd_clamp_margin),
        ]
        for i, (label, widget) in enumerate(fields):
            r, c = i // 2, (i % 2) * 2
            g.addWidget(QLabel(label), r, c)
            g.addWidget(widget, r, c + 1)
        grp.setLayout(g)
        layout.addWidget(grp)

        btn = QPushButton("Calculate detailed flyback parameters")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_flyback_detail)
        layout.addWidget(btn)

        grp_res = QGroupBox("2. Results")
        r = QGridLayout()
        self.fbd_res = {}
        labels = [
            ("D at Vin_min:", "duty"),
            ("Reflected voltage Vor:", "vor"),
            ("Turns ratio Np:Ns:", "ratio"),
            ("Primary inductance Lm:", "lm"),
            ("Primary peak current Ipk:", "ipk"),
            ("Estimated primary turns Np:", "np"),
            ("Estimated air gap:", "gap"),
            ("CCM/DCM boundary load:", "boundary"),
            ("MOSFET Vds stress:", "vds"),
            ("Secondary diode VRRM:", "vrrm"),
            ("Leakage energy per cycle:", "eleak"),
            ("Clamp voltage target:", "clamp"),
        ]
        for i, (label, key) in enumerate(labels):
            w = QLineEdit()
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #1e8449;")
            self.fbd_res[key] = w
            rr, cc = i // 2, (i % 2) * 2
            r.addWidget(QLabel(label), rr, cc)
            r.addWidget(w, rr, cc + 1)
        grp_res.setLayout(r)
        layout.addWidget(grp_res)

        self.fbd_note = QTextBrowser()
        self.fbd_note.setMinimumHeight(120)
        self.fbd_note.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d5d8dc;")
        layout.addWidget(self.fbd_note)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_flyback_detail(self):
        try:
            vin_min = float(self.fbd_vin_min.text())
            vin_max = float(self.fbd_vin_max.text())
            vout = float(self.fbd_vout.text())
            iout = float(self.fbd_iout.text())
            eff = float(self.fbd_eff.text())
            fsw = float(self.fbd_fsw.text()) * 1e3
            dmax = float(self.fbd_dmax.text()) / 100.0
            vf = float(self.fbd_vf.text())
            bmax = float(self.fbd_bmax.text())
            ae = float(self.fbd_ae.text()) * 1e-6
            leak_ratio = float(self.fbd_leak.text()) / 100.0
            clamp_margin = float(self.fbd_clamp_margin.text()) / 100.0

            if min(vin_min, vin_max, vout, iout, eff, fsw, dmax, bmax, ae) <= 0:
                raise ValueError
            if dmax >= 0.8 or vin_max < vin_min:
                raise ValueError

            pout = vout * iout
            pin = pout / eff
            vor = vin_min * dmax / (1.0 - dmax)
            nps = vor / (vout + vf)

            ton = dmax / fsw
            iavg_primary_on = pin / (vin_min * dmax)
            ipk = 2.0 * iavg_primary_on
            lm = vin_min * ton / ipk
            np_turns = max(1, math.ceil(vin_min * ton / (bmax * ae)))

            mu0 = 4.0 * math.pi * 1e-7
            gap = mu0 * (np_turns ** 2) * ae / lm
            load_boundary = 0.5 * lm * (ipk ** 2) * fsw * eff / vout
            vds = vin_max + vor * (1.0 + clamp_margin)
            vrrm = vout + vf + vin_max / nps
            lleak = lm * leak_ratio
            eleak = 0.5 * lleak * ipk ** 2
            clamp_v = vor * (1.0 + clamp_margin)
            p_clamp = eleak * fsw

            self.fbd_res["duty"].setText(f"{dmax:.3f}")
            self.fbd_res["vor"].setText(f"{vor:.1f} V")
            self.fbd_res["ratio"].setText(f"{nps:.2f} : 1")
            self.fbd_res["lm"].setText(f"{lm * 1e6:.1f} uH")
            self.fbd_res["ipk"].setText(f"{ipk:.2f} A")
            self.fbd_res["np"].setText(f"{np_turns} turns")
            self.fbd_res["gap"].setText(f"{gap * 1e3:.3f} mm")
            self.fbd_res["boundary"].setText(f"{load_boundary:.2f} A output")
            self.fbd_res["vds"].setText(f"{vds:.1f} V")
            self.fbd_res["vrrm"].setText(f"{vrrm:.1f} V")
            self.fbd_res["eleak"].setText(f"{eleak * 1e6:.2f} uJ")
            self.fbd_res["clamp"].setText(f"{clamp_v:.1f} V, P~{p_clamp:.2f} W")

            mode = "BCM/DCM boundary is above full load; design tends DCM." if load_boundary > iout else "Full load is above boundary; design tends CCM."
            self.fbd_note.setHtml(
                f"<b>Mode hint:</b> {mode}<br>"
                f"<b>Clamp hint:</b> MOSFET rating should exceed Vds stress with margin. "
                f"RCD resistor initial estimate: R ~= Vclamp^2 / Pleak if using dissipative clamp.<br>"
                f"<b>Thermal hint:</b> clamp loss estimate is only leakage-energy loss; verify leakage inductance from sample transformer."
            )
        except Exception:
            QMessageBox.warning(self, "Input error", "Please check flyback detailed design inputs.")

    # ==============================================================================
    # Tab 5: LDO Thermal
    # ==============================================================================
    def init_ldo_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info_lbl = QLabel("<b>核心逻辑：</b> LDO 的功耗 $P_D = (V_{in} - V_{out}) \\times I_{out} + V_{in} \\times I_q$<br>"
                          "<b>结温计算：</b> $T_J = T_A + P_D \\times \\theta_{JA}$")
        info_lbl.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        layout.addWidget(info_lbl)

        # 参数输入
        grp_in = QGroupBox("输入参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.ldo_inp_vin = QLineEdit("12.0"); grid.addWidget(QLabel("输入电压 Vin [V]:"), 0, 0); grid.addWidget(self.ldo_inp_vin, 0, 1)
        self.ldo_inp_vout = QLineEdit("3.3"); grid.addWidget(QLabel("输出电压 Vout [V]:"), 0, 2); grid.addWidget(self.ldo_inp_vout, 0, 3)
        self.ldo_inp_iout = QLineEdit("0.3"); grid.addWidget(QLabel("负载电流 Iout [A]:"), 1, 0); grid.addWidget(self.ldo_inp_iout, 1, 1)
        self.ldo_inp_iq = QLineEdit("0.005"); grid.addWidget(QLabel("静态电流 Iq [A]:"), 1, 2); grid.addWidget(self.ldo_inp_iq, 1, 3)
        
        self.ldo_inp_rja = QLineEdit("65.0"); grid.addWidget(QLabel("热阻 θ_JA [°C/W]:"), 2, 0); grid.addWidget(self.ldo_inp_rja, 2, 1)
        self.ldo_inp_ta = QLineEdit("60.0"); grid.addWidget(QLabel("最高环境温度 Ta [°C]:"), 2, 2); grid.addWidget(self.ldo_inp_ta, 2, 3)
        
        btn = QPushButton("计算功耗与结温 (T_J)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; margin-top: 10px;")
        btn.clicked.connect(self.calc_ldo)
        grid.addWidget(btn, 3, 0, 1, 4)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)

        # 结果输出
        grp_res = QGroupBox("计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.ldo_out_pd = QLineEdit()
        self.ldo_out_tj = QLineEdit()
        self.ldo_status_lbl = QLabel("等待计算...")
        
        for w in [self.ldo_out_pd, self.ldo_out_tj]: 
            w.setReadOnly(True)
            
        r_grid.addWidget(QLabel("总功耗 Pd [W]:"), 0, 0); r_grid.addWidget(self.ldo_out_pd, 0, 1)
        r_grid.addWidget(QLabel("最高结温 T_J [°C]:"), 1, 0); r_grid.addWidget(self.ldo_out_tj, 1, 1)
        r_grid.addWidget(self.ldo_status_lbl, 2, 0, 1, 2)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_ldo(self):
        try:
            vin = float(self.ldo_inp_vin.text())
            vout = float(self.ldo_inp_vout.text())
            iout = float(self.ldo_inp_iout.text())
            iq = float(self.ldo_inp_iq.text())
            rja = float(self.ldo_inp_rja.text())
            ta = float(self.ldo_inp_ta.text())
            
            res = calc_ldo_thermal(vin, vout, iout, iq, rja, ta)
            pd = res['pd_w']
            tj = res['tj_c']
            
            self.ldo_out_pd.setText(f"{pd:.4f}")
            self.ldo_out_tj.setText(f"{tj:.2f}")
            
            # T_J 范围判定
            if tj >= 150:
                self.ldo_status_lbl.setText("【极危】结温已超过绝对最大额定值，芯片可能瞬间烧毁！")
                self.ldo_status_lbl.setStyleSheet("color: #c0392b; font-weight: bold;")
                self.ldo_out_tj.setStyleSheet("background-color: #f2d7d5; color: #c0392b; font-weight: bold; font-size: 14px;")
            elif tj >= 125:
                self.ldo_status_lbl.setText("【警告】结温超过 125°C 工业级上限，长期运行寿命将严重衰减！")
                self.ldo_status_lbl.setStyleSheet("color: #d35400; font-weight: bold;")
                self.ldo_out_tj.setStyleSheet("background-color: #fdebd0; color: #d35400; font-weight: bold; font-size: 14px;")
            elif tj >= 100:
                self.ldo_status_lbl.setText("【注意】结温较高，符合允许范围，但烫手。")
                self.ldo_status_lbl.setStyleSheet("color: #b7950b; font-weight: bold;")
                self.ldo_out_tj.setStyleSheet("background-color: #fcf3cf; color: #b7950b; font-weight: bold; font-size: 14px;")
            else:
                self.ldo_status_lbl.setText("【安全】热裕量充足，芯片运行在安全温度区间内。")
                self.ldo_status_lbl.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.ldo_out_tj.setStyleSheet("background-color: #e8f8f5; color: #27ae60; font-weight: bold; font-size: 14px;")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数据无效: {e}")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("DC-DC 计算原理说明")
        dialog.resize(850, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 10px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 8px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
        </style>
        
        <h1>电源设计计算指南</h1>
        
        <h2>1. Buck 电感计算</h2>
        <p><b>原理：</b> 利用伏秒平衡原理。电感两端电压积分在一个周期内为 0。</p>
        <ul>
            <li>开通时：V_L = Vin - Vout，持续时间 D*T</li>
            <li>关断时：V_L = -Vout，持续时间 (1-D)*T</li>
            <li>纹波电流 ΔIL = (Vin - Vout) * D / (L * f)</li>
        </ul>

        <h2>2. Boost 右半平面零点 (RHPZ)</h2>
        <p>Boost 和 Flyback 拓扑特有的现象。当负载突增，环路试图增加占空比 D 来提高电压。</p>
        <div class="box">
            <b>物理意义：</b> D 瞬间增加 -> (1-D) 减小 -> 二极管导通时间变短 -> 输出能量<b>暂时</b>减少 -> 电压反而<b>下跌</b>。
            这种“反向响应”表现为相位滞后 90 度但增益增加，极难补偿。
        </div>
        <p><b>对策：</b> 必须把环路带宽 fc 限制在 RHPZ 频率 of 1/3 ~ 1/5 以下。</p>

        <h2>3. 负载动态响应 (Load Transient)</h2>
        <p>评估负载电流跳变（如 CPU 唤醒）时输出电压的波动。</p>
        <ul>
            <li><b>ESR 跌落：</b> 瞬间发生，由电容内阻决定。 $\Delta V = \Delta I \cdot ESR$</li>
            <li><b>电容跌落：</b> 环路反应过来之前，由电容电荷支撑。 $\Delta V \approx \frac{\Delta I}{2\pi f_c C_{out}}$</li>
            <li><b>结论：</b> 要想动态好，要么加大 fc (带宽)，要么加大 Cout，或者减小 ESR。</li>
        </ul>
        
        <h2>4. 电容纹波电流 (RMS Current)</h2>
        <p>选择滤波电容（尤其是铝电解）时，必须确保其额定纹波电流 (Ripple Current Rating) 大于实际电路产生的 RMS 值，否则电容会发热爆炸。</p>
        <ul>
            <li><b>Buck 输入电容：</b> 电流是脉冲的，RMS 很大！最大值发生在 D=0.5 时，约为 $0.5 \cdot I_{out}$。</li>
            <li><b>Boost 输出电容：</b> 二极管电流是脉冲的，RMS 很大！与 Buck 输入电容类似。</li>
            <li><b>反激 (Flyback)：</b> 输入和输出电容都承受脉冲电流，应力极大，需选用 Low ESR 品并考虑并联。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()
