from modules.base_module import BaseModule
# capacitor_tool_window.py

import math
from io import BytesIO
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QComboBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class CapacitorToolWindow(BaseModule):
    category = "5. 无源器件与物理连接 (Passives & Physical)"
    display_name = "电容工具箱"
    description = "铝电解寿命 / RMS合成 / 偏置"
    window_id = "comp_cap"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('电容器寿命与选型助手 (Capacitor Tool)')
        self.setGeometry(350, 350, 950, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("计算原理与选型指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(220)
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

        self.tab_life = QWidget()
        self.tab_rms = QWidget()
        self.tab_topology = QWidget()
        self.tab_mlcc = QWidget()
        self.tab_holdup = QWidget() # 升级：包含超级电容计算

        self.init_life_ui(self.tab_life)
        self.init_rms_ui(self.tab_rms)
        self.init_topology_rms_ui(self.tab_topology)
        self.init_mlcc_ui(self.tab_mlcc)
        self.init_holdup_ui(self.tab_holdup)

        self.tabs.addTab(self.tab_life, "铝电解电容寿命估算")
        self.tabs.addTab(self.tab_rms, "RMS 有效值电流合成")
        self.tabs.addTab(self.tab_topology, "拓扑场景 RMS")
        self.tabs.addTab(self.tab_mlcc, "MLCC 直流偏置特性")
        self.tabs.addTab(self.tab_holdup, "掉电保持 & 超级电容 (Hold-up/Supercap)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 电解电容寿命计算
    # ==============================================================================
    def init_life_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入参数
        grp_in = QGroupBox("1. 电容器规格与工况")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.life_l0 = QLineEdit("2000")
        self.life_l0.setToolTip("Datasheet 中的耐久性时间 (Endurance/Load Life)")
        grid.addWidget(QLabel("额定寿命 L0 [Hours]:"), 0, 0); grid.addWidget(self.life_l0, 0, 1)
        
        self.life_t0 = QLineEdit("105")
        self.life_t0.setToolTip("Datasheet 中的最高工作温度")
        grid.addWidget(QLabel("额定温度 T0 [°C]:"), 0, 2); grid.addWidget(self.life_t0, 0, 3)
        
        self.life_ta = QLineEdit("65")
        self.life_ta.setToolTip("电容周围的环境温度 (不含自热)")
        grid.addWidget(QLabel("实际环境温度 Ta [°C]:"), 1, 0); grid.addWidget(self.life_ta, 1, 1)
        
        self.life_dt = QLineEdit("10")
        self.life_dt.setToolTip("由纹波电流引起的内部温升 (ΔT)。\n可通过测量电容表面温度减去环境温度估算，或根据纹波电流推算。")
        grid.addWidget(QLabel("纹波自热温升 ΔT [°C]:"), 1, 2); grid.addWidget(self.life_dt, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算预期寿命")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.setStyleSheet("background-color: #3498db; color: white;")
        btn.clicked.connect(self.calc_lifetime)
        layout.addWidget(btn)
        
        # 结果
        grp_res = QGroupBox("2. 估算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.life_res_hrs = QLineEdit()
        self.life_res_yrs = QLineEdit()
        self.life_core_temp = QLineEdit()
        
        r_grid.addWidget(QLabel("核心温度估算 (T_core):"), 0, 0); r_grid.addWidget(self.life_core_temp, 0, 1)
        
        r_grid.addWidget(QLabel("预期寿命 (Hours):"), 1, 0); r_grid.addWidget(self.life_res_hrs, 1, 1)
        self.l_formula = QLabel()
        self.l_formula.setPixmap(self.render_formula(r'L = L_0 \cdot 2^{\frac{T_0 - T_{core}}{10}}'))
        r_grid.addWidget(self.l_formula, 1, 2, 2, 1)
        
        r_grid.addWidget(QLabel("预期寿命 (Years):"), 2, 0); r_grid.addWidget(self.life_res_yrs, 2, 1)
        
        # Style
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.life_res_hrs, self.life_res_yrs]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
        self.life_core_temp.setReadOnly(True); self.life_core_temp.setStyleSheet("background-color: #f0f0f0;")
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Tips
        tip = QLabel("注意：阿伦尼乌斯定律仅为理论估算。每降低10°C寿命翻倍是通用法则，"
                     "但实际上受电解液挥发、密封橡胶老化等限制，寿命通常有上限 (如 15年)。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic; margin-top: 10px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_lifetime(self):
        try:
            l0 = float(self.life_l0.text())
            t0 = float(self.life_t0.text())
            ta = float(self.life_ta.text())
            dt = float(self.life_dt.text())
            
            t_core = ta + dt
            
            # Arrhenius Equation (Simplified "10-degree rule")
            # L = L0 * 2^((T0 - T_core) / 10)
            life_hours = l0 * (2 ** ((t0 - t_core) / 10.0))
            life_years = life_hours / (24 * 365)
            
            self.life_core_temp.setText(f"{t_core:.1f} °C")
            self.life_res_hrs.setText(f"{life_hours:,.0f} 小时")
            self.life_res_yrs.setText(f"{life_years:.2f} 年")
            
            # Warning
            if t_core > t0:
                self.life_core_temp.setStyleSheet("background-color: #fff5f5; color: red; font-weight: bold;")
                QMessageBox.warning(self, "过热警告", 
                                    f"核心温度 ({t_core}°C) 已超过额定温度 ({t0}°C)！\n"
                                    "电容可能会迅速失效或爆炸。请优化散热或降低纹波。")
            else:
                self.life_core_temp.setStyleSheet("background-color: #f0f0f0;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    # ==============================================================================
    # Tab 2: RMS 纹波合成
    # ==============================================================================
    def init_rms_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("当电容器上流过多个频率的纹波电流时（例如 Buck 输入电容同时包含开关频率纹波和工频纹波），"
                      "需要计算总的 RMS 电流来评估发热。")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Table
        self.rms_table = QTableWidget()
        self.rms_table.setColumnCount(3)
        self.rms_table.setHorizontalHeaderLabels(["频率成分 (备注)", "频率 Hz (可选)", "电流有效值 I_rms (A)"])
        self.rms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.rms_table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("添加一行")
        btn_add.clicked.connect(self.add_rms_row)
        btn_layout.addWidget(btn_add)
        
        btn_del = QPushButton("删除选中行")
        btn_del.clicked.connect(self.del_rms_row)
        btn_layout.addWidget(btn_del)
        
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self.clear_rms_rows)
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)
        
        # Calc Button
        btn_calc = QPushButton("计算总 RMS 电流")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_total_rms)
        layout.addWidget(btn_calc)
        
        # Result
        res_box = QGroupBox("合成结果")
        h_res = QHBoxLayout()
        self.rms_res_val = QLineEdit()
        self.rms_res_val.setReadOnly(True)
        self.rms_res_val.setStyleSheet("font-size: 18px; font-weight: bold; color: #8e44ad; background-color: #f4ecf7;")
        self.rms_res_val.setAlignment(Qt.AlignCenter)
        
        h_res.addWidget(QLabel("总有效值 (I_total_rms):"))
        h_res.addWidget(self.rms_res_val)
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'I_{total} = \sqrt{I_1^2 + I_2^2 + \dots + I_n^2}'))
        h_res.addWidget(l_form)
        res_box.setLayout(h_res)
        layout.addWidget(res_box)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # Init with 2 rows
        self.add_rms_row_data("开关频率主纹波", "", "2.0")
        self.add_rms_row_data("工频纹波 (100Hz)", "100", "0.5")

    def add_rms_row(self):
        self.add_rms_row_data("", "", "")

    def add_rms_row_data(self, name, freq, i_val):
        row = self.rms_table.rowCount()
        self.rms_table.insertRow(row)
        self.rms_table.setItem(row, 0, QTableWidgetItem(name))
        self.rms_table.setItem(row, 1, QTableWidgetItem(freq))
        self.rms_table.setItem(row, 2, QTableWidgetItem(i_val))

    def del_rms_row(self):
        row = self.rms_table.currentRow()
        if row >= 0:
            self.rms_table.removeRow(row)

    def clear_rms_rows(self):
        self.rms_table.setRowCount(0)

    def calc_total_rms(self):
        total_sq = 0.0
        try:
            rows = self.rms_table.rowCount()
            for r in range(rows):
                item = self.rms_table.item(r, 2)
                if item and item.text().strip():
                    val = float(item.text())
                    total_sq += val ** 2
            
            total_rms = math.sqrt(total_sq)
            self.rms_res_val.setText(f"{total_rms:.3f} A")
        except Exception as e:
            QMessageBox.warning(self, "错误", "请在 'I_rms' 列输入有效的数字")

    # ==============================================================================
    # Tab 2B: Topology-specific capacitor RMS current
    # ==============================================================================
    def init_topology_rms_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            "Fast RMS current estimates for common power topologies. Use it before capacitor selection and lifetime checks."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #566573; font-style: italic;")
        layout.addWidget(info)

        grp = QGroupBox("1. Topology and operating point")
        g = QGridLayout()
        self.topo_mode = QComboBox()
        self.topo_mode.addItems([
            "Buck input capacitor",
            "Buck output capacitor",
            "Boost output capacitor",
            "Flyback output capacitor",
            "3-phase inverter DC-Link",
        ])
        self.topo_vin = QLineEdit("48")
        self.topo_vout = QLineEdit("12")
        self.topo_iout = QLineEdit("10")
        self.topo_duty = QLineEdit("25")
        self.topo_lir = QLineEdit("30")
        self.topo_m = QLineEdit("0.8")
        self.topo_pf = QLineEdit("0.9")
        self.topo_esr = QLineEdit("20")
        self.topo_rth = QLineEdit("12")
        self.topo_ta = QLineEdit("65")

        fields = [
            ("Topology:", self.topo_mode),
            ("Vin / DC bus [V]:", self.topo_vin),
            ("Vout / phase-line context [V]:", self.topo_vout),
            ("Output/RMS load current [A]:", self.topo_iout),
            ("Duty [%] (auto if blank):", self.topo_duty),
            ("Inductor ripple ratio [%]:", self.topo_lir),
            ("Inverter modulation index:", self.topo_m),
            ("Power factor:", self.topo_pf),
            ("Capacitor ESR [mOhm]:", self.topo_esr),
            ("Cap thermal Rth [C/W]:", self.topo_rth),
            ("Ambient near capacitor [C]:", self.topo_ta),
        ]
        for i, (label, widget) in enumerate(fields):
            r, c = i // 2, (i % 2) * 2
            g.addWidget(QLabel(label), r, c)
            g.addWidget(widget, r, c + 1)
        grp.setLayout(g)
        layout.addWidget(grp)

        btn = QPushButton("Calculate topology RMS")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_topology_rms)
        layout.addWidget(btn)

        grp_res = QGroupBox("2. Result")
        r = QGridLayout()
        self.topo_res_rms = QLineEdit()
        self.topo_res_loss = QLineEdit()
        self.topo_res_dt = QLineEdit()
        self.topo_res_tcore = QLineEdit()
        self.topo_res_formula = QLineEdit()
        for w in [self.topo_res_rms, self.topo_res_loss, self.topo_res_dt, self.topo_res_tcore, self.topo_res_formula]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #1e8449;")
        r.addWidget(QLabel("Capacitor RMS current:"), 0, 0); r.addWidget(self.topo_res_rms, 0, 1)
        r.addWidget(QLabel("ESR heating:"), 1, 0); r.addWidget(self.topo_res_loss, 1, 1)
        r.addWidget(QLabel("Estimated self-heating:"), 2, 0); r.addWidget(self.topo_res_dt, 2, 1)
        r.addWidget(QLabel("Estimated core temperature:"), 3, 0); r.addWidget(self.topo_res_tcore, 3, 1)
        r.addWidget(QLabel("Model used:"), 4, 0); r.addWidget(self.topo_res_formula, 4, 1)
        grp_res.setLayout(r)
        layout.addWidget(grp_res)

        self.topo_note = QTextBrowser()
        self.topo_note.setMinimumHeight(120)
        self.topo_note.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d5d8dc;")
        layout.addWidget(self.topo_note)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_topology_rms(self):
        try:
            mode = self.topo_mode.currentText()
            vin = float(self.topo_vin.text())
            vout = float(self.topo_vout.text())
            iout = float(self.topo_iout.text())
            duty_text = self.topo_duty.text().strip()
            duty = float(duty_text) / 100.0 if duty_text else None
            lir = float(self.topo_lir.text()) / 100.0
            m = float(self.topo_m.text())
            pf = float(self.topo_pf.text())
            esr = float(self.topo_esr.text()) * 1e-3
            rth = float(self.topo_rth.text())
            ta = float(self.topo_ta.text())
            if min(abs(vin), abs(vout), abs(iout), esr, rth) <= 0:
                raise ValueError

            formula = ""
            note = ""
            if mode == "Buck input capacitor":
                d = duty if duty is not None else vout / vin
                ic = iout * math.sqrt(max(d * (1.0 - d), 0.0))
                formula = "Icin = Iout * sqrt(D*(1-D))"
                note = "Worst case is near D=0.5. This is often the hottest capacitor in high-current buck designs."
            elif mode == "Buck output capacitor":
                delta_i = iout * lir
                ic = delta_i / math.sqrt(12.0)
                formula = "Icout = DeltaIL / sqrt(12)"
                note = "Ceramic caps handle ripple well, but effective capacitance and loop stability still need checking."
            elif mode == "Boost output capacitor":
                d = duty if duty is not None else max(0.0, 1.0 - vin / vout)
                ic = iout * math.sqrt(max(d / max(1.0 - d, 1e-9), 0.0))
                formula = "Icout = Iout * sqrt(D/(1-D))"
                note = "Boost output capacitor RMS rises quickly at high duty. Parallel low-ESR caps are common."
            elif mode == "Flyback output capacitor":
                d = duty if duty is not None else 0.45
                sec_duty = max(1.0 - d, 1e-9)
                ic = iout * math.sqrt(max(d / sec_duty, 0.0))
                formula = "Icout ~= Iout * sqrt(Doff_inverse - 1)"
                note = "Flyback output current is pulsed; verify with transformer turns ratio and diode current waveform."
            else:
                # Practical approximation for PWM inverter DC-link capacitor ripple.
                m = max(0.0, min(m, 1.2))
                pf = max(0.0, min(pf, 1.0))
                ic = iout * math.sqrt(max(0.25 + (m ** 2) / 12.0 - (m * pf) / (2.0 * math.sqrt(3.0)), 0.0))
                formula = "Ic_dc ~= Iphase * sqrt(1/4 + m^2/12 - m*PF/(2*sqrt(3)))"
                note = "Approximation for balanced three-phase sinusoidal PWM. Validate for discontinuous PWM or low PF."

            ploss = ic ** 2 * esr
            dt = ploss * rth
            tcore = ta + dt
            self.topo_res_rms.setText(f"{ic:.3f} A")
            self.topo_res_loss.setText(f"{ploss:.3f} W")
            self.topo_res_dt.setText(f"{dt:.1f} C")
            self.topo_res_tcore.setText(f"{tcore:.1f} C")
            self.topo_res_formula.setText(formula)

            if tcore >= 105:
                self.topo_res_tcore.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
            elif tcore >= 85:
                self.topo_res_tcore.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold;")
            else:
                self.topo_res_tcore.setStyleSheet("background-color: #e8f8f5; color: #1e8449; font-weight: bold;")
            self.topo_note.setHtml(
                f"{note}<br>Use the estimated core temperature as the T_core input/check for the lifetime tab."
            )
        except Exception:
            QMessageBox.warning(self, "Input error", "Please check topology RMS inputs.")

    # ==============================================================================
    # Tab 3: MLCC DC Bias Derating
    # ==============================================================================
    def init_mlcc_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 规格输入
        grp_spec = QGroupBox("1. MLCC 选型参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        # 封装选择
        self.mlcc_pkg_combo = QComboBox()
        self.pkg_data = {
            "1210 (3225) - 大尺寸": 0.5,
            "1206 (3216)": 1.0,
            "0805 (2012)": 2.5,
            "0603 (1608)": 4.5,
            "0402 (1005)": 8.0,
            "0201 (0603) - 极小": 15.0
        }
        for k in self.pkg_data.keys():
            self.mlcc_pkg_combo.addItem(k)
        self.mlcc_pkg_combo.setCurrentIndex(3) # Default 0603
        
        grid.addWidget(QLabel("封装尺寸 (Package):"), 0, 0); grid.addWidget(self.mlcc_pkg_combo, 0, 1)
        
        # 介质选择
        self.mlcc_diel_combo = QComboBox()
        self.mlcc_diel_combo.addItems(["X5R / X7R / X7S (High K)", "C0G / NP0 (Class I)"])
        grid.addWidget(QLabel("介质类型 (Dielectric):"), 0, 2); grid.addWidget(self.mlcc_diel_combo, 0, 3)
        
        # 参数
        self.mlcc_cnom = QLineEdit("10"); self.mlcc_cnom.setPlaceholderText("标称容值")
        grid.addWidget(QLabel("标称容值 [uF]:"), 1, 0); grid.addWidget(self.mlcc_cnom, 1, 1)
        
        self.mlcc_vrated = QLineEdit("50"); self.mlcc_vrated.setPlaceholderText("耐压")
        grid.addWidget(QLabel("额定电压 V_rated [V]:"), 1, 2); grid.addWidget(self.mlcc_vrated, 1, 3)
        
        # 工况
        self.mlcc_vdc = QLineEdit("24"); self.mlcc_vdc.setPlaceholderText("实际DC偏置")
        grid.addWidget(QLabel("DC 偏置电压 [V]:"), 2, 0); grid.addWidget(self.mlcc_vdc, 2, 1)
        
        grp_spec.setLayout(grid)
        layout.addWidget(grp_spec)
        
        # 按钮
        btn = QPushButton("估算有效容值 (Estimate C_eff)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_mlcc_bias)
        layout.addWidget(btn)
        
        # 2. 结果
        grp_res = QGroupBox("2. 估算结果 (Estimation)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.mlcc_res_ceff = QLineEdit()
        self.mlcc_res_drop = QLineEdit()
        self.mlcc_res_ratio = QLineEdit()
        
        # Row 1
        r_grid.addWidget(QLabel("有效容值 (C_eff):"), 0, 0)
        r_grid.addWidget(self.mlcc_res_ceff, 0, 1)
        r_grid.addWidget(QLabel("uF"), 0, 2)
        
        # Row 2
        r_grid.addWidget(QLabel("容量保持率:"), 1, 0)
        r_grid.addWidget(self.mlcc_res_ratio, 1, 1)
        r_grid.addWidget(QLabel("% (相对于标称值)"), 1, 2)
        
        # Row 3
        r_grid.addWidget(QLabel("衰减幅度:"), 2, 0)
        r_grid.addWidget(self.mlcc_res_drop, 2, 1)
        
        # 公式
        l_f = QLabel()
        l_f.setPixmap(self.render_formula(r'C_{eff} \approx \frac{C_{nom}}{1 + K_{pkg}(\frac{V_{dc}}{V_{rated}})^2}'))
        r_grid.addWidget(l_f, 0, 3, 3, 1)
        
        # Styles
        style_eff = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 16px;"
        style_warn = "background-color: #fdedec; font-weight: bold; color: #c0392b;"
        self.mlcc_res_ceff.setReadOnly(True); self.mlcc_res_ceff.setStyleSheet(style_eff)
        self.mlcc_res_drop.setReadOnly(True); self.mlcc_res_drop.setStyleSheet(style_warn)
        self.mlcc_res_ratio.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Info
        info_label = QLabel("注：此计算基于通用二类陶瓷电容 (Class II) 的饱和特性经验拟合。"
                            "不同厂家 (Murata/TDK/Samsung) 工艺差异巨大，精确值请务必查阅厂家提供的 'DC Bias Characteristics' 曲线。"
                            "对于高压高容应用，建议优先选择更大尺寸封装或更高耐压等级以减少衰减。")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_mlcc_bias(self):
        try:
            cnom = float(self.mlcc_cnom.text())
            vrated = float(self.mlcc_vrated.text())
            vdc = float(self.mlcc_vdc.text())
            
            if vrated <= 0: raise ValueError
            
            # C0G/NP0 Check
            is_c0g = (self.mlcc_diel_combo.currentIndex() == 1)
            
            ratio = 1.0
            
            if is_c0g:
                ratio = 1.0
                self.mlcc_res_drop.setText("无显著衰减 (C0G/NP0)")
            else:
                # High K (X7R/X5R)
                pkg_key = self.mlcc_pkg_combo.currentText()
                k_factor = self.pkg_data.get(pkg_key, 2.0)
                
                v_stress = vdc / vrated
                if v_stress > 1.0:
                    QMessageBox.warning(self, "过压警告", "DC 偏置电压超过了额定电压！")
                
                denominator = 1.0 + k_factor * (v_stress ** 2)
                ratio = 1.0 / denominator
                
                if ratio < 0.1: ratio = 0.1
                
                drop_pct = (1.0 - ratio) * 100
                self.mlcc_res_drop.setText(f"-{drop_pct:.1f} %")

            c_eff = cnom * ratio
            
            self.mlcc_res_ceff.setText(f"{c_eff:.2f} uF")
            self.mlcc_res_ratio.setText(f"{ratio*100:.1f}")
            
            if ratio < 0.5:
                self.mlcc_res_ratio.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
            elif ratio < 0.8:
                self.mlcc_res_ratio.setStyleSheet("background-color: #fef9e7; color: #d35400; font-weight: bold;")
            else:
                self.mlcc_res_ratio.setStyleSheet("background-color: #e8f8f5; color: green; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    # ==============================================================================
    # Tab 4: 掉电保持 & 超级电容 (Hold-up & Supercap) - 融合升级版
    # ==============================================================================
    def init_holdup_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能：计算 AC-DC 输入大电容或超级电容的恒功率放电时间。\n"
                      "适用场景：掉电保持 (Hold-up Time)、超级电容备份电源 (UPS)。\n"
                      "兼容特性：支持 ESR 压降修正（对大电流放电至关重要）。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 基础参数
        grp_param = QGroupBox("1. 电源与电容参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.hu_vin_min = QLineEdit("260"); self.hu_vin_min.setToolTip("断电时刻电容两端的起始电压 (V_start)")
        grid.addWidget(QLabel("起始电压 (V_start) [V]:"), 0, 0); grid.addWidget(self.hu_vin_min, 0, 1)
        
        self.hu_v_stop = QLineEdit("100"); self.hu_v_stop.setToolTip("DC-DC 停止工作的最低输入电压 (UVLO)")
        grid.addWidget(QLabel("停止工作电压 (V_stop/UVLO) [V]:"), 0, 2); grid.addWidget(self.hu_v_stop, 0, 3)
        
        self.hu_pout = QLineEdit("60"); self.hu_pout.setToolTip("负载功率 (恒功率负载)")
        grid.addWidget(QLabel("输出功率 (P_out) [W]:"), 1, 0); grid.addWidget(self.hu_pout, 1, 1)
        
        self.hu_eff = QLineEdit("0.85"); self.hu_eff.setToolTip("后级变换器效率 (0~1)")
        grid.addWidget(QLabel("变换器效率 (η):"), 1, 2); grid.addWidget(self.hu_eff, 1, 3)
        
        self.hu_esr = QLineEdit("0.0"); self.hu_esr.setToolTip("电容 ESR [Ω]。\nAC-DC 母线电容通常可忽略(设为0)。\n超级电容必须填！")
        grid.addWidget(QLabel("电容 ESR [Ω] (Supercap必填):"), 2, 0); grid.addWidget(self.hu_esr, 2, 1)
        
        grp_param.setLayout(grid)
        layout.addWidget(grp_param)
        
        # 2. 计算目标
        grp_calc = QGroupBox("2. 计算目标选择")
        vbox_mode = QVBoxLayout()
        
        self.hu_mode_group = QButtonGroup(self)
        self.rb_calc_cap = QRadioButton("已知目标保持时间 -> 计算所需电容 (Calc C)")
        self.rb_calc_time = QRadioButton("已知电容值 -> 计算保持时间 (Calc Time)")
        self.rb_calc_cap.setChecked(True)
        self.hu_mode_group.addButton(self.rb_calc_cap)
        self.hu_mode_group.addButton(self.rb_calc_time)
        
        hbox_rb = QHBoxLayout()
        hbox_rb.addWidget(self.rb_calc_cap)
        hbox_rb.addWidget(self.rb_calc_time)
        vbox_mode.addLayout(hbox_rb)
        
        # 动态输入区
        self.hu_target_stack = QGridLayout()
        self.lbl_hu_target = QLabel("目标保持时间 (T_hold) [ms]:")
        self.hu_target_val = QLineEdit("20")
        self.hu_target_stack.addWidget(self.lbl_hu_target, 0, 0)
        self.hu_target_stack.addWidget(self.hu_target_val, 0, 1)
        
        vbox_mode.addLayout(self.hu_target_stack)
        
        # 绑定切换事件
        self.hu_mode_group.buttonClicked.connect(self.update_holdup_mode)
        
        grp_calc.setLayout(vbox_mode)
        layout.addWidget(grp_calc)
        
        # 按钮
        btn = QPushButton("计算 Hold-up Time / 电容")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_holdup)
        layout.addWidget(btn)
        
        # 3. 结果
        grp_res = QGroupBox("3. 计算结果")
        res_layout = QGridLayout()
        res_layout.setColumnStretch(1, 1)
        
        self.hu_res_val = QLineEdit()
        self.hu_res_val.setReadOnly(True)
        self.hu_res_val.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; background-color: #e8f8f5;")
        
        self.hu_res_drop = QLineEdit()
        self.hu_res_drop.setReadOnly(True)
        self.hu_res_drop.setStyleSheet("color: #c0392b; font-weight: bold;")
        
        res_layout.addWidget(QLabel("计算结果:"), 0, 0); res_layout.addWidget(self.hu_res_val, 0, 1)
        res_layout.addWidget(QLabel("ESR 最大压降:"), 1, 0); res_layout.addWidget(self.hu_res_drop, 1, 1)
        
        # 公式显示
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r't = \frac{0.5 \cdot C \cdot (V_{start}^2 - (V_{stop} + I_{max}R)^2)}{P_{load}/\eta}'))
        res_layout.addWidget(l_form, 0, 2, 2, 1)
        
        grp_res.setLayout(res_layout)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def update_holdup_mode(self):
        if self.rb_calc_cap.isChecked():
            self.lbl_hu_target.setText("目标保持时间 (T_hold) [ms]:")
            self.hu_target_val.setText("20")
        else:
            self.lbl_hu_target.setText("已知电容值 (C_total) [uF]:")
            self.hu_target_val.setText("100")

    def calc_holdup(self):
        try:
            v_start = float(self.hu_vin_min.text())
            v_stop = float(self.hu_v_stop.text())
            p_out = float(self.hu_pout.text())
            eff = float(self.hu_eff.text())
            esr = float(self.hu_esr.text())
            target_val = float(self.hu_target_val.text())
            
            if v_start <= v_stop:
                QMessageBox.warning(self, "电压错误", "起始电压 V_start 必须大于停止电压 V_stop")
                return
            if p_out <= 0 or eff <= 0 or target_val <= 0:
                raise ValueError("参数必须大于0")
                
            p_in = p_out / eff
            
            # --- ESR Impact Analysis ---
            # Max current occurs at the lowest voltage (V_stop).
            # I_max_avg = P_in / V_stop
            # Voltage Drop V_drop = I_max_avg * ESR
            # The internal capacitor voltage V_cap_internal must be V_stop + V_drop
            # So effective stop voltage is V_stop_eff = V_stop + I * ESR
            # But I depends on V_terminal (V_stop).
            
            i_max = p_in / v_stop
            v_drop = i_max * esr
            v_stop_eff = v_stop + v_drop
            
            self.hu_res_drop.setText(f"{v_drop:.3f} V (at {i_max:.2f}A)")
            
            if v_stop_eff >= v_start:
                self.hu_res_val.setText("无法满足 (ESR压降过大)")
                self.hu_res_val.setStyleSheet("font-size: 18px; font-weight: bold; color: white; background-color: #e74c3c;")
                QMessageBox.warning(self, "失败", 
                                    f"ESR 压降 ({v_drop:.2f}V) 导致有效截止电压 ({v_stop_eff:.2f}V) 超过了起始电压 ({v_start}V)。\n"
                                    "电容一放电，端电压就会立刻跌落到 UVLO 以下。\n"
                                    "请减小 ESR、降低功率或提高起始电压。")
                return
            else:
                self.hu_res_val.setStyleSheet("font-size: 18px; font-weight: bold; color: #27ae60; background-color: #e8f8f5;")

            # Energy available = 0.5 * C * (V_start^2 - V_stop_eff^2)
            delta_v_sq = (v_start ** 2) - (v_stop_eff ** 2)
            
            if self.rb_calc_cap.isChecked():
                # Calc C given T(ms)
                t_sec = target_val / 1000.0
                # E = P * t = 0.5 * C * dv2
                # C = 2 * P * t / dv2
                c_farad = (2 * p_in * t_sec) / delta_v_sq
                
                # Format
                if c_farad >= 1.0:
                    self.hu_res_val.setText(f"所需电容 C = {c_farad:.3f} F")
                else:
                    self.hu_res_val.setText(f"所需电容 C = {c_farad*1e6:.1f} uF")
                    
            else:
                # Calc T(ms) given C(uF/F ?)
                # Input assumes uF for consistency with old layout, but supercap implies F.
                c_input_val = target_val
                # If user thinks in Farads, they might enter 1.0. 
                # If user thinks in uF, they enter 1000000.
                # Let's strictly follow label [uF].
                c_farad = c_input_val * 1e-6
                
                energy_avail = 0.5 * c_farad * delta_v_sq
                t_sec = energy_avail / p_in
                
                if t_sec < 1.0:
                    self.hu_res_val.setText(f"保持时间 T = {t_sec*1000:.2f} ms")
                else:
                    self.hu_res_val.setText(f"保持时间 T = {t_sec:.3f} s")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("电容应用与选型指南")
        dialog.resize(850, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 使用原生字符串 r"" 避免转义字符警告
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 20px;}
            h3 { color: #e67e22; margin-top: 15px; font-weight: bold; }
            li { margin-bottom: 8px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
            .warn { color: #c0392b; font-weight: bold; }
            .box { background-color: #e8f6f3; padding: 10px; border-left: 5px solid #1abc9c; }
        </style>
        
        <h1>1. 掉电保持 & 超级电容 (Supercap Backup)</h1>
        <p>在电源断电后，依靠电容存储的能量维持系统运行一段时间。负载通常通过 DC-DC 供电，表现为<b>恒功率负载 (Constant Power Load)</b>。</p>
        
        <h3>核心公式 (能量守恒)</h3>
        <p><code>0.5 * C * (V_{start}^2 - V_{cutoff}^2) = P_{in} * t</code></p>
        
        <h3>ESR 的致命影响 (Voltage Drop)</h3>
        <p>对于超级电容或大电流应用，ESR 不可忽略。当负载电流流过时，电容内阻会产生压降 $V_{drop} = I \cdot ESR$。</p>
        <ul>
            <li>这意味着端电压会比电容内部电势低。</li>
            <li>当端电压触及 UVLO ($V_{stop}$) 时，电容内部其实还剩 $V_{stop} + V_{drop}$ 的电压，这部分能量无法被利用！</li>
            <li><b>计算修正：</b> 本工具已包含此修正。若 $I \cdot ESR$ 过大，可能导致系统一断电就因压降直接触发欠压关机。</li>
        </ul>

        <hr>

        <h1>2. 铝电解电容寿命估算</h1>
        <p>基于经典的<b>阿伦尼乌斯 (Arrhenius) 定律</b>（10度法则）：</p>
        <p><code>L = L0 * 2^((T0 - Tm)/10)</code></p>
        <ul>
            <li><b>核心温度 Tm:</b> 是环境温度与纹波电流自热温升之和。</li>
            <li><b>建议：</b> 设计寿命应留有余量，避免电容成为系统短板。</li>
        </ul>

        <hr>

        <h1>3. MLCC 直流偏置特性 (DC Bias)</h1>
        <p><b>陷阱：</b> 高介电常数 MLCC (X7R/X5R) 的容值会随直流电压升高而大幅衰减。</p>
        <div class="box">
            <b>案例：</b> 一个 0805 10uF/25V 的 X5R 电容，在 12V 偏置下，有效容值可能只剩 3uF (-70%)！
        </div>
        <p>在设计滤波器、环路补偿或定时电路时，必须使用<b>有效容值</b>。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()
