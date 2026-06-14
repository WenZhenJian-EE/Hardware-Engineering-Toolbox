from modules.base_module import BaseModule
# rc_charge_window.py

import math
import matplotlib.pyplot as plt
from io import BytesIO

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class RcChargeWindow(BaseModule):
    category = "5. 无源器件与物理连接 (Passives & Physical)"
    display_name = "RC 充放电"
    description = "标准RC / 交直流预充 / 母线放电"
    window_id = "phy_rc"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('RC 充放电与预充电设计助手')
        self.setGeometry(350, 350, 1050, 800) 
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 教程按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("查看设计笔记 / 教程")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(200)
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

        self.tab_standard = QWidget()
        self.tab_dc_pre = QWidget()
        self.tab_ac_pre = QWidget()
        self.tab_bus_discharge = QWidget()
        self.tab_xcap_discharge = QWidget()

        self.init_standard_ui(self.tab_standard)
        self.init_dc_pre_ui(self.tab_dc_pre)
        self.init_ac_pre_ui(self.tab_ac_pre)
        self.init_bus_discharge_ui(self.tab_bus_discharge)
        self.init_xcap_discharge_ui(self.tab_xcap_discharge)

        self.tabs.addTab(self.tab_standard, "标准 RC 充放电")
        self.tabs.addTab(self.tab_dc_pre, "直流预充电设计")
        self.tabs.addTab(self.tab_ac_pre, "交流预充电设计")
        self.tabs.addTab(self.tab_bus_discharge, "高压母线放电")
        self.tabs.addTab(self.tab_xcap_discharge, "X 电容安规放电 (IEC 62368)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 标准 RC 充放电
    # ==============================================================================
    def init_standard_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("计算目标:"))
        self.std_mode_combo = QComboBox()
        self.std_mode_combo.addItems(["计算时间/时间常数 (已知 R, C)", "计算电阻 R (已知 C, Time)", "计算电容 C (已知 R, Time)"])
        self.std_mode_combo.currentIndexChanged.connect(self.update_std_inputs)
        mode_layout.addWidget(self.std_mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # 输入
        input_group = QGroupBox("电路参数")
        input_layout = QGridLayout()
        
        self.std_us_input = QLineEdit("12")
        input_layout.addWidget(QLabel("电源电压 (Us) [V]:"), 0, 0)
        input_layout.addWidget(self.std_us_input, 0, 1)
        
        # Resistor
        self.std_r_label = QLabel("电阻 (R):")
        self.std_r_input = QLineEdit("10")
        self.std_r_unit = QComboBox(); self.std_r_unit.addItems(["kΩ", "Ω", "MΩ"])
        
        input_layout.addWidget(self.std_r_label, 1, 0)
        r_box = QHBoxLayout(); r_box.addWidget(self.std_r_input); r_box.addWidget(self.std_r_unit); r_box.setContentsMargins(0,0,0,0)
        self.std_r_container = QWidget(); self.std_r_container.setLayout(r_box)
        input_layout.addWidget(self.std_r_container, 1, 1)
        
        # Capacitor
        self.std_c_label = QLabel("电容 (C):")
        self.std_c_input = QLineEdit("100")
        self.std_c_unit = QComboBox(); self.std_c_unit.addItems(["uF", "nF", "pF"])
        
        input_layout.addWidget(self.std_c_label, 2, 0)
        c_box = QHBoxLayout(); c_box.addWidget(self.std_c_input); c_box.addWidget(self.std_c_unit); c_box.setContentsMargins(0,0,0,0)
        self.std_c_container = QWidget(); self.std_c_container.setLayout(c_box)
        input_layout.addWidget(self.std_c_container, 2, 1)

        # Time
        self.std_time_label = QLabel("目标时间常数 (τ):")
        self.std_time_input = QLineEdit()
        self.std_time_input.setPlaceholderText("计算结果")
        self.std_time_unit = QLabel("s") 
        
        input_layout.addWidget(self.std_time_label, 3, 0)
        t_box = QHBoxLayout(); t_box.addWidget(self.std_time_input); t_box.addWidget(self.std_time_unit); t_box.setContentsMargins(0,0,0,0)
        self.std_t_container = QWidget(); self.std_t_container.setLayout(t_box)
        input_layout.addWidget(self.std_t_container, 3, 1)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 按钮
        self.std_calc_btn = QPushButton("开始计算")
        self.std_calc_btn.setFixedHeight(45)
        self.std_calc_btn.clicked.connect(self.calc_standard)
        layout.addWidget(self.std_calc_btn)
        
        # 结果标签
        self.std_result_label = QLabel("等待计算...")
        self.std_result_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #3498db; margin: 10px 0;")
        self.std_result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.std_result_label)
        
        # 表格
        self.std_table = QTableWidget()
        self.std_table.setColumnCount(4)
        self.std_table.setHorizontalHeaderLabels(["时间 (t)", "倍数", "充电电压 Uc (V)", "放电电压 Uc (V)"])
        self.std_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.std_table)
        
        tab.setLayout(layout)
        self.update_std_inputs() 

    def update_std_inputs(self):
        idx = self.std_mode_combo.currentIndex()
        
        self.std_r_input.setReadOnly(False); self.std_r_input.setStyleSheet("")
        self.std_c_input.setReadOnly(False); self.std_c_input.setStyleSheet("")
        self.std_time_input.setReadOnly(False); self.std_time_input.setStyleSheet("")
        
        if idx == 0:
            self.std_time_input.setReadOnly(True)
            self.std_time_input.setText("")
            self.std_time_input.setPlaceholderText("结果：时间常数 τ")
            self.std_time_input.setStyleSheet("background-color: #f0f0f0;")
            self.std_time_label.setText("时间常数 (τ):")
        elif idx == 1:
            self.std_r_input.setReadOnly(True)
            self.std_r_input.setText("")
            self.std_r_input.setPlaceholderText("结果：电阻 R")
            self.std_r_input.setStyleSheet("background-color: #f0f0f0;")
            self.std_time_label.setText("目标时间常数 (τ):")
        elif idx == 2:
            self.std_c_input.setReadOnly(True)
            self.std_c_input.setText("")
            self.std_c_input.setPlaceholderText("结果：电容 C")
            self.std_c_input.setStyleSheet("background-color: #f0f0f0;")
            self.std_time_label.setText("目标时间常数 (τ):")

    def calc_standard(self):
        try:
            mode = self.std_mode_combo.currentIndex()
            us = float(self.std_us_input.text())
            
            r_mult = 1000 if self.std_r_unit.currentText() == "kΩ" else (1000000 if self.std_r_unit.currentText() == "MΩ" else 1)
            c_mult = 1e-6 if self.std_c_unit.currentText() == "uF" else (1e-9 if self.std_c_unit.currentText() == "nF" else 1e-12)
            
            r = c = tau = 0
            
            if mode == 0: # Calc Tau
                r = float(self.std_r_input.text()) * r_mult
                c = float(self.std_c_input.text()) * c_mult
                tau = r * c
                self.std_time_input.setText(f"{tau:.6g}")
                self.std_result_label.setText(f"计算结果: τ = {tau*1000:.2f} ms")
            elif mode == 1: # Calc R
                c = float(self.std_c_input.text()) * c_mult
                tau = float(self.std_time_input.text())
                if c <= 0: raise ValueError
                r = tau / c
                self.std_r_input.setText(f"{r/r_mult:.4f}")
                self.std_result_label.setText(f"计算结果: R = {r/1000:.2f} kΩ")
            elif mode == 2: # Calc C
                r = float(self.std_r_input.text()) * r_mult
                tau = float(self.std_time_input.text())
                if r <= 0: raise ValueError
                c = tau / r
                self.std_c_input.setText(f"{c/c_mult:.4f}")
                self.std_result_label.setText(f"计算结果: C = {c*1e6:.2f} uF")

            self.std_table.setRowCount(6)
            factors = [1, 2, 2.3, 3, 4, 5]
            for i, k in enumerate(factors):
                t = k * tau
                v_charge = us * (1 - math.exp(-k))
                v_discharge = us * math.exp(-k)
                self.std_table.setItem(i, 0, QTableWidgetItem(f"{t*1000:.2f} ms"))
                self.std_table.setItem(i, 1, QTableWidgetItem(f"{k} τ"))
                self.std_table.setItem(i, 2, QTableWidgetItem(f"{v_charge:.2f} V"))
                self.std_table.setItem(i, 3, QTableWidgetItem(f"{v_discharge:.2f} V"))
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    # ==============================================================================
    # Tab 2: 直流预充电设计
    # ==============================================================================
    def init_dc_pre_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入
        input_group = QGroupBox("设计要求 (DC Pre-charge)")
        grid = QGridLayout()
        
        self.dc_us = QLineEdit("400"); grid.addWidget(QLabel("总电压 (Us) [V]:"), 0, 0); grid.addWidget(self.dc_us, 0, 1)
        self.dc_c = QLineEdit("400"); grid.addWidget(QLabel("负载电容 (C) [uF]:"), 1, 0); grid.addWidget(self.dc_c, 1, 1)
        self.dc_t = QLineEdit("0.92"); grid.addWidget(QLabel("预充时间 (T) [s]:"), 2, 0); grid.addWidget(self.dc_t, 2, 1)
        
        self.dc_target_combo = QComboBox()
        self.dc_target_combo.addItems(["90%", "95%", "自定义"])
        self.dc_target_combo.currentIndexChanged.connect(self.on_dc_target_changed)
        grid.addWidget(QLabel("目标电压比例:"), 3, 0); grid.addWidget(self.dc_target_combo, 3, 1)
        
        self.dc_target_custom = QLineEdit("90")
        self.dc_target_custom.setPlaceholderText("输入百分比 (如 85)")
        self.dc_target_custom.setVisible(False)
        grid.addWidget(self.dc_target_custom, 3, 2)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算预充电阻 & 功率选型")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_dc_pre)
        layout.addWidget(btn)
        
        # 结果
        res_group = QGroupBox("计算结果与选型建议")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        # 设置列宽比例，保证公式显示空间
        res_grid.setColumnStretch(1, 1)
        
        self.dc_r_res = QLineEdit()
        self.dc_i_res = QLineEdit()
        self.dc_e_res = QLineEdit()
        self.dc_p_res = QLineEdit()
        
        # Row 0
        res_grid.addWidget(QLabel("推荐电阻 (R):"), 0, 0); 
        res_grid.addWidget(self.dc_r_res, 0, 1)
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'R = \frac{-T}{C \cdot \ln(1 - \%)}')); 
        l_r.setMinimumWidth(200)
        res_grid.addWidget(l_r, 0, 2)
        
        # Row 1
        res_grid.addWidget(QLabel("峰值冲击电流 (I_peak):"), 1, 0); 
        res_grid.addWidget(self.dc_i_res, 1, 1)
        l_i = QLabel(); l_i.setPixmap(self.render_formula(r'I_{peak} = U_s / R'));
        l_i.setMinimumWidth(200)
        res_grid.addWidget(l_i, 1, 2)
        
        # Row 2
        res_grid.addWidget(QLabel("脉冲能量 (Pulse Energy):"), 2, 0); 
        res_grid.addWidget(self.dc_e_res, 2, 1)
        l_e = QLabel(); l_e.setPixmap(self.render_formula(r'E = \frac{1}{2} C U_s^2'));
        l_e.setMinimumWidth(200)
        res_grid.addWidget(l_e, 2, 2)
        
        # Row 3
        res_grid.addWidget(QLabel("电阻功率选型建议:"), 3, 0); 
        res_grid.addWidget(self.dc_p_res, 3, 1)
        tip = QLabel("注: 按 10 倍过载能力估算\n即 P_rated > (E/T)/10")
        tip.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        res_grid.addWidget(tip, 3, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_p = "background-color: #fff5f5; font-weight: bold; color: #c0392b;"
        self.dc_r_res.setReadOnly(True); self.dc_r_res.setStyleSheet(style_res)
        self.dc_i_res.setReadOnly(True)
        self.dc_e_res.setReadOnly(True)
        self.dc_p_res.setReadOnly(True); self.dc_p_res.setStyleSheet(style_p)
        
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        
        tab.setLayout(layout)

    def on_dc_target_changed(self):
        is_custom = self.dc_target_combo.currentText() == "自定义"
        self.dc_target_custom.setVisible(is_custom)

    def calc_dc_pre(self):
        try:
            us = float(self.dc_us.text())
            c = float(self.dc_c.text()) * 1e-6
            t = float(self.dc_t.text())
            
            if self.dc_target_combo.currentText() == "自定义":
                k = float(self.dc_target_custom.text()) / 100.0
            else:
                k = float(self.dc_target_combo.currentText().replace("%", "")) / 100.0
            
            if k >= 1.0 or k <= 0:
                raise ValueError("目标比例必须在 0~100% 之间")

            r = -t / (c * math.log(1 - k))
            i_peak = us / r
            energy = 0.5 * c * (us ** 2)
            
            p_pulse_avg = energy / t
            p_rated_rec = p_pulse_avg / 10.0
            
            self.dc_r_res.setText(f"{r:.2f} Ω")
            self.dc_i_res.setText(f"{i_peak:.2f} A")
            self.dc_e_res.setText(f"{energy:.2f} J")
            self.dc_p_res.setText(f"建议额定功率 > {p_rated_rec:.1f} W")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {e}")
        except Exception:
            QMessageBox.warning(self, "错误", "计算出错")

    # ==============================================================================
    # Tab 3: 交流预充电设计
    # ==============================================================================
    def init_ac_pre_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        input_group = QGroupBox("设计参数 (AC Pre-charge)")
        grid = QGridLayout()
        
        self.ac_vrms = QLineEdit("220"); grid.addWidget(QLabel("交流电压 (Vrms) [V]:"), 0, 0); grid.addWidget(self.ac_vrms, 0, 1)
        self.ac_c = QLineEdit("1000"); grid.addWidget(QLabel("负载电容 (C) [uF]:"), 1, 0); grid.addWidget(self.ac_c, 1, 1)
        self.ac_t = QLineEdit("0.5"); grid.addWidget(QLabel("目标预充时间 (T) [s]:"), 2, 0); grid.addWidget(self.ac_t, 2, 1)
        
        self.ac_imax_limit = QLineEdit("50"); grid.addWidget(QLabel("冲击电流限制 (I_max) [A]:"), 3, 0); grid.addWidget(self.ac_imax_limit, 3, 1)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算推荐电阻 & 安全校核")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_ac_pre)
        layout.addWidget(btn)
        
        # 结果
        res_group = QGroupBox("计算结果")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        res_grid.setColumnStretch(1, 1)
        
        self.ac_r_rec = QLineEdit()
        self.ac_ipeak = QLineEdit()
        self.ac_status = QLineEdit()
        self.ac_energy = QLineEdit()
        self.ac_p_rec = QLineEdit()
        
        # Row 0
        res_grid.addWidget(QLabel("推荐电阻值 (R):"), 0, 0); 
        res_grid.addWidget(self.ac_r_rec, 0, 1)
        l_ac_r = QLabel(); l_ac_r.setPixmap(self.render_formula(r'R \approx T / (5C)')); l_ac_r.setMinimumWidth(200)
        res_grid.addWidget(l_ac_r, 0, 2)
        
        # Row 1
        res_grid.addWidget(QLabel("实际冲击电流 (I_peak):"), 1, 0); 
        res_grid.addWidget(self.ac_ipeak, 1, 1)
        l_ac_i = QLabel(); l_ac_i.setPixmap(self.render_formula(r'I_{peak} = \sqrt{2} V_{rms} / R')); l_ac_i.setMinimumWidth(200)
        res_grid.addWidget(l_ac_i, 1, 2)
        
        # Row 2 (新增功率建议)
        res_grid.addWidget(QLabel("脉冲能量 (E):"), 2, 0); 
        res_grid.addWidget(self.ac_energy, 2, 1)
        l_ac_e = QLabel(); l_ac_e.setPixmap(self.render_formula(r'E \approx \frac{1}{2} C (\sqrt{2}V_{rms})^2')); l_ac_e.setMinimumWidth(200)
        res_grid.addWidget(l_ac_e, 2, 2)
        
        # Row 3 (功率)
        res_grid.addWidget(QLabel("电阻功率选型建议:"), 3, 0); 
        res_grid.addWidget(self.ac_p_rec, 3, 1)
        tip_ac = QLabel("注: 按 10 倍过载能力估算")
        tip_ac.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        res_grid.addWidget(tip_ac, 3, 2)

        # Row 4
        res_grid.addWidget(QLabel("安全校核结果:"), 4, 0); 
        res_grid.addWidget(self.ac_status, 4, 1)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_p = "background-color: #fff5f5; font-weight: bold; color: #c0392b;"
        self.ac_r_rec.setReadOnly(True); self.ac_r_rec.setStyleSheet(style_res)
        self.ac_ipeak.setReadOnly(True)
        self.ac_status.setReadOnly(True)
        self.ac_energy.setReadOnly(True)
        self.ac_p_rec.setReadOnly(True); self.ac_p_rec.setStyleSheet(style_p)
        
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        layout.addWidget(QLabel("说明：交流预充电通常认为 5τ (5RC) 时间后进入稳态。此处 R = T / 5C。"))
        layout.addStretch()
        
        tab.setLayout(layout)

    def calc_ac_pre(self):
        try:
            v_rms = float(self.ac_vrms.text())
            c = float(self.ac_c.text()) * 1e-6
            t_target = float(self.ac_t.text())
            i_limit = float(self.ac_imax_limit.text())
            
            r_rec = t_target / (5 * c)
            
            v_peak = v_rms * math.sqrt(2)
            i_peak = v_peak / r_rec
            
            # Energy & Power
            energy = 0.5 * c * (v_peak ** 2)
            p_pulse_avg = energy / t_target
            p_rated_rec = p_pulse_avg / 10.0 # 10倍过载能力估算
            
            self.ac_r_rec.setText(f"{r_rec:.2f} Ω")
            self.ac_ipeak.setText(f"{i_peak:.2f} A")
            self.ac_energy.setText(f"{energy:.2f} J")
            self.ac_p_rec.setText(f"建议额定功率 > {p_rated_rec:.1f} W")
            
            if i_peak <= i_limit:
                self.ac_status.setText(f"安全 ( < {i_limit} A )")
                self.ac_status.setStyleSheet("font-weight: bold; color: green;")
            else:
                self.ac_status.setText(f"警告！超过限制 ({i_limit} A)")
                self.ac_status.setStyleSheet("font-weight: bold; color: red;")
                QMessageBox.warning(self, "冲击电流过大", 
                                    f"当前目标时间算出的电阻 ({r_rec:.1f}Ω) 会导致 {i_peak:.1f}A 的冲击电流，\n"
                                    f"超过了您设定的 {i_limit}A 限制。\n\n"
                                    "建议：增加目标预充时间，或选用抗浪涌能力更强的器件。")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 4: 高压母线放电设计 (新增)
    # ==============================================================================
    def init_bus_discharge_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入区域
        input_group = QGroupBox("安规与放电要求")
        grid = QGridLayout()
        
        self.bd_vbus = QLineEdit("800"); grid.addWidget(QLabel("母线电压 (V_bus) [V]:"), 0, 0); grid.addWidget(self.bd_vbus, 0, 1)
        self.bd_cbus = QLineEdit("2000"); grid.addWidget(QLabel("总母线电容 (C_total) [uF]:"), 1, 0); grid.addWidget(self.bd_cbus, 1, 1)
        self.bd_vsafe = QLineEdit("60"); grid.addWidget(QLabel("目标安全电压 (V_safe) [V]:"), 2, 0); grid.addWidget(self.bd_vsafe, 2, 1)
        self.bd_time = QLineEdit("120"); grid.addWidget(QLabel("规定放电时间 (T) [s]:"), 3, 0); grid.addWidget(self.bd_time, 3, 1)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算放电电阻与能耗")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_bus_discharge)
        layout.addWidget(btn)
        
        # 结果区域
        res_group = QGroupBox("计算结果")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        res_grid.setColumnStretch(1, 1)
        
        self.bd_r_max = QLineEdit()
        self.bd_p_steady = QLineEdit()
        self.bd_energy = QLineEdit()
        self.bd_tau = QLineEdit()
        
        # Row 0: R
        res_grid.addWidget(QLabel("最大允许电阻 (R_max):"), 0, 0)
        res_grid.addWidget(self.bd_r_max, 0, 1)
        l_bd_r = QLabel(); l_bd_r.setPixmap(self.render_formula(r'R \leq \frac{T}{C \cdot \ln(V_{bus}/V_{safe})}')); l_bd_r.setMinimumWidth(220)
        res_grid.addWidget(l_bd_r, 0, 2)
        
        # Row 1: Steady Power
        res_grid.addWidget(QLabel("稳态功耗 (常接时):"), 1, 0)
        res_grid.addWidget(self.bd_p_steady, 1, 1)
        l_bd_p = QLabel(); l_bd_p.setPixmap(self.render_formula(r'P_{loss} = V_{bus}^2 / R')); l_bd_p.setMinimumWidth(220)
        res_grid.addWidget(l_bd_p, 1, 2)
        
        # Row 2: Transient Energy
        res_grid.addWidget(QLabel("电阻瞬态能量冲击 (E):"), 2, 0)
        res_grid.addWidget(self.bd_energy, 2, 1)
        l_bd_e = QLabel(); l_bd_e.setPixmap(self.render_formula(r'E \approx \frac{1}{2} C V_{bus}^2')); l_bd_e.setMinimumWidth(220)
        res_grid.addWidget(l_bd_e, 2, 2)

        # Row 3: Tau
        res_grid.addWidget(QLabel("时间常数 (τ = RC):"), 3, 0)
        res_grid.addWidget(self.bd_tau, 3, 1)
        
        style_res = "background-color: #fdf2e9; font-weight: bold; color: #d35400;"
        style_p = "background-color: #fff5f5; font-weight: bold; color: #c0392b;"
        self.bd_r_max.setReadOnly(True); self.bd_r_max.setStyleSheet(style_res)
        self.bd_p_steady.setReadOnly(True); self.bd_p_steady.setStyleSheet(style_p)
        self.bd_energy.setReadOnly(True)
        self.bd_tau.setReadOnly(True)
        
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        
        tip_box = QLabel("选型建议：\n1. 若使用常接泄放电阻(Passive Bleeder)，电阻功率需大于稳态功耗(P_loss)。\n2. 若使用主动放电电路(Active Discharge)，电阻只需耐受短时脉冲能量(E)，但需注意瞬时功率峰值。")
        tip_box.setStyleSheet("color: #555; background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        layout.addWidget(tip_box)
        layout.addStretch()
        
        tab.setLayout(layout)

    def calc_bus_discharge(self):
        try:
            v_bus = float(self.bd_vbus.text())
            c_bus = float(self.bd_cbus.text()) * 1e-6
            v_safe = float(self.bd_vsafe.text())
            t_limit = float(self.bd_time.text())
            
            if v_safe >= v_bus:
                QMessageBox.warning(self, "参数错误", "安全电压必须小于母线电压")
                return
            if v_safe <= 0 or t_limit <= 0 or c_bus <= 0:
                QMessageBox.warning(self, "参数错误", "输入值必须为正数")
                return

            # Formula: V_safe = V_bus * exp(-t / RC)
            # ln(V_safe / V_bus) = -t / RC
            # RC = -t / ln(V_safe / V_bus) = t / ln(V_bus / V_safe)
            # R = t / (C * ln(V_bus / V_safe))
            
            ln_val = math.log(v_bus / v_safe)
            r_max = t_limit / (c_bus * ln_val)
            
            # Steady State Power (if connected continuously)
            p_steady = (v_bus ** 2) / r_max
            
            # Total Energy Stored
            energy = 0.5 * c_bus * (v_bus ** 2)
            
            # Tau
            tau = r_max * c_bus
            
            # Formatting
            if r_max >= 1e6:
                r_str = f"{r_max/1e6:.3f} MΩ"
            elif r_max >= 1e3:
                r_str = f"{r_max/1e3:.3f} kΩ"
            else:
                r_str = f"{r_max:.2f} Ω"
                
            self.bd_r_max.setText(r_str)
            self.bd_p_steady.setText(f"{p_steady:.2f} W")
            self.bd_energy.setText(f"{energy:.1f} J")
            self.bd_tau.setText(f"{tau:.1f} s")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    # ==============================================================================
    # Tab 5: X-Cap Discharge (IEC 62368)
    # ==============================================================================
    def init_xcap_discharge_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        input_group = QGroupBox("安规与器件参数 (IEC 62368 / 60950)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        # Max AC Voltage
        self.xc_vac = QLineEdit("264"); grid.addWidget(QLabel("最大输入电压 (Vac_max) [Vrms]:"), 0, 0); grid.addWidget(self.xc_vac, 0, 1)
        
        # X Cap
        self.xc_val = QLineEdit("0.47"); grid.addWidget(QLabel("X 电容总容值 (C_x) [uF]:"), 1, 0); grid.addWidget(self.xc_val, 1, 1)
        
        # Tolerance
        self.xc_tol_c = QLineEdit("20"); grid.addWidget(QLabel("电容容差 (+%) :"), 1, 2); grid.addWidget(self.xc_tol_c, 1, 3)
        self.xc_tol_r = QLineEdit("5"); grid.addWidget(QLabel("电阻容差 (+%) :"), 2, 2); grid.addWidget(self.xc_tol_r, 2, 3)
        
        # Standard Limits
        self.xc_time = QLineEdit("1.0"); self.xc_time.setToolTip("标准通常要求 1s 或 2s (Type A/B equipment)"); grid.addWidget(QLabel("安规限制时间 (T_limit) [s]:"), 2, 0); grid.addWidget(self.xc_time, 2, 1)
        self.xc_vsafe = QLineEdit("60"); grid.addWidget(QLabel("安全电压阈值 (V_safe) [Vpk]:"), 3, 0); grid.addWidget(self.xc_vsafe, 3, 1)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算最大允许放电电阻")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_xcap_discharge)
        layout.addWidget(btn)
        
        # Results
        res_group = QGroupBox("选型指导 (Worst Case Analysis)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.xc_r_max = QLineEdit()
        self.xc_tau_max = QLineEdit()
        self.xc_power = QLineEdit()
        
        # R Max
        r_grid.addWidget(QLabel("最大标称电阻 (R_nom_max):"), 0, 0)
        r_grid.addWidget(self.xc_r_max, 0, 1)
        # 修复 LaTeX 语法: \leq 替代 \le
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'R_{nom} \leq \frac{-T}{\ln(V_{safe}/V_{peak}) \cdot C_{max} \cdot (1+Tol_R)}'))
        l_r.setMinimumWidth(220)
        r_grid.addWidget(l_r, 0, 2)
        
        # Time Constant
        r_grid.addWidget(QLabel("最恶劣时间常数 (τ_max):"), 1, 0)
        r_grid.addWidget(self.xc_tau_max, 1, 1)
        l_tau = QLabel(); l_tau.setPixmap(self.render_formula(r'\tau_{max} = R_{max} \cdot C_{max}'))
        r_grid.addWidget(l_tau, 1, 2)
        
        # Power Loss
        r_grid.addWidget(QLabel("电阻稳态功耗 (P_loss @ Vac):"), 2, 0)
        r_grid.addWidget(self.xc_power, 2, 1)
        l_p = QLabel(); l_p.setPixmap(self.render_formula(r'P \approx V_{ac}^2 / R_{nom}'))
        r_grid.addWidget(l_p, 2, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_warn = "background-color: #fff5f5; font-weight: bold; color: #c0392b;"
        
        self.xc_r_max.setReadOnly(True); self.xc_r_max.setStyleSheet(style_res)
        self.xc_tau_max.setReadOnly(True)
        self.xc_power.setReadOnly(True); self.xc_power.setStyleSheet(style_warn)
        
        res_group.setLayout(r_grid)
        layout.addWidget(res_group)
        
        # Tips
        tip = QLabel("设计建议：\n1. 通常使用 2~3 个 1206 电阻串联以满足耐压要求 (单个 1206 耐压约 200V)。\n2. 若总电阻 > R_nom_max，则无法满足安规放电时间要求。\n3. 若功耗过大，可考虑使用带有 X 电容放电功能的 IC (如 CAP200DG)。")
        tip.setStyleSheet("color: #555; background-color: #f0f0f0; padding: 10px; border-radius: 4px;")
        layout.addWidget(tip)
        layout.addStretch()
        
        tab.setLayout(layout)

    def calc_xcap_discharge(self):
        try:
            vac = float(self.xc_vac.text())
            c_nom = float(self.xc_val.text()) * 1e-6
            tol_c = float(self.xc_tol_c.text()) / 100.0
            tol_r = float(self.xc_tol_r.text()) / 100.0
            t_limit = float(self.xc_time.text())
            v_safe = float(self.xc_vsafe.text())
            
            v_peak = vac * math.sqrt(2)
            
            if v_peak <= v_safe:
                self.xc_r_max.setText("无需放电电阻")
                return
                
            # Worst case capacitance (High)
            c_max = c_nom * (1 + tol_c)
            
            # Required Time Constant (Tau) to drop from Vpeak to Vsafe in T_limit
            # Vsafe = Vpeak * exp(-T / Tau) -> ln(Vsafe/Vpeak) = -T/Tau -> Tau = -T / ln(...)
            tau_limit = -t_limit / math.log(v_safe / v_peak)
            
            # R_actual_max <= Tau_limit / C_max
            r_actual_max = tau_limit / c_max
            
            # Nominal Resistance
            # R_actual_max = R_nom * (1 + tol_r)
            r_nom_limit = r_actual_max / (1 + tol_r)
            
            # Power loss at nominal R and VAC input
            # P = V^2 / R
            p_loss = (vac ** 2) / r_nom_limit
            
            # Display
            if r_nom_limit >= 1e6:
                r_str = f"{r_nom_limit/1e6:.3f} MΩ"
            elif r_nom_limit >= 1e3:
                r_str = f"{r_nom_limit/1e3:.3f} kΩ"
            else:
                r_str = f"{r_nom_limit:.2f} Ω"
                
            self.xc_r_max.setText(r_str)
            self.xc_tau_max.setText(f"{tau_limit:.3f} s")
            self.xc_power.setText(f"{p_loss*1000:.1f} mW")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("RC 充放电与预充电设计笔记")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = """
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 20px;}
            h3 { color: #e67e22; margin-top: 15px; }
            li { margin-bottom: 5px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
            .formula { background-color: #e8f6f3; padding: 10px; border-left: 4px solid #1abc9c; font-family: "Courier New"; }
        </style>
        
        <h1>RC 电路充放电与预充电设计</h1>
        
        <h2>1. 直流预充电电路设计 (DC Pre-charge)</h2>
        <p><b>目标：</b>防止主接触器闭合时的电弧和二次冲击，限制初始冲击电流。</p>
        <h3>核心公式</h3>
        <p>直流 RC 串联充电电压：</p>
        <div class="formula">Ut = Us * (1 - e^(-t/RC))</div>
        
        <h3>计算步骤</h3>
        <ol>
            <li><b>确定要求：</b> 预充时间 T (如 0.5s~2s) 和 目标电压 Ut (如 90% 或 95% Us)。</li>
            <li><b>计算电阻 R：</b>
                <ul>
                    <li>目标 90%: R ≈ T / (2.3 * C)</li>
                    <li>目标 95%: R ≈ T / (3.0 * C)</li>
                    <li>通用公式: R = -T / (C * ln(1 - Ut/Us))</li>
                </ul>
            </li>
            <li><b>校核：</b>
                <ul>
                    <li><b>峰值电流：</b> I_peak = Us / R (需在器件承受范围内)</li>
                    <li><b>电阻能量：</b> E = 0.5 * C * Us^2 (需核对电阻脉冲能量耐受能力)</li>
                </ul>
            </li>
        </ol>

        <h2>2. 交流预充电电路设计 (AC Pre-charge)</h2>
        <p><b>区别：</b> 交流充电是非连续的“棘轮式”上升，不能直接套用直流公式。</p>
        <h3>设计思路</h3>
        <ol>
            <li><b>限制冲击电流 (确定 R)：</b>
                <ul>
                    <li>考虑最坏情况：峰值时刻闭合。</li>
                    <li>V_peak = V_rms * √2</li>
                    <li>R_min = V_peak / I_peak_max (I_max 由整流桥/保险丝决定)</li>
                </ul>
            </li>
            <li><b>确定预充时间 (确定 T)：</b>
                <ul>
                    <li>工程上认为 <b>5τ (5RC)</b> 后进入稳态。</li>
                    <li>T_precharge ≈ 5 * R * C</li>
                </ul>
            </li>
        </ol>

        <h2>3. 高压母线放电 (Bus Discharge)</h2>
        <p><b>目标：</b>安规要求设备停机后，母线电压需在规定时间(如2min)内降至安全电压(60V)以下。</p>
        <div class="formula">V_safe = V_bus * e^(-t/RC)</div>
        <ul>
            <li><b>R_max:</b> 必须小于 T / (C * ln(V_bus / V_safe)) 才能满足时间要求。</li>
            <li><b>能量冲击：</b> 电阻需要吸收母线电容存储的几乎所有能量 E = 0.5*C*V^2。</li>
            <li><b>稳态功耗：</b> 若使用被动泄放(并联在母线上)，电阻会持续消耗功率 P = V^2/R，需权衡放电速度与待机功耗。</li>
        </ul>

        <h2>4. 标准 RC 充放电特性</h2>
        <p><b>时间常数 τ = RC</b></p>
        <ul>
            <li>1τ: 63% (充) / 37% (放)</li>
            <li>2τ: 86% (充) / 14% (放)</li>
            <li>3τ: 95% (充) / 5% (放)</li>
            <li>5τ: 99% (充) / <1% (放) (基本完成)</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()