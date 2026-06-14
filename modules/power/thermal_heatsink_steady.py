from modules.base_module import BaseModule
# thermal_heatsink_steady.py

import matplotlib.pyplot as plt
from io import BytesIO
import math

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class HeatsinkCalculatorWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "散热器热设计"
    description = "热阻 / 强迫风冷 / 密封 / 瞬态 / 风量"
    window_id = "thermal_heatsink"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('散热器选型与热设计工具 (Heatsink & Enclosure)')
        self.setGeometry(350, 350, 950, 800) 

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("热设计教程 (含风量计算)")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # Tab 容器
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_steady = QWidget()
        self.tab_air = QWidget() 
        self.tab_enclosure = QWidget() 
        self.tab_transient = QWidget()
        self.tab_sys_air = QWidget() # New: System Airflow

        self.init_steady_ui(self.tab_steady)
        self.init_air_ui(self.tab_air)
        self.init_enclosure_ui(self.tab_enclosure)
        self.init_transient_ui(self.tab_transient)
        self.init_sys_airflow_ui(self.tab_sys_air) # Init New Tab

        self.tabs.addTab(self.tab_steady, "1. 散热器热阻 (Heatsink Rth)")
        self.tabs.addTab(self.tab_air, "2. 强迫风冷 (Forced Air)")
        self.tabs.addTab(self.tab_enclosure, "3. 密封外壳温升 (Sealed Enclosure)")
        self.tabs.addTab(self.tab_transient, "4. 瞬态热容与过载 (Transient)")
        self.tabs.addTab(self.tab_sys_air, "5. 系统风量设计 (System Airflow)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 稳态热阻计算 (Existing)
    # ==============================================================================
    def init_steady_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入部分
        input_group = QGroupBox("1. 输入设计参数")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        self.p_diss_input = QLineEdit("15")
        self.t_j_max_input = QLineEdit("150")
        self.t_amb_input = QLineEdit("50")
        self.r_jc_input = QLineEdit("1.0")
        self.r_cs_input = QLineEdit("0.5")

        inputs = [
            ("器件功耗 (P_diss) [W]:", self.p_diss_input),
            ("最高结温 (T_j_max) [°C]:", self.t_j_max_input),
            ("最高环境温度 (T_amb) [°C]:", self.t_amb_input),
            ("结-壳热阻 (R_jc) [°C/W]:", self.r_jc_input),
            ("壳-散热器热阻 (R_cs) [°C/W]:", self.r_cs_input)
        ]
        
        for i, (label, widget) in enumerate(inputs):
            input_layout.addWidget(QLabel(label), i, 0)
            input_layout.addWidget(widget, i, 1)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 按钮区
        btn_layout = QHBoxLayout()
        self.calculate_button = QPushButton("计算所需散热器热阻")
        self.calculate_button.setCursor(Qt.PointingHandCursor)
        self.calculate_button.setFixedHeight(45)
        self.calculate_button.setFont(QFont('Arial', 11, QFont.Bold))
        self.calculate_button.setStyleSheet("background-color: #3498db; color: white;")
        self.calculate_button.clicked.connect(self.on_calculate_steady)
        
        btn_layout.addWidget(self.calculate_button)
        layout.addLayout(btn_layout)

        # Output
        output_group = QGroupBox("2. 计算结果")
        output_main_layout = QHBoxLayout()
        output_main_layout.setSpacing(20)
        
        results_layout = QGridLayout()
        results_layout.setVerticalSpacing(15)
        
        self.r_sa_max_output = QLineEdit()
        self.t_case_output = QLineEdit()
        
        result_style = """
            QLineEdit { 
                background-color: #e8f8f5; 
                color: #27ae60; 
                font-weight: bold; 
                font-size: 16px;
                border: 1px solid #2ecc71;
            }
        """
        for w in [self.r_sa_max_output, self.t_case_output]:
            w.setReadOnly(True)
            w.setStyleSheet(result_style)
            w.setFixedHeight(40)

        results_layout.addWidget(QLabel("所需散热器最大热阻 (R_sa_max):"), 0, 0)
        results_layout.addWidget(self.r_sa_max_output, 0, 1)
        results_layout.addWidget(QLabel("估算器件外壳温度 (T_case):"), 1, 0)
        results_layout.addWidget(self.t_case_output, 1, 1)
        
        formulas_layout = QVBoxLayout()
        formulas_layout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        formulas_layout.setSpacing(20)
        
        l_form1 = QLabel(); l_form1.setPixmap(self.render_formula(r'R_{sa\_max} = \frac{T_{j\_max} - T_{amb}}{P_{diss}} - R_{jc} - R_{cs}'))
        l_form2 = QLabel(); l_form2.setPixmap(self.render_formula(r'T_{case} = T_{amb} + P_{diss} \cdot (R_{cs} + R_{sa})'))
        
        formulas_layout.addWidget(l_form1)
        formulas_layout.addWidget(l_form2)
        
        output_main_layout.addLayout(results_layout, 2)
        line = QFrame(); line.setFrameShape(QFrame.VLine); line.setFrameShadow(QFrame.Sunken); line.setStyleSheet("color: #e0e0e0;")
        output_main_layout.addWidget(line)
        output_main_layout.addLayout(formulas_layout, 3)
        
        output_group.setLayout(output_main_layout)
        layout.addWidget(output_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.on_calculate_steady()

    def on_calculate_steady(self):
        try:
            p_diss = float(self.p_diss_input.text())
            t_j_max = float(self.t_j_max_input.text())
            t_amb = float(self.t_amb_input.text())
            r_jc = float(self.r_jc_input.text())
            r_cs = float(self.r_cs_input.text())

            if p_diss <= 0: raise ValueError("器件功耗必须大于0。")
            if t_j_max <= t_amb: raise ValueError("最高结温必须高于环境温度。")

            r_sa_max = (t_j_max - t_amb) / p_diss - r_jc - r_cs
            
            if r_sa_max > 0:
                self.r_sa_max_output.setText(f"{r_sa_max:.3f} °C/W")
                t_case = t_amb + p_diss * (r_cs + r_sa_max)
                self.t_case_output.setText(f"{t_case:.2f} °C")
            else:
                self.r_sa_max_output.setText("无需/无法散热")
                self.r_sa_max_output.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold;")
                self.t_case_output.clear()
                
                t_case_no_heatsink = t_amb + p_diss * r_jc
                if t_case_no_heatsink < t_j_max:
                     QMessageBox.information(self, '提示', f'无需散热器。\n即使不加散热器，结温 (约 {t_case_no_heatsink:.1f}°C) 也低于限制。')
                else:
                     QMessageBox.warning(self, '严重警告', f'计算结果为负值！\n不加散热器时结温将超限。这意味着 R_jc 过大或功耗过高，即使理想散热也无法满足要求。')

        except Exception as e:
            QMessageBox.warning(self, '输入错误', f'请输入有效的数值！\n详细信息: {e}')
        except Exception as e:
            QMessageBox.critical(self, '发生错误', f'程序出现未知错误: {e}')

    # ==============================================================================
    # Tab 2: 强迫风冷与流速 (Existing)
    # ==============================================================================
    def init_air_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. CFM to Velocity Converter
        grp_conv = QGroupBox("1. 风速换算 (CFM -> m/s)")
        grid_conv = QGridLayout()
        grid_conv.setVerticalSpacing(12)
        
        self.fan_cfm = QLineEdit("10"); self.fan_cfm.setToolTip("风扇流量 (Cubic Feet per Minute)")
        grid_conv.addWidget(QLabel("风扇流量 [CFM]:"), 0, 0); grid_conv.addWidget(self.fan_cfm, 0, 1)
        
        self.duct_w = QLineEdit("50"); self.duct_w.setPlaceholderText("宽度"); 
        self.duct_h = QLineEdit("30"); self.duct_h.setPlaceholderText("高度")
        hbox_dim = QHBoxLayout(); hbox_dim.addWidget(self.duct_w); hbox_dim.addWidget(QLabel("x")); hbox_dim.addWidget(self.duct_h)
        grid_conv.addWidget(QLabel("风道截面 WxH [mm]:"), 0, 2); grid_conv.addLayout(hbox_dim, 0, 3)
        
        btn_calc_vel = QPushButton("计算平均风速")
        btn_calc_vel.setStyleSheet("background-color: #3498db; color: white;")
        btn_calc_vel.clicked.connect(self.calc_velocity)
        grid_conv.addWidget(btn_calc_vel, 1, 0, 1, 4)
        
        self.res_lfm = QLineEdit(); self.res_lfm.setReadOnly(True)
        self.res_ms = QLineEdit(); self.res_ms.setReadOnly(True)
        self.res_ms.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
        
        grid_conv.addWidget(QLabel("流速 [LFM]:"), 2, 0); grid_conv.addWidget(self.res_lfm, 2, 1)
        grid_conv.addWidget(QLabel("流速 [m/s]:"), 2, 2); grid_conv.addWidget(self.res_ms, 2, 3)
        
        grp_conv.setLayout(grid_conv)
        layout.addWidget(grp_conv)
        
        # 2. Forced Air Rth Estimation
        grp_rth = QGroupBox("2. 强迫风冷热阻估算 (Forced Air Rth)")
        grid_rth = QGridLayout()
        grid_rth.setVerticalSpacing(12)
        
        self.rth_nat = QLineEdit("5.0"); self.rth_nat.setToolTip("散热器在自然对流下的热阻 (Datasheet值)")
        grid_rth.addWidget(QLabel("自然对流热阻 R_nat [°C/W]:"), 0, 0); grid_rth.addWidget(self.rth_nat, 0, 1)
        
        self.air_vel = QLineEdit("2.0"); self.air_vel.setToolTip("流过散热器的风速")
        grid_rth.addWidget(QLabel("表面风速 V_air [m/s]:"), 0, 2); grid_rth.addWidget(self.air_vel, 0, 3)
        
        btn_calc_rth = QPushButton("估算风冷热阻")
        btn_calc_rth.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc_rth.clicked.connect(self.calc_forced_rth)
        grid_rth.addWidget(btn_calc_rth, 1, 0, 1, 4)
        
        self.res_rth_forced = QLineEdit(); 
        self.res_rth_forced.setReadOnly(True)
        self.res_rth_forced.setStyleSheet("background-color: #fdf2e9; font-weight: bold; color: #d35400; font-size: 16px;")
        
        grid_rth.addWidget(QLabel("风冷热阻 R_forced [°C/W]:"), 2, 0); grid_rth.addWidget(self.res_rth_forced, 2, 1)
        
        l_formula = QLabel()
        l_formula.setPixmap(self.render_formula(r'R_{th,forced} \approx R_{th,nat} \times \frac{1}{\sqrt{1 + V_{m/s}}}'))
        grid_rth.addWidget(l_formula, 2, 2, 1, 2)
        
        grp_rth.setLayout(grid_rth)
        layout.addWidget(grp_rth)
        
        info = QLabel("注：风阻换算公式仅为工程估算，实际散热效果受翅片形状、风压、湍流等影响，建议留 20%~30% 余量。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_velocity(self):
        try:
            cfm = float(self.fan_cfm.text())
            w_mm = float(self.duct_w.text())
            h_mm = float(self.duct_h.text())
            
            if w_mm <= 0 or h_mm <= 0: return
            
            # Area in ft^2
            # 1 ft = 304.8 mm
            area_m2 = (w_mm * h_mm) / 1e6
            area_ft2 = area_m2 * 10.7639
            
            lfm = cfm / area_ft2
            ms = lfm * 0.00508
            
            self.res_lfm.setText(f"{lfm:.1f}")
            self.res_ms.setText(f"{ms:.2f}")
            
            # Auto-fill next section
            self.air_vel.setText(f"{ms:.2f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def calc_forced_rth(self):
        try:
            r_nat = float(self.rth_nat.text())
            v_ms = float(self.air_vel.text())
            
            if r_nat <= 0: return
            if v_ms < 0: v_ms = 0
            
            # Empirical Formula: R_forced = R_nat / sqrt(1 + V)
            factor = math.sqrt(1.0 + v_ms)
            r_forced = r_nat / factor
            
            self.res_rth_forced.setText(f"{r_forced:.3f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 3: 密封外壳温升 (Existing)
    # ==============================================================================
    def init_enclosure_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：估算完全密封外壳 (无通风孔) 的内部温升。\n"
                      "基于经验公式：ΔT ≈ k * (P / Area)^0.8。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. 物理参数
        grp_in = QGroupBox("1. 外壳参数与功耗")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.enc_l = QLineEdit("100"); grid.addWidget(QLabel("长度 L [mm]:"), 0, 0); grid.addWidget(self.enc_l, 0, 1)
        self.enc_w = QLineEdit("50");  grid.addWidget(QLabel("宽度 W [mm]:"), 0, 2); grid.addWidget(self.enc_w, 0, 3)
        self.enc_h = QLineEdit("30");  grid.addWidget(QLabel("高度 H [mm]:"), 1, 0); grid.addWidget(self.enc_h, 1, 1)
        
        self.enc_p = QLineEdit("2.0"); grid.addWidget(QLabel("内部总功耗 P [W]:"), 1, 2); grid.addWidget(self.enc_p, 1, 3)
        
        self.enc_mat = QComboBox()
        self.enc_mat.addItem("塑料外壳 (k=450)", 450)
        self.enc_mat.addItem("金属外壳 - 喷漆/氧化 (k=300)", 300)
        self.enc_mat.addItem("金属外壳 - 光亮 (k=400)", 400)
        self.enc_mat.addItem("自定义系数", 0)
        self.enc_mat.currentIndexChanged.connect(self.on_enc_mat_changed)
        
        self.enc_k = QLineEdit("450")
        
        grid.addWidget(QLabel("外壳材质:"), 2, 0); grid.addWidget(self.enc_mat, 2, 1)
        grid.addWidget(QLabel("修正系数 k:"), 2, 2); grid.addWidget(self.enc_k, 2, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn_calc = QPushButton("计算内部温升")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_enclosure)
        layout.addWidget(btn_calc)
        
        # 2. 结果
        grp_res = QGroupBox("2. 估算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.enc_area = QLineEdit()
        self.enc_dt = QLineEdit()
        self.enc_t_int = QLineEdit()
        
        self.enc_t_amb = QLineEdit("25"); self.enc_t_amb.setPlaceholderText("环境温度")
        
        r_grid.addWidget(QLabel("有效表面积 Area:"), 0, 0); r_grid.addWidget(self.enc_area, 0, 1)
        r_grid.addWidget(QLabel("m² (不含底面则减半)"), 0, 2)
        
        r_grid.addWidget(QLabel("内部空气温升 ΔT_int:"), 1, 0); r_grid.addWidget(self.enc_dt, 1, 1)
        l_form = QLabel(); l_form.setPixmap(self.render_formula(r'\Delta T \approx k \cdot (P / Area)^{0.8}'))
        r_grid.addWidget(l_form, 1, 2)
        
        r_grid.addWidget(QLabel("环境温度 T_amb [°C]:"), 2, 0); r_grid.addWidget(self.enc_t_amb, 2, 1)
        r_grid.addWidget(QLabel("内部估算温度 T_internal:"), 3, 0); r_grid.addWidget(self.enc_t_int, 3, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400; font-size: 14px;"
        
        self.enc_area.setReadOnly(True); self.enc_area.setStyleSheet(style)
        self.enc_dt.setReadOnly(True); self.enc_dt.setStyleSheet(style_warn)
        self.enc_t_int.setReadOnly(True); self.enc_t_int.setStyleSheet(style_warn)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        tips = QLabel("提示：计算假设外壳所有面都参与散热。如果底部紧贴绝热表面，建议将计算出的面积减小（如取 80%~90%）。\n"
                      "此计算仅供评估“闷在盒子里”的空气温度，器件结温需在此基础上叠加 Rth_ja。")
        tips.setStyleSheet("color: #7f8c8d; font-style: italic;")
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        layout.addStretch()
        tab.setLayout(layout)

    def on_enc_mat_changed(self):
        data = self.enc_mat.currentData()
        if data != 0:
            self.enc_k.setText(str(data))

    def calc_enclosure(self):
        try:
            l = float(self.enc_l.text()) / 1000.0 # m
            w = float(self.enc_w.text()) / 1000.0
            h = float(self.enc_h.text()) / 1000.0
            p = float(self.enc_p.text())
            k = float(self.enc_k.text())
            t_amb = float(self.enc_t_amb.text())
            
            if l*w*h == 0: raise ValueError
            
            # Total Surface Area = 2(LW + LH + WH)
            area = 2 * (l*w + l*h + w*h)
            
            # Empirical Formula
            # dT = k * (P / A)^0.8
            # P/A is power density in W/m2
            p_density = p / area
            dt = k * (p_density ** 0.8)
            
            t_int = t_amb + dt
            
            self.enc_area.setText(f"{area:.4f}")
            self.enc_dt.setText(f"+ {dt:.1f} °C")
            self.enc_t_int.setText(f"{t_int:.1f} °C")
            
            if t_int > 85:
                self.enc_t_int.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold; font-size: 14px;")
            else:
                self.enc_t_int.setStyleSheet("background-color: #fff8e1; color: #d35400; font-weight: bold; font-size: 14px;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 4: 瞬态热容与过载 (Transient & Overload) - NEW
    # ==============================================================================
    def init_transient_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：估算短时过载冲击下的温升。利用散热器(金属)的热容来吸收能量。\n"
                      "假设条件：绝热模式 (Adiabatic)，即假设脉冲极短，热量来不及散发到环境，全部被金属吸收。结果为最恶劣情况估算。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 15px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. Inputs
        grp_in = QGroupBox("1. 瞬态冲击参数")
        g_in = QGridLayout()
        g_in.setVerticalSpacing(12)
        
        self.tr_mat = QComboBox()
        self.tr_mat.addItem("铝 (Aluminum) - c=900 J/kgK", 900)
        self.tr_mat.addItem("铜 (Copper) - c=385 J/kgK", 385)
        self.tr_mat.addItem("铁/钢 (Iron/Steel) - c=450 J/kgK", 450)
        self.tr_mat.currentIndexChanged.connect(self.on_tr_mat_changed)
        
        self.tr_c = QLineEdit("900"); 
        g_in.addWidget(QLabel("散热器材质:"), 0, 0); g_in.addWidget(self.tr_mat, 0, 1)
        g_in.addWidget(QLabel("比热容 c [J/kgK]:"), 0, 2); g_in.addWidget(self.tr_c, 0, 3)
        
        self.tr_mass = QLineEdit("200"); g_in.addWidget(QLabel("散热器重量 [g]:"), 1, 0); g_in.addWidget(self.tr_mass, 1, 1)
        self.tr_p = QLineEdit("500"); g_in.addWidget(QLabel("冲击功率 P_shock [W]:"), 1, 2); g_in.addWidget(self.tr_p, 1, 3)
        
        self.tr_time = QLineEdit("10"); g_in.addWidget(QLabel("持续时间 t [s]:"), 2, 0); g_in.addWidget(self.tr_time, 2, 1)
        self.tr_tamb = QLineEdit("25"); g_in.addWidget(QLabel("初始温度 T_start [°C]:"), 2, 2); g_in.addWidget(self.tr_tamb, 2, 3)
        
        grp_in.setLayout(g_in)
        layout.addWidget(grp_in)
        
        btn_calc = QPushButton("计算瞬态温升 (绝热模型)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_transient)
        layout.addWidget(btn_calc)
        
        # 2. Results
        grp_res = QGroupBox("2. 估算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.tr_res_energy = QLineEdit(); r_grid.addWidget(QLabel("注入能量 Energy [J]:"), 0, 0); r_grid.addWidget(self.tr_res_energy, 0, 1)
        self.tr_res_cth = QLineEdit(); r_grid.addWidget(QLabel("热容量 Cth [J/K]:"), 0, 2); r_grid.addWidget(self.tr_res_cth, 0, 3)
        
        self.tr_res_dt = QLineEdit(); 
        self.tr_res_dt.setStyleSheet("background-color: #fff8e1; font-weight: bold; color: #d35400; font-size: 14px;")
        r_grid.addWidget(QLabel("温升 ΔT [°C]:"), 1, 0); r_grid.addWidget(self.tr_res_dt, 1, 1)
        
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'\Delta T = \frac{E}{C_{th}} = \frac{P \cdot t}{c \cdot m}'))
        r_grid.addWidget(l_form, 1, 2, 1, 2)
        
        self.tr_res_final = QLineEdit()
        self.tr_res_final.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 16px;")
        r_grid.addWidget(QLabel("最终温度 T_end [°C]:"), 2, 0); r_grid.addWidget(self.tr_res_final, 2, 1)
        
        for w in [self.tr_res_energy, self.tr_res_cth, self.tr_res_dt, self.tr_res_final]:
            w.setReadOnly(True)

        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def on_tr_mat_changed(self):
        data = self.tr_mat.currentData()
        if data:
            self.tr_c.setText(str(data))

    def calc_transient(self):
        try:
            c = float(self.tr_c.text()) # J/kgK
            mass_g = float(self.tr_mass.text())
            mass_kg = mass_g / 1000.0
            p = float(self.tr_p.text())
            t = float(self.tr_time.text())
            t_start = float(self.tr_tamb.text())
            
            if mass_kg <= 0: raise ValueError
            
            # Energy E = P * t
            energy = p * t
            
            # Heat Capacity Cth = c * m
            c_th = c * mass_kg
            
            # Delta T = E / Cth
            dt = energy / c_th
            
            t_end = t_start + dt
            
            self.tr_res_energy.setText(f"{energy:.1f}")
            self.tr_res_cth.setText(f"{c_th:.1f}")
            self.tr_res_dt.setText(f"+ {dt:.1f}")
            self.tr_res_final.setText(f"{t_end:.1f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    # ==============================================================================
    # Tab 5: 系统风量设计 (System Airflow) - NEW
    # ==============================================================================
    def init_sys_airflow_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：估算整机系统所需的散热风量 (CFM)。\n"
                      "基于热平衡公式：Q = (C_const * P) / ΔT，并考虑高海拔空气密度修正。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. Inputs
        grp_in = QGroupBox("1. 系统热负荷与工况")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.af_p = QLineEdit("500"); grid.addWidget(QLabel("系统总热耗 P_loss [W]:"), 0, 0); grid.addWidget(self.af_p, 0, 1)
        self.af_dt = QLineEdit("15"); self.af_dt.setToolTip("进出风口允许温升 (T_exhaust - T_inlet)")
        grid.addWidget(QLabel("允许温升 ΔT [°C]:"), 0, 2); grid.addWidget(self.af_dt, 0, 3)
        
        self.af_alt = QComboBox(); 
        self.af_alt.addItems(["海平面 (0m)", "1000m", "2000m", "3000m", "4000m", "5000m"])
        self.af_alt.setEditable(True) # Allow custom input like "1500"
        self.af_alt.setToolTip("海拔越高，空气越稀薄，冷却能力越差，需要更大的风量。")
        grid.addWidget(QLabel("工作海拔 Altitude:"), 1, 0); grid.addWidget(self.af_alt, 1, 1)
        
        self.af_margin = QLineEdit("20"); self.af_margin.setToolTip("设计裕量，弥补风道漏风、风扇老化等因素")
        grid.addWidget(QLabel("安全裕量 Margin [%]:"), 1, 2); grid.addWidget(self.af_margin, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn_calc = QPushButton("计算所需风量 (Required Airflow)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_sys_airflow)
        layout.addWidget(btn_calc)
        
        # 2. Results
        grp_res = QGroupBox("2. 风量需求结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.af_res_cfm = QLineEdit()
        self.af_res_lfm = QLineEdit() # Convert to LFM if Area is known? No, just CMM
        self.af_res_cmm = QLineEdit()
        self.af_factor = QLineEdit()
        
        # CFM
        r_grid.addWidget(QLabel("所需最小风量 [CFM]:"), 0, 0); r_grid.addWidget(self.af_res_cfm, 0, 1)
        l_form = QLabel(); l_form.setPixmap(self.render_formula(r'CFM \approx \frac{3.16 \cdot P(W)}{\Delta T(^\circ C)} \times K_{alt}'))
        r_grid.addWidget(l_form, 0, 2, 2, 1)
        
        # CMM
        r_grid.addWidget(QLabel("所需最小风量 [CMM/m³/min]:"), 1, 0); r_grid.addWidget(self.af_res_cmm, 1, 1)
        
        # Factor
        r_grid.addWidget(QLabel("海拔修正系数 (Density Factor):"), 2, 0); r_grid.addWidget(self.af_factor, 2, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 16px;"
        self.af_res_cfm.setReadOnly(True); self.af_res_cfm.setStyleSheet(style)
        self.af_res_cmm.setReadOnly(True); self.af_res_cmm.setStyleSheet("background-color: #f4f6f6;")
        self.af_factor.setReadOnly(True); self.af_factor.setStyleSheet("background-color: #fff8e1; color: #d35400;")
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        tips = QLabel("提示：计算结果为理论净风量。选型风扇时，需查阅风扇的 P-Q 曲线（风压-风量曲线）。\n"
                      "由于系统存在风阻（System Impedance），实际工作点风量远小于风扇标称的最大风量（空载风量）。\n"
                      "建议：风扇标称风量应为计算值的 1.5~2 倍（视风道阻力而定）。")
        tips.setStyleSheet("color: #7f8c8d; font-style: italic; background-color: #f9f9f9; padding: 10px; border-radius: 4px;")
        tips.setWordWrap(True)
        layout.addWidget(tips)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_sys_airflow(self):
        try:
            p_loss = float(self.af_p.text())
            dt = float(self.af_dt.text())
            margin_pct = float(self.af_margin.text()) / 100.0
            
            # Parse Altitude
            alt_txt = self.af_alt.currentText()
            # Extract number
            import re
            nums = re.findall(r'\d+', alt_txt)
            if nums:
                h = float(nums[0])
            else:
                h = 0.0 # Default sea level
            
            if dt <= 0: raise ValueError("温升必须大于0")
            
            # 1. Base CFM at Sea Level
            # Formula: CFM = 3.16 * P / dT
            cfm_base = 3.16 * p_loss / dt
            
            # 2. Altitude Correction (Density Ratio)
            # Density Ratio sigma = rho_alt / rho_sea
            # Approx formula: sigma = (1 - 2.25577e-5 * H)^5.2559  (Troposphere < 11km)
            if h > 0:
                sigma = (1 - 2.25577e-5 * h) ** 5.2559
                # Required Flow increases as density decreases to maintain mass flow
                # CFM_req = CFM_base / sigma
                alt_factor = 1.0 / sigma
            else:
                alt_factor = 1.0
            
            # 3. Apply Margin
            cfm_total = cfm_base * alt_factor * (1 + margin_pct)
            
            # Convert to CMM (m3/min)
            # 1 CFM = 0.0283168 m3/min (CMM)
            cmm_total = cfm_total * 0.0283168
            
            self.af_res_cfm.setText(f"{cfm_total:.1f} CFM")
            self.af_res_cmm.setText(f"{cmm_total:.2f} CMM")
            self.af_factor.setText(f"{alt_factor:.2f} (H={h:.0f}m)")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("散热器选型与系统风量指南")
        dialog.resize(800, 750)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 使用原始字符串 r"" 来避免 \D 等字符被 Python 转义
        html_content = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            code { background-color: #e0e0e0; padding: 2px 4px; border-radius: 3px; font-family: monospace; color: #c0392b; }
            .box { background-color: #fffde7; padding: 10px; border-left: 4px solid #f1c40f; margin: 10px 0; }
        </style>
        <h1>热设计计算指南</h1>
        
        <h2>1. 系统风量计算 (System Airflow)</h2>
        <div class="box">
            <b>痛点：</b> 机箱要开多大的孔？选多大的风扇？<br>
            这取决于总热耗 $P$ 和允许的温升 $\Delta T$。
        </div>
        <p><b>基本公式 (海平面)：</b></p>
        <p>$$CFM = \frac{3.16 \times P_{loss}(W)}{\Delta T(^\circ C)}$$</p>
        <ul>
            <li><b>P_loss:</b> 机箱内所有发热器件的总功耗。</li>
            <li><b>ΔT:</b> 出风口温度 - 进风口温度。通常设计值取 10~20°C。温升越小，所需风量越大，噪声通常也越大。</li>
        </ul>
        
        <h3>海拔修正 (Altitude Derating)</h3>
        <p>空气密度随海拔升高而降低，带走热量的能力变差（质量流量下降）。</p>
        <p><b>修正系数：</b> $CFM_{req} = CFM_{sea} \times K_{alt}$</p>
        <ul>
            <li>0m: K=1.0</li>
            <li>2000m: K ≈ 1.25 (需增加 25% 风量)</li>
            <li>5000m: K ≈ 1.75 (需增加 75% 风量)</li>
        </ul>

        <h2>2. 稳态热阻计算 (Steady State)</h2>
        <p>公式：<code>Tj = Tamb + P * (Rjc + Rcs + Rsa)</code></p>
        <ul>
            <li><b>Rjc:</b> 结到壳 (Junction-to-Case)，器件内部属性，查 Datasheet。</li>
            <li><b>Rcs:</b> 壳到散热器 (Case-to-Sink)，取决于导热硅脂或绝缘片。典型值：硅脂 0.1~0.5。</li>
            <li><b>Rsa:</b> 散热器到环境 (Sink-to-Ambient)，散热器核心指标。</li>
        </ul>

        <h2>3. 密封外壳温升 (Sealed Enclosure)</h2>
        <p><b>经验法则：</b> $\Delta T \approx k \cdot (P/Area)^{0.8}$。</p>
        <ul>
            <li><b>塑料外壳:</b> k=450 (导热差)</li>
            <li><b>金属喷漆:</b> k=300 (辐射好)</li>
            <li><b>金属光亮:</b> k=400 (辐射差)</li>
        </ul>
        
        <h2>4. 瞬态热容 (Transient Thermal Capacity)</h2>
        <div class="box">
            <b>应用场景：</b> 电源启动浪涌、短时过载测试 (Overload)。
        </div>
        <p>当负载时间极短（如 1s~30s）时，热量主要由散热器的<b>热容 (Thermal Mass)</b> 吸收，还来不及传导到环境中。</p>
        <p><b>计算公式（绝热模型）：</b> $\Delta T = \frac{Energy}{C_{th}} = \frac{P \times t}{c \times m}$</p>
        <ul>
            <li>$c$: 比热容 (Aluminum ≈ 900 J/kgK, Copper ≈ 385 J/kgK)。</li>
            <li>$m$: 散热器质量 (kg)。</li>
        </ul>
        """
        text.setHtml(html_content)
        layout.addWidget(text)
        dialog.exec_()