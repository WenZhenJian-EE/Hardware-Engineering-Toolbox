from modules.base_module import BaseModule
# analog_pwm_tool.py

import sys
import math
import matplotlib.pyplot as plt
from io import BytesIO

# 补全了必要的 PyQt5 组件，确保独立运行不报错
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QComboBox, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

class PwmToolWindow(BaseModule):
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "PWM & MCU & IC"
    description = "DAC滤波 / MCU定时器 / IC频率"
    window_id = "analog_pwm"

    def init_module_ui(self):
        
        self.init_ui()

    # 内置公式渲染函数 (无需依赖 utils.py)
    def init_ui(self):
        self.setWindowTitle('PWM 工具箱 (DAC 滤波 & MCU 配置 & 芯片 R/C)')
        self.setGeometry(300, 300, 950, 750)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("原理与公式说明")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(180)
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

        self.tab_filter = QWidget()
        self.tab_mcu = QWidget()
        self.tab_ic = QWidget() # New Tab: IC Freq Calc

        self.init_filter_ui(self.tab_filter)
        self.init_mcu_ui(self.tab_mcu)
        self.init_ic_ui(self.tab_ic)

        self.tabs.addTab(self.tab_filter, "1. PWM DAC 滤波器设计")
        self.tabs.addTab(self.tab_mcu, "2. MCU 定时器配置 (Timer Calc)")
        self.tabs.addTab(self.tab_ic, "3. 常用 PWM 芯片频率 (IC Freq)") 

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # -----------------------------------------------------------
    # Tab 1: Filter Design (Original Functionality)
    # -----------------------------------------------------------
    def init_filter_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Inputs
        grp_param = QGroupBox("1. PWM 系统参数 (System Parameters)")
        grid_param = QGridLayout()
        grid_param.setVerticalSpacing(15)

        self.in_freq = QLineEdit("10000"); grid_param.addWidget(QLabel("PWM 频率 (Hz):"), 0, 0); grid_param.addWidget(self.in_freq, 0, 1)
        self.in_vref = QLineEdit("3.3");   grid_param.addWidget(QLabel("PWM 电平 Vcc (V):"), 0, 2); grid_param.addWidget(self.in_vref, 0, 3)
        self.in_bits = QLineEdit("8");     grid_param.addWidget(QLabel("分辨率 (Bits):"), 1, 0); grid_param.addWidget(self.in_bits, 1, 1)
        
        self.combo_c = QComboBox()
        self.combo_c.addItems(["100pF", "1nF", "10nF", "100nF", "1uF", "10uF"])
        self.combo_c.setCurrentText("100nF")
        grid_param.addWidget(QLabel("选用电容 C (参考):"), 1, 2); grid_param.addWidget(self.combo_c, 1, 3)

        grp_param.setLayout(grid_param)
        layout.addWidget(grp_param)

        grp_target = QGroupBox("2. 设计约束 (Design Constraints)")
        grid_target = QGridLayout()
        grid_target.setVerticalSpacing(15)
        self.in_ripple = QLineEdit("3.3"); self.in_ripple.setPlaceholderText("例如 3.3")
        grid_target.addWidget(QLabel("目标最大纹波 Vpp (mV):"), 0, 0); grid_target.addWidget(self.in_ripple, 0, 1)
        self.in_settle = QLineEdit("10"); 
        grid_target.addWidget(QLabel("目标建立时间 T_settle (ms):"), 0, 2); grid_target.addWidget(self.in_settle, 0, 3)
        grp_target.setLayout(grid_target)
        layout.addWidget(grp_target)

        btn_calc = QPushButton("计算并推荐滤波器电路")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calculate_filter)
        layout.addWidget(btn_calc)

        grp_res = QGroupBox("3. 推荐电路与性能分析 (Result)")
        self.res_layout = QVBoxLayout()
        self.lbl_recommend = QLabel("等待计算...")
        self.lbl_recommend.setStyleSheet("font-size: 16px; font-weight: bold; color: #555; padding: 5px;")
        self.res_layout.addWidget(self.lbl_recommend)
        
        grid_res = QGridLayout()
        self.out_topo = QLineEdit(); grid_res.addWidget(QLabel("电路结构:"), 0, 0); grid_res.addWidget(self.out_topo, 0, 1)
        self.out_r_val = QLineEdit(); grid_res.addWidget(QLabel("推荐电阻 R:"), 0, 2); grid_res.addWidget(self.out_r_val, 0, 3)
        self.out_ripple = QLineEdit(); grid_res.addWidget(QLabel("实际纹波 Vpp:"), 1, 0); grid_res.addWidget(self.out_ripple, 1, 1)
        self.out_settle = QLineEdit(); grid_res.addWidget(QLabel("实际建立时间:"), 1, 2); grid_res.addWidget(self.out_settle, 1, 3)
        self.out_fc = QLineEdit(); grid_res.addWidget(QLabel("截止频率 (-3dB):"), 2, 0); grid_res.addWidget(self.out_fc, 2, 1)
        self.out_lsb = QLineEdit(); grid_res.addWidget(QLabel("1 LSB 电压:"), 2, 2); grid_res.addWidget(self.out_lsb, 2, 3)

        style_res = "background-color: #f4f6f6; color: #2c3e50; font-weight: bold;"
        for w in [self.out_topo, self.out_r_val, self.out_ripple, self.out_settle, self.out_fc, self.out_lsb]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
        self.res_layout.addLayout(grid_res)
        self.lbl_note = QLabel(""); self.lbl_note.setWordWrap(True)
        self.lbl_note.setStyleSheet("color: #e67e22; font-style: italic; margin-top: 10px;")
        self.res_layout.addWidget(self.lbl_note)
        grp_res.setLayout(self.res_layout)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    # -----------------------------------------------------------
    # Tab 2: MCU Timer & PWM Calculation
    # -----------------------------------------------------------
    def init_mcu_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Clock Settings
        grp_clk = QGroupBox("1. 时钟与频率设置 (Clock & Frequency)")
        grid_clk = QGridLayout()
        grid_clk.setVerticalSpacing(15)
        
        self.mcu_sysclk = QLineEdit("168"); self.mcu_sysclk.setToolTip("定时器输入时钟频率 (Timer Clock)")
        grid_clk.addWidget(QLabel("定时器主频 (SysClk) [MHz]:"), 0, 0); grid_clk.addWidget(self.mcu_sysclk, 0, 1)
        
        self.mcu_fsw = QLineEdit("20"); self.mcu_fsw.setToolTip("目标 PWM 开关频率")
        grid_clk.addWidget(QLabel("目标开关频率 (Fsw) [kHz]:"), 0, 2); grid_clk.addWidget(self.mcu_fsw, 0, 3)
        
        self.mcu_mode = QComboBox()
        self.mcu_mode.addItems(["向上/向下计数 (Edge Aligned)", "中心对齐 (Center Aligned / Up-Down)"])
        grid_clk.addWidget(QLabel("计数模式 (Counting Mode):"), 1, 0); grid_clk.addWidget(self.mcu_mode, 1, 1, 1, 3)
        
        grp_clk.setLayout(grid_clk)
        layout.addWidget(grp_clk)
        
        # 2. Deadtime Settings
        grp_dt = QGroupBox("2. 死区时间设置 (Deadtime)")
        grid_dt = QGridLayout()
        self.mcu_dt_ns = QLineEdit("500"); self.mcu_dt_ns.setToolTip("需要的死区时间 (纳秒)")
        grid_dt.addWidget(QLabel("目标死区时间 (DT) [ns]:"), 0, 0); grid_dt.addWidget(self.mcu_dt_ns, 0, 1)
        grp_dt.setLayout(grid_dt)
        layout.addWidget(grp_dt)
        
        btn_calc = QPushButton("计算寄存器配置 (ARR, Prescaler, DT)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_mcu_timer)
        layout.addWidget(btn_calc)
        
        # 3. Results
        grp_res = QGroupBox("3. 寄存器配置参考 (Register Values)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.res_arr = QLineEdit()
        self.res_psc = QLineEdit("0 (1:1)")
        self.res_dt_ticks = QLineEdit()
        self.res_real_fsw = QLineEdit()
        self.res_res_bits = QLineEdit()
        self.res_step_ns = QLineEdit()
        
        # ARR / Period
        r_grid.addWidget(QLabel("周期寄存器值 (ARR / Period):"), 0, 0); r_grid.addWidget(self.res_arr, 0, 1)
        l_arr = QLabel(); l_arr.setPixmap(self.render_formula(r'ARR = \frac{SysClk}{F_{sw}} - 1 \quad or \quad \frac{SysClk}{2 \cdot F_{sw}}')); 
        r_grid.addWidget(l_arr, 0, 2)
        
        # Deadtime
        r_grid.addWidget(QLabel("死区 Tick 数 (DTG/DB):"), 1, 0); r_grid.addWidget(self.res_dt_ticks, 1, 1)
        l_dt = QLabel(); l_dt.setPixmap(self.render_formula(r'DT_{ticks} = DT_{ns} \cdot SysClk'));
        r_grid.addWidget(l_dt, 1, 2)
        
        # Resolution
        r_grid.addWidget(QLabel("PWM 有效分辨率 (Bits):"), 2, 0); r_grid.addWidget(self.res_res_bits, 2, 1)
        l_res = QLabel(); l_res.setPixmap(self.render_formula(r'Bits = \log_2(ARR + 1)'));
        r_grid.addWidget(l_res, 2, 2)
        
        # Step
        r_grid.addWidget(QLabel("最小调节步长 (Time Step):"), 3, 0); r_grid.addWidget(self.res_step_ns, 3, 1)
        
        style = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad;"
        for w in [self.res_arr, self.res_dt_ticks, self.res_real_fsw, self.res_res_bits, self.res_step_ns, self.res_psc]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    # -----------------------------------------------------------
    # Tab 3: Common PWM IC Frequency Calculator (NEW)
    # -----------------------------------------------------------
    def init_ic_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Config
        grp_cfg = QGroupBox("1. 芯片与目标频率")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)

        self.ic_combo = QComboBox()
        self.ic_data = {
            "UC3842 / UC3843 / UC284x": {"formula_desc": "Fsw = Fosc", "mult": 1.0, "eq": r'F_{osc} = \frac{1.72}{R_T C_T}'},
            "UC3844 / UC3845 (Max Duty 50%)": {"formula_desc": "Fsw = Fosc / 2", "mult": 2.0, "eq": r'F_{osc} = \frac{1.72}{R_T C_T}'},
            "TL494 / KA7500 (Push-Pull)": {"formula_desc": "Fsw = Fosc / 2", "mult": 2.0, "eq": r'F_{osc} = \frac{1.1}{R_T C_T}'},
            "SG3525 / KA3525 (Push-Pull)": {"formula_desc": "Fsw = Fosc / 2, ignore Rd", "mult": 2.0, "eq": r'F_{osc} \approx \frac{1}{0.7 R_T C_T}'},
            "NCP1252 (Current Mode)": {"formula_desc": "Fixed R, C internal", "mult": 1.0, "eq": r'F_{sw}(kHz) = \frac{6250}{R_T(k\Omega)}', "type": "R_only"}
        }
        self.ic_combo.addItems(list(self.ic_data.keys()))
        self.ic_combo.currentIndexChanged.connect(self.update_ic_formula)
        
        grid.addWidget(QLabel("选择 PWM 芯片:"), 0, 0); grid.addWidget(self.ic_combo, 0, 1)

        self.ic_fsw = QLineEdit("50")
        grid.addWidget(QLabel("目标开关频率 Fsw [kHz]:"), 0, 2); grid.addWidget(self.ic_fsw, 0, 3)

        grp_cfg.setLayout(grid)
        layout.addWidget(grp_cfg)

        # Formula Display
        self.ic_formula_lbl = QLabel()
        self.ic_formula_lbl.setAlignment(Qt.AlignCenter)
        self.ic_formula_lbl.setFixedHeight(60)
        self.ic_formula_lbl.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; margin: 5px;")
        layout.addWidget(self.ic_formula_lbl)

        btn = QPushButton("计算推荐 R/C 组合")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_ic_rc)
        layout.addWidget(btn)

        # 2. Results Table
        grp_res = QGroupBox("2. 推荐元件值 (Recommended Values)")
        vbox_res = QVBoxLayout()
        self.ic_table = QTableWidget(0, 4)
        self.ic_table.setHorizontalHeaderLabels(["电容 Ct (推荐)", "理论电阻 Rt", "最近标准电阻 (E24/E96)", "实际 Fsw (kHz)"])
        self.ic_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vbox_res.addWidget(self.ic_table)
        grp_res.setLayout(vbox_res)
        layout.addWidget(grp_res)

        self.update_ic_formula() # Init label
        tab.setLayout(layout)

    def update_ic_formula(self):
        key = self.ic_combo.currentText()
        data = self.ic_data[key]
        self.ic_formula_lbl.setPixmap(self.render_formula(data['eq'] + r'\quad (' + data['formula_desc'] + r')'))

    def calc_ic_rc(self):
        try:
            fsw_target = float(self.ic_fsw.text()) * 1e3 # Hz
            key = self.ic_combo.currentText()
            data = self.ic_data[key]
            
            # F_osc needed
            f_osc_target = fsw_target * data['mult']
            
            self.ic_table.setRowCount(0)
            
            # Special case for R-only chips (like NCP1252)
            if "type" in data and data["type"] == "R_only":
                # NCP1252: Fsw(kHz) = 6250 / Rt(k) -> Rt(k) = 6250 / Fsw(kHz)
                # Formula uses Fsw directly usually, let's check dict
                # My dict says Fsw(kHz) = ... so use fsw_target in kHz
                fsw_khz = fsw_target / 1000.0
                rt_k = 6250.0 / fsw_khz
                rt_val = rt_k * 1000.0
                
                row = 0
                self.ic_table.insertRow(row)
                self.ic_table.setItem(row, 0, QTableWidgetItem("Internal"))
                self.ic_table.setItem(row, 1, QTableWidgetItem(f"{rt_k:.2f} kΩ"))
                
                std_r = self.find_nearest_resistor(rt_val)
                self.ic_table.setItem(row, 2, QTableWidgetItem(f"{std_r/1000:.2f} kΩ"))
                
                # Recalc actual freq
                # F = 6250 / R_k
                real_f = 6250.0 / (std_r/1000.0)
                self.ic_table.setItem(row, 3, QTableWidgetItem(f"{real_f:.2f} kHz"))
                return

            # Standard RC chips
            # List of standard capacitors to try
            caps = [100e-12, 220e-12, 330e-12, 470e-12, 
                    1e-9, 2.2e-9, 3.3e-9, 4.7e-9, 
                    10e-9]
            
            row_idx = 0
            for ct in caps:
                # Calculate required Rt based on chip formula
                # 1. UC384x: F = 1.72 / (R C) -> R = 1.72 / (F C)
                # 2. TL494: F = 1.1 / (R C) -> R = 1.1 / (F C)
                # 3. SG3525: F = 1 / (0.7 R C) -> R = 1 / (0.7 F C)
                
                rt = 0
                if "UC384" in key:
                    rt = 1.72 / (f_osc_target * ct)
                elif "TL494" in key:
                    rt = 1.1 / (f_osc_target * ct)
                elif "SG3525" in key:
                    rt = 1.0 / (0.7 * f_osc_target * ct)
                
                # Filter unreasonable R values (e.g. < 500 Ohm or > 500k usually not ideal)
                if 500 < rt < 500000:
                    self.ic_table.insertRow(row_idx)
                    
                    # Cap String
                    c_str = f"{ct*1e9:.1f} nF" if ct >= 1e-9 else f"{ct*1e12:.0f} pF"
                    self.ic_table.setItem(row_idx, 0, QTableWidgetItem(c_str))
                    
                    # Theo R
                    self.ic_table.setItem(row_idx, 1, QTableWidgetItem(f"{rt/1000:.2f} kΩ"))
                    
                    # Std R
                    std_r = self.find_nearest_resistor(rt)
                    self.ic_table.setItem(row_idx, 2, QTableWidgetItem(f"{std_r/1000:.2f} kΩ"))
                    
                    # Real Fsw
                    real_f_osc = 0
                    if "UC384" in key: real_f_osc = 1.72 / (std_r * ct)
                    elif "TL494" in key: real_f_osc = 1.1 / (std_r * ct)
                    elif "SG3525" in key: real_f_osc = 1.0 / (0.7 * std_r * ct)
                    
                    real_fsw = real_f_osc / data['mult']
                    self.ic_table.setItem(row_idx, 3, QTableWidgetItem(f"{real_fsw/1000:.2f} kHz"))
                    
                    row_idx += 1
            
            if row_idx == 0:
                QMessageBox.information(self, "提示", "未找到合适的 RC 组合，请尝试更改频率范围。")

        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的频率数值")

    # --- Helpers ---
    def parse_input_c(self):
        txt = self.combo_c.currentText()
        val = 100e-9 
        try:
            if "pF" in txt: val = float(txt.replace("pF", "")) * 1e-12
            elif "uF" in txt: val = float(txt.replace("uF", "")) * 1e-6
            elif "nF" in txt: val = float(txt.replace("nF", "")) * 1e-9
        except: pass
        return val

    def find_nearest_resistor(self, r_ohm):
        if r_ohm <= 0: return 0
        e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
        power = math.floor(math.log10(r_ohm))
        base = r_ohm / (10**power)
        nearest = min(e24, key=lambda x: abs(x - base))
        return nearest * (10**power)

    # --- Calculation Logic: Filter ---
    def calculate_filter(self):
        try:
            f_pwm = float(self.in_freq.text())
            v_cc = float(self.in_vref.text())
            bits = float(self.in_bits.text())
            v_rip_target = float(self.in_ripple.text()) / 1000.0
            t_set_target = float(self.in_settle.text()) / 1000.0
            c_sel = self.parse_input_c()

            if f_pwm <= 0 or v_cc <= 0 or v_rip_target <= 0: raise ValueError

            lsb_voltage = v_cc / (2**bits)
            self.out_lsb.setText(f"{lsb_voltage*1000:.2f} mV")

            rc_min_ripple_1st = v_cc / (4.0 * f_pwm * v_rip_target)
            rc_max_settle = t_set_target / (bits * 0.693)

            use_2nd_order = False
            tau_final = 0.0
            topo_str = ""

            if rc_min_ripple_1st <= rc_max_settle:
                topo_str = "一阶 RC (1st Order RC)"
                tau_final = math.sqrt(rc_min_ripple_1st * rc_max_settle)
                r_final = tau_final / c_sel
                self.lbl_recommend.setText("✅ 推荐方案：一阶 RC 滤波器")
                self.lbl_recommend.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; padding: 5px;")
                self.lbl_note.setText("需求可用一阶 RC 满足。")
            else:
                rc_sq = v_cc / (8.0 * math.pi * (f_pwm**2) * v_rip_target)
                rc_min_ripple_2nd = math.sqrt(rc_sq)
                t_est_2nd = 1.5 * rc_min_ripple_2nd * bits * 0.693
                topo_str = "二阶 RC (2nd Order RC)"
                use_2nd_order = True
                
                if t_est_2nd <= t_set_target:
                    tau_final = rc_min_ripple_2nd
                    r_final = tau_final / c_sel
                    self.lbl_recommend.setText("⚠️ 推荐方案：二阶 RC 滤波器")
                    self.lbl_recommend.setStyleSheet("font-size: 16px; font-weight: bold; color: #d35400; padding: 5px;")
                    self.lbl_note.setText("需使用二阶 RC (R1=R2, C1=C2)。建议加运放跟随。")
                else:
                    tau_final = rc_min_ripple_2nd
                    r_final = tau_final / c_sel
                    self.lbl_recommend.setText("❌ 警告：物理限制")
                    self.lbl_recommend.setStyleSheet("font-size: 16px; font-weight: bold; color: #c0392b; padding: 5px;")
                    self.lbl_note.setText("需求过高，建议提高 PWM 频率或降低分辨率。")

            r_disp = self.find_nearest_resistor(r_final)
            tau_real = r_disp * c_sel
            
            if not use_2nd_order:
                v_pp_real = v_cc / (4.0 * f_pwm * tau_real)
                t_set_real = tau_real * bits * 0.693
                fc = 1.0 / (2.0 * math.pi * tau_real)
            else:
                v_pp_real = v_cc / (8.0 * math.pi * (f_pwm**2) * (tau_real**2))
                t_set_real = 1.5 * tau_real * bits * 0.693
                fc = 1.0 / (2.0 * math.pi * tau_real)

            self.out_topo.setText(topo_str)
            self.out_r_val.setText(f"{r_disp/1000.0:.2f} kΩ" if r_disp >= 1000 else f"{r_disp:.1f} Ω")
            
            style_res = "background-color: #f4f6f6; font-weight: bold;"
            self.out_ripple.setText(f"{v_pp_real*1000:.2f} mV")
            self.out_ripple.setStyleSheet(style_res + ("color: red;" if v_pp_real > v_rip_target else "color: green;"))
            self.out_settle.setText(f"{t_set_real*1000:.1f} ms")
            self.out_settle.setStyleSheet(style_res + ("color: red;" if t_set_real > t_set_target else "color: green;"))
            self.out_fc.setText(f"{fc:.1f} Hz")

        except Exception as e:
            QMessageBox.warning(self, "输入错误", "请输入有效的数字参数")

    # --- Calculation Logic: MCU Timer ---
    def calc_mcu_timer(self):
        try:
            sysclk_mhz = float(self.mcu_sysclk.text())
            fsw_khz = float(self.mcu_fsw.text())
            dt_ns = float(self.mcu_dt_ns.text())
            mode = self.mcu_mode.currentIndex() # 0: Edge, 1: Center
            
            if sysclk_mhz <= 0 or fsw_khz <= 0: raise ValueError
            
            sysclk = sysclk_mhz * 1e6
            fsw = fsw_khz * 1e3
            
            # 1. ARR Calculation
            if mode == 0: # Edge Aligned
                arr_val = (sysclk / fsw) - 1
            else: # Center Aligned
                arr_val = sysclk / (2 * fsw)
            
            arr_int = int(round(arr_val))
            
            # 2. Deadtime Calculation (Ticks)
            dt_ticks = dt_ns * 1e-9 * sysclk
            dt_ticks_int = int(round(dt_ticks))
            
            # 3. Resolution (Bits)
            res_bits = math.log2(arr_int) if arr_int > 0 else 0
            
            # 4. Time Step per Tick
            step_ns = (1.0 / sysclk) * 1e9
            
            self.res_arr.setText(f"{arr_int}")
            self.res_dt_ticks.setText(f"{dt_ticks_int} ({dt_ticks_int * step_ns:.0f} ns)")
            self.res_res_bits.setText(f"{res_bits:.2f} Bits ({int(2**res_bits)} steps)")
            self.res_step_ns.setText(f"{step_ns:.2f} ns")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效数值")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("PWM & MCU & IC 助手指南")
        dialog.resize(800, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; font-size: 16px;}
            li { margin-bottom: 5px; }
            .box { background-color: #ecf0f1; padding: 10px; border-left: 5px solid #bdc3c7; }
        </style>
        
        <h1>1. PWM DAC 滤波器设计指南</h1>
        <p>利用 PWM 的占空比来产生模拟电压。RC 滤波器的作用是将 PWM 方波中的交流分量滤除，只保留直流平均值。</p>
        
        <h3>核心矛盾：纹波 vs 速度</h3>
        <ul>
            <li><b>RC 越大：</b> 纹波越小，但响应建立时间越慢。</li>
            <li><b>RC 越小：</b> 响应快，但纹波大。</li>
        </ul>
        <p>本工具会自动权衡这两个指标，优先推荐一阶 RC。如果一阶无法同时满足纹波和时间要求，则推荐二阶 RC。</p>

        <hr>

        <h1>2. MCU 定时器配置 (Timer Calc)</h1>
        <p>用于快速计算 STM32, C2000, DSP 等微控制器的 PWM 寄存器值。</p>
        <p><b>公式：</b>Edge Aligned: $ARR = \frac{SysClk}{F_{sw}} - 1$. Center Aligned: $ARR = \frac{SysClk}{2 F_{sw}}$.</p>

        <hr>

        <h1>3. 通用 PWM 芯片频率设定</h1>
        <div class="box">
            <b>设计痛点：</b> 每次设计模拟电源（如 Flyback, Push-Pull）时，计算 RT/CT 都需要翻阅数据手册。
        </div>
        <h3>支持芯片：</h3>
        <ul>
            <li><b>UC3842/3/4/5:</b> 经典电流模式 PWM。注意 3844/45 内部有触发器，开关频率是振荡频率的一半。</li>
            <li><b>TL494 / KA7500:</b> 电压模式控制。推挽模式下，输出频率也是振荡频率的一半。</li>
            <li><b>SG3525:</b> 内置死区设置。本工具忽略死区电阻 Rd 的影响（假设 Rd 较小），做快速估算。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        btn = QPushButton("关闭")
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn)
        
        dialog.exec_()
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PwmToolWindow()
    window.show()
    sys.exit(app.exec_())