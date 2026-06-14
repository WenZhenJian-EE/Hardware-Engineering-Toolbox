from modules.base_module import BaseModule
# ct_design_window.py

import math
import matplotlib.pyplot as plt
from io import BytesIO

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class CtDesignWindow(BaseModule):
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "电流检测设计"
    description = "CT互感器 / Shunt分流器"
    window_id = "sense_ct"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('电流检测设计工具 (CT & Shunt Calculator)')
        self.setGeometry(350, 350, 950, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计原理与指南 (CT & Shunt)")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(250)
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

        # Tab 1: CT Calculator
        self.tab_calc = QWidget()
        self.init_ct_ui(self.tab_calc)
        self.tabs.addTab(self.tab_calc, "互感器(CT) 设计与校核")

        # Tab 2: Shunt Resistor Calculator
        self.tab_shunt = QWidget()
        self.init_shunt_ui(self.tab_shunt)
        self.tabs.addTab(self.tab_shunt, "分流器(Shunt) 误差分析")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 采样电阻计算 & 饱和校核 (CT)
    # ==============================================================================
    def init_ct_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 采样需求参数
        grp_req = QGroupBox("1. 采样需求与 CT 参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.ct_ipri = QLineEdit("50"); grid.addWidget(QLabel("最大初级电流 I_pri_rms [A]:"), 0, 0); grid.addWidget(self.ct_ipri, 0, 1)
        self.ct_ratio = QLineEdit("1000"); grid.addWidget(QLabel("CT 匝比 (1:N) N:"), 0, 2); grid.addWidget(self.ct_ratio, 0, 3)
        self.ct_freq = QLineEdit("50"); grid.addWidget(QLabel("工作频率 f [Hz]:"), 1, 0); grid.addWidget(self.ct_freq, 1, 1)
        self.ct_vout_pk = QLineEdit("1.65"); 
        self.ct_vout_pk.setToolTip("ADC 输入允许的最大峰值电压。\n例如 3.3V 单端 ADC 偏置在 1.65V，则摆幅峰值约为 1.65V。")
        grid.addWidget(QLabel("目标输出电压 V_out_peak [V]:"), 1, 2); grid.addWidget(self.ct_vout_pk, 1, 3)
        
        grp_req.setLayout(grid)
        layout.addWidget(grp_req)
        
        # 2. 磁芯参数 (用于饱和检查)
        grp_core = QGroupBox("2. 磁芯参数 (用于饱和校核)")
        grid_core = QGridLayout()
        grid_core.setVerticalSpacing(15)
        
        self.ct_ae = QLineEdit("20"); self.ct_ae.setToolTip("磁芯有效截面积 Ae")
        grid_core.addWidget(QLabel("磁芯截面积 Ae [mm²]:"), 0, 0); grid_core.addWidget(self.ct_ae, 0, 1)
        
        self.ct_bmax = QLineEdit("1.2"); self.ct_bmax.setToolTip("硅钢片通常 1.0~1.5T，铁氧体通常 0.3T，纳米晶 1.2T")
        grid_core.addWidget(QLabel("饱和磁密 B_max [T]:"), 0, 2); grid_core.addWidget(self.ct_bmax, 0, 3)
        
        self.ct_rsec = QLineEdit("10"); self.ct_rsec.setToolTip("CT 次级绕组的直流电阻 DCR")
        grid_core.addWidget(QLabel("次级内阻 R_sec [Ω]:"), 1, 0); grid_core.addWidget(self.ct_rsec, 1, 1)
        
        grp_core.setLayout(grid_core)
        layout.addWidget(grp_core)
        
        # 按钮
        btn = QPushButton("计算 CT 电阻 & 校核饱和")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_ct)
        layout.addWidget(btn)
        
        # 3. 计算结果
        grp_res = QGroupBox("3. 计算结果与状态")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.res_r_burden = QLineEdit()
        self.res_p_burden = QLineEdit()
        self.res_b_op = QLineEdit()
        self.res_status = QLineEdit()
        
        # Row 0: R_burden
        r_grid.addWidget(QLabel("推荐采样电阻 (R_burden):"), 0, 0)
        r_grid.addWidget(self.res_r_burden, 0, 1)
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'R_{burden} = \frac{V_{out\_pk} \cdot N}{I_{pri\_rms} \cdot \sqrt{2}}'))
        r_grid.addWidget(l_r, 0, 2)
        
        # Row 1: Power
        r_grid.addWidget(QLabel("电阻功耗 (P_res):"), 1, 0)
        r_grid.addWidget(self.res_p_burden, 1, 1)
        l_p = QLabel(); l_p.setPixmap(self.render_formula(r'P = (I_{pri\_rms}/N)^2 \cdot R_{burden}'))
        r_grid.addWidget(l_p, 1, 2)
        
        # Row 2: Flux Density
        r_grid.addWidget(QLabel("工作磁通密度 (B_op):"), 2, 0)
        r_grid.addWidget(self.res_b_op, 2, 1)
        # B = V_sec_rms / (4.44 * f * N * Ae)
        l_b = QLabel(); l_b.setPixmap(self.render_formula(r'B_{op} \approx \frac{I_{sec\_rms}(R_{bur}+R_{sec})}{4.44 \cdot f \cdot N \cdot A_e}'))
        r_grid.addWidget(l_b, 2, 2)
        
        # Row 3: Status
        r_grid.addWidget(QLabel("饱和状态校核:"), 3, 0)
        r_grid.addWidget(self.res_status, 3, 1)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_r_burden, self.res_p_burden, self.res_b_op, self.res_status]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Tip
        tip = QLabel("提示：若 B_op 接近或超过 B_max，CT 将会饱和，导致波形畸变，测量值变小。解决方法：减小采样电阻、增加匝数或增大磁芯截面。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic; background-color: #f9f9f9; padding: 10px; border-radius: 4px;")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        
        layout.addStretch()
        tab.setLayout(layout)

    # ==============================================================================
    # Tab 2: 分流器 (Shunt) 误差分析
    # ==============================================================================
    def init_shunt_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 基础参数
        grp_basic = QGroupBox("1. 电阻与电流参数 (Basic Specs)")
        g1 = QGridLayout()
        self.sh_i_max = QLineEdit("50"); g1.addWidget(QLabel("最大电流 I_max [A]:"), 0, 0); g1.addWidget(self.sh_i_max, 0, 1)
        self.sh_r_val = QLineEdit("1.0"); self.sh_r_val.setToolTip("分流器阻值，单位毫欧")
        g1.addWidget(QLabel("电阻阻值 R [mΩ]:"), 0, 2); g1.addWidget(self.sh_r_val, 0, 3)
        self.sh_p_rating = QLineEdit("3"); g1.addWidget(QLabel("额定功率 P_rating [W]:"), 1, 0); g1.addWidget(self.sh_p_rating, 1, 1)
        grp_basic.setLayout(g1)
        layout.addWidget(grp_basic)
        
        # 2. 温漂与精度 (TCR & Thermal)
        grp_therm = QGroupBox("2. 温升与温漂分析 (Thermal & TCR)")
        g2 = QGridLayout()
        
        self.sh_tcr = QLineEdit("50"); self.sh_tcr.setToolTip("电阻温度系数，通常 20~100 ppm/℃")
        g2.addWidget(QLabel("TCR [ppm/℃]:"), 0, 0); g2.addWidget(self.sh_tcr, 0, 1)
        
        self.sh_r_th = QLineEdit("20"); self.sh_r_th.setToolTip("热阻 RθJA (℃/W)，取决于封装和PCB散热面积。\n2512封装约为 20~60 ℃/W，大功率模块更低。")
        g2.addWidget(QLabel("热阻 Rθ [℃/W]:"), 0, 2); g2.addWidget(self.sh_r_th, 0, 3)
        
        self.sh_t_amb = QLineEdit("25"); 
        g2.addWidget(QLabel("环境温度 T_amb [℃]:"), 1, 0); g2.addWidget(self.sh_t_amb, 1, 1)
        
        grp_therm.setLayout(g2)
        layout.addWidget(grp_therm)
        
        # 3. 寄生参数与高频 (Parasitic & HF)
        grp_para = QGroupBox("3. 寄生电感与 PCB 误差 (HF & Layout)")
        g3 = QGridLayout()
        
        self.sh_esl = QLineEdit("3"); self.sh_esl.setToolTip("电阻寄生电感，贴片电阻通常 1~5 nH")
        g3.addWidget(QLabel("寄生电感 ESL [nH]:"), 0, 0); g3.addWidget(self.sh_esl, 0, 1)
        
        self.sh_didt = QLineEdit("0.1"); self.sh_didt.setToolTip("电流变化率，用于计算感性尖峰电压。")
        g3.addWidget(QLabel("电流变化率 di/dt [A/μs]:"), 0, 2); g3.addWidget(self.sh_didt, 0, 3)
        
        self.sh_pcb_l = QLineEdit("0"); self.sh_pcb_l.setToolTip("如果未使用 Kelvin 连接，包含在测量回路中的铜箔长度。0表示理想 Kelvin 连接。")
        g3.addWidget(QLabel("非 Kelvin 走线长 [mm]:"), 1, 0); g3.addWidget(self.sh_pcb_l, 1, 1)
        self.sh_pcb_w = QLineEdit("5"); 
        g3.addWidget(QLabel("走线宽度 [mm]:"), 1, 2); g3.addWidget(self.sh_pcb_w, 1, 3)
        
        grp_para.setLayout(g3)
        layout.addWidget(grp_para)
        
        # 按钮
        btn = QPushButton("计算 Shunt 误差")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_shunt)
        layout.addWidget(btn)
        
        # 4. 结果
        grp_res = QGroupBox("4. 分析结果 (Analysis Results)")
        r_grid = QGridLayout()
        
        self.sh_res_p = QLineEdit()
        self.sh_res_temp = QLineEdit()
        self.sh_res_drift = QLineEdit()
        self.sh_res_err_amp = QLineEdit()
        self.sh_res_v_spike = QLineEdit()
        self.sh_res_pcb_err = QLineEdit()
        
        # Row 1: Power & Temp
        r_grid.addWidget(QLabel("实际功耗 (I²R):"), 0, 0); r_grid.addWidget(self.sh_res_p, 0, 1)
        r_grid.addWidget(QLabel("估算元件温度 (T_j):"), 0, 2); r_grid.addWidget(self.sh_res_temp, 0, 3)
        
        # Row 2: Drift
        r_grid.addWidget(QLabel("阻值温漂 (%):"), 1, 0); r_grid.addWidget(self.sh_res_drift, 1, 1)
        r_grid.addWidget(QLabel("温漂电流误差 (Error):"), 1, 2); r_grid.addWidget(self.sh_res_err_amp, 1, 3)
        
        # Row 3: Dynamic
        r_grid.addWidget(QLabel("感性尖峰 (L·di/dt):"), 2, 0); r_grid.addWidget(self.sh_res_v_spike, 2, 1)
        r_grid.addWidget(QLabel("PCB 走线误差 (Non-Kelvin):"), 2, 2); r_grid.addWidget(self.sh_res_pcb_err, 2, 3)
        
        style_res = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad;"
        for w in [self.sh_res_p, self.sh_res_temp, self.sh_res_drift, self.sh_res_err_amp, self.sh_res_v_spike, self.sh_res_pcb_err]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    # ==============================================================================
    # Logic
    # ==============================================================================
    def calc_ct(self):
        try:
            # Inputs
            i_pri_rms = float(self.ct_ipri.text())
            n_ratio = float(self.ct_ratio.text())
            f = float(self.ct_freq.text())
            v_out_pk = float(self.ct_vout_pk.text())
            
            ae_mm2 = float(self.ct_ae.text())
            b_max = float(self.ct_bmax.text())
            r_sec = float(self.ct_rsec.text())
            
            if n_ratio <= 0 or f <= 0 or ae_mm2 <= 0: raise ValueError
            
            # 1. Secondary Current
            i_sec_rms = i_pri_rms / n_ratio
            i_sec_pk = i_sec_rms * math.sqrt(2)
            
            # 2. Burden Resistor
            # V_out_pk = I_sec_pk * R_burden
            r_burden = v_out_pk / i_sec_pk if i_sec_pk > 0 else 0
            
            # 3. Power
            p_res = (i_sec_rms ** 2) * r_burden
            
            # 4. Saturation Check
            # Total Voltage seen by core (EMF) includes Burden + Internal Winding Resistance
            # V_core_rms = I_sec_rms * (R_burden + R_sec)
            v_core_rms = i_sec_rms * (r_burden + r_sec)
            
            # Faraday's Law for Sine Wave: V_rms = 4.44 * f * N * B * Ae
            # B = V_rms / (4.44 * f * N * Ae)
            ae_m2 = ae_mm2 * 1e-6
            b_op = v_core_rms / (4.44 * f * n_ratio * ae_m2)
            
            # Display
            self.res_r_burden.setText(f"{r_burden:.2f} Ω")
            self.res_p_burden.setText(f"{p_res*1000:.1f} mW")
            self.res_b_op.setText(f"{b_op:.3f} T")
            
            # Status
            limit = b_max * 0.9 # 90% margin
            if b_op < limit:
                self.res_status.setText(f"安全 (Safe) < {limit:.2f}T")
                self.res_status.setStyleSheet("background-color: #e8f8f5; color: green; font-weight: bold;")
            else:
                self.res_status.setText(f"饱和警告! > {limit:.2f}T")
                self.res_status.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
                QMessageBox.warning(self, "设计风险", 
                                    f"当前设计下，磁芯工作磁密 B_op = {b_op:.3f} T，\n"
                                    f"接近或超过了材料极限 {b_max} T。\n\n"
                                    "建议：\n1. 减小采样电阻 R_burden（降低 ADC 输入电压范围）。\n"
                                    "2. 选用截面积 Ae 更大的 CT。\n"
                                    "3. 增加匝数 N。")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def calc_shunt(self):
        try:
            # Inputs
            i_val = float(self.sh_i_max.text())
            r_mohm = float(self.sh_r_val.text())
            p_rating = float(self.sh_p_rating.text())
            
            tcr = float(self.sh_tcr.text())
            r_theta = float(self.sh_r_th.text())
            t_amb = float(self.sh_t_amb.text())
            
            esl_nh = float(self.sh_esl.text())
            didt_aus = float(self.sh_didt.text())
            
            pcb_l = float(self.sh_pcb_l.text())
            pcb_w = float(self.sh_pcb_w.text())

            r_ohm = r_mohm / 1000.0

            # 1. Power & Thermal
            p_actual = i_val**2 * r_ohm
            temp_rise = p_actual * r_theta
            t_final = t_amb + temp_rise
            
            self.sh_res_p.setText(f"{p_actual:.2f} W")
            
            # Warning for Power
            if p_actual > p_rating:
                self.sh_res_p.setStyleSheet("background-color: #ffcccc; color: red; font-weight: bold;")
                self.sh_res_p.setText(f"{p_actual:.2f} W (过载!)")
            else:
                self.sh_res_p.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; font-weight: bold;")

            self.sh_res_temp.setText(f"{t_final:.1f} ℃ (+{temp_rise:.1f})")

            # 2. Drift Analysis
            # Delta R = R * TCR * Delta T
            # TCR is ppm/C -> 1e-6
            delta_r_factor = tcr * 1e-6 * temp_rise
            drift_percent = delta_r_factor * 100
            
            # Error in Amps?
            # V_ideal = I * R
            # V_actual = I * R * (1 + delta)
            # Calculated I_read = V_actual / R_nominal = I * (1+delta)
            # Error_amps = I_read - I = I * delta
            err_amps = i_val * delta_r_factor
            
            self.sh_res_drift.setText(f"{drift_percent:.3f} %")
            self.sh_res_err_amp.setText(f"{err_amps:.3f} A")

            # 3. Inductive Spike
            # V = L * di/dt
            # L in Henry (nH * 1e-9), di/dt in A/s (A/us * 1e6)
            v_spike = (esl_nh * 1e-9) * (didt_aus * 1e6)
            self.sh_res_v_spike.setText(f"{v_spike*1000:.1f} mV")

            # 4. PCB Trace Error (Non-Kelvin)
            # R = rho * L / A
            # 1oz Copper ~ 0.5 mOhm/square
            # Square count = L / W
            # Approx 0.5 mOhm * (L/W)
            if pcb_l > 0 and pcb_w > 0:
                r_sq_mohm = 0.5 
                r_trace_mohm = r_sq_mohm * (pcb_l / pcb_w)
                # Error voltage = I * R_trace
                # This voltage is added to the sense voltage if tapped incorrectly
                v_err_pcb = i_val * (r_trace_mohm / 1000.0)
                # Compare to signal V = I * R_shunt
                v_sig = i_val * r_ohm
                pcb_err_percent = (v_err_pcb / v_sig) * 100 if v_sig > 0 else 0
                self.sh_res_pcb_err.setText(f"{r_trace_mohm:.2f}mΩ ({pcb_err_percent:.1f}%)")
            else:
                self.sh_res_pcb_err.setText("0.00 mΩ (Kelvin)")

        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数字参数")

    def show_tutorial(self):
        """显示 CT & Shunt 设计指南"""
        dialog = QDialog(self)
        dialog.setWindowTitle("CT 与分流器设计原理")
        dialog.resize(850, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 25px;}
            h3 { color: #d35400; margin-top: 15px; font-size: 16px;}
            li { margin-bottom: 8px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
            .formula { 
                background-color: #e8f6f3; 
                padding: 10px; 
                border-left: 5px solid #1abc9c; 
                font-family: "Courier New", monospace; 
                font-weight: bold; 
                margin: 10px 0; 
                color: #2c3e50;
            }
            .warn {
                background-color: #fdedec;
                padding: 10px;
                border-left: 5px solid #e74c3c;
                margin: 10px 0;
                color: #c0392b;
            }
        </style>
        
        <h1>电流检测设计指南 (CT & Shunt)</h1>
        
        <h2>PART A: 电流互感器 (CT)</h2>
        <h3>1. 采样电阻计算</h3>
        <p>CT 将初级大电流按比例缩小到次级。次级串联电阻 <b>R<sub>burden</sub></b> 将电流转为电压。</p>
        <div class="formula">
            R<sub>burden</sub> = V<sub>adc_peak</sub> / I<sub>sec_peak</sub><br>
            I<sub>sec_peak</sub> = (I<sub>pri_rms</sub> × √2) / N
        </div>

        <h3>2. 饱和原理</h3>
        <p>CT 饱和是因为次级产生的反电动势伏秒积超过了磁芯容量。若 <b>V<sub>emf</sub></b> 太高，需要的磁通密度 <b>B</b> 超过 <b>B<sub>max</sub></b>，CT 饱和，测量值偏小。</p>
        <div class="formula">
            B<sub>op</sub> = V<sub>rms_total</sub> / (4.44 × f × N × Ae)
        </div>
        
        <hr>

        <h2>PART B: 分流器 (Shunt Resistor)</h2>
        
        <h3>1. 功率与热效应 (Power & Heating)</h3>
        <p>大电流流过电阻产生大量热量 (<b>P = I²R</b>)。</p>
        <ul>
            <li><b>降额使用：</b> 建议长期工作功率不超过额定功率的 50%~70%。</li>
            <li><b>热阻 (Rθ)：</b> 决定了温升。大封装 (如 2512, 3920) 或金属合金电阻通常散热更好。</li>
        </ul>

        <h3>2. 温漂误差 (TCR Error)</h3>
        <p>电阻值随温度变化。TCR (Temperature Coefficient of Resistance) 单位是 ppm/℃。</p>
        <div class="warn">
            <b>案例：</b> 100A 电流，TCR = 100ppm/℃，温升 100℃。<br>
            阻值变化 = 100 × 100ppm = 1%<br>
            <b>测量误差 = 100A × 1% = 1A !</b>
        </div>
        <p>设计建议：对于高精度需求，选用低 TCR (如 < 50ppm) 的锰铜/康铜合金电阻。</p>

        <h3>3. 寄生电感 (ESL)</h3>
        <p>在开关电源 (高 di/dt) 应用中，电阻自身的寄生电感会产生尖峰电压：</p>
        <div class="formula">
            V<sub>spike</sub> = ESL × (di/dt)
        </div>
        <p>这会导致电流波形前沿出现过冲。建议选用长边电极或低 ESL 的特殊电阻。</p>

        <h3>4. Kelvin 接法 (四线制)</h3>
        <p><b>必须</b>使用开尔文连接：将电压采样线直接从电阻焊盘内侧引出，避免包含焊锡和 PCB 铜箔的电阻。</p>
        <p>一段 10mm 长、5mm 宽的 1oz 铜箔约为 1mΩ，这可能比你的采样电阻本体阻值还大！</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()