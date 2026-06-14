from modules.base_module import BaseModule
# control_loop_comp.py

import math
import cmath
import numpy as np 
from io import BytesIO
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

# ==============================================================================
# Helper: Step Response Simulation (Zero Dependency)
# ==============================================================================
def simulate_step_response(num_s, den_s, t_duration=0.005, dt=1e-6):
    """
    Simulate step response using Runge-Kutta 4th Order (RK4) with dynamic time-stepping.
    H(s) = num_s / den_s -> State Space -> RK4 integration
    """
    if len(den_s) == 0 or den_s[0] == 0: 
        return np.array([]), np.array([])
    
    norm = den_s[0]
    den = [d/norm for d in den_s]
    num = [n/norm for n in num_s]
    
    # Pad num with zeros if needed
    if len(num) < len(den):
        num = [0.0]*(len(den)-len(num)) + num
        
    n = len(den) - 1 # Order
    
    if n == 0:
        # Static system
        t = np.arange(0, t_duration, dt if dt > 0 else 1e-6)
        y = np.full_like(t, num[0] * 1.0)
        return t, y
        
    # Construct Control Canonical Form
    A = np.zeros((n, n))
    for i in range(n-1):
        A[i, i+1] = 1.0
    for i in range(n):
        A[n-1, i] = -den[n-i]
        
    B = np.zeros(n)
    B[n-1] = 1.0
    
    D = num[0]
    C = np.zeros(n)
    for i in range(n):
        idx_poly = n - i
        C[i] = num[idx_poly] - num[0]*den[idx_poly]
        
    # Calculate eigenvalues to determine stable time-step and duration
    try:
        eigenvalues = np.linalg.eigvals(A)
        max_eig = np.max(np.abs(eigenvalues))
        real_parts = np.real(eigenvalues)
        mags = np.abs(eigenvalues)
    except Exception:
        eigenvalues = []
        max_eig = 1e3
        real_parts = []
        mags = []
        
    if max_eig < 1e-9:
        max_eig = 1e-9

    # Determine dynamic t_duration if the default duration was passed
    if t_duration == 0.005 and len(eigenvalues) > 0:
        # Slowest stable pole determines duration
        stable_real = real_parts[real_parts < -1e-3]
        if len(stable_real) > 0:
            tau_max = -1.0 / np.max(stable_real) # np.max because it's negative (closer to 0 is slower)
            t_duration = 6.0 * tau_max
        else:
            # Fallback to pole magnitudes
            valid_mags = mags[mags > 1e-3]
            if len(valid_mags) > 0:
                tau_min_freq = 1.0 / np.min(valid_mags)
                t_duration = 6.0 * tau_min_freq
                
        # Bound t_duration to reasonable limits (1us to 0.5s) for power electronics
        t_duration = np.clip(t_duration, 1e-6, 0.5)
    
    # Determine stable dt for RK4
    dt_actual = min(t_duration / 1000, 0.15 / max_eig)
    
    # Limit number of steps to prevent hang
    if t_duration / dt_actual > 5000:
        dt_actual = t_duration / 5000
        
    t = np.arange(0, t_duration, dt_actual)
    y = np.zeros_like(t)
    state = np.zeros(n)
    u = 1.0
    
    # RK4 Integration Loop
    for k in range(len(t)):
        # Output equation
        y[k] = np.dot(C, state) + D * u
        
        # State derivatives function: dx/dt = A*x + B*u
        k1 = np.dot(A, state) + B * u
        k2 = np.dot(A, state + 0.5 * dt_actual * k1) + B * u
        k3 = np.dot(A, state + 0.5 * dt_actual * k2) + B * u
        k4 = np.dot(A, state + dt_actual * k3) + B * u
        
        state = state + (dt_actual / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
    return t, y

def calc_step_info(t, y):
    """ Calculate Overshoot and Settling Time """
    if len(y) == 0: return 0, 0
    final_val = y[-1]
    if abs(final_val) < 1e-6: return 0, 0
    
    peak_val = np.max(np.abs(y))
    overshoot = (peak_val - final_val) / final_val * 100 if final_val > 0 else 0
    
    # Settling time (2%)
    margin = 0.02 * final_val
    upper = final_val + margin
    lower = final_val - margin
    
    # Find last time it was out of bounds
    out_of_bounds = np.where((y > upper) | (y < lower))[0]
    if len(out_of_bounds) == 0:
        settling_time = 0
    else:
        last_idx = out_of_bounds[-1]
        settling_time = t[last_idx]
        
    return overshoot, settling_time

class LoopCompensationWindow(BaseModule):
    category = "3. 环路控制与滤波 (Control & Filter)"
    display_name = "环路补偿设计"
    description = "Type II/III / TL431 / 光耦 / 分压"
    window_id = "control_loop"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('环路补偿设计工具 (Loop Compensation Designer)')
        self.setGeometry(350, 350, 1100, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("环路原理 & 光耦避坑指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
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

        self.tab_type2 = QWidget()
        self.tab_type3 = QWidget()
        self.tab_tl431 = QWidget()
        self.tab_hv = QWidget() 

        self.init_type2_ui(self.tab_type2)
        self.init_type3_ui(self.tab_type3)
        self.init_tl431_ui(self.tab_tl431)
        self.init_hv_ui(self.tab_hv)

        self.tabs.addTab(self.tab_type2, "Type II (电流模式 Buck/Flyback)")
        self.tabs.addTab(self.tab_type3, "Type III (电压模式 Buck)")
        self.tabs.addTab(self.tab_tl431, "TL431 + 光耦隔离环路")
        self.tabs.addTab(self.tab_hv, "高压分压补偿 (HV Divider)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: Type II (Current Mode)
    # ==============================================================================
    def init_type2_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_plant = QGroupBox("1. 功率级参数 (Power Stage)")
        grid_plant = QGridLayout()
        
        self.t2_vout = QLineEdit("5.0")
        self.t2_vout.setToolTip("输出电压 (DC)。")
        grid_plant.addWidget(QLabel("Vout [V]:"), 0, 0); grid_plant.addWidget(self.t2_vout, 0, 1)
        
        self.t2_iout = QLineEdit("2.0")
        self.t2_iout.setToolTip("最大负载电流。\n用于计算负载电阻 Rload，决定低频极点。")
        grid_plant.addWidget(QLabel("Iout [A]:"), 0, 2); grid_plant.addWidget(self.t2_iout, 0, 3)
        
        self.t2_cout = QLineEdit("47")
        self.t2_cout.setToolTip("输出电容有效值。\n注意 MLCC 的 DC Bias 降容效应。")
        grid_plant.addWidget(QLabel("Cout [uF]:"), 1, 0); grid_plant.addWidget(self.t2_cout, 1, 1)
        
        self.t2_esr = QLineEdit("10")
        self.t2_esr.setToolTip("输出电容 ESR。\n产生零点 fz = 1/(2π*ESR*C)。\nMLCC通常<5mΩ，固态10-30mΩ。")
        grid_plant.addWidget(QLabel("ESR [mΩ]:"), 1, 2); grid_plant.addWidget(self.t2_esr, 1, 3)
        
        self.t2_fsw = QLineEdit("500")
        self.t2_fsw.setToolTip("开关频率。")
        grid_plant.addWidget(QLabel("fsw [kHz]:"), 2, 0); grid_plant.addWidget(self.t2_fsw, 2, 1)
        
        self.t2_ri = QLineEdit("0.1")
        self.t2_ri.setToolTip("电流采样增益 (Ri)。\nRi = Rsense * 采样放大倍数。\n决定了功率级的直流增益 Adc = Rload / Ri。")
        grid_plant.addWidget(QLabel("Rsense (Ri) [Ω]:"), 2, 2); grid_plant.addWidget(self.t2_ri, 2, 3)
        
        grp_plant.setLayout(grid_plant)
        layout.addWidget(grp_plant)
        
        grp_target = QGroupBox("2. 补偿目标")
        grid_target = QGridLayout()
        
        self.t2_fc = QLineEdit("50")
        self.t2_fc.setToolTip("目标穿越频率。\n建议取 fsw/10 左右。")
        grid_target.addWidget(QLabel("目标 fc [kHz]:"), 0, 0); grid_target.addWidget(self.t2_fc, 0, 1)
        
        self.t2_pm = QLineEdit("60")
        self.t2_pm.setToolTip("目标相位裕度。\n建议 45° ~ 60°。")
        grid_target.addWidget(QLabel("目标 PM [deg]:"), 0, 2); grid_target.addWidget(self.t2_pm, 0, 3)
        
        self.t2_vref = QLineEdit("0.8")
        self.t2_vref.setToolTip("芯片基准电压。")
        grid_target.addWidget(QLabel("Vref [V]:"), 1, 0); grid_target.addWidget(self.t2_vref, 1, 1)
        
        self.t2_r1 = QLineEdit("10")
        self.t2_r1.setToolTip("上分压电阻。\n通常作为设计起点，如 10kΩ ~ 50kΩ。")
        grid_target.addWidget(QLabel("上分压 R1 [kΩ]:"), 1, 2); grid_target.addWidget(self.t2_r1, 1, 3)
        
        grp_target.setLayout(grid_target)
        layout.addWidget(grp_target)
        
        btn = QPushButton("计算 Type II 参数")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_type2)
        layout.addWidget(btn)
        
        # 3. 结果与元件位置说明
        grp_res = QGroupBox("3. 补偿网络 (Type II)")
        res_grid = QGridLayout()
        
        self.t2_res_r2 = QLineEdit(); res_grid.addWidget(QLabel("R2 (下分压):"), 0, 0); res_grid.addWidget(self.t2_res_r2, 0, 1)
        self.t2_res_r3 = QLineEdit(); res_grid.addWidget(QLabel("R3 (补偿电阻):"), 0, 2); res_grid.addWidget(self.t2_res_r3, 0, 3)
        self.t2_res_c1 = QLineEdit(); res_grid.addWidget(QLabel("C1 (主极点):"), 1, 0); res_grid.addWidget(self.t2_res_c1, 1, 1)
        self.t2_res_c2 = QLineEdit(); res_grid.addWidget(QLabel("C2 (高频极点):"), 1, 2); res_grid.addWidget(self.t2_res_c2, 1, 3)
        
        desc_frame = QFrame()
        desc_frame.setStyleSheet("background-color: #fff8e1; border-radius: 5px; padding: 8px;")
        desc_layout = QVBoxLayout(desc_frame)
        desc_layout.addWidget(QLabel("<b>元件位置指南 (Type II):</b>"))
        grid_desc = QGridLayout()
        grid_desc.setSpacing(10)
        grid_desc.addWidget(QLabel("<b>R1 (上分压):</b> 接 Vout 和 FB"), 0, 0)
        grid_desc.addWidget(QLabel("<b>R2 (下分压):</b> 接 FB 和 GND"), 0, 1)
        grid_desc.addWidget(QLabel("<b>R3 + C1:</b> 串联，跨接在 FB 和 COMP (运放输出) 之间"), 1, 0)
        grid_desc.addWidget(QLabel("<b>C2:</b> 单独并联在 FB 和 COMP 之间 (可选，消高频噪)"), 1, 1)
        desc_layout.addLayout(grid_desc)
        res_grid.addWidget(desc_frame, 2, 0, 1, 4)
        
        # Buttons
        h_btn_layout = QHBoxLayout()
        self.btn_plot_t2 = QPushButton("绘制伯德图 (Bode Plot)")
        self.btn_plot_t2.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        self.btn_plot_t2.clicked.connect(self.plot_type2)
        self.btn_plot_t2.setEnabled(False)
        h_btn_layout.addWidget(self.btn_plot_t2)

        self.btn_step_t2 = QPushButton("仿真阶跃响应 (Time Domain)")
        self.btn_step_t2.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        self.btn_step_t2.clicked.connect(self.plot_step_t2)
        self.btn_step_t2.setEnabled(False)
        h_btn_layout.addWidget(self.btn_step_t2)

        res_grid.addLayout(h_btn_layout, 3, 0, 1, 4)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.t2_res_r2, self.t2_res_r3, self.t2_res_c1, self.t2_res_c2]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
            
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_type2(self):
        try:
            vout = float(self.t2_vout.text()); iout = float(self.t2_iout.text())
            cout = float(self.t2_cout.text())*1e-6; esr = float(self.t2_esr.text())*1e-3
            fsw = float(self.t2_fsw.text())*1e3; ri = float(self.t2_ri.text())
            fc = float(self.t2_fc.text())*1e3; pm_target = float(self.t2_pm.text())
            vref = float(self.t2_vref.text()); r1 = float(self.t2_r1.text())*1e3
            
            r_load = vout/iout if iout>0 else 1e6
            a_dc = r_load/ri
            fp_load = 1/(2*math.pi*r_load*cout)
            fz_esr = 1/(2*math.pi*esr*cout)
            g_plant_mag = a_dc * math.sqrt(1+(fc/fz_esr)**2) / math.sqrt(1+(fc/fp_load)**2)
            phase_plant = -math.atan(fc/fp_load)*180/math.pi + math.atan(fc/fz_esr)*180/math.pi
            
            target_comp_gain = 1.0/g_plant_mag
            boost = pm_target - phase_plant - 90
            if boost <= 0: boost = 5
            if boost > 85: boost = 85
            k = math.tan((boost/2 + 45)*math.pi/180)
            fz_c = fc/k
            fp_c = fc*k
            
            r2 = r1*vref/(vout-vref)
            r3 = target_comp_gain*r1
            c1 = 1/(2*math.pi*fz_c*r3)
            c2 = 1/(2*math.pi*fp_c*r3)
            
            self.t2_res_r2.setText(f"{self.fmt_res(r2)}")
            self.t2_res_r3.setText(f"{self.fmt_res(r3)}")
            self.t2_res_c1.setText(f"{self.fmt_cap(c1)}")
            self.t2_res_c2.setText(f"{self.fmt_cap(c2)}")
            self.btn_plot_t2.setEnabled(True)
            self.btn_step_t2.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def get_type2_tf(self):
        # Return num, den of Closed Loop T(s) = L/(1+L)
        vout = float(self.t2_vout.text()); iout = float(self.t2_iout.text())
        cout = float(self.t2_cout.text())*1e-6; esr = float(self.t2_esr.text())*1e-3
        ri = float(self.t2_ri.text())
        r1 = float(self.t2_r1.text())*1e3
        r3 = self.parse_val(self.t2_res_r3.text())
        c1 = self.parse_val(self.t2_res_c1.text())
        c2 = self.parse_val(self.t2_res_c2.text())
        
        r_load = vout/iout if iout>0 else 1e6
        
        # Plant Gp(s) = Adc * (1 + s/wz_esr) / (1 + s/wp_load)
        adc = r_load/ri
        wz_esr = 1.0/(esr*cout) if esr>0 else 1e9
        wp_load = 1.0/(r_load*cout)
        
        # Plant Num/Den
        num_p = [adc/wz_esr, adc]
        den_p = [1/wp_load, 1]
        
        # Comp Gc(s) = (1 + s R3 C1) / [ s R1 (C1+C2) * (1 + s R3 C_ser) ]
        # C_sum = C1+C2, C_ser = C1*C2/(C1+C2)
        c_sum = c1+c2
        c_ser = (c1*c2)/c_sum if c_sum>0 else 0
        
        # Gc Num/Den
        # Num = s*R3*C1 + 1
        num_c = [r3*c1, 1]
        # Den = s^2 * R1*Csum*R3*Cser + s * R1*Csum
        # coeff s^2: R1*Csum * R3*Cser = R1 * R3 * C1 * C2
        # coeff s^1: R1*Csum
        # coeff s^0: 0
        den_c = [r1*r3*c1*c2, r1*c_sum, 0]
        
        # Loop L = Num_p*Num_c / Den_p*Den_c
        num_l = np.convolve(num_p, num_c)
        den_l = np.convolve(den_p, den_c)
        
        # Closed Loop T = L / (1+L) = Num_L / (Num_L + Den_L)
        # Pad to same length
        max_len = max(len(num_l), len(den_l))
        num_l_pad = np.pad(num_l, (max_len-len(num_l), 0))
        den_l_pad = np.pad(den_l, (max_len-len(den_l), 0))
        
        num_cl = num_l_pad
        den_cl = num_l_pad + den_l_pad
        
        return num_cl, den_cl

    def plot_type2(self):
        try:
            vout = float(self.t2_vout.text()); iout = float(self.t2_iout.text())
            cout = float(self.t2_cout.text())*1e-6; esr = float(self.t2_esr.text())*1e-3
            ri = float(self.t2_ri.text()); fsw = float(self.t2_fsw.text())*1e3
            r1 = float(self.t2_r1.text())*1e3
            r3 = self.parse_val(self.t2_res_r3.text())
            c1 = self.parse_val(self.t2_res_c1.text())
            c2 = self.parse_val(self.t2_res_c2.text())
            
            r_load = vout/iout if iout>0 else 1e6
            fp_load = 1/(2*math.pi*r_load*cout)
            fz_esr = 1/(2*math.pi*esr*cout)
            a_dc_plant = r_load/ri
            
            f = np.logspace(1, math.log10(fsw), 500)
            s = 1j*2*np.pi*f
            Hp = a_dc_plant * (1 + s/(2*np.pi*fz_esr)) / (1 + s/(2*np.pi*fp_load))
            
            c_sum = c1+c2
            c_ser = (c1*c2)/c_sum if c_sum>0 else 0
            num = 1 + s*r3*c1
            den = s*r1*c_sum * (1 + s*r3*c_ser)
            Hc = num/den
            T = Hp * Hc
            self.show_bode_dialog(f, T, "Type II Loop Bode Plot")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def plot_step_t2(self):
        try:
            num, den = self.get_type2_tf()
            self.show_step_dialog(num, den, "Type II Step Response")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ==============================================================================
    # Tab 2: Type III (Voltage Mode)
    # ==============================================================================
    def init_type3_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_plant = QGroupBox("1. 功率级 (LC Filter)")
        grid = QGridLayout()
        self.t3_l = QLineEdit("10"); self.t3_l.setToolTip("滤波电感值。"); grid.addWidget(QLabel("L [uH]:"), 0, 0); grid.addWidget(self.t3_l, 0, 1)
        self.t3_cout = QLineEdit("100"); self.t3_cout.setToolTip("输出电容值。"); grid.addWidget(QLabel("C [uF]:"), 0, 2); grid.addWidget(self.t3_cout, 0, 3)
        self.t3_esr = QLineEdit("10"); self.t3_esr.setToolTip("电容 ESR (会产生零点，影响相位)。"); grid.addWidget(QLabel("ESR [mΩ]:"), 1, 0); grid.addWidget(self.t3_esr, 1, 1)
        self.t3_vin = QLineEdit("12"); self.t3_vin.setToolTip("输入电压。"); grid.addWidget(QLabel("Vin [V]:"), 1, 2); grid.addWidget(self.t3_vin, 1, 3)
        self.t3_vramp = QLineEdit("1.0"); self.t3_vramp.setToolTip("PWM 锯齿波幅值 (Peak-to-Peak)。\n决定了调制器增益 Gain_mod = Vin / Vramp。"); grid.addWidget(QLabel("Vramp [V]:"), 2, 0); grid.addWidget(self.t3_vramp, 2, 1)
        self.t3_fsw = QLineEdit("100"); self.t3_fsw.setToolTip("开关频率。"); grid.addWidget(QLabel("fsw [kHz]:"), 2, 2); grid.addWidget(self.t3_fsw, 2, 3)
        grp_plant.setLayout(grid)
        layout.addWidget(grp_plant)
        
        grp_tgt = QGroupBox("2. 目标")
        grid_t = QGridLayout()
        self.t3_fc = QLineEdit("10"); self.t3_fc.setToolTip("目标穿越频率。建议 < fsw/10。"); grid_t.addWidget(QLabel("目标 fc [kHz]:"), 0, 0); grid_t.addWidget(self.t3_fc, 0, 1)
        self.t3_pm = QLineEdit("55"); self.t3_pm.setToolTip("目标相位裕度。建议 > 45°。"); grid_t.addWidget(QLabel("目标 PM [deg]:"), 0, 2); grid_t.addWidget(self.t3_pm, 0, 3)
        self.t3_r1 = QLineEdit("10"); self.t3_r1.setToolTip("上分压电阻 (设计起点)。"); grid_t.addWidget(QLabel("上分压 R1 [kΩ]:"), 1, 0); grid_t.addWidget(self.t3_r1, 1, 1)
        self.t3_vref = QLineEdit("0.8"); self.t3_vref.setToolTip("基准电压。"); grid_t.addWidget(QLabel("Vref [V]:"), 1, 2); grid_t.addWidget(self.t3_vref, 1, 3)
        self.t3_vout = QLineEdit("3.3"); self.t3_vout.setToolTip("输出电压。"); grid_t.addWidget(QLabel("Vout [V]:"), 2, 0); grid_t.addWidget(self.t3_vout, 2, 1)
        grp_tgt.setLayout(grid_t)
        layout.addWidget(grp_tgt)
        
        btn = QPushButton("计算 Type III 参数")
        btn.setFixedHeight(40)
        btn.clicked.connect(self.calc_type3)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("3. 补偿网络 (Type III)")
        r_grid = QGridLayout()
        self.t3_res_r2 = QLineEdit(); r_grid.addWidget(QLabel("R2 (下分压):"), 0, 0); r_grid.addWidget(self.t3_res_r2, 0, 1)
        self.t3_res_r3 = QLineEdit(); r_grid.addWidget(QLabel("R3 (反馈):"), 0, 2); r_grid.addWidget(self.t3_res_r3, 0, 3)
        self.t3_res_c1 = QLineEdit(); r_grid.addWidget(QLabel("C1 (主极点):"), 1, 0); r_grid.addWidget(self.t3_res_c1, 1, 1)
        self.t3_res_c2 = QLineEdit(); r_grid.addWidget(QLabel("C2 (串联):"), 1, 2); r_grid.addWidget(self.t3_res_c2, 1, 3)
        self.t3_res_c3 = QLineEdit(); r_grid.addWidget(QLabel("C3 (前馈):"), 2, 0); r_grid.addWidget(self.t3_res_c3, 2, 1)
        
        desc_frame = QFrame()
        desc_frame.setStyleSheet("background-color: #fff8e1; border-radius: 5px; padding: 8px;")
        desc_layout = QVBoxLayout(desc_frame)
        desc_layout.addWidget(QLabel("<b>元件位置指南 (Type III):</b>"))
        grid_desc = QGridLayout()
        grid_desc.addWidget(QLabel("<b>R1 (上分压):</b> 接 Vout 和 FB"), 0, 0)
        grid_desc.addWidget(QLabel("<b>R2 (下分压):</b> 接 FB 和 GND"), 0, 1)
        grid_desc.addWidget(QLabel("<b>R3 + C2:</b> 串联，跨接在 FB 和 COMP"), 1, 0)
        grid_desc.addWidget(QLabel("<b>C1:</b> 并联，接 FB <--> COMP"), 1, 1)
        grid_desc.addWidget(QLabel("<b>C3:</b> 并联在 R1 两端 (前馈)"), 2, 0, 1, 2)
        desc_layout.addLayout(grid_desc)
        r_grid.addWidget(desc_frame, 3, 0, 1, 4)
        
        h_btn_layout = QHBoxLayout()
        self.btn_plot_t3 = QPushButton("绘制伯德图")
        self.btn_plot_t3.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        self.btn_plot_t3.clicked.connect(self.plot_type3)
        self.btn_plot_t3.setEnabled(False)
        h_btn_layout.addWidget(self.btn_plot_t3)

        self.btn_step_t3 = QPushButton("仿真阶跃响应")
        self.btn_step_t3.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        self.btn_step_t3.clicked.connect(self.plot_step_t3)
        self.btn_step_t3.setEnabled(False)
        h_btn_layout.addWidget(self.btn_step_t3)

        r_grid.addLayout(h_btn_layout, 4, 0, 1, 4)
        
        for w in [self.t3_res_r2, self.t3_res_r3, self.t3_res_c1, self.t3_res_c2, self.t3_res_c3]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #e8f8f5; font-weight: bold;")
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_type3(self):
        try:
            l = float(self.t3_l.text())*1e-6; c_out = float(self.t3_cout.text())*1e-6
            esr = float(self.t3_esr.text())*1e-3; vin = float(self.t3_vin.text())
            vramp = float(self.t3_vramp.text()); fc = float(self.t3_fc.text())*1e3
            pm = float(self.t3_pm.text()); r1 = float(self.t3_r1.text())*1e3
            vref = float(self.t3_vref.text()); vout = float(self.t3_vout.text())
            
            f_lc = 1/(2*math.pi*math.sqrt(l*c_out))
            f_esr = 1/(2*math.pi*esr*c_out) if esr>0 else 1e9
            a_mod = vin/vramp
            g_plant_mag = a_mod * ((f_lc/fc)**2)
            phase_plant = -180 + math.atan(fc/f_esr)*180/math.pi
            
            boost = pm - phase_plant + 90
            if boost > 160: boost = 160
            k = math.tan((boost/4 + 45)*math.pi/180)
            fz = fc/k; fp = fc*k
            g_comp_target = 1.0/g_plant_mag
            
            r2 = r1*vref/(vout-vref)
            r3 = g_comp_target*r1
            c2 = 1/(2*math.pi*fz*r3)
            c1 = 1/(2*math.pi*fp*r3)
            c3 = 1/(2*math.pi*fz*r1)
            
            self.t3_res_r2.setText(f"{self.fmt_res(r2)}")
            self.t3_res_r3.setText(f"{self.fmt_res(r3)}")
            self.t3_res_c1.setText(f"{self.fmt_cap(c1)}")
            self.t3_res_c2.setText(f"{self.fmt_cap(c2)}")
            self.t3_res_c3.setText(f"{self.fmt_cap(c3)}")
            self.btn_plot_t3.setEnabled(True)
            self.btn_step_t3.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def get_type3_tf(self):
        l = float(self.t3_l.text())*1e-6; c_out = float(self.t3_cout.text())*1e-6
        esr = float(self.t3_esr.text())*1e-3; vin = float(self.t3_vin.text())
        vramp = float(self.t3_vramp.text())
        r1 = float(self.t3_r1.text())*1e3
        r3 = self.parse_val(self.t3_res_r3.text())
        c1 = self.parse_val(self.t3_res_c1.text())
        c2 = self.parse_val(self.t3_res_c2.text())
        c3 = self.parse_val(self.t3_res_c3.text())
        
        # Plant: Gp(s) = (Vin/Vramp) * (1 + s*esr*C) / (1 + s^2 LC)
        # Simplify Den: s^2 LC + 1 (Approx ideal LC)
        # Or better: s^2 LC + s(L/R_load + ESR*C) + 1 ?
        # Let's stick to user inputs. Ideally LC has damping.
        # Assume Q=1 damping for step response to avoid infinite oscillation in model
        # Damping R = sqrt(L/C). 
        # den = s^2 LC + s * (sqrt(L/C)*C) + 1 ??
        # Let's just use s^2 LC + 1 and small resistance.
        
        num_p = [vin/vramp * esr * c_out, vin/vramp]
        den_p = [l*c_out, 1e-3*math.sqrt(l*c_out), 1] # Add slight damping
        
        # Comp Z2 = (1/sC1) || (R3 + 1/sC2)
        # Z2 = (1 + s R3 C2) / [ s(C1+C2) * (1 + s R3 C_ser) ]
        # Comp Z1 = R1 || (1/sC3) = R1 / (1 + s R1 C3)
        # Hc = Z2 / Z1
        # Hc = [ (1+sR3C2) * (1+sR1C3) ] / [ s R1(C1+C2) * (1+sR3C_ser) ]
        
        c_sum = c1+c2
        c_ser = (c1*c2)/c_sum if c_sum>0 else 0
        
        # Num Hc: (s R3 C2 + 1)(s R1 C3 + 1)
        # = s^2 (R3 C2 R1 C3) + s (R3 C2 + R1 C3) + 1
        num_c = [r3*c2*r1*c3, r3*c2+r1*c3, 1]
        
        # Den Hc: s R1 Csum * (s R3 Cser + 1)
        # = s^2 (R1 Csum R3 Cser) + s (R1 Csum)
        den_c = [r1*c_sum*r3*c_ser, r1*c_sum, 0]
        
        num_l = np.convolve(num_p, num_c)
        den_l = np.convolve(den_p, den_c)
        
        max_len = max(len(num_l), len(den_l))
        num_l = np.pad(num_l, (max_len-len(num_l), 0))
        den_l = np.pad(den_l, (max_len-len(den_l), 0))
        
        return num_l, num_l + den_l

    def plot_type3(self):
        try:
            l = float(self.t3_l.text())*1e-6; c_out = float(self.t3_cout.text())*1e-6
            esr = float(self.t3_esr.text())*1e-3; vin = float(self.t3_vin.text())
            vramp = float(self.t3_vramp.text()); fsw = float(self.t3_fsw.text())*1e3
            r1 = float(self.t3_r1.text())*1e3
            r3 = self.parse_val(self.t3_res_r3.text())
            c1 = self.parse_val(self.t3_res_c1.text())
            c2 = self.parse_val(self.t3_res_c2.text())
            c3 = self.parse_val(self.t3_res_c3.text())
            
            f = np.logspace(2, math.log10(fsw), 500)
            s = 1j*2*np.pi*f
            Hp = (vin/vramp)*(1+s*esr*c_out)/(1+s**2*l*c_out)
            Z1 = r1/(1+s*r1*c3)
            c_ser_fb = (c1*c2)/(c1+c2) if (c1+c2)>0 else 0
            Z2 = (1+s*r3*c2)/(s*(c1+c2)*(1+s*r3*c_ser_fb))
            Hc = Z2/Z1
            T = Hp*Hc
            self.show_bode_dialog(f, T, "Type III Loop Bode Plot")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def plot_step_t3(self):
        try:
            num, den = self.get_type3_tf()
            self.show_step_dialog(num, den, "Type III Step Response")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ==============================================================================
    # Tab 3: TL431 + Optocoupler (UPDATED)
    # ==============================================================================
    def init_tl431_ui(self, tab):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        info_lbl = QLabel("适用：反激 (Flyback) 或 LLC 隔离电源。包含 TL431 交流环路补偿与光耦直流静态工作点验证。")
        info_lbl.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info_lbl)

        # 1. 交流与系统参数
        grp_cfg = QGroupBox("1. 交流环路与系统参数 (AC Loop & System Params)")
        grid = QGridLayout()
        self.tl_vout = QLineEdit("12"); grid.addWidget(QLabel("Vout [V]:"), 0, 0); grid.addWidget(self.tl_vout, 0, 1)
        self.tl_r_upper = QLineEdit("10"); self.tl_r_upper.setToolTip("上分压电阻。\n建议 2kΩ ~ 20kΩ。"); grid.addWidget(QLabel("R_upper [kΩ]:"), 0, 2); grid.addWidget(self.tl_r_upper, 0, 3)
        
        self.tl_fc = QLineEdit("1.0"); self.tl_fc.setToolTip("目标带宽。\n反激通常 < 2kHz。"); grid.addWidget(QLabel("目标 fc [kHz]:"), 1, 0); grid.addWidget(self.tl_fc, 1, 1)
        self.tl_pm = QLineEdit("60"); self.tl_pm.setToolTip("目标相位裕度。"); grid.addWidget(QLabel("目标 PM [deg]:"), 1, 2); grid.addWidget(self.tl_pm, 1, 3)
        
        self.tl_opto_fp = QLineEdit("8.0")
        self.tl_opto_fp.setToolTip("光耦极点频率。\nPC817 通常在 5kHz~15kHz，取决于负载电阻。"); 
        grid.addWidget(QLabel("光耦极点 f_opto [kHz]:"), 2, 0); grid.addWidget(self.tl_opto_fp, 2, 1)
        
        self.tl_gain_req = QLineEdit("15")
        self.tl_gain_req.setToolTip("所需补偿中频增益 (Mid-band Gain)。\n如果不知道，可以根据 G_loop = G_plant * G_comp = 1 推算。"); 
        grid.addWidget(QLabel("所需增益 Gain [dB]:"), 2, 2); grid.addWidget(self.tl_gain_req, 2, 3)
        
        btn_est_gain = QPushButton("估算所需增益?")
        btn_est_gain.setStyleSheet("text-align: left; color: #2980b9; border: none;")
        btn_est_gain.clicked.connect(lambda: QMessageBox.information(self, "增益估算", "补偿器的中频增益通常由 G_plant 决定。\n\n公式：Gain_comp_dB = - Gain_plant_dB (@ fc)\n\n对于反激：\nG_plant_dc ≈ (Vin / Vramp) * (N_s/N_p)\n\n请输入你需要补偿器提供的增益值。"))
        grid.addWidget(btn_est_gain, 3, 2, 1, 2)
        
        grp_cfg.setLayout(grid)
        layout.addWidget(grp_cfg)
        
        # 2. 直流偏置参数
        grp_in = QGroupBox("2. 光耦直流偏置参数 (Opto DC Bias Params)")
        grid_dc = QGridLayout()
        grid_dc.setVerticalSpacing(12)
        
        self.opto_vf = QLineEdit("1.2"); self.opto_vf.setToolTip("光耦 LED 正向压降，查 Datasheet (如 PC817 为 1.2V)")
        grid_dc.addWidget(QLabel("光耦 Vf [V]:"), 0, 0); grid_dc.addWidget(self.opto_vf, 0, 1)
        
        self.opto_r_led = QLineEdit("1.0"); self.opto_r_led.setToolTip("LED 限流电阻 (R_bias)，连接在 Vout 和光耦阳极之间 (kΩ)")
        grid_dc.addWidget(QLabel("LED 限流电阻 R_led [kΩ]:"), 0, 2); grid_dc.addWidget(self.opto_r_led, 0, 3)
        
        self.opto_ctr = QLineEdit("0.5"); self.opto_ctr.setToolTip("光耦 CTR (Current Transfer Ratio)。\n请填入最恶劣情况下的值 (考虑温度、老化、低电流)。建议取 0.5 (50%) 或更低。")
        grid_dc.addWidget(QLabel("最差 CTR (Ratio):"), 1, 0); grid_dc.addWidget(self.opto_ctr, 1, 1)
        
        self.opto_r_pullup = QLineEdit("20"); self.opto_r_pullup.setToolTip("原边 PWM 芯片反馈脚的上拉电阻 (kΩ)")
        grid_dc.addWidget(QLabel("原边上拉电阻 R_pullup [kΩ]:"), 1, 2); grid_dc.addWidget(self.opto_r_pullup, 1, 3)
        
        self.opto_vdd = QLineEdit("5.0"); self.opto_vdd.setToolTip("原边 PWM 芯片反馈脚的内部基准或上拉电压 (V)")
        grid_dc.addWidget(QLabel("原边上拉电压 Vdd [V]:"), 2, 0); grid_dc.addWidget(self.opto_vdd, 2, 1)
        
        self.opto_r_par = QLineEdit("0"); self.opto_r_par.setToolTip("并联在光耦 LED 两端的电阻 (kΩ)。\n用于为 TL431 提供额外的阴极电流。填 0 表示无并联。")
        grid_dc.addWidget(QLabel("光耦并联电阻 R_par [kΩ]:"), 2, 2); grid_dc.addWidget(self.opto_r_par, 2, 3)
        
        grp_in.setLayout(grid_dc)
        layout.addWidget(grp_in)

        # 按钮组合
        h_action = QHBoxLayout()
        btn_ac = QPushButton("① 计算交流补偿元件")
        btn_ac.setFixedHeight(40)
        btn_ac.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_ac.clicked.connect(self.calc_tl431)
        h_action.addWidget(btn_ac)
        
        btn_dc = QPushButton("② 计算直流工作点余量")
        btn_dc.setFixedHeight(40)
        btn_dc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_dc.clicked.connect(self.calc_opto_dc)
        h_action.addWidget(btn_dc)
        layout.addLayout(h_action)
        
        # 3. 分析结果
        grp_res = QGroupBox("3. 综合分析结果 (Results)")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(10)
        
        # 交流部分
        self.tl_res_r_lower = QLineEdit(); res_grid.addWidget(QLabel("R_lower:"), 0, 0); res_grid.addWidget(self.tl_res_r_lower, 0, 1)
        self.tl_res_r_comp = QLineEdit(); res_grid.addWidget(QLabel("R_comp (R_LED):"), 0, 2); res_grid.addWidget(self.tl_res_r_comp, 0, 3)
        self.tl_res_c_comp = QLineEdit(); res_grid.addWidget(QLabel("C_comp (主极点):"), 1, 0); res_grid.addWidget(self.tl_res_c_comp, 1, 1)
        self.tl_res_c_hf = QLineEdit(); res_grid.addWidget(QLabel("C_hf (可选高频):"), 1, 2); res_grid.addWidget(self.tl_res_c_hf, 1, 3)
        
        h_btn = QHBoxLayout()
        self.btn_plot_tl = QPushButton("绘制开环Bode图")
        self.btn_plot_tl.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        self.btn_plot_tl.clicked.connect(self.plot_tl431)
        self.btn_plot_tl.setEnabled(False)
        h_btn.addWidget(self.btn_plot_tl)

        self.btn_step_tl = QPushButton("仿真阶跃响应")
        self.btn_step_tl.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        self.btn_step_tl.clicked.connect(self.plot_step_tl)
        self.btn_step_tl.setEnabled(False)
        h_btn.addWidget(self.btn_step_tl)
        res_grid.addLayout(h_btn, 2, 0, 1, 4)
        
        # 分隔线
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        res_grid.addWidget(line, 3, 0, 1, 4)
        
        # 直流部分
        self.opto_ic_req = QLineEdit()
        self.opto_if_req = QLineEdit()
        self.opto_if_avail = QLineEdit()
        self.opto_ika_check = QLineEdit()
        self.opto_status = QLineEdit()
        
        res_grid.addWidget(QLabel("原边所需下拉 Ic_req:"), 4, 0); res_grid.addWidget(self.opto_ic_req, 4, 1)
        res_grid.addWidget(QLabel("所需 LED 电流 If_req:"), 4, 2); res_grid.addWidget(self.opto_if_req, 4, 3)
        res_grid.addWidget(QLabel("副边最大可供 If_max:"), 5, 0); res_grid.addWidget(self.opto_if_avail, 5, 1)
        res_grid.addWidget(QLabel("TL431 阴极电流 Ika:"), 5, 2); res_grid.addWidget(self.opto_ika_check, 5, 3)
        res_grid.addWidget(QLabel("直流评估结果:"), 6, 0); res_grid.addWidget(self.opto_status, 6, 1, 1, 3)
        
        self.opto_suggestion_lbl = QLabel("")
        self.opto_suggestion_lbl.setWordWrap(True)
        res_grid.addWidget(self.opto_suggestion_lbl, 7, 0, 1, 4)
        
        for w in [self.tl_res_r_lower, self.tl_res_r_comp, self.tl_res_c_comp, self.tl_res_c_hf,
                  self.opto_ic_req, self.opto_if_req, self.opto_if_avail, self.opto_ika_check]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #e8f8f5; font-weight: bold;")
        self.opto_status.setReadOnly(True)
        
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        
        desc_frame = QFrame()
        desc_frame.setStyleSheet("background-color: #fff8e1; border-radius: 5px; padding: 8px;")
        desc_layout = QVBoxLayout(desc_frame)
        grid_desc = QGridLayout()
        grid_desc.addWidget(QLabel("<b>R_upper:</b> 接 Vout 和 REF\n<b>R_lower:</b> 接 REF 和 GND"), 0, 0)
        grid_desc.addWidget(QLabel("<b>R_comp(R_led) + C_comp:</b> 串联接 REF 和 Cathode\n<b>C_hf:</b> 跨接在 Cathode 和 REF (或 R_upper 并联)"), 0, 1)
        desc_layout.addLayout(grid_desc)
        layout.addWidget(desc_frame)
        
        layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        tab.setLayout(main_layout)

    def calc_tl431(self):
        try:
            vout = float(self.tl_vout.text()); r_up = float(self.tl_r_upper.text())*1e3
            fc = float(self.tl_fc.text())*1e3; pm = float(self.tl_pm.text())
            gain_db = float(self.tl_gain_req.text())
            fp_opto = float(self.tl_opto_fp.text())*1e3
            vref = 2.5
            
            # 1. R_lower
            if vout <= vref: r_low = 1e9
            else: r_low = r_up * vref / (vout - vref)
            
            # 2. Phase Boost Calculation
            # We need to compensate for Plant Phase Lag AND Opto Phase Lag
            # Phase_Plant_Lag typically -90 (single pole dominating) or more.
            # Let's assume user wants PM.
            # Total Lag at fc = 90 (integrator) + atan(fc/fz) - atan(fc/fp) ...
            
            # Simplified approach: 
            # We treat the TL431 compensator as Type II. 
            # But the Plant has an EXTRA pole from Opto.
            # Phase_Lag_Opto at fc
            phi_opto = math.atan(fc / fp_opto) * 180 / math.pi
            
            # Typical Current Mode Plant has -90 deg lag at low freq (Load Pole).
            # So Plant Phase approx -90 - phi_opto.
            # We want Margin PM.
            # Loop Phase = Phase_Comp + Phase_Plant = -90 + Boost + (-90 - phi_opto)
            # Loop Phase = -180 + Boost - phi_opto
            # PM = 180 + Loop Phase = Boost - phi_opto
            # So Required Boost = PM + phi_opto
            
            req_boost = pm + phi_opto
            
            # Limit boost reasonable range for Type II (max 90, practical < 75)
            if req_boost > 80: req_boost = 80
            if req_boost < 10: req_boost = 10
            
            k = math.tan((req_boost/2 + 45) * math.pi / 180)
            fz = fc / k
            
            # 3. Gain Calculation
            # Mid band gain of TL431 Type II is set by R_comp / R_upper (roughly)
            # Actually G_comp(s) = (1 + s/wz) / (s * R_up * C_comp)
            # Magnitude at fc: |G| = sqrt(1+(fc/fz)^2) / (2*pi*fc * R_up * C_comp)
            # Target Magnitude G_target = 10^(gain_db/20)
            
            g_target = 10**(gain_db/20)
            
            # Solve for C_comp
            # G_target = math.sqrt(1 + (fc/fz)**2) / (2*math.pi*fc * r_up * C_comp)
            # C_comp = math.sqrt(1 + (fc/fz)**2) / (2*math.pi*fc * r_up * G_target)
            
            c_comp = math.sqrt(1 + (fc/fz)**2) / (2*math.pi*fc * r_up * g_target)
            
            # R_comp (in series with C_comp) determines zero fz
            # fz = 1 / (2*pi * R_comp * C_comp)
            # R_comp = 1 / (2*pi * fz * C_comp)
            r_comp = 1 / (2*math.pi * fz * c_comp)
            
            # Optional HF Pole to cancel Opto Zero or ESR Zero? 
            # Usually put C_hf across R_upper to form a pole fp_hf = 1/(2*pi*R_up*C_hf)
            # Let's set fp_hf = 5 * fc or switch frequency noise filter
            fp_hf = fc * 5
            c_hf = 1 / (2*math.pi * fp_hf * r_up)

            self.tl_res_r_lower.setText(f"{self.fmt_res(r_low)}")
            self.tl_res_r_comp.setText(f"{self.fmt_res(r_comp)}")
            self.tl_res_c_comp.setText(f"{self.fmt_cap(c_comp)}")
            self.tl_res_c_hf.setText(f"{self.fmt_cap(c_hf)}")
            self.btn_plot_tl.setEnabled(True)
            self.btn_step_tl.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def get_tl431_tf(self):
        # Return Loop T(s)
        r_up = float(self.tl_r_upper.text())*1e3
        r_comp = self.parse_val(self.tl_res_r_comp.text())
        c_comp = self.parse_val(self.tl_res_c_comp.text())
        c_hf = self.parse_val(self.tl_res_c_hf.text())
        fp_opto = float(self.tl_opto_fp.text())*1e3
        fc = float(self.tl_fc.text())*1e3
        gain_db = float(self.tl_gain_req.text())
        
        # Plant: Assume simple integrator-like with opto pole for simulation
        # G_plant approx = K / (s * (1+s/w_opto)) ?
        # No, current mode plant is ~ 1/(1+s/w_load).
        # To match the "Gain Req", we construct a Plant that has Gain = -Gain_Req at fc.
        # Let's model Plant as: Gp = Kp / [(1+s/wp_load)(1+s/wp_opto)]
        # wp_load is usually low freq (eg 10Hz).
        wp_load = 2*math.pi*10 
        wp_opto = 2*math.pi*fp_opto
        
        # Calculate Kp such that |Gp(fc)| = 1 / G_comp_target
        # |Gp| = Kp / [ sqrt(1+(fc/10)^2) * sqrt(1+(fc/fp_opto)^2) ]
        g_comp_target = 10**(gain_db/20)
        g_plant_target = 1.0 / g_comp_target
        denom_mag = math.sqrt(1+(fc/10)**2) * math.sqrt(1+(fc/fp_opto)**2)
        kp = g_plant_target * denom_mag
        
        # Plant Num/Den
        num_p = [kp]
        # Den = (1+s/w1)(1+s/w2) = 1 + s(1/w1+1/w2) + s^2/(w1w2)
        den_p = [1/(wp_load*wp_opto), 1/wp_load + 1/wp_opto, 1]
        
        # Comp Gc(s)
        # Z_cathode = R_comp + 1/sC_comp = (1 + s R_comp C_comp) / s C_comp
        # Z_ref = R_upper || 1/sC_hf = R_upper / (1 + s R_upper C_hf)
        # Gc(s) = Z_cathode / Z_ref ? No, it's Z_fb / Z_in structure roughly.
        # Transfer function V_cathode / V_ref = - Z_cathode / Z_ref ?
        # Actually it's Transconductance gm * Z_cathode?
        # Let's use the Type II transfer function we designed for:
        # Gc = (1 + s/wz) / (s * R_up * C_comp)
        # wz = 1/(R_comp*C_comp)
        
        wz = 1/(r_comp*c_comp)
        # If C_hf exists, it adds a pole at wp_hf = 1/(R_up*C_hf)
        wp_hf = 1/(r_up*c_hf) if c_hf > 0 else 1e9
        
        # Gc = (1 + s/wz) / [ s * R_up * C_comp * (1 + s/wp_hf) ]
        # Num = s/wz + 1
        num_c = [1/wz, 1]
        # Den = s^2 (R_up C_comp / wp_hf) + s (R_up C_comp)
        k_c = r_up * c_comp
        den_c = [k_c/wp_hf, k_c, 0]
        
        num_l = np.convolve(num_p, num_c)
        den_l = np.convolve(den_p, den_c)
        
        max_len = max(len(num_l), len(den_l))
        num_l = np.pad(num_l, (max_len-len(num_l), 0))
        den_l = np.pad(den_l, (max_len-len(den_l), 0))
        
        return num_l, num_l + den_l

    def plot_tl431(self):
        try:
            num, den_cl = self.get_tl431_tf()
            # Loop L = num_l / den_l (Wait, get_tl431_tf returns Closed Loop)
            # I need Open Loop for Bode.
            # Re-calculate L(s) logic locally for Bode
            r_up = float(self.tl_r_upper.text())*1e3
            r_comp = self.parse_val(self.tl_res_r_comp.text())
            c_comp = self.parse_val(self.tl_res_c_comp.text())
            c_hf = self.parse_val(self.tl_res_c_hf.text())
            fc = float(self.tl_fc.text())*1e3
            fp_opto = float(self.tl_opto_fp.text())*1e3
            
            f = np.logspace(1, math.log10(fc*100), 500)
            s = 1j*2*np.pi*f
            
            # Gc
            wz = 1/(r_comp*c_comp)
            wp_hf = 1/(r_up*c_hf) if c_hf > 0 else 1e9
            Gc = (1 + s/wz) / (s * r_up * c_comp * (1 + s/wp_hf))
            
            # Gp (Approximate)
            wp_load = 2*math.pi*10
            wp_opto = 2*math.pi*fp_opto
            gain_db = float(self.tl_gain_req.text())
            g_plant_target_mag = 1.0 / (10**(gain_db/20))
            denom_mag = math.sqrt(1+(fc/10)**2) * math.sqrt(1+(fc/fp_opto)**2)
            kp = g_plant_target_mag * denom_mag
            Gp = kp / ((1+s/wp_load)*(1+s/wp_opto))
            
            L = Gp * Gc
            self.show_bode_dialog(f, L, "TL431 Isolated Loop Gain (Open Loop)")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def plot_step_tl(self):
        try:
            num, den = self.get_tl431_tf()
            self.show_step_dialog(num, den, "TL431 Closed Loop Step Response")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ==============================================================================
    # Tab 4: Opto DC Bias
    # ==============================================================================


    def calc_opto_dc(self):
        try:
            vout = float(self.tl_vout.text())
            vf = float(self.opto_vf.text())
            r_led = float(self.opto_r_led.text()) * 1e3 
            ctr = float(self.opto_ctr.text())
            r_pull = float(self.opto_r_pullup.text()) * 1e3 
            vdd = float(self.opto_vdd.text())
            r_par = float(self.opto_r_par.text()) * 1e3 
            
            vref_tl431 = 2.5
            v_ce_sat = 0.3 
            
            ic_req = (vdd - v_ce_sat) / r_pull
            if_req = ic_req / ctr
            if_max_avail = (vout - vref_tl431 - vf) / r_led
            
            i_par = 0
            if r_par > 0:
                i_par = vf / r_par 
            
            ika_actual = if_req + i_par
            
            self.opto_ic_req.setText(f"{ic_req*1000:.2f} mA")
            self.opto_if_req.setText(f"{if_req*1000:.2f} mA")
            self.opto_if_avail.setText(f"{if_max_avail*1000:.2f} mA")
            self.opto_ika_check.setText(f"{ika_actual*1000:.2f} mA")
            
            msgs = []
            is_ok = True
            
            self.opto_suggestion_lbl.setText("")
            self.opto_suggestion_lbl.setStyleSheet("")

            if if_max_avail < if_req:
                msgs.append("驱动能力不足 (If_max < If_req)")
                is_ok = False
            
            if ika_actual < 1.0e-3:
                msgs.append("TL431 电流不足 (<1mA)")
                is_ok = False
                
            if is_ok:
                self.opto_status.setText("设计合理 (Pass)")
                self.opto_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.opto_status.setText(f"失败: {'; '.join(msgs)}")
                self.opto_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
                if ika_actual < 1.0e-3:
                    rec_r_par = vf / (1.5e-3 - if_req) if (1.5e-3 > if_req) else 1000
                    if rec_r_par > 0:
                        msg = (f"⚠️ 改进建议：TL431 工作电流不足！\n"
                               f"建议在光耦 LED 两端并联一个约 {rec_r_par/1000:.1f}kΩ 的电阻 (R_par)，以提供额外的偏置电流。")
                        self.opto_suggestion_lbl.setText(msg)
                        self.opto_suggestion_lbl.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold; border: 1px solid #ffeeba; border-radius: 4px; padding: 10px;")

        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 5: HV Compensated Divider
    # ==============================================================================
    def init_hv_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info_label = QLabel("应用场景：PFC 母线电压采样、LLC 高压反馈。\n"
                            "高压侧的大电阻串联会带来寄生电容，导致反馈信号在瞬态下失真（相位滞后）。\n"
                            "需在下分压电阻并联电容，满足 R1*C1 = R2*C2，实现全频段平坦增益。")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        grp_high = QGroupBox("1. 上分压臂参数 (High Side)")
        g_high = QGridLayout()
        
        self.hv_r1_total = QLineEdit("3000"); self.hv_r1_total.setToolTip("上分压总电阻。例如 3个 1MΩ 串联，填 3000。")
        g_high.addWidget(QLabel("上分压总电阻 R1 [kΩ]:"), 0, 0); g_high.addWidget(self.hv_r1_total, 0, 1)
        
        self.hv_c1_parasitic = QLineEdit("0.2"); self.hv_c1_parasitic.setToolTip("上分压总寄生电容。\n单个 1206 电阻寄生电容约 0.2~0.5pF。\n若是 N 个电阻串联，总电容 = C_unit / N。")
        g_high.addWidget(QLabel("上臂总寄生电容 C1 [pF]:"), 0, 2); g_high.addWidget(self.hv_c1_parasitic, 0, 3)
        
        grp_high.setLayout(g_high)
        layout.addWidget(grp_high)
        
        grp_low = QGroupBox("2. 下分压臂参数 (Low Side)")
        g_low = QGridLayout()
        
        self.hv_r2 = QLineEdit("10"); g_low.addWidget(QLabel("下分压电阻 R2 [kΩ]:"), 0, 0); g_low.addWidget(self.hv_r2, 0, 1)
        
        self.hv_c2_res = QLineEdit()
        self.hv_c2_res.setReadOnly(True); self.hv_c2_res.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;")
        g_low.addWidget(QLabel("需并联补偿电容 C2 [pF]:"), 1, 0); g_low.addWidget(self.hv_c2_res, 1, 1)
        
        btn_calc = QPushButton("计算补偿电容 C_comp")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_hv_comp)
        g_low.addWidget(btn_calc, 0, 2, 2, 2) 
        
        grp_low.setLayout(g_low)
        layout.addWidget(grp_low)
        
        grp_helper = QGroupBox("小工具：串联寄生电容估算")
        g_help = QGridLayout()
        
        self.hv_help_c_unit = QLineEdit("0.4"); g_help.addWidget(QLabel("单颗电阻寄生电容 [pF]:"), 0, 0); g_help.addWidget(self.hv_help_c_unit, 0, 1)
        self.hv_help_n = QLineEdit("3"); g_help.addWidget(QLabel("串联数量 N:"), 0, 2); g_help.addWidget(self.hv_help_n, 0, 3)
        
        btn_help = QPushButton("估算 C1 -> 填入上方")
        btn_help.clicked.connect(self.calc_hv_helper)
        g_help.addWidget(btn_help, 0, 4)
        
        grp_helper.setLayout(g_help)
        layout.addWidget(grp_helper)
        
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'R_1 C_1 = R_2 C_2 \Rightarrow C_{comp} = C_1 \cdot \frac{R_1}{R_2}'))
        l_form.setAlignment(Qt.AlignCenter)
        layout.addWidget(l_form)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_hv_helper(self):
        try:
            c_unit = float(self.hv_help_c_unit.text())
            n = float(self.hv_help_n.text())
            if n > 0:
                c_total = c_unit / n
                self.hv_c1_parasitic.setText(f"{c_total:.3f}")
        except: pass

    def calc_hv_comp(self):
        try:
            r1 = float(self.hv_r1_total.text()) # kOhm
            c1 = float(self.hv_c1_parasitic.text()) # pF
            r2 = float(self.hv_r2.text()) # kOhm
            
            if r2 <= 0: return
            
            c2 = c1 * (r1 / r2)
            self.hv_c2_res.setText(f"{c2:.2f} pF")
        except:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Common Plotting Methods
    # ==============================================================================
    def show_bode_dialog(self, f, T, title):
        try:
            mag = 20*np.log10(np.abs(T))
            phase = np.angle(T, deg=True)
            # Unwrap phase
            phase = np.unwrap(phase*np.pi/180)*180/np.pi
            
            # Find cross over
            # Simple approximate
            idx_cross = np.argmin(np.abs(mag))
            fc_meas = f[idx_cross]
            pm_meas = phase[idx_cross] + 180 # Typical margin calc
            
            plt.rcParams.update({'font.size': 10})
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True, dpi=100)
            
            ax1.semilogx(f, mag, 'b', lw=2)
            ax1.set_ylabel('Gain (dB)'); ax1.set_title(title); 
            ax1.grid(True, which='both', linestyle='--', alpha=0.6); 
            ax1.axhline(y=0, color='k', lw=1)
            ax1.axvline(x=fc_meas, color='r', linestyle=':', label=f'fc={fc_meas/1e3:.1f}kHz')
            ax1.legend()
            
            ax2.semilogx(f, phase, 'g', lw=2)
            ax2.set_ylabel('Phase (deg)'); ax2.set_xlabel('Frequency (Hz)'); 
            ax2.grid(True, which='both', linestyle='--', alpha=0.6)
            ax2.axvline(x=fc_meas, color='r', linestyle=':')
            # Mark PM
            while pm_meas > 180: pm_meas -= 360
            while pm_meas < -180: pm_meas += 360
            ax2.text(fc_meas, phase[idx_cross], f' PM={pm_meas:.1f}°', color='r', fontweight='bold')
            
            dialog = QDialog(self); dialog.setWindowTitle(title); dialog.resize(900, 750)
            layout = QVBoxLayout(dialog)
            scroll = QScrollArea(); content = QWidget(); scroll.setWidget(content); scroll.setWidgetResizable(True)
            l_layout = QVBoxLayout(content)
            img_label = QLabel()
            
            buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            img_label.setPixmap(pixmap)
            
            l_layout.addWidget(img_label)
            layout.addWidget(scroll); dialog.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Plot Error", str(e))

    def show_step_dialog(self, num, den, title):
        try:
            t, y = simulate_step_response(num, den, t_duration=0.005, dt=1e-6)
            os_val, st_val = calc_step_info(t, y)
            
            plt.rcParams.update({'font.size': 10})
            fig, ax = plt.subplots(figsize=(9, 6), dpi=100)
            ax.plot(t*1000, y, 'b-', lw=2)
            ax.axhline(y=1.0, color='k', linestyle='--', lw=1, label="Target")
            ax.set_xlabel("Time (ms)")
            ax.set_ylabel("Normalized Output")
            ax.set_title(title)
            ax.grid(True, alpha=0.6)
            
            # Annotate
            info_text = f"Overshoot: {os_val:.1f}%\nSettling Time: {st_val*1000:.2f}ms"
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, info_text, transform=ax.transAxes, fontsize=11,
                    verticalalignment='top', bbox=props)
            
            dialog = QDialog(self); dialog.setWindowTitle(title); dialog.resize(900, 700)
            layout = QVBoxLayout(dialog)
            
            img_label = QLabel()
            buf = BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight'); plt.close(fig)
            pixmap = QPixmap(); pixmap.loadFromData(buf.getvalue())
            img_label.setPixmap(pixmap)
            
            layout.addWidget(img_label)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Sim Error", str(e))

    def fmt_res(self, val):
        if val >= 1e6: return f"{val/1e6:.2f} MΩ"
        if val >= 1e3: return f"{val/1e3:.2f} kΩ"
        return f"{val:.2f} Ω"
    
    def fmt_cap(self, val):
        if val < 1e-9: return f"{val*1e12:.0f} pF"
        if val < 1e-6: return f"{val*1e9:.1f} nF"
        return f"{val*1e6:.2f} uF"

    def parse_val(self, text):
        if not text: return 0.0
        t = text.split(' ')[0]
        try:
            val = float(t)
        except: return 0.0
        if 'MΩ' in text: val*=1e6
        elif 'kΩ' in text: val*=1e3
        elif 'uF' in text: val*=1e-6
        elif 'nF' in text: val*=1e-9
        elif 'pF' in text: val*=1e-12
        return val

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("环路补偿与光耦偏置指南")
        dialog.resize(850, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            .warn { color: #c0392b; font-weight: bold; }
            .box { background-color: #e8f6f3; padding: 10px; border-left: 5px solid #1abc9c; }
        </style>
        
        <h1>环路补偿设计指南</h1>
        
        <h2>1. 隔离反馈设计 (Isolated Feedback)</h2>
        <div class="box">
            <b>痛点：</b> 反激或 LLC 电源中，光耦不仅传递直流信号，还传递交流误差信号。光耦的 CTR 非线性及低频极点是设计难点。
        </div>
        <h3>关键步骤：</h3>
        <ul>
            <li><b>光耦极点 (Opto Pole):</b> 光耦通常会在 5kHz~20kHz 引入一个极点。这会造成约 45°~90° 的相位滞后。如果不补偿，环路极易在 2kHz 以上震荡。本工具会在计算所需相位提升 (Boost) 时自动扣除这个滞后。</li>
            <li><b>TL431 Type II:</b> 利用 TL431 周围的 R_comp, C_comp 构成 Type II 补偿网络。其零点 $f_z$ 用于抵消功率级的极点，主极点 $f_p$ (由光耦或 C_hf 提供) 用于抑制高频噪声。</li>
        </ul>

        <h2>2. 阶跃响应仿真 (Step Response)</h2>
        <p>频域的 Bode 图虽然专业，但时域的波形更直观。</p>
        <ul>
            <li><b>超调量 (Overshoot):</b> 越小越好。过大的超调可能导致输出过压保护 (OVP)。通常目标 < 10%~20%。</li>
            <li><b>调节时间 (Settling Time):</b> 负载跳变后，电压恢复到稳态范围所需的时间。反映了环路的响应速度（带宽）。带宽越高，恢复越快。</li>
        </ul>

        <h2>3. 高压分压补偿 (HV Divider)</h2>
        <p>在大功率 PFC 或 LLC 中，采样电阻通常很大（MΩ级）。电阻寄生电容会形成低通滤波，导致环路响应变慢。</p>
        <p><b>对策：</b> 在下分压电阻并联电容 $C_{comp}$，使得 $R_1 C_1 = R_2 C_2$，实现零极点对消。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()