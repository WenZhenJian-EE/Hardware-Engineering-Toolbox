from modules.base_module import BaseModule
# control_digital_pid.py

import math
import cmath
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QRadioButton, QButtonGroup,
                             QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class DigitalControlWindow(BaseModule):
    category = "3. 环路控制与滤波 (Control & Filter)"
    display_name = "数字控制 PID"
    description = "数字PID / S转Z域 / 数字滤波"
    window_id = "control_digital"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('数字电源环路与滤波设计助手 (Digital Control & Filtering)')
        self.setGeometry(350, 350, 1100, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("数字控制与滤波指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(200)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_pid = QWidget()
        self.tab_s2z = QWidget()
        self.tab_filter = QWidget() # New: ADC Filter

        self.init_pid_ui(self.tab_pid)
        self.init_s2z_ui(self.tab_s2z)
        self.init_filter_ui(self.tab_filter)

        self.tabs.addTab(self.tab_pid, "1. 数字 PID 设计 (Buck/Boost)")
        self.tabs.addTab(self.tab_s2z, "2. S域 转 Z域 (系数计算器)")
        self.tabs.addTab(self.tab_filter, "3. ADC 数字滤波器设计 (LPF)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 数字 PID 设计 (基于功率级模型)
    # ==============================================================================
    def init_pid_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 功率级参数
        grp_plant = QGroupBox("1. 功率级与采样设置 (Plant & Sampling)")
        grid_p = QGridLayout()
        grid_p.setVerticalSpacing(12)
        
        self.pid_mode = QComboBox()
        self.pid_mode.addItems(["电流模式 Buck (Current Mode)", "电压模式 Buck (Voltage Mode)", "Boost (Current Mode)"])
        grid_p.addWidget(QLabel("控制拓扑:"), 0, 0); grid_p.addWidget(self.pid_mode, 0, 1)
        
        self.pid_vin = QLineEdit("12"); grid_p.addWidget(QLabel("输入电压 Vin [V]:"), 1, 0); grid_p.addWidget(self.pid_vin, 1, 1)
        self.pid_vout = QLineEdit("3.3"); grid_p.addWidget(QLabel("输出电压 Vout [V]:"), 1, 2); grid_p.addWidget(self.pid_vout, 1, 3)
        self.pid_iout = QLineEdit("2.0"); grid_p.addWidget(QLabel("负载电流 Iout [A]:"), 2, 0); grid_p.addWidget(self.pid_iout, 2, 1)
        self.pid_l = QLineEdit("10"); grid_p.addWidget(QLabel("电感 L [uH]:"), 2, 2); grid_p.addWidget(self.pid_l, 2, 3)
        self.pid_c = QLineEdit("47"); grid_p.addWidget(QLabel("输出电容 C [uF]:"), 3, 0); grid_p.addWidget(self.pid_c, 3, 1)
        self.pid_fsw = QLineEdit("100"); self.pid_fsw.setToolTip("数字控制的中断频率/采样频率通常等于开关频率")
        grid_p.addWidget(QLabel("采样频率 Fs [kHz]:"), 3, 2); grid_p.addWidget(self.pid_fsw, 3, 3)
        
        # 采样反馈增益 H (ADC Gain)
        self.pid_v_max_adc = QLineEdit("3.3"); 
        grid_p.addWidget(QLabel("ADC 参考电压 [V]:"), 4, 0); grid_p.addWidget(self.pid_v_max_adc, 4, 1)
        self.pid_v_sense_div = QLineEdit("0.5"); self.pid_v_sense_div.setToolTip("硬件分压比。例如 10k/10k 分压则为 0.5")
        grid_p.addWidget(QLabel("硬件分压比 K_div:"), 4, 2); grid_p.addWidget(self.pid_v_sense_div, 4, 3)
        
        grp_plant.setLayout(grid_p)
        layout.addWidget(grp_plant)
        
        # 2. 目标与计算
        grp_tgt = QGroupBox("2. 设计目标")
        grid_t = QGridLayout()
        self.pid_fc = QLineEdit("5.0"); self.pid_fc.setToolTip("穿越频率，建议取 Fs/20 ~ Fs/10")
        grid_t.addWidget(QLabel("目标带宽 fc [kHz]:"), 0, 0); grid_t.addWidget(self.pid_fc, 0, 1)
        
        self.pid_pm = QLineEdit("60"); 
        grid_t.addWidget(QLabel("目标相位裕度 PM [deg]:"), 0, 2); grid_t.addWidget(self.pid_pm, 0, 3)
        
        btn_calc = QPushButton("计算数字 PID 系数 (Kp, Ki, Kd)")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_pid)
        grid_t.addWidget(btn_calc, 1, 0, 1, 4)
        
        grp_tgt.setLayout(grid_t)
        layout.addWidget(grp_tgt)
        
        # 3. 结果
        grp_res = QGroupBox("3. 控制器系数 (Parallel Form)")
        res_layout = QGridLayout()
        
        self.res_kp = QLineEdit()
        self.res_ki = QLineEdit()
        self.res_kd = QLineEdit()
        
        # 公式显示
        eq_label = QLabel()
        eq_label.setPixmap(self.render_formula(r'u[n] = K_p e[n] + K_i \sum_{k=0}^n e[k] + K_d (e[n]-e[n-1])'))
        res_layout.addWidget(eq_label, 0, 0, 1, 4)
        
        res_layout.addWidget(QLabel("比例系数 Kp:"), 1, 0); res_layout.addWidget(self.res_kp, 1, 1)
        res_layout.addWidget(QLabel("积分系数 Ki:"), 2, 0); res_layout.addWidget(self.res_ki, 2, 1)
        res_layout.addWidget(QLabel("微分系数 Kd:"), 3, 0); res_layout.addWidget(self.res_kd, 3, 1)
        
        # 提示
        tip = QLabel("注意：Ki 系数已包含采样时间 Ts (Ki_digital = Ki_analog * Ts)。\n适用于常见的增量式或位置式离散 PID 算法。")
        tip.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        res_layout.addWidget(tip, 4, 0, 1, 4)
        
        for w in [self.res_kp, self.res_ki, self.res_kd]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;")
            
        grp_res.setLayout(res_layout)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_pid(self):
        try:
            # 读取参数
            vin = float(self.pid_vin.text())
            vout = float(self.pid_vout.text())
            iout = float(self.pid_iout.text())
            l_val = float(self.pid_l.text()) * 1e-6
            c_val = float(self.pid_c.text()) * 1e-6
            fs = float(self.pid_fsw.text()) * 1e3
            ts = 1.0 / fs
            
            fc = float(self.pid_fc.text()) * 1e3
            pm = float(self.pid_pm.text())
            
            v_ref_adc = float(self.pid_v_max_adc.text())
            k_div = float(self.pid_v_sense_div.text())
            
            # 1. 功率级建模 (Plant Model)
            mode = self.pid_mode.currentIndex()
            r_load = vout / iout if iout > 0 else 100.0
            
            gain_plant_mag = 0.0
            phase_plant_deg = 0.0
            
            if mode == 0: # Current Mode Buck
                fp = 1 / (2 * math.pi * r_load * c_val)
                gain_plant_mag = r_load / math.sqrt(1 + (fc/fp)**2)
                phase_plant_deg = -math.atan(fc/fp) * 180 / math.pi
                
                phase_delay = -360 * fc * (1.5 * ts)
                phase_plant_deg += phase_delay

            elif mode == 1: # Voltage Mode Buck
                f0 = 1 / (2 * math.pi * math.sqrt(l_val * c_val))
                gain_plant_mag = vin * (f0/fc)**2
                phase_plant_deg = -180 # Ideal LC
                
                phase_delay = -360 * fc * (1.5 * ts)
                phase_plant_deg += phase_delay
                
            else: # Boost (Current Mode)
                duty = 1 - (vin/vout)
                fp = 1 / (2 * math.pi * r_load * c_val) # Actually 2/(R C) roughly
                gain_plant_mag = (1-duty) * r_load / 2 # Rough approx
                gain_plant_mag = gain_plant_mag / math.sqrt(1 + (fc/fp)**2)
                phase_plant_deg = -90 # 1st order
                phase_delay = -360 * fc * (1.5 * ts)
                phase_plant_deg += phase_delay

            # 2. 计算所需补偿器增益和相位
            target_gain_comp = 1.0 / gain_plant_mag
            required_phase_boost = pm - 180 - phase_plant_deg
            
            # 3. 设计 PI (Type II)
            angle_rad = (required_phase_boost + 90) * math.pi / 180
            if angle_rad <= 0.1: angle_rad = 0.1 # Limit
            if angle_rad >= 1.5: angle_rad = 1.5
            
            fz = fc / math.tan(angle_rad)
            
            kp_analog = target_gain_comp * (2*math.pi*fc) / math.sqrt((2*math.pi*fc)**2 + (2*math.pi*fz)**2)
            ki_analog = kp_analog * (2 * math.pi * fz)
            
            kd_digital = 0
            if mode == 1: 
                pass # Simple PI for voltage mode usually not enough, but keeping simple here

            # 4. Map to Digital Coefficients (Ts = 1/Fs)
            kp_dig = kp_analog
            ki_dig = ki_analog * ts
            
            self.res_kp.setText(f"{kp_dig:.4f}")
            self.res_ki.setText(f"{ki_dig:.4f}")
            self.res_kd.setText(f"{kd_digital:.4f}")
            
            if required_phase_boost > 80:
                self.res_kp.setText(f"{kp_dig:.4f} (Phase Margin Warning!)")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 2: S to Z (Coefficient Calculator)
    # ==============================================================================
    def init_s2z_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Input: Analog Compensator
        grp_an = QGroupBox("1. 模拟补偿器参数 (Analog 2p2z / Type II)")
        grid_an = QGridLayout()
        
        self.sz_fz = QLineEdit("1.0"); grid_an.addWidget(QLabel("零点频率 fz [kHz]:"), 0, 0); grid_an.addWidget(self.sz_fz, 0, 1)
        self.sz_fp = QLineEdit("50.0"); grid_an.addWidget(QLabel("极点频率 fp [kHz]:"), 0, 2); grid_an.addWidget(self.sz_fp, 0, 3)
        self.sz_gain = QLineEdit("10.0"); grid_an.addWidget(QLabel("中频增益/直流增益 [V/V]:"), 1, 0); grid_an.addWidget(self.sz_gain, 1, 1)
        self.sz_fs = QLineEdit("100"); grid_an.addWidget(QLabel("采样频率 Fs [kHz]:"), 1, 2); grid_an.addWidget(self.sz_fs, 1, 3)
        
        grp_an.setLayout(grid_an)
        layout.addWidget(grp_an)
        
        # Method
        grp_method = QGroupBox("2. 离散化方法")
        v_method = QVBoxLayout()
        self.rb_tustin = QRadioButton("双线性变换 (Tustin / Bilinear) - 推荐")
        self.rb_euler = QRadioButton("后向差分 (Backward Euler) - 简单")
        self.rb_tustin.setChecked(True)
        v_method.addWidget(self.rb_tustin)
        v_method.addWidget(self.rb_euler)
        grp_method.setLayout(v_method)
        layout.addWidget(grp_method)
        
        btn_conv = QPushButton("转换系数 (Convert)")
        btn_conv.setFixedHeight(40)
        btn_conv.clicked.connect(self.calc_s2z)
        layout.addWidget(btn_conv)
        
        # Output
        grp_out = QGroupBox("3. 数字滤波器系数 (Biquad: b0, b1, b2, a1, a2)")
        grid_out = QGridLayout()
        
        self.res_b0 = QLineEdit(); grid_out.addWidget(QLabel("b0:"), 0, 0); grid_out.addWidget(self.res_b0, 0, 1)
        self.res_b1 = QLineEdit(); grid_out.addWidget(QLabel("b1:"), 1, 0); grid_out.addWidget(self.res_b1, 1, 1)
        self.res_b2 = QLineEdit(); grid_out.addWidget(QLabel("b2:"), 2, 0); grid_out.addWidget(self.res_b2, 2, 1)
        self.res_a1 = QLineEdit(); grid_out.addWidget(QLabel("a1:"), 0, 2); grid_out.addWidget(self.res_a1, 0, 3)
        self.res_a2 = QLineEdit(); grid_out.addWidget(QLabel("a2:"), 1, 2); grid_out.addWidget(self.res_a2, 1, 3)
        
        eq_lbl = QLabel("H(z) = (b0 + b1*z^-1 + b2*z^-2) / (1 - a1*z^-1 - a2*z^-2)")
        eq_lbl.setStyleSheet("color: #2980b9; font-weight: bold; margin-top: 10px;")
        grid_out.addWidget(eq_lbl, 3, 0, 1, 4)
        
        grp_out.setLayout(grid_out)
        layout.addWidget(grp_out)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_s2z(self):
        try:
            fz = float(self.sz_fz.text()) * 1e3
            fp = float(self.sz_fp.text()) * 1e3
            gain = float(self.sz_gain.text())
            fs = float(self.sz_fs.text()) * 1e3
            ts = 1.0/fs
            
            wz = 2*math.pi*fz
            wp = 2*math.pi*fp
            
            if self.rb_euler.isChecked():
                # Backward Euler: s = (1 - z^-1) / Ts
                # H(s) = Gain * (s + wz) / (s + wp)
                # H(z) = Gain * ((1 - z^-1) / Ts + wz) / ((1 - z^-1) / Ts + wp)
                #      = Gain * ((1 + wz*Ts) - z^-1) / ((1 + wp*Ts) - z^-1)
                #      = [Gain * (1 + wz*Ts) / (1 + wp*Ts) - (Gain / (1 + wp*Ts)) * z^-1] / [1 - (1 / (1 + wp*Ts)) * z^-1]
                # standard form: H(z) = (b0 + b1 * z^-1) / (1 - a1 * z^-1)
                b0 = gain * (1.0 + wz * ts) / (1.0 + wp * ts)
                b1 = -gain / (1.0 + wp * ts)
                a1 = 1.0 / (1.0 + wp * ts)
            else:
                # Tustin / Bilinear
                k_bilinear = 2/ts
                b0_raw = gain * (k_bilinear + wz)
                b1_raw = gain * (wz - k_bilinear)
                a0_raw = (k_bilinear + wp)
                a1_raw = (wp - k_bilinear)
                
                b0 = b0_raw / a0_raw
                b1 = b1_raw / a0_raw
                a1 = - (a1_raw / a0_raw) # Sign flip for standard difference equation
            
            self.res_b0.setText(f"{b0:.5f}")
            self.res_b1.setText(f"{b1:.5f}")
            self.res_b2.setText("0.0")
            self.res_a1.setText(f"{a1:.5f}")
            self.res_a2.setText("0.0")
            
        except Exception:
            QMessageBox.warning(self, "错误", "计算失败")

    # ==============================================================================
    # Tab 3: Digital Filter Design (ADC LPF) - NEW Feature
    # ==============================================================================
    def init_filter_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：设计用于 ADC 采样信号平滑的数字滤波器。\n"
                      "一阶惯性滤波 (Alpha Filter) 适合资源受限的 MCU；二阶巴特沃斯适合高性能 DSP。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. Inputs
        grp_in = QGroupBox("1. 滤波器参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.filt_type = QComboBox()
        self.filt_type.addItems(["一阶低通 (First Order Lag / Alpha)", "二阶巴特沃斯低通 (2nd Butterworth LPF)"])
        self.filt_type.currentIndexChanged.connect(self.update_filter_ui)
        grid.addWidget(QLabel("滤波器类型:"), 0, 0); grid.addWidget(self.filt_type, 0, 1)
        
        self.filt_fs = QLineEdit("20000"); self.filt_fs.setToolTip("ADC 采样频率 Hz")
        grid.addWidget(QLabel("采样频率 fs [Hz]:"), 1, 0); grid.addWidget(self.filt_fs, 1, 1)
        
        self.filt_fc = QLineEdit("1000"); self.filt_fc.setToolTip("目标截止频率 (-3dB) Hz")
        grid.addWidget(QLabel("截止频率 fc [Hz]:"), 1, 2); grid.addWidget(self.filt_fc, 1, 3)
        
        btn_calc = QPushButton("计算滤波器系数")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_filter)
        grid.addWidget(btn_calc, 2, 0, 1, 4)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. Results
        grp_res = QGroupBox("2. 滤波器系数与实现")
        self.res_stack = QGridLayout()
        
        # Alpha Filter Result
        self.res_alpha = QLineEdit()
        self.res_alpha.setReadOnly(True); self.res_alpha.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold; font-size: 16px;")
        
        # Biquad Result
        self.res_bq_b0 = QLineEdit(); self.res_bq_b1 = QLineEdit(); self.res_bq_b2 = QLineEdit()
        self.res_bq_a1 = QLineEdit(); self.res_bq_a2 = QLineEdit()
        for w in [self.res_bq_b0, self.res_bq_b1, self.res_bq_b2, self.res_bq_a1, self.res_bq_a2]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
            
        self.filt_eq_label = QLabel()
        self.filt_eq_label.setStyleSheet("color: #2980b9; font-weight: bold; margin-top: 10px; font-size: 14px;")
        self.filt_eq_label.setAlignment(Qt.AlignCenter)
        
        grp_res.setLayout(self.res_stack)
        layout.addWidget(grp_res)
        
        # 3. Plot
        btn_plot = QPushButton("绘制幅频响应 (Bode Plot)")
        btn_plot.clicked.connect(self.plot_digital_filter)
        layout.addWidget(btn_plot)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.update_filter_ui()

    def update_filter_ui(self):
        # Clear layout
        for i in reversed(range(self.res_stack.count())): 
            self.res_stack.itemAt(i).widget().setParent(None)
            
        idx = self.filt_type.currentIndex()
        if idx == 0: # 1st Order
            self.res_stack.addWidget(QLabel("平滑系数 Alpha:"), 0, 0)
            self.res_stack.addWidget(self.res_alpha, 0, 1)
            self.filt_eq_label.setText("y[n] = α * x[n] + (1 - α) * y[n-1]")
            self.res_stack.addWidget(self.filt_eq_label, 1, 0, 1, 2)
        else: # 2nd Order
            self.res_stack.addWidget(QLabel("b0:"), 0, 0); self.res_stack.addWidget(self.res_bq_b0, 0, 1)
            self.res_stack.addWidget(QLabel("b1:"), 0, 2); self.res_stack.addWidget(self.res_bq_b1, 0, 3)
            self.res_stack.addWidget(QLabel("b2:"), 0, 4); self.res_stack.addWidget(self.res_bq_b2, 0, 5)
            self.res_stack.addWidget(QLabel("a1:"), 1, 0); self.res_stack.addWidget(self.res_bq_a1, 1, 1)
            self.res_stack.addWidget(QLabel("a2:"), 1, 2); self.res_stack.addWidget(self.res_bq_a2, 1, 3)
            self.filt_eq_label.setText("y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]")
            self.res_stack.addWidget(self.filt_eq_label, 2, 0, 1, 6)

    def calc_filter(self):
        try:
            fs = float(self.filt_fs.text())
            fc = float(self.filt_fc.text())
            
            if fs <= 0 or fc <= 0 or fc >= fs/2:
                QMessageBox.warning(self, "错误", "频率无效，且必须满足 fc < fs/2 (奈奎斯特)")
                return
            
            idx = self.filt_type.currentIndex()
            
            if idx == 0: # 1st Order (Exact Impulse Invariance / Matched Z)
                # alpha = 1 - exp(-2*pi*fc/fs)
                # This matches the step response of RC circuit exactly
                w_c = 2 * math.pi * fc
                t_s = 1.0 / fs
                alpha = 1.0 - math.exp(-w_c * t_s)
                
                self.res_alpha.setText(f"{alpha:.6f}")
                self.filter_coeffs = {'type': '1st', 'a': alpha}
                
            else: # 2nd Order Butterworth (Bilinear)
                # Prewarp
                omega = math.tan(math.pi * fc / fs)
                k1 = math.sqrt(2) * omega
                k2 = omega * omega
                norm = 1 / (1 + k1 + k2)
                
                b0 = k2 * norm
                b1 = 2 * b0
                b2 = b0
                a1 = 2 * (k2 - 1) * norm
                a2 = (1 - k1 + k2) * norm
                
                self.res_bq_b0.setText(f"{b0:.6f}")
                self.res_bq_b1.setText(f"{b1:.6f}")
                self.res_bq_b2.setText(f"{b2:.6f}")
                self.res_bq_a1.setText(f"{a1:.6f}")
                self.res_bq_a2.setText(f"{a2:.6f}")
                
                self.filter_coeffs = {'type': '2nd', 'b': [b0, b1, b2], 'a': [1.0, a1, a2]}
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def plot_digital_filter(self):
        if not hasattr(self, 'filter_coeffs'): return
        
        try:
            fs = float(self.filt_fs.text())
            f = np.logspace(1, math.log10(fs/2), 500)
            w = 2 * np.pi * f / fs # Normalized rad/sample
            z = np.exp(1j * w)
            
            if self.filter_coeffs['type'] == '1st':
                alpha = self.filter_coeffs['a']
                # H(z) = alpha / (1 - (1-alpha)z^-1)
                H = alpha / (1 - (1-alpha)/z)
            else:
                b = self.filter_coeffs['b']
                a = self.filter_coeffs['a']
                # H(z) = (b0 + b1 z^-1 + b2 z^-2) / (1 + a1 z^-1 + a2 z^-2)
                num = b[0] + b[1]/z + b[2]/(z**2)
                den = a[0] + a[1]/z + a[2]/(z**2)
                H = num / den
                
            mag = 20 * np.log10(np.abs(H))
            
            plt.rcParams.update({'font.size': 10})
            fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
            ax.semilogx(f, mag, 'b', lw=2)
            ax.set_title("Digital Filter Frequency Response")
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("Gain (dB)")
            ax.grid(True, which="both", linestyle='--', alpha=0.6)
            ax.axvline(float(self.filt_fc.text()), color='r', linestyle=':', label='Cutoff fc')
            ax.axhline(-3, color='g', linestyle='--', label='-3dB')
            ax.legend()
            
            # Show Dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("数字滤波器伯德图")
            dialog.resize(850, 600)
            layout = QVBoxLayout(dialog)
            
            scroll = QScrollArea()
            content = QWidget()
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
            l_layout = QVBoxLayout(content)
            img_label = QLabel()
            
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            img_label.setPixmap(pixmap)
            
            l_layout.addWidget(img_label)
            layout.addWidget(scroll)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Plot Error", str(e))

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("数字控制 PID & 滤波指南")
        dialog.resize(800, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
            .box { background-color: #e8f6f3; padding: 10px; border-left: 5px solid #1abc9c; margin: 10px 0; }
        </style>
        <h1>数字电源控制指南</h1>
        
        <h2>1. ADC 信号数字滤波 (Digital Filtering)</h2>
        <div class="box">
            <b>应用场景：</b> 开关电源的电压电流采样通常含有大量开关噪声。为了防止控制环路抖动，必须进行低通滤波。<br>
            <b>设计原则：</b> $f_c$ 应远低于开关频率 $f_{sw}$ (如 1/10)，但要高于环路带宽，以免引入过大相位滞后。
        </div>
        
        <h3>A. 一阶惯性滤波 (First Order Lag)</h3>
        <p>公式：<code>y[n] = α * x[n] + (1 - α) * y[n-1]</code></p>
        <p>特点：计算量极小（仅1次乘法1次加法），非常适合低成本 MCU。其相频特性与 RC 低通滤波器完全一致。</p>
        <p><b>系数 $\alpha$：</b> $\alpha \approx 2\pi f_c / f_s$ (当 $f_c \ll f_s$ 时)。</p>

        <h3>B. 二阶巴特沃斯 (Butterworth)</h3>
        <p>公式：<code>y[n] = b0*x[n] + ... - a1*y[n-1] ...</code></p>
        <p>特点：滚降速度快 (-40dB/dec)，能更干净地滤除高频噪声，但计算量稍大，且相位滞后比一阶大。适合 DSP 且对噪声敏感的场合。</p>

        <h2>2. PID 调试口诀</h2>
        <ul>
            <li><b>Kp (比例):</b> 决定响应速度。太大震荡，太小响应慢。先调 Kp 让波形微震荡。</li>
            <li><b>Ki (积分):</b> 消除静差。Ki = Kp / Ti。加入 Ki 后会增加超调，需适当减小 Kp。</li>
            <li><b>Kd (微分):</b> 抑制超调，但在电源中因噪声大通常不用，或只用很小的 Kd。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()