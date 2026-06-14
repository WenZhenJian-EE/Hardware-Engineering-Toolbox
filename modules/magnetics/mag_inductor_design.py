from modules.base_module import BaseModule
# mag_inductor_design.py
# (原 mag_inductor_bias.py 的增强版，包含 PCB 平面电感设计与边缘磁通修正)

import math
import matplotlib.pyplot as plt
from io import BytesIO

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class InductorDesignWindow(BaseModule):
    category = "1. 磁性元件与电源拓扑 (Magnetics & Topology)"
    display_name = "电感设计"
    description = "Buck / 气隙 / 空心线圈 / 偏置"
    window_id = "mag_inductor"

    def init_module_ui(self):
        
        # 定义常用磁粉芯的 DC Bias 拟合系数 (参考 Magnetics 目录)
        # Formula: %Perm = 1 / (a + b * H^c)
        # 注意: H 单位通常为 Oersteds (Oe)
        self.bias_materials = {
            "Kool Mµ 60u (Ref)":  {'a': 1.0, 'b': 0.0076, 'c': 1.85},
            "Kool Mµ 26u (Ref)":  {'a': 1.0, 'b': 0.0028, 'c': 1.95},
            "High Flux 60u (Ref)": {'a': 1.0, 'b': 0.0018, 'c': 2.15},
            "XFlux 60u (Ref)":     {'a': 1.0, 'b': 0.0006, 'c': 2.30},
            "Custom (自定义)":     {'a': 1.0, 'b': 0.01,   'c': 2.0}
        }
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('电感与磁性元件设计工坊 (Inductor Design Studio)')
        self.setGeometry(350, 350, 1050, 850) # 增加高度以容纳曲线图
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计指南：PCB电感 / 软饱和 / 边缘磁通")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(280)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_design = QWidget()
        self.tab_gap = QWidget()
        self.tab_air = QWidget() 
        self.tab_planar = QWidget() # New: PCB Planar Inductor
        self.tab_bias = QWidget() 

        self.init_design_ui(self.tab_design)
        self.init_gap_ui(self.tab_gap)
        self.init_air_ui(self.tab_air)
        self.init_planar_ui(self.tab_planar) # Initialize New UI
        self.init_bias_ui(self.tab_bias)

        self.tabs.addTab(self.tab_design, "Buck 电感设计 (CCM)")
        self.tabs.addTab(self.tab_gap, "磁芯气隙计算 (Air Gap & Fringing)")
        self.tabs.addTab(self.tab_air, "空心线圈计算 (Air Core)")
        self.tabs.addTab(self.tab_planar, "PCB 平面螺旋电感 (Planar)") # Add New Tab
        self.tabs.addTab(self.tab_bias, "直流偏置特性评估 (DC Bias)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: Inductor Design (Buck)
    # ==============================================================================
    def init_design_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 输入参数
        input_group = QGroupBox("设计参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        # Vin, Vout
        self.ind_vin = QLineEdit("12"); grid.addWidget(QLabel("输入电压 Vin [V]:"), 0, 0); grid.addWidget(self.ind_vin, 0, 1)
        self.ind_vout = QLineEdit("5"); grid.addWidget(QLabel("输出电压 Vout [V]:"), 0, 2); grid.addWidget(self.ind_vout, 0, 3)
        
        # Iout, Fsw
        self.ind_iout = QLineEdit("2"); grid.addWidget(QLabel("负载电流 Iout [A]:"), 1, 0); grid.addWidget(self.ind_iout, 1, 1)
        self.ind_fsw = QLineEdit("100"); grid.addWidget(QLabel("开关频率 fsw [kHz]:"), 1, 2); grid.addWidget(self.ind_fsw, 1, 3)
        
        # Ripple Ratio (K)
        self.ind_k = QLineEdit("0.3"); 
        self.ind_k.setToolTip("电流纹波系数 (r)。通常取 0.2 ~ 0.4。")
        grid.addWidget(QLabel("纹波系数 K (0.2~0.4):"), 2, 0); grid.addWidget(self.ind_k, 2, 1)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        # 按钮
        btn = QPushButton("计算电感参数")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_inductor)
        layout.addWidget(btn)
        
        # 2. 计算结果
        res_group = QGroupBox("计算结果")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(12)
        
        self.res_l_min = QLineEdit()
        self.res_i_ripple = QLineEdit()
        self.res_i_peak = QLineEdit()
        self.res_i_rms = QLineEdit()
        
        res_grid.addWidget(QLabel("最小电感量 L_min:"), 0, 0); res_grid.addWidget(self.res_l_min, 0, 1)
        l_form1 = QLabel(); l_form1.setPixmap(self.render_formula(r'L = \frac{V_{out}(V_{in}-V_{out})}{V_{in} \cdot f_{sw} \cdot \Delta I_L}'))
        res_grid.addWidget(l_form1, 0, 2)
        
        res_grid.addWidget(QLabel("纹波电流 ΔIL:"), 1, 0); res_grid.addWidget(self.res_i_ripple, 1, 1)
        res_grid.addWidget(QLabel("峰值电流 I_peak:"), 2, 0); res_grid.addWidget(self.res_i_peak, 2, 1)
        res_grid.addWidget(QLabel("有效值电流 I_rms:"), 3, 0); res_grid.addWidget(self.res_i_rms, 3, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_l_min, self.res_i_ripple, self.res_i_peak, self.res_i_rms]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        
        tab.setLayout(layout)

    def calc_inductor(self):
        try:
            vin = float(self.ind_vin.text())
            vout = float(self.ind_vout.text())
            iout = float(self.ind_iout.text())
            fsw = float(self.ind_fsw.text()) * 1000
            k = float(self.ind_k.text())
            
            if vin <= vout: raise ValueError("Vin 必须大于 Vout")
            
            # Buck Duty
            d = vout / vin
            
            # Ripple Current
            delta_i = k * iout
            
            # L min
            l_val = (vout * (vin - vout)) / (vin * fsw * delta_i)
            
            # Peak & RMS
            i_peak = iout + delta_i / 2
            i_rms = math.sqrt(iout**2 + (delta_i**2)/12)
            
            self.res_l_min.setText(f"{l_val*1e6:.2f} uH")
            self.res_i_ripple.setText(f"{delta_i:.2f} A")
            self.res_i_peak.setText(f"{i_peak:.2f} A")
            self.res_i_rms.setText(f"{i_rms:.2f} A")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    # ==============================================================================
    # Tab 2: Air Gap Calculator (UPDATED with Fringing Flux)
    # ==============================================================================
    def init_gap_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 磁芯参数
        grp_core = QGroupBox("1. 磁芯参数 (Core Params)")
        grid_core = QGridLayout()
        grid_core.setVerticalSpacing(12)
        
        self.gap_ae = QLineEdit("100") # Ae
        self.gap_ae.setToolTip("磁芯有效截面积 (Ae)。\n查磁芯 Datasheet，例如 EE25 通常约为 40mm²。")
        grid_core.addWidget(QLabel("有效截面积 Ae [mm²]:"), 0, 0); grid_core.addWidget(self.gap_ae, 0, 1)
        
        self.gap_n = QLineEdit("50") # Turns
        self.gap_n.setToolTip("绕组匝数 (N)。")
        grid_core.addWidget(QLabel("匝数 N [Ts]:"), 0, 2); grid_core.addWidget(self.gap_n, 0, 3)

        # New: Window Height for Fringing Flux
        self.gap_window_h = QLineEdit("15")
        self.gap_window_h.setToolTip("磁芯窗口高度/绕组宽度 G (mm)。\n用于计算 Cooper 边缘磁通效应。\nEE磁芯通常是Bobbin的绕线宽度。")
        grid_core.addWidget(QLabel("窗口高度 G [mm]:"), 1, 0); grid_core.addWidget(self.gap_window_h, 1, 1)
        grid_core.addWidget(QLabel("(用于边缘磁通校正)"), 1, 2)

        # New: Path Length le & Permeability ur
        self.gap_le = QLineEdit("50")
        self.gap_le.setToolTip("磁路长度 le (mm)。查规格书，默认 50mm。")
        grid_core.addWidget(QLabel("磁路长度 le [mm]:"), 2, 0); grid_core.addWidget(self.gap_le, 2, 1)

        self.gap_ur = QLineEdit("2000")
        self.gap_ur.setToolTip("磁芯相对磁导率 ur。查材质手册，PC40通常约为 2000-2300。")
        grid_core.addWidget(QLabel("相对磁导率 ur:"), 2, 2); grid_core.addWidget(self.gap_ur, 2, 3)
        
        grp_core.setLayout(grid_core)
        layout.addWidget(grp_core)
        
        # 2. 计算模式
        grp_calc = QGroupBox("2. 气隙计算目标")
        grid_calc = QGridLayout()
        
        self.gap_mode = QComboBox()
        self.gap_mode.addItems(["已知电感量 L -> 求气隙 lg", "已知 AL 值 -> 求气隙 lg"])
        self.gap_mode.currentIndexChanged.connect(self.update_gap_ui)
        grid_calc.addWidget(QLabel("计算目标:"), 0, 0); grid_calc.addWidget(self.gap_mode, 0, 1)
        
        self.gap_val_label = QLabel("目标电感量 L [uH]:")
        self.gap_val = QLineEdit("100")
        grid_calc.addWidget(self.gap_val_label, 1, 0); grid_calc.addWidget(self.gap_val, 1, 1)
        
        btn = QPushButton("计算气隙 & 边缘磁通修正")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_gap)
        grid_calc.addWidget(btn, 2, 0, 1, 2)
        
        grp_calc.setLayout(grid_calc)
        layout.addWidget(grp_calc)
        
        # 3. 结果
        grp_res = QGroupBox("3. 计算结果与修正建议")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        
        self.res_lg = QLineEdit()
        self.res_fringing_f = QLineEdit()
        self.res_lg_corr = QLineEdit()
        
        # Theoretical Result
        res_grid.addWidget(QLabel("理论气隙 (Theoretical lg):"), 0, 0)
        res_grid.addWidget(self.res_lg, 0, 1)
        
        self.gap_formula = QLabel()
        self.gap_formula.setPixmap(self.render_formula(r'l_g \approx \frac{\mu_0 N^2 A_e}{L} - \frac{l_e}{\mu_r}'))
        res_grid.addWidget(self.gap_formula, 0, 2)

        # Correction Factors
        res_grid.addWidget(QLabel("边缘磁通系数 (F):"), 1, 0)
        res_grid.addWidget(self.res_fringing_f, 1, 1)
        
        l_cooper = QLabel()
        l_cooper.setPixmap(self.render_formula(r'F = 1 + \frac{l_g}{\sqrt{A_e}} \ln\left(\frac{2G}{l_g}\right)'))
        res_grid.addWidget(l_cooper, 1, 2)

        res_grid.addWidget(QLabel("修正建议气隙 (Rec lg'):"), 2, 0)
        res_grid.addWidget(self.res_lg_corr, 2, 1)
        res_grid.addWidget(QLabel("说明: 实际电感量会因边缘效应变大 (L' = F*L)。\n为了保持目标电感量，需将气隙磨大到建议值。"), 2, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400; font-size: 14px;"
        
        self.res_lg.setReadOnly(True); self.res_lg.setStyleSheet(style)
        self.res_fringing_f.setReadOnly(True); self.res_fringing_f.setStyleSheet(style)
        self.res_lg_corr.setReadOnly(True); self.res_lg_corr.setStyleSheet(style_warn)
        
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def update_gap_ui(self):
        if self.gap_mode.currentIndex() == 0:
            self.gap_val_label.setText("目标电感量 L [uH]:")
            self.gap_val.setText("100")
            self.gap_formula.setPixmap(self.render_formula(r'l_g \approx \frac{\mu_0 N^2 A_e}{L} - \frac{l_e}{\mu_r}'))
        else:
            self.gap_val_label.setText("AL 值 [nH/N²]:")
            self.gap_val.setText("200")
            self.gap_formula.setPixmap(self.render_formula(r'l_g \approx \frac{\mu_0 A_e}{A_L} - \frac{l_e}{\mu_r}'))

    def calc_gap(self):
        try:
            ae_mm2 = float(self.gap_ae.text())
            ae = ae_mm2 * 1e-6 # mm2 -> m2
            n = float(self.gap_n.text())
            val = float(self.gap_val.text())
            g_mm = float(self.gap_window_h.text())
            le_mm = float(self.gap_le.text()) if self.gap_le.text() else 50.0
            le = le_mm * 1e-3 # mm -> m
            ur = float(self.gap_ur.text()) if self.gap_ur.text() else 2000.0
            
            mu0 = 4 * math.pi * 1e-7
            
            if self.gap_mode.currentIndex() == 0: # L -> lg
                l_target = val * 1e-6 # uH -> H
                if l_target <= 0: raise ValueError
                # L = mu0 * Ae * N^2 / (lg + le/ur)
                # lg = (mu0 * Ae * N^2) / L - le / ur
                lg = (mu0 * ae * n**2) / l_target - le / ur
            else: # AL -> lg
                al = val * 1e-9 # nH -> H
                if al <= 0: raise ValueError
                # AL = mu0 * Ae / (lg + le/ur)
                # lg = (mu0 * Ae) / AL - le / ur
                lg = (mu0 * ae) / al - le / ur
            
            lg_mm = lg * 1000.0
            if lg_mm < 0:
                lg_mm = 0.0
            self.res_lg.setText(f"{lg_mm:.3f} mm")

            # Fringing Flux Correction (Cooper Formula)
            # F = 1 + (lg / sqrt(Ae)) * ln(2G / lg)
            # Use units consistently (e.g. mm)
            if g_mm > 0 and lg_mm > 0 and ae_mm2 > 0:
                sqrt_ae = math.sqrt(ae_mm2)
                
                # Check for log domain
                term_log = (2 * g_mm) / lg_mm
                if term_log > 0:
                    fringing_f = 1.0 + (lg_mm / sqrt_ae) * math.log(term_log)
                else:
                    fringing_f = 1.0
                
                # Actual L with lg would be L_act = F * L_theoretical
                # To maintain L_target, we need to increase gap.
                # L approx 1/lg. So L_target = const / lg_new * F(lg_new)
                # Approximation: lg_new = lg_theoretical * F(lg_theoretical)
                lg_corr_mm = lg_mm * fringing_f
                
                self.res_fringing_f.setText(f"{fringing_f:.3f}")
                self.res_lg_corr.setText(f"{lg_corr_mm:.3f} mm")
            else:
                self.res_fringing_f.setText("-")
                self.res_lg_corr.setText("-")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 3: Air Core Inductor
    # ==============================================================================
    def init_air_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 线圈几何参数
        grp_geo = QGroupBox("1. 线圈几何参数 (Geometry)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.air_dia = QLineEdit("10"); 
        self.air_dia.setToolTip("线圈骨架直径或内径 (Inner/Form Diameter)。\n计算时会自动加上线径得到平均直径。")
        grid.addWidget(QLabel("骨架/内径 D_in [mm]:"), 0, 0); grid.addWidget(self.air_dia, 0, 1)
        
        self.air_turns = QLineEdit("10"); 
        grid.addWidget(QLabel("圈数 N [Turns]:"), 0, 2); grid.addWidget(self.air_turns, 0, 3)
        
        self.air_wire_d = QLineEdit("0.5"); 
        grid.addWidget(QLabel("线径 d_wire [mm]:"), 1, 0); grid.addWidget(self.air_wire_d, 1, 1)
        
        self.air_len = QLineEdit("5.0"); 
        self.air_len.setToolTip("线圈总长度 (Length)。\n如果是密绕，勾选下方选项自动计算。")
        grid.addWidget(QLabel("线圈长度 l [mm]:"), 1, 2); grid.addWidget(self.air_len, 1, 3)
        
        self.air_close_wound = QCheckBox("密绕 (Close Wound)")
        self.air_close_wound.setToolTip("勾选后，线圈长度将自动计算为：圈数 × 线径")
        self.air_close_wound.stateChanged.connect(self.on_close_wound_changed)
        grid.addWidget(self.air_close_wound, 2, 2, 1, 2)
        
        grp_geo.setLayout(grid)
        layout.addWidget(grp_geo)
        
        # 2. 计算按钮
        btn_layout = QHBoxLayout()
        
        btn_calc_l = QPushButton("计算电感量 L")
        btn_calc_l.setFixedHeight(45)
        btn_calc_l.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc_l.clicked.connect(self.calc_air_ind)
        
        btn_calc_n = QPushButton("反推圈数 N (已知目标 L)")
        btn_calc_n.setFixedHeight(45)
        btn_calc_n.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc_n.clicked.connect(self.calc_air_turns)
        
        btn_layout.addWidget(btn_calc_l)
        btn_layout.addWidget(btn_calc_n)
        layout.addLayout(btn_layout)
        
        # 3. 结果显示
        grp_res = QGroupBox("2. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.air_res_l = QLineEdit()
        self.air_res_n_req = QLineEdit()
        self.air_target_l = QLineEdit("1.0") # 用于反推的目标电感
        self.air_target_l.setPlaceholderText("目标 L [uH]")
        
        r_grid.addWidget(QLabel("计算电感量 L [uH]:"), 0, 0); r_grid.addWidget(self.air_res_l, 0, 1)
        
        l_f1 = QLabel()
        l_f1.setPixmap(self.render_formula(r'L (\mu H) \approx \frac{d^2 n^2}{18d + 40l} \quad (d, l \text{ in inches})'))
        r_grid.addWidget(l_f1, 0, 2)
        
        r_grid.addWidget(QLabel("反推圈数 (目标 L [uH]):"), 1, 0); 
        h_box = QHBoxLayout(); h_box.setContentsMargins(0,0,0,0)
        h_box.addWidget(self.air_target_l); h_box.addWidget(self.air_res_n_req)
        w_box = QWidget(); w_box.setLayout(h_box)
        r_grid.addWidget(w_box, 1, 1)
        r_grid.addWidget(QLabel("基于 Wheeler 公式近似反推"), 1, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        self.air_res_l.setReadOnly(True); self.air_res_l.setStyleSheet(style)
        self.air_res_n_req.setReadOnly(True); self.air_res_n_req.setStyleSheet(style)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        tip = QLabel("说明：使用 Wheeler 公式计算 (单层空心线圈)。\n公式中的直径 d 为线圈平均直径 (骨架直径 + 线径)。\n精度：当长径比 (l/d) > 0.4 时精度较高。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic; margin-top: 10px;")
        layout.addWidget(tip)
        
        layout.addStretch()
        tab.setLayout(layout)

    def on_close_wound_changed(self, state):
        if state == Qt.Checked:
            self.air_len.setReadOnly(True)
            self.air_len.setStyleSheet("background-color: #f0f0f0;")
            self.update_air_len()
        else:
            self.air_len.setReadOnly(False)
            self.air_len.setStyleSheet("")

    def update_air_len(self):
        try:
            n = float(self.air_turns.text())
            d_wire = float(self.air_wire_d.text())
            # 考虑绝缘层厚度，通常增加 5%~10%，或者简单相乘
            # 这里简单相乘
            length = n * d_wire
            self.air_len.setText(f"{length:.2f}")
        except: pass

    def calc_air_ind(self):
        try:
            if self.air_close_wound.isChecked():
                self.update_air_len()
                
            d_form = float(self.air_dia.text())
            n = float(self.air_turns.text())
            d_wire = float(self.air_wire_d.text())
            length = float(self.air_len.text())
            
            if d_form <= 0 or length <= 0: raise ValueError
            
            # Wheeler Formula uses Inches
            # L (uH) = (d^2 * n^2) / (18*d + 40*l)
            # d is mean diameter in inches
            # l is length in inches
            
            d_mean_mm = d_form + d_wire
            d_in = d_mean_mm / 25.4
            l_in = length / 25.4
            
            if 18*d_in + 40*l_in == 0: return
            
            l_uh = (d_in**2 * n**2) / (18*d_in + 40*l_in)
            
            self.air_res_l.setText(f"{l_uh:.3f} uH")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def calc_air_turns(self):
        try:
            target_l = float(self.air_target_l.text())
            d_form = float(self.air_dia.text())
            d_wire = float(self.air_wire_d.text())
            
            d_mean_mm = d_form + d_wire
            d_in = d_mean_mm / 25.4
            
            if self.air_close_wound.isChecked():
                # l_in = n * d_wire_in
                d_wire_in = d_wire / 25.4
                # L = (d^2 * n^2) / (18d + 40 * n * dw)
                # Quadratic formula Ax^2 + Bx + C = 0 for n
                a = d_in**2
                b = -40 * d_wire_in * target_l
                c = -18 * d_in * target_l
                
                delta = b**2 - 4*a*c
                if delta < 0: 
                    self.air_res_n_req.setText("无法求解")
                    return
                n1 = (-b + math.sqrt(delta)) / (2*a)
                
                self.air_res_n_req.setText(f"{n1:.1f} Turns")
                self.air_turns.setText(f"{n1:.1f}")
                self.update_air_len()
                
            else:
                # Fixed length assumption
                length = float(self.air_len.text())
                l_in = length / 25.4
                term = target_l * (18*d_in + 40*l_in) / (d_in**2)
                if term < 0: return
                n = math.sqrt(term)
                self.air_res_n_req.setText(f"{n:.1f} Turns")
                self.air_turns.setText(f"{n:.1f}")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的目标电感值")

    # ==============================================================================
    # Tab 4: PCB Planar Inductor (NEW Feature)
    # ==============================================================================
    def init_planar_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("基于电流片近似法 (Current Sheet Approximation) 计算 PCB 平面螺旋电感。\n适用于 NFC、无线充电、高频滤波等场合。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)

        # 1. 几何参数
        grp_geo = QGroupBox("1. 螺旋线圈几何参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.planar_shape = QComboBox()
        self.planar_shape.addItems(["正方形 (Square)", "六边形 (Hexagonal)", "八边形 (Octagonal)", "圆形 (Circular)"])
        grid.addWidget(QLabel("线圈形状:"), 0, 0); grid.addWidget(self.planar_shape, 0, 1)
        
        self.planar_n = QLineEdit("5"); grid.addWidget(QLabel("圈数 N:"), 0, 2); grid.addWidget(self.planar_n, 0, 3)
        
        self.planar_w = QLineEdit("0.5"); self.planar_w.setToolTip("线宽 Trace Width")
        grid.addWidget(QLabel("线宽 w [mm]:"), 1, 0); grid.addWidget(self.planar_w, 1, 1)
        
        self.planar_s = QLineEdit("0.2"); self.planar_s.setToolTip("线间距 Spacing")
        grid.addWidget(QLabel("线距 s [mm]:"), 1, 2); grid.addWidget(self.planar_s, 1, 3)
        
        self.planar_din = QLineEdit("10"); self.planar_din.setToolTip("内径 (Inner Diameter)。指最内圈的空洞直径。")
        grid.addWidget(QLabel("内径 Din [mm]:"), 2, 0); grid.addWidget(self.planar_din, 2, 1)
        
        self.planar_t = QLineEdit("0.035"); self.planar_t.setToolTip("铜厚 (1oz = 0.035mm)")
        grid.addWidget(QLabel("铜厚 t [mm]:"), 2, 2); grid.addWidget(self.planar_t, 2, 3)
        
        grp_geo.setLayout(grid)
        layout.addWidget(grp_geo)
        
        # 计算按钮
        btn = QPushButton("计算电感量 L & 直流电阻 DCR")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_planar)
        layout.addWidget(btn)
        
        # 2. 结果
        grp_res = QGroupBox("2. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_planar_l = QLineEdit()
        self.res_planar_dcr = QLineEdit()
        self.res_planar_dout = QLineEdit() # 外径
        
        r_grid.addWidget(QLabel("电感量 L [uH]:"), 0, 0); r_grid.addWidget(self.res_planar_l, 0, 1)
        
        # 公式
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'L \approx \frac{\mu_0 n^2 d_{avg} c_1}{2} [\ln(\frac{c_2}{\rho}) + c_3 \rho + c_4 \rho^2]'))
        r_grid.addWidget(l_form, 0, 2, 2, 1)
        
        r_grid.addWidget(QLabel("直流电阻 DCR [mΩ]:"), 1, 0); r_grid.addWidget(self.res_planar_dcr, 1, 1)
        r_grid.addWidget(QLabel("计算外径 Dout [mm]:"), 2, 0); r_grid.addWidget(self.res_planar_dout, 2, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.res_planar_l, self.res_planar_dcr, self.res_planar_dout]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_planar(self):
        try:
            n = float(self.planar_n.text())
            w = float(self.planar_w.text()) * 1e-3
            s = float(self.planar_s.text()) * 1e-3
            din = float(self.planar_din.text()) * 1e-3
            t_cu = float(self.planar_t.text()) * 1e-3
            
            if n <= 0 or w <= 0 or din <= 0: raise ValueError
            
            # Coefficients [c1, c2, c3, c4]
            coeffs = {
                0: [1.27, 2.07, 0.18, 0.13], # Square
                1: [1.09, 2.23, 0.17, 0.19], # Hexagonal
                2: [1.07, 2.29, 0.19, 0.19], # Octagonal
                3: [1.00, 2.46, 0.20, 0.20]  # Circular
            }
            c = coeffs[self.planar_shape.currentIndex()]
            
            # Dimensions
            # Total width of winding (one side) = N*w + (N-1)*s
            winding_width = n * w + (n - 1) * s
            dout = din + 2 * winding_width
            
            d_avg = (dout + din) / 2.0
            fill_ratio = (dout - din) / (dout + din)
            
            # Inductance Calculation (Current Sheet Approx)
            mu0 = 4 * math.pi * 1e-7
            term1 = math.log(c[1] / fill_ratio)
            term2 = c[2] * fill_ratio
            term3 = c[3] * (fill_ratio ** 2)
            
            l_val = (mu0 * n**2 * d_avg * c[0]) / 2 * (term1 + term2 + term3)
            
            # DCR Calculation
            # Approx Length: N * Perimeter_avg
            # Perimeter factors relative to d_avg (diameter or side):
            # Square: 4 * d_avg (d is side)
            # Circle: pi * d_avg
            # Hex: 3.46 * d_avg (approx, 2*sqrt(3))
            # Oct: 3.31 * d_avg (approx, 8/(1+sqrt(2)))
            peri_factors = [4.0, 3.46, 3.31, math.pi]
            kp = peri_factors[self.planar_shape.currentIndex()]
            
            total_len = n * kp * d_avg
            
            rho = 1.72e-8 # Copper
            area = w * t_cu
            dcr = rho * total_len / area
            
            self.res_planar_l.setText(f"{l_val*1e6:.3f} uH")
            self.res_planar_dcr.setText(f"{dcr*1000:.1f} mΩ")
            self.res_planar_dout.setText(f"{dout*1000:.2f} mm")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 5: DC Bias Saturation Check
    # ==============================================================================
    def init_bias_ui(self, tab):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Left Panel: Inputs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setFixedWidth(400)
        
        # 1. 材质选择与系数
        grp_mat = QGroupBox("1. 磁粉芯材质拟合参数")
        grid_mat = QGridLayout()
        grid_mat.setVerticalSpacing(10)
        
        self.bias_mat_combo = QComboBox()
        self.bias_mat_combo.addItems(list(self.bias_materials.keys()))
        self.bias_mat_combo.currentTextChanged.connect(self.update_bias_coeffs)
        grid_mat.addWidget(QLabel("选择材质:"), 0, 0, 1, 2)
        grid_mat.addWidget(self.bias_mat_combo, 0, 2, 1, 2)
        
        self.bias_a = QLineEdit()
        self.bias_b = QLineEdit()
        self.bias_c = QLineEdit()
        
        grid_mat.addWidget(QLabel("系数 a:"), 1, 0); grid_mat.addWidget(self.bias_a, 1, 1)
        grid_mat.addWidget(QLabel("系数 b:"), 1, 2); grid_mat.addWidget(self.bias_b, 1, 3)
        grid_mat.addWidget(QLabel("系数 c:"), 2, 0); grid_mat.addWidget(self.bias_c, 2, 1)
        
        lbl_f = QLabel()
        lbl_f.setPixmap(self.render_formula(r'\% \mu = \frac{100}{a + b \cdot H^c} \quad (H \text{ in Oe})', target_height=40))
        grid_mat.addWidget(lbl_f, 3, 0, 1, 4)
        
        grp_mat.setLayout(grid_mat)
        left_layout.addWidget(grp_mat)
        
        # 2. 物理参数
        grp_phy = QGroupBox("2. 电感物理参数")
        grid_phy = QGridLayout()
        
        self.bias_l0 = QLineEdit("100"); grid_phy.addWidget(QLabel("初始电感 L0 [uH]:"), 0, 0); grid_phy.addWidget(self.bias_l0, 0, 1)
        self.bias_n  = QLineEdit("40");  grid_phy.addWidget(QLabel("匝数 N [Ts]:"), 0, 2); grid_phy.addWidget(self.bias_n, 0, 3)
        self.bias_le = QLineEdit("50");  grid_phy.addWidget(QLabel("磁路长度 le [mm]:"), 1, 0); grid_phy.addWidget(self.bias_le, 1, 1)
        # Note: le in mm, but formula H uses cm usually. We handle conversion.
        self.bias_le.setToolTip("磁芯的平均磁路长度 (Path Length)，单位 mm。例如 CS270060 约为 63.5mm。")
        
        grp_phy.setLayout(grid_phy)
        left_layout.addWidget(grp_phy)
        
        # 3. 分析范围
        grp_anl = QGroupBox("3. 分析范围")
        grid_anl = QGridLayout()
        self.bias_imax = QLineEdit("10"); grid_anl.addWidget(QLabel("最大分析电流 [A]:"), 0, 0); grid_anl.addWidget(self.bias_imax, 0, 1)
        self.bias_idesign = QLineEdit("5"); grid_anl.addWidget(QLabel("设计工作电流 [A]:"), 0, 2); grid_anl.addWidget(self.bias_idesign, 0, 3)
        
        btn_plot = QPushButton("生成 DC Bias 曲线")
        btn_plot.setFixedHeight(40)
        btn_plot.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        btn_plot.clicked.connect(self.plot_bias_curve)
        grid_anl.addWidget(btn_plot, 1, 0, 1, 4)
        
        grp_anl.setLayout(grid_anl)
        left_layout.addWidget(grp_anl)
        
        left_layout.addStretch()
        
        # Right Panel: Plot
        self.plot_label = QLabel()
        self.plot_label.setAlignment(Qt.AlignCenter)
        self.plot_label.setStyleSheet("border: 1px solid #bdc3c7; background-color: white;")
        self.plot_label.setMinimumSize(500, 400)
        
        layout.addWidget(left_widget)
        layout.addWidget(self.plot_label, stretch=1)
        
        tab.setLayout(layout)
        self.update_bias_coeffs() # Init with first material

    def update_bias_coeffs(self):
        name = self.bias_mat_combo.currentText()
        if name in self.bias_materials:
            p = self.bias_materials[name]
            self.bias_a.setText(str(p['a']))
            self.bias_b.setText(str(p['b']))
            self.bias_c.setText(str(p['c']))

    def plot_bias_curve(self):
        try:
            # Get Params
            a = float(self.bias_a.text())
            b = float(self.bias_b.text())
            c = float(self.bias_c.text())
            
            l0 = float(self.bias_l0.text())
            n = float(self.bias_n.text())
            le_mm = float(self.bias_le.text())
            imax = float(self.bias_imax.text())
            i_des = float(self.bias_idesign.text())
            
            if le_mm <= 0 or imax <= 0: return
            
            le_cm = le_mm / 10.0
            
            # Generate Data
            i_vals = []
            l_vals = []
            p_vals = []
            
            steps = 50
            for k in range(steps + 1):
                i = imax * k / steps
                # H = 0.4 * pi * N * I / le(cm)
                h_oe = (0.4 * math.pi * n * i) / le_cm
                
                # Perm % = 1 / (a + b * H^c)
                term = a + b * (h_oe ** c)
                perm_ratio = 1.0 / term
                
                l_curr = l0 * perm_ratio
                
                i_vals.append(i)
                l_vals.append(l_curr)
                p_vals.append(perm_ratio * 100) # %
                
            # Specific point calculation
            h_des = (0.4 * math.pi * n * i_des) / le_cm
            term_des = a + b * (h_des ** c)
            l_des = l0 / term_des
            p_des = (1.0 / term_des) * 100
            
            # Plotting
            plt.rcParams.update({'font.size': 10})
            fig, ax1 = plt.subplots(figsize=(6, 4.5), dpi=100)
            
            color = '#2980b9'
            ax1.set_xlabel('DC Current (A)')
            ax1.set_ylabel('Inductance (uH)', color=color, fontweight='bold')
            ax1.plot(i_vals, l_vals, color=color, linewidth=2, label='Inductance')
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.grid(True, which='both', linestyle='--', alpha=0.6)
            
            # Highlight Design Point
            ax1.plot([i_des], [l_des], 'ro')
            ax1.annotate(f'{l_des:.1f}uH\n({p_des:.0f}%)', xy=(i_des, l_des), xytext=(i_des, l_des + l0*0.1),
                         arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6),
                         ha='center', fontsize=9, color='#c0392b', fontweight='bold')
            
            # Secondary Axis for % Permeability
            ax2 = ax1.twinx()  
            color2 = '#27ae60'
            ax2.set_ylabel('% Initial Permeability', color=color2)
            ax2.plot(i_vals, p_vals, color=color2, linestyle=':', alpha=0.6)
            ax2.tick_params(axis='y', labelcolor=color2)
            ax2.set_ylim(0, 110)
            
            plt.title(f'DC Bias Characteristics (Soft Saturation)\nL @ {i_des}A = {l_des:.2f} uH', fontsize=11, fontweight='bold')
            fig.tight_layout()
            
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.plot_label.setPixmap(pixmap)
            
        except Exception as e:
            QMessageBox.warning(self, "计算错误", f"发生错误: {str(e)}\n请检查输入数值是否合法。")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("电感设计与软饱和指南")
        dialog.resize(750, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = """
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            .warn { color: #c0392b; font-weight: bold; }
        </style>
        
        <h1>电感设计指南</h1>
        
        <h2>1. PCB 平面电感 (Planar Inductor)</h2>
        <p><b>原理：</b> 利用 PCB 走线构成螺旋线圈。优点是高度低、一致性好；缺点是感量有限、占板面积大。</p>
        <p><b>计算方法 (Current Sheet Approx)：</b></p>
        <p><code>L = 0.5 * μ0 * n² * d_avg * c1 * [ln(c2/ρ) + c3*ρ + c4*ρ²]</code></p>
        <ul>
            <li>适用于方形、圆形、八边形等形状。</li>
            <li>ρ (Fill Ratio) = (Dout - Din) / (Dout + Din)。代表线圈的充满程度。</li>
            <li><b>注意：</b> 这种电感通常没有磁芯，漏磁严重。如需增大感量，可上下贴铁氧体薄片。</li>
        </ul>

        <h2>2. Buck 电感设计原理</h2>
        <p>电感的主要作用是储能和平滑电流。核心公式基于法拉第定律：<code>V = L * di/dt</code>。</p>
        <ul>
            <li><b>L_min:</b> 保证电流连续模式 (CCM) 或满足特定的纹波要求。</li>
            <li><b>纹波系数 K:</b> 定义为 ΔI / I_out。通常取 0.2 ~ 0.4。取值过小会导致电感体积巨大；取值过大会导致磁芯损耗增加和输出电容压力大。</li>
        </ul>

        <h2>3. 为什么需要气隙 (Air Gap)？</h2>
        <p>对于铁氧体 (Ferrite) 等高导磁率磁芯，其饱和磁通密度 (Bsat) 虽然高，但磁导率太高导致极其容易饱和 (只需很小的 H 就会达到 Bsat)。</p>
        <p><b>气隙的作用：</b> 像在磁路中串联一个大电阻，极大增加了磁阻，从而降低了等效磁导率。这使得电感能够承受更大的直流偏置电流而不饱和。</p>

        <h2>4. 气隙计算与修正</h2>
        <p>基本公式：<code>lg = (μ0 * Ae * N²) / L</code></p>
        <p><b>边缘磁通 (Fringing Flux)：</b> 磁力线在气隙处会向外“鼓出”，导致实际有效的 Ae 变大。这使得<b>实际电感量比计算值大</b>。</p>
        <ul>
            <li>工程经验：计算出 lg 后，通常需要<b>增加 10% ~ 20%</b> 的磨损深度来抵消边缘效应。</li>
            <li>或者，在绕制完成后，通过实测微调气隙（垫纸片或研磨）。</li>
        </ul>
        
        <h2>5. 直流偏置 (DC Bias) 与软饱和</h2>
        <p>对于<b>磁粉芯 (Powder Cores)</b> 如铁硅铝 (Kool Mu)、铁粉芯、High Flux 等，它们没有像铁氧体那样明显的“硬饱和”点（气隙分散在材料内部）。</p>
        <p><b>特性：</b> 随着直流电流 (DC Current) 增加，磁场强度 H 增大，磁导率 μ 会逐渐下降。这就是<b>软饱和 (Soft Saturation)</b>。</p>
        <ul>
            <li><b>危险：</b> 如果设计时只看初始电感 L0，而忽略了满载时的跌落，可能导致满载时电感量仅剩 50% 甚至更低。</li>
            <li><b>后果：</b> 电感量大幅下降 -> 纹波电流剧增 -> 磁芯损耗飙升/MOS管过热/输出纹波电压超标。</li>
            <li><b>设计建议：</b> 必须校核满载电流下的电感量，确保其不低于设计最小值 (L_min)。</li>
        </ul>

        <h2>6. 空心线圈 (Air Core)</h2>
        <p><b>应用场景：</b> 射频电路 (RF)、高频滤波、音箱分频器、Class-D 功放输出滤波等。</p>
        <p><b>优点：</b></p>
        <ul>
            <li><b>绝对线性：</b> 没有磁芯，永远不会饱和 (Saturation Free)。</li>
            <li><b>无磁滞损耗：</b> 没有铁损 (Core Loss)，适合超高频。</li>
        </ul>
        <p><b>缺点与注意事项：</b></p>
        <ul>
            <li><b>体积大：</b> 获得相同电感量，需要的匝数比有磁芯的多得多。</li>
            <li><b>电磁干扰 (EMI)：</b> 磁力线不被束缚，向周围辐射严重。需注意与其他敏感电路的距离或屏蔽。</li>
            <li><b>Q 值：</b> 受趋肤效应 (Skin Effect) 和邻近效应影响。高频下建议使用多股绞线 (Litz Wire) 或镀银线。</li>
        </ul>
        <p><b>计算公式 (Wheeler)：</b></p>
        <div style="background-color: #e8f6f3; padding: 10px; border-radius: 5px; margin: 5px 0;">
            <p style="font-size: 16px; font-weight: bold; color: #2c3e50; margin: 0;">L (µH) = (d² · n²) / (18d + 40l)</p>
            <p style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">(注: d, l 单位为英寸 inches)</p>
        </div>
        <p><i>提示：长径比 (l/d) > 0.4 时公式精度较高。</i></p>
        
        <h2>7. 边缘磁通修正 (Fringing Flux Factor)</h2>
        <p>对于大气息电感（如 PFC、LLC 谐振电感），气隙附近的磁力线会向外扩散，导致有效截面积 $A_e$ 增加，电感量比理论计算值大。</p>
        <p><b>Cooper 公式修正系数 $F$:</b></p>
        <p>$$F = 1 + \\frac{l_g}{\\sqrt{A_e}} \\ln\\left(\\frac{2G}{l_g}\\right)$$</p>
        <ul>
            <li>$G$: 窗口高度 (Window Height)，通常对应骨架的绕线宽度。</li>
            <li>$l_g$: 气隙长度。</li>
            <li>$A_e$: 磁芯截面积。</li>
        </ul>
        <p><b>修正逻辑：</b> 实际电感量 $L_{real} = F \\cdot L_{calc}$。为了抵消这个增量，设计气隙需要磨得比理论值更大（$l_{g}' \\approx l_g \\cdot F$）。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()