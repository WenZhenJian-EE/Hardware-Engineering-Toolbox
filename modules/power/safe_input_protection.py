from modules.base_module import BaseModule
# safe_fuse_inrush.py

import math
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class FuseCalculatorWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "输入保护器件"
    description = "保险丝 I²t / NTC 能量"
    window_id = "safe_fuse"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('输入保护设计助手 (保险丝 & NTC)')
        self.setGeometry(350, 350, 950, 750)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计原理：I²t 与 能量")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # Tab
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_fuse = QWidget()
        self.tab_ntc = QWidget() # 新增: NTC
        self.tab_xcap = QWidget() # 新增: X-Capacitor Safety Discharge

        self.init_fuse_ui(self.tab_fuse)
        self.init_ntc_ui(self.tab_ntc)
        self.init_xcap_ui(self.tab_xcap)

        self.tabs.addTab(self.tab_fuse, "保险丝选型 (I²t 计算)")
        self.tabs.addTab(self.tab_ntc, "NTC 抑制电阻 (能量与冷却)")
        self.tabs.addTab(self.tab_xcap, "X电容安全放电与待机功耗")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: Fuse I2t Calculation
    # ==============================================================================
    def init_fuse_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 电路参数
        grp_in = QGroupBox("1. 输入电路参数 (Input Stage)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        # Voltage
        self.fuse_v_type = QComboBox()
        self.fuse_v_type.addItems(["AC 输入 (220Vac 等)", "DC 输入 (24Vdc 等)"])
        self.fuse_v_type.currentIndexChanged.connect(self.update_fuse_v_label)
        grid.addWidget(QLabel("输入类型:"), 0, 0); grid.addWidget(self.fuse_v_type, 0, 1)
        
        self.fuse_vin = QLineEdit("230")
        self.lbl_vin = QLabel("输入电压 Vin [Vrms]:")
        grid.addWidget(self.lbl_vin, 0, 2); grid.addWidget(self.fuse_vin, 0, 3)
        
        # Capacitor
        self.fuse_c = QLineEdit("100")
        self.fuse_c.setToolTip("输入端的总储能电容 (Bulk Capacitor)。\n浪涌能量主要去向。")
        grid.addWidget(QLabel("输入电容 C_bulk [uF]:"), 1, 0); grid.addWidget(self.fuse_c, 1, 1)
        
        # Resistance
        self.fuse_r = QLineEdit("5.0")
        self.fuse_r.setToolTip("回路总串联电阻。\n包括: NTC(冷态), ESR, 整流桥内阻, 线路阻抗等。\n不要填 0，否则电流无穷大！建议估算 0.1~10Ω。")
        grid.addWidget(QLabel("回路总电阻 R_series [Ω]:"), 1, 2); grid.addWidget(self.fuse_r, 1, 3)
        
        # Safety Factor
        self.fuse_factor = QLineEdit("0.3") # Pulse Cycle Withstand Capability
        self.fuse_factor.setToolTip("脉冲折减系数 (Pulse Derating Factor)。\n为了保证保险丝能承受 10万次以上的开机浪涌，\n实际产生的 I2t 应不大于保险丝额定 Melting I2t 的 20%~30%。")
        grid.addWidget(QLabel("脉冲折减系数 (通常 0.2~0.3):"), 2, 0); grid.addWidget(self.fuse_factor, 2, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # Calculate Button
        btn = QPushButton("计算浪涌能量与 I2t")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_fuse)
        layout.addWidget(btn)
        
        # 2. 结果显示
        grp_res = QGroupBox("2. 计算结果与选型建议")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.res_ipeak = QLineEdit()
        self.res_tau = QLineEdit()
        self.res_i2t_calc = QLineEdit()
        self.res_i2t_req = QLineEdit()
        
        # Peak Current
        r_grid.addWidget(QLabel("峰值浪涌电流 (I_peak):"), 0, 0)
        r_grid.addWidget(self.res_ipeak, 0, 1)
        l_ipk = QLabel(); l_ipk.setPixmap(self.render_formula(r'I_{peak} = V_{peak} / R_{series}'))
        r_grid.addWidget(l_ipk, 0, 2)
        
        # Time Constant
        r_grid.addWidget(QLabel("充电时间常数 (τ = RC):"), 1, 0)
        r_grid.addWidget(self.res_tau, 1, 1)
        
        # Calculated I2t
        r_grid.addWidget(QLabel("浪涌 I²t (Calculated):"), 2, 0)
        r_grid.addWidget(self.res_i2t_calc, 2, 1)
        l_i2t = QLabel(); l_i2t.setPixmap(self.render_formula(r'I^2t \approx \frac{1}{2} I_{peak}^2 \tau = \frac{1}{2} \frac{V_{peak}^2 C}{R_{series}}'))
        r_grid.addWidget(l_i2t, 2, 2)
        
        # Fuse Requirement
        r_grid.addWidget(QLabel("保险丝最小 Melting I²t:"), 3, 0)
        r_grid.addWidget(self.res_i2t_req, 3, 1)
        l_req = QLabel(); l_req.setPixmap(self.render_formula(r'I^2t_{fuse} \geq \frac{I^2t_{calc}}{Factor}'))
        r_grid.addWidget(l_req, 3, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_req = "background-color: #fff8e1; font-weight: bold; color: #d35400; font-size: 14px;"
        
        self.res_ipeak.setReadOnly(True); self.res_ipeak.setStyleSheet(style_res)
        self.res_tau.setReadOnly(True); self.res_tau.setStyleSheet(style_res)
        self.res_i2t_calc.setReadOnly(True); self.res_i2t_calc.setStyleSheet(style_res)
        self.res_i2t_req.setReadOnly(True); self.res_i2t_req.setStyleSheet(style_req)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Warning Tip
        tip = QLabel("注意：请查阅保险丝 Datasheet 中的 'Melting Integral (I²t)' 参数。\n选型值必须大于计算出的 '最小 Melting I²t'，否则长期开关机可能导致保险丝疲劳熔断。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic; background-color: #f9f9f9; padding: 10px; border-radius: 4px;")
        layout.addWidget(tip)
        
        layout.addStretch()
        tab.setLayout(layout)

    def update_fuse_v_label(self):
        if self.fuse_v_type.currentIndex() == 0:
            self.lbl_vin.setText("输入电压 Vin [Vrms]:")
            self.fuse_vin.setText("230")
        else:
            self.lbl_vin.setText("输入电压 Vin [Vdc]:")
            self.fuse_vin.setText("24")

    def calc_fuse(self):
        try:
            vin_val = float(self.fuse_vin.text())
            c_uF = float(self.fuse_c.text())
            r_ohm = float(self.fuse_r.text())
            factor = float(self.fuse_factor.text())
            
            if r_ohm <= 0.001: raise ValueError("电阻不能为0")
            if factor <= 0 or factor > 1: raise ValueError("折减系数应在 0~1 之间")
            
            # Determine Peak Voltage
            if self.fuse_v_type.currentIndex() == 0: # AC
                v_peak = vin_val * math.sqrt(2)
            else: # DC
                v_peak = vin_val
                
            c_farad = c_uF * 1e-6
            
            # 1. Peak Current
            i_peak = v_peak / r_ohm
            
            # 2. Time Constant
            tau = r_ohm * c_farad
            
            # 3. I2t Calculation (Adiabatic approximation for RC charging)
            i2t_calc = 0.5 * (i_peak ** 2) * tau
            
            # 4. Requirement
            i2t_req = i2t_calc / factor
            
            self.res_ipeak.setText(f"{i_peak:.2f} A")
            self.res_tau.setText(f"{tau*1000:.2f} ms")
            self.res_i2t_calc.setText(f"{i2t_calc:.4f} A²s")
            self.res_i2t_req.setText(f"> {i2t_req:.4f} A²s")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数值无效: {str(e)}")

    # ==============================================================================
    # Tab 2: NTC Inrush Selection (New)
    # ==============================================================================
    def init_ntc_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 能量计算 (Energy Load)
        grp_sys = QGroupBox("1. 系统电容与能量 (Capacitor Energy)")
        grid_sys = QGridLayout()
        grid_sys.setVerticalSpacing(15)
        
        self.ntc_vin_max = QLineEdit("264"); self.ntc_vin_max.setToolTip("输入电压最大值 (AC则填RMS)")
        grid_sys.addWidget(QLabel("最大输入电压 Vin_max [V]:"), 0, 0); grid_sys.addWidget(self.ntc_vin_max, 0, 1)
        
        self.ntc_type = QComboBox(); self.ntc_type.addItems(["AC (RMS)", "DC (V)"])
        grid_sys.addWidget(self.ntc_type, 0, 2)
        
        self.ntc_c_bulk = QLineEdit("100"); self.ntc_c_bulk.setToolTip("母线总电容")
        grid_sys.addWidget(QLabel("母线电容 C_bulk [uF]:"), 1, 0); grid_sys.addWidget(self.ntc_c_bulk, 1, 1)
        
        grp_sys.setLayout(grid_sys)
        layout.addWidget(grp_sys)
        
        # 2. 候选器件参数 (Candidate NTC)
        grp_dev = QGroupBox("2. 候选 NTC 参数 (查 Datasheet)")
        grid_dev = QGridLayout()
        grid_dev.setVerticalSpacing(15)
        
        self.ntc_j_rating = QLineEdit("30"); self.ntc_j_rating.setToolTip("查阅规格书 'Max Energy Rating' 或 'C_test @ V_test'")
        grid_dev.addWidget(QLabel("最大能量额定值 [J]:"), 0, 0); grid_dev.addWidget(self.ntc_j_rating, 0, 1)
        
        self.ntc_diss = QLineEdit("15"); self.ntc_diss.setToolTip("耗散系数 (Dissipation Factor, δ)。\n通常 D-10 约为 10mW/C，D-20 约为 20mW/C。")
        grid_dev.addWidget(QLabel("耗散系数 (δ) [mW/°C]:"), 1, 0); grid_dev.addWidget(self.ntc_diss, 1, 1)
        
        grid_dev.addWidget(QLabel("注：用于估算冷却时间"), 1, 2)
        
        grp_dev.setLayout(grid_dev)
        layout.addWidget(grp_dev)
        
        # Button
        btn = QPushButton("计算能量冲击与冷却时间")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_ntc)
        layout.addWidget(btn)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.ntc_e_sys = QLineEdit()
        self.ntc_e_rec = QLineEdit()
        self.ntc_tau = QLineEdit()
        self.ntc_cool_time = QLineEdit()
        
        # Row 0: Energy
        r_grid.addWidget(QLabel("系统冲击能量 E_inrush:"), 0, 0); r_grid.addWidget(self.ntc_e_sys, 0, 1)
        l_e = QLabel(); l_e.setPixmap(self.render_formula(r'E = \frac{1}{2} C_{bulk} V_{peak}^2'))
        r_grid.addWidget(l_e, 0, 2)
        
        # Row 1: Requirement
        r_grid.addWidget(QLabel("NTC 最小能量规格 (Rec):"), 1, 0); r_grid.addWidget(self.ntc_e_rec, 1, 1)
        r_grid.addWidget(QLabel("建议预留 1.5~2 倍裕量"), 1, 2)
        
        # Row 2: Cooling
        r_grid.addWidget(QLabel("热时间常数 τ (估算):"), 2, 0); r_grid.addWidget(self.ntc_tau, 2, 1)
        l_tau = QLabel(); l_tau.setPixmap(self.render_formula(r'\tau_{th} \approx \frac{E_{rating}}{\delta \cdot \Delta T_{max}}'))
        r_grid.addWidget(l_tau, 2, 2)
        
        # Row 3: Restart Time
        r_grid.addWidget(QLabel("建议最小重启间隔 (3τ):"), 3, 0); r_grid.addWidget(self.ntc_cool_time, 3, 1)
        r_grid.addWidget(QLabel("冷却到室温需 3~5τ"), 3, 2)
        
        # Style
        style_res = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400;"
        
        for w in [self.ntc_e_sys, self.ntc_e_rec, self.ntc_tau]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
        self.ntc_cool_time.setReadOnly(True); self.ntc_cool_time.setStyleSheet(style_warn)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        
        tab.setLayout(layout)

    def calc_ntc(self):
        try:
            v_in = float(self.ntc_vin_max.text())
            c_uf = float(self.ntc_c_bulk.text())
            
            j_rate = float(self.ntc_j_rating.text())
            diss_mw = float(self.ntc_diss.text())
            
            if c_uf <= 0 or j_rate <= 0 or diss_mw <= 0: raise ValueError
            
            # 1. Calc System Energy
            if self.ntc_type.currentIndex() == 0: # AC
                v_peak = v_in * math.sqrt(2)
            else:
                v_peak = v_in
                
            e_sys = 0.5 * (c_uf * 1e-6) * (v_peak ** 2)
            
            # 2. Recommendation
            e_rec = e_sys * 1.5 # 1.5x Margin
            
            # 3. Estimate Thermal Time Constant (Tau)
            # Tau = Heat_Capacity / Dissipation_Factor
            # Where Heat_Capacity ~ Energy_Rating / Max_Temp_Rise (approx)
            # Assuming typical NTC max working temp rise is ~160C (25C -> 185C)
            delta_t_max = 160.0
            heat_capacity = j_rate / delta_t_max # J/C
            
            # Dissipation is mW/C -> W/C
            diss_w = diss_mw / 1000.0
            
            tau = heat_capacity / diss_w
            
            # 4. Cooling Time (3*Tau to 95% recovery)
            t_cool = 3 * tau
            
            self.ntc_e_sys.setText(f"{e_sys:.2f} J")
            self.ntc_e_rec.setText(f"> {e_rec:.2f} J")
            
            self.ntc_tau.setText(f"~ {tau:.1f} s")
            self.ntc_cool_time.setText(f"~ {t_cool:.0f} s")
            
            if e_sys > j_rate:
                self.ntc_e_sys.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
                QMessageBox.warning(self, "能量过大", f"当前电容充电能量 ({e_sys:.1f}J) 超过了 NTC 的额定值 ({j_rate:.1f}J)！\nNTC 可能会在开机瞬间炸裂。")
            else:
                self.ntc_e_sys.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def init_xcap_ui(self, tab):
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Left side: inputs and results
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setFixedWidth(450)
        
        # 1. 设计规格 (Specifications)
        grp_spec = QGroupBox("1. 设计规格 (Specifications)")
        g_spec = QGridLayout()
        g_spec.setVerticalSpacing(10)
        
        self.xcap_vac = QLineEdit("230")
        self.xcap_vac.setToolTip("标称输入交流电压有效值 (Vrms)")
        g_spec.addWidget(QLabel("交流输入电压 [Vrms]:"), 0, 0)
        g_spec.addWidget(self.xcap_vac, 0, 1)
        
        self.xcap_cx = QLineEdit("1.0")
        self.xcap_cx.setToolTip("输入端 X 电容总值 (uF)。多颗电容并联请填入总和。")
        g_spec.addWidget(QLabel("X电容总值 [uF]:"), 0, 2)
        g_spec.addWidget(self.xcap_cx, 0, 3)
        
        self.xcap_t_limit = QLineEdit("2.0")
        self.xcap_t_limit.setToolTip("安规要求的最大允许放电时间 (s)。IEC62368典型要求 < 2.0s，部分高要求产品如可插拔A型设备可能取 1.0s。")
        g_spec.addWidget(QLabel("放电时间限制 [s]:"), 1, 0)
        g_spec.addWidget(self.xcap_t_limit, 1, 1)
        
        self.xcap_v_safe = QLineEdit("60")
        self.xcap_v_safe.setToolTip("安全电压阈值 (V)。标准通常规定为 60V (对于潮湿环境可能是 34V，或规定衰减至原峰值的 37%)。")
        g_spec.addWidget(QLabel("安全电压阈值 [V]:"), 1, 2)
        g_spec.addWidget(self.xcap_v_safe, 1, 3)
        
        grp_spec.setLayout(g_spec)
        left_layout.addWidget(grp_spec)
        
        # 2. 放电电阻配置 (Resistors Config)
        grp_res_cfg = QGroupBox("2. 放电电阻配置 (Resistor Config)")
        g_res_cfg = QGridLayout()
        g_res_cfg.setVerticalSpacing(10)
        
        self.xcap_res_type = QComboBox()
        self.xcap_res_type.addItems(["自动推荐最佳阻值", "自定义选用总阻值 (MΩ)"])
        self.xcap_res_type.currentIndexChanged.connect(self.on_xcap_res_type_changed)
        g_res_cfg.addWidget(QLabel("阻值选择模式:"), 0, 0)
        g_res_cfg.addWidget(self.xcap_res_type, 0, 1, 1, 3)
        
        self.xcap_custom_res = QLineEdit("1.0")
        self.xcap_custom_res.setEnabled(False)
        self.xcap_custom_res.setStyleSheet("background-color: #f0f0f0;")
        self.xcap_custom_res.setToolTip("手动填入的放电电阻总阻值 (MΩ)。如果是由多个电阻串/并联，请填入等效总阻值。")
        g_res_cfg.addWidget(QLabel("实际总阻值 [MΩ]:"), 1, 0)
        g_res_cfg.addWidget(self.xcap_custom_res, 1, 1)
        
        self.xcap_n_series = QLineEdit("2")
        self.xcap_n_series.setToolTip("串联的电阻个数。为满足高压爬电距离和电压应力，一般在 AC 线上串联 2 或 3 个 SMD 电阻（如 1206/0805）。")
        g_res_cfg.addWidget(QLabel("串联电阻个数 N:"), 1, 2)
        g_res_cfg.addWidget(self.xcap_n_series, 1, 3)
        
        grp_res_cfg.setLayout(g_res_cfg)
        left_layout.addWidget(grp_res_cfg)
        
        # Calculate Button
        btn_calc = QPushButton("计算 X电容放电与待机功耗")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_xcap)
        left_layout.addWidget(btn_calc)
        
        # 3. 计算结果 (Results)
        grp_res = QGroupBox("3. 评估结果")
        g_res = QGridLayout()
        g_res.setVerticalSpacing(8)
        
        self.res_xcap_v_peak = QLineEdit(); self.res_xcap_v_peak.setReadOnly(True)
        self.res_xcap_r_max = QLineEdit(); self.res_xcap_r_max.setReadOnly(True)
        self.res_xcap_r_rec_e24 = QLineEdit(); self.res_xcap_r_rec_e24.setReadOnly(True)
        self.res_xcap_r_actual = QLineEdit(); self.res_xcap_r_actual.setReadOnly(True)
        self.res_xcap_r_single = QLineEdit(); self.res_xcap_r_single.setReadOnly(True)
        self.res_xcap_power_loss = QLineEdit(); self.res_xcap_power_loss.setReadOnly(True)
        self.res_xcap_status = QLineEdit(); self.res_xcap_status.setReadOnly(True)
        
        g_res.addWidget(QLabel("输入电压峰值 V_pk:"), 0, 0); g_res.addWidget(self.res_xcap_v_peak, 0, 1)
        g_res.addWidget(QLabel("最大允许总阻值 R_max:"), 0, 2); g_res.addWidget(self.res_xcap_r_max, 0, 3)
        
        g_res.addWidget(QLabel("推荐标准阻值 (E24):"), 1, 0); g_res.addWidget(self.res_xcap_r_rec_e24, 1, 1)
        g_res.addWidget(QLabel("选用实际总阻值 R_act:"), 1, 2); g_res.addWidget(self.res_xcap_r_actual, 1, 3)
        
        g_res.addWidget(QLabel("单个串联分担阻值:"), 2, 0); g_res.addWidget(self.res_xcap_r_single, 2, 1)
        g_res.addWidget(QLabel("待机功耗损耗 Ploss:"), 2, 2); g_res.addWidget(self.res_xcap_power_loss, 2, 3)
        
        g_res.addWidget(QLabel("安规放电校验结果:"), 3, 0); g_res.addWidget(self.res_xcap_status, 3, 1, 1, 3)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_power = "background-color: #fdedec; color: #c0392b; font-weight: bold;"
        for w in [self.res_xcap_v_peak, self.res_xcap_r_max, self.res_xcap_r_rec_e24, self.res_xcap_r_actual, self.res_xcap_r_single]:
            w.setStyleSheet(style_res)
        self.res_xcap_power_loss.setStyleSheet(style_power)
        
        grp_res.setLayout(g_res)
        left_layout.addWidget(grp_res)
        
        left_layout.addStretch()
        
        # Right side: plot
        self.xcap_plot_label = QLabel()
        self.xcap_plot_label.setAlignment(Qt.AlignCenter)
        self.xcap_plot_label.setStyleSheet("border: 1px solid #bdc3c7; background-color: white; border-radius: 4px;")
        self.xcap_plot_label.setMinimumSize(400, 350)
        
        layout.addWidget(left_widget)
        layout.addWidget(self.xcap_plot_label, stretch=1)
        
        tab.setLayout(layout)

    def on_xcap_res_type_changed(self, index):
        if index == 1: # 自定义选用总阻值
            self.xcap_custom_res.setEnabled(True)
            self.xcap_custom_res.setStyleSheet("background-color: #ffffff;")
        else:
            self.xcap_custom_res.setEnabled(False)
            self.xcap_custom_res.setStyleSheet("background-color: #f0f0f0;")

    def calc_xcap(self):
        try:
            vac = float(self.xcap_vac.text())
            cx_uf = float(self.xcap_cx.text())
            t_limit = float(self.xcap_t_limit.text())
            v_safe = float(self.xcap_v_safe.text())
            n_series = int(float(self.xcap_n_series.text()))
            
            if cx_uf <= 0 or t_limit <= 0 or v_safe <= 0 or n_series <= 0:
                raise ValueError
                
            v_peak = vac * math.sqrt(2)
            
            # 1. Calculate R_max (MΩ)
            if v_peak <= v_safe:
                r_max_m = 999.9
            else:
                cx_f = cx_uf * 1e-6
                r_max = t_limit / (cx_f * math.log(v_peak / v_safe)) # ohms
                r_max_m = r_max / 1e6 # MΩ
                
            # 2. Recommended E24 resistance
            e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
            if r_max_m == 999.9:
                r_rec_m = 10.0
            else:
                decade = 10 ** math.floor(math.log10(r_max_m))
                val_norm = r_max_m / decade
                target_norm = val_norm * 0.9 # 10% margin
                e24_candidates = [e for e in e24 if e <= target_norm]
                if e24_candidates:
                    r_rec_m = max(e24_candidates) * decade
                else:
                    r_rec_m = max(e24) * (decade / 10.0)
            
            # 3. Determine actual R used
            if self.xcap_res_type.currentIndex() == 0:
                r_actual_m = r_rec_m
                self.xcap_custom_res.setText(f"{r_actual_m:.3f}")
            else:
                r_actual_m = float(self.xcap_custom_res.text())
                
            r_actual_ohms = r_actual_m * 1e6
            r_single_m = r_actual_m / n_series
            
            # 4. Standby power loss (mW) = Vac^2 / R_actual_ohms * 1000
            p_loss_mw = (vac ** 2) / r_actual_ohms * 1000.0
            
            # 5. Check if passes safety time limit
            if v_peak <= v_safe:
                t_actual = 0.0
            else:
                t_actual = r_actual_ohms * (cx_uf * 1e-6) * math.log(v_peak / v_safe)
                
            self.res_xcap_v_peak.setText(f"{v_peak:.1f} V")
            self.res_xcap_r_max.setText(f"{r_max_m:.3f} MΩ")
            self.res_xcap_r_rec_e24.setText(f"{r_rec_m:.3f} MΩ")
            self.res_xcap_r_actual.setText(f"{r_actual_m:.3f} MΩ")
            self.res_xcap_r_single.setText(f"{r_single_m:.3f} MΩ")
            self.res_xcap_power_loss.setText(f"{p_loss_mw:.2f} mW")
            
            if t_actual <= t_limit:
                self.res_xcap_status.setText(f"PASS (放电时间 {t_actual:.2f} s < {t_limit:.1f} s)")
                self.res_xcap_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.res_xcap_status.setText(f"FAIL (放电时间 {t_actual:.2f} s > {t_limit:.1f} s)")
                self.res_xcap_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
            # Plot discharge curve
            self.plot_xcap_curve(v_peak, r_actual_ohms, cx_uf * 1e-6, t_limit, v_safe)
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数值无效: {str(e)}")

    def plot_xcap_curve(self, v_peak, r_ohms, c_farads, t_limit, v_safe):
        try:
            t_max = max(3.0, t_limit * 1.5)
            t_vals = np.linspace(0, t_max, 200)
            
            rc = r_ohms * c_farads
            v_vals = v_peak * np.exp(-t_vals / rc)
            
            plt.rcParams.update({
                'font.family': 'sans-serif',
                'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
            })
            fig, ax = plt.subplots(figsize=(5.5, 4), dpi=100)
            ax.plot(t_vals, v_vals, 'b-', linewidth=2, label="放电电压 v(t)")
            
            ax.axhline(y=v_safe, color='r', linestyle='--', alpha=0.7, label=f"安全阈值 {v_safe}V")
            ax.axvline(x=t_limit, color='g', linestyle='--', alpha=0.7, label=f"放电时限 {t_limit}s")
            
            # Calculate actual voltage at t_limit
            v_at_t_limit = v_peak * math.exp(-t_limit / rc)
            ax.plot(t_limit, v_at_t_limit, 'ro', markersize=8, label=f"实际电压 @{t_limit}s: {v_at_t_limit:.1f}V")
            
            ax.set_title("X电容放电电压衰减曲线", fontsize=11, fontweight='bold')
            ax.set_xlabel("时间 t (s)", fontsize=9)
            ax.set_ylabel("电压 V (V)", fontsize=9)
            ax.set_ylim(0, v_peak * 1.1)
            ax.grid(True, which="both", linestyle='--', alpha=0.5)
            ax.legend(loc='upper right', fontsize=8)
            
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.xcap_plot_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Plot error: {e}")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("输入保护器件选型原理")
        dialog.resize(800, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 8px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
        </style>
        
        <h1>输入保护设计指南：保险丝、NTC 与 X电容放电</h1>
        
        <h2>1. 保险丝 (Fuse) - I²t 匹配</h2>
        <p><b>原理：</b> 开机瞬间，电解电容相当于短路，产生巨大的浪涌电流。如果这个能量 ($I^2t$) 超过了保险丝的熔断值 (Melting $I^2t$)，保险丝就会被误熔断。</p>
        <ul>
            <li><b>计算：</b> 将浪涌简化 infant RC 充电模型，$\int i^2 dt = 0.5 \cdot I_{peak}^2 \cdot \tau$。</li>
            <li><b>选型：</b> Datasheet 中的 Melting $I^2t$ 必须大于计算值的 3~5 倍（脉冲折减系数），以防止老化疲劳。</li>
        </ul>

        <h2>2. 功率型 NTC - 能量与冷却</h2>
        <p>NTC 热敏电阻用于抑制开机浪涌。冷态时电阻大，限制电流；热态时电阻小，降低损耗。</p>
        
        <h3>A. 能量选型 (Energy Rating)</h3>
        <p>NTC 必须能承受母线电容充电的全部能量。如果选小了，NTC 还没来得及变热阻值下降，就被巨大的能量瞬间炸裂。</p>
        <div class="box">
            <b>公式：</b> $E = \frac{1}{2} C_{bulk} V_{peak}^2$<br>
            <b>建议：</b> NTC 的 Max Energy Rating 应至少为计算值的 1.5 倍。
        </div>

        <h3>B. 冷却时间 (Cooling Time)</h3>
        <p><b>痛点：</b> NTC 变热后阻值很低。如果此时断电并立刻重开机，NTC 还没冷却（阻值未恢复），就失去了浪涌抑制作用，可能导致跳闸或整流桥损坏。</p>
        <ul>
            <li><b>热时间常数 ($\tau$)：</b> NTC 冷却到温度差 63.2% 所需的时间。与体积有关，D-10 约为 40s，D-20 约为 100s。</li>
            <li><b>估算：</b> 本工具根据耗散系数 ($K_{diss}$) 估算 $\tau$。</li>
            <li><b>建议：</b> 电路设计应保证断电后至少等待 3$\tau$ 的时间再重启动，或使用继电器旁路 NTC 方案。</li>
        </ul>

        <h2>3. X电容安全放电与待机损耗</h2>
        <p><b>安规要求：</b> 根据 IEC 62368-1 / GB 4943，若可插拔电源设备的交流插头被拔出，电网断开后输入端 X 电容上的残留电荷必须安全释放，防止电击使用者。</p>
        <ul>
            <li><b>放电时间限制：</b> 拔出后 2 秒内（对某些高要求场合为 1 秒），输入端电压必须衰减至 60V（或原电压峰值的 37%）以下。当 $C_x \le 0.1\mu\text{F}$ 时通常豁免。</li>
            <li><b>理论放电模型：</b> $v(t) = V_{peak} \cdot e^{-t / (R \cdot C)}$，求解可得最大允许放电总电阻：
                <br><code>R_max = t_limit / (C_x * ln(V_peak / V_safe))</code>
            </li>
            <li><b>待机损耗：</b> 放电电阻始终跨接在交流输入 L-N 两端，产生待机空载损耗 $P = V_{ac}^2 / R$。为降低待机功耗，阻值应尽可能选大，但必须保证小于 $R_{max}$ 并留有 10%~20% 阻值余量。</li>
            <li><b>串联设计：</b> 由于高压应力以及爬电距离要求，实际电路中通常采用 2 个或更多个电阻串联（例如 2 颗 1206 或 0805 电阻串联）。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()