from modules.base_module import BaseModule
# power_waveform_rms.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QTabWidget, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

class WaveformCalculatorWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "波形 RMS 计算"
    description = "梯形 / 三角 / 正弦 / PWM"
    window_id = "power_waveform"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('波形数学模型与特征参数分析 (Waveform Analytics)')
        self.setGeometry(300, 300, 1050, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- 顶部栏：标题与教程 ---
        top_bar = QHBoxLayout()
        header_lbl = QLabel("基于线性分段微积分模型，推导任意电力电子波形的有效值 (RMS)、平均值 (AVG) 及交流热应力 (AC_RMS)。")
        header_lbl.setStyleSheet("color: #7f8c8d; font-style: italic; font-weight: bold;")
        top_bar.addWidget(header_lbl)
        
        top_bar.addStretch()
        
        self.help_btn = QPushButton("波形公式推导底层算法与理论")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(280)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        
        main_layout.addLayout(top_bar)

        # --- Tab 页签 ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; color: #3498db; }
        """)

        self.tab_trap = QWidget()
        self.tab_rect = QWidget()
        self.tab_sine = QWidget()
        self.tab_decouple = QWidget()

        self.init_trap_ui(self.tab_trap)
        self.init_rect_ui(self.tab_rect)
        self.init_sine_ui(self.tab_sine)
        self.init_decouple_ui(self.tab_decouple)

        self.tabs.addTab(self.tab_trap, "1. 梯形与三角波族 (CCM/DCM)")
        self.tabs.addTab(self.tab_rect, "2. 矩形与阶梯波族 (Square/PWM)")
        self.tabs.addTab(self.tab_sine, "3. 正弦及其衍生波 (Sine/Phase-Control)")
        self.tabs.addTab(self.tab_decouple, "4. 交直流解耦与复合波形")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def _create_result_field(self):
        w = QLineEdit()
        w.setReadOnly(True)
        w.setStyleSheet("background:#f9fbfc; color:#2c3e50; font-weight:bold; font-size:14px; border: 1px solid #dcdde1; border-radius: 3px; padding: 3px;")
        return w

    # ==============================================================================
    # Tab 1: 梯形波 & 三角波 (CCM / DCM)
    # ==============================================================================
    def init_trap_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("本页面基于由电感积分引申出的<b>线性分段波形母体公式</b>，计算 CCM 和 DCM 运行模式下的各类脉冲波形。")
        info.setStyleSheet("color: #34495e; margin-bottom: 10px;")
        layout.addWidget(info)
        
        h_main = QHBoxLayout()
        
        # -- 梯形脉冲波 (CCM) --
        grp_ccm = QGroupBox("1. 梯形脉冲波 (CCM)")
        grp_ccm.setStyleSheet("QGroupBox { border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 10px; } QGroupBox::title { color: #2980b9; font-weight: bold; }")
        g1 = QGridLayout()
        g1.setVerticalSpacing(12)
        
        self.trap_d = QLineEdit("0.45"); g1.addWidget(QLabel("波形占空比 D (总占比):"), 0, 0); g1.addWidget(self.trap_d, 0, 1)
        self.trap_max = QLineEdit("12"); g1.addWidget(QLabel("最大值 I_max/V_max:"), 1, 0); g1.addWidget(self.trap_max, 1, 1)
        self.trap_min = QLineEdit("6"); g1.addWidget(QLabel("最小值 I_min/V_min:"), 2, 0); g1.addWidget(self.trap_min, 2, 1)
        
        btn_trap = QPushButton("计算梯形波参数"); btn_trap.clicked.connect(self.calc_trap)
        btn_trap.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; height: 35px;")
        g1.addWidget(btn_trap, 3, 0, 1, 2)
        
        self.trap_avg = self._create_result_field(); self.trap_rms = self._create_result_field()
        self.trap_ac = self._create_result_field(); self.trap_kf = self._create_result_field()
        
        g1.addWidget(QLabel("均方根/有效值 (RMS):"), 4, 0); g1.addWidget(self.trap_rms, 4, 1)
        g1.addWidget(QLabel("直流平均值 (AVG):"), 5, 0); g1.addWidget(self.trap_avg, 5, 1)
        g1.addWidget(QLabel("交流热损耗 (AC_RMS):"), 6, 0); g1.addWidget(self.trap_ac, 6, 1)
        g1.addWidget(QLabel("波形/峰值因数 (K_f / K_p):"), 7, 0); g1.addWidget(self.trap_kf, 7, 1)
        
        f1 = QLabel(); f1.setPixmap(render_formula(r'RMS = \sqrt{D \cdot \frac{I_{max}^2 + I_{max}I_{min} + I_{min}^2}{3}}'))
        g1.addWidget(f1, 8, 0, 1, 2, alignment=Qt.AlignCenter)
        grp_ccm.setLayout(g1)
        
        # -- 断续三角波 (DCM) --
        grp_dcm = QGroupBox("2. 断续三角波 (DCM)")
        grp_dcm.setStyleSheet("QGroupBox { border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 10px; } QGroupBox::title { color: #8e44ad; font-weight: bold; }")
        g2 = QGridLayout()
        g2.setVerticalSpacing(12)
        
        self.dcm_d1 = QLineEdit("0.3"); g2.addWidget(QLabel("上升时间占空比 D1:"), 0, 0); g2.addWidget(self.dcm_d1, 0, 1)
        self.dcm_d2 = QLineEdit("0.4"); g2.addWidget(QLabel("下降时间占空比 D2:"), 1, 0); g2.addWidget(self.dcm_d2, 1, 1)
        self.dcm_pk = QLineEdit("10"); g2.addWidget(QLabel("最高峰值 I_peak:"), 2, 0); g2.addWidget(self.dcm_pk, 2, 1)
        
        btn_dcm = QPushButton("计算三角波参数"); btn_dcm.clicked.connect(self.calc_dcm)
        btn_dcm.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; height: 35px;")
        g2.addWidget(btn_dcm, 3, 0, 1, 2)
        
        self.dcm_avg = self._create_result_field(); self.dcm_rms = self._create_result_field()
        self.dcm_ac = self._create_result_field(); self.dcm_kf = self._create_result_field()
        
        g2.addWidget(QLabel("均方根/有效值 (RMS):"), 4, 0); g2.addWidget(self.dcm_rms, 4, 1)
        g2.addWidget(QLabel("直流平均值 (AVG):"), 5, 0); g2.addWidget(self.dcm_avg, 5, 1)
        g2.addWidget(QLabel("交流热损耗 (AC_RMS):"), 6, 0); g2.addWidget(self.dcm_ac, 6, 1)
        g2.addWidget(QLabel("波形/峰值因数 (K_f / K_p):"), 7, 0); g2.addWidget(self.dcm_kf, 7, 1)
        
        f2 = QLabel(); f2.setPixmap(render_formula(r'RMS = I_{peak} \sqrt{\frac{D_1+D_2}{3}}'))
        g2.addWidget(f2, 8, 0, 1, 2, alignment=Qt.AlignCenter)
        grp_dcm.setLayout(g2)
        
        h_main.addWidget(grp_ccm)
        h_main.addWidget(grp_dcm)
        layout.addLayout(h_main)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_trap(self):
        try:
            d = float(self.trap_d.text())
            imax = float(self.trap_max.text())
            imin = float(self.trap_min.text())
            if d < 0 or d > 1: raise ValueError
            
            avg = d * (imax + imin) / 2.0
            rms = math.sqrt(d * (imax**2 + imax*imin + imin**2) / 3.0)
            ac = math.sqrt(max(0, rms**2 - avg**2))
            kf = rms / avg if avg > 0 else 0
            kp = imax / rms if rms > 0 else 0
            
            self.trap_avg.setText(f"{avg:.4f}")
            self.trap_rms.setText(f"{rms:.4f}")
            self.trap_ac.setText(f"{ac:.4f}")
            self.trap_kf.setText(f"Kf:{kf:.2f} | Kp:{kp:.2f}")
        except: pass

    def calc_dcm(self):
        try:
            d1 = float(self.dcm_d1.text())
            d2 = float(self.dcm_d2.text())
            ipk = float(self.dcm_pk.text())
            if d1 < 0 or d2 < 0 or (d1+d2) > 1: raise ValueError
            
            dt = d1 + d2
            avg = dt * ipk / 2.0
            rms = ipk * math.sqrt(dt / 3.0)
            ac = math.sqrt(max(0, rms**2 - avg**2))
            kf = rms / avg if avg > 0 else 0
            kp = ipk / rms if rms > 0 else 0
            
            self.dcm_avg.setText(f"{avg:.4f}")
            self.dcm_rms.setText(f"{rms:.4f}")
            self.dcm_ac.setText(f"{ac:.4f}")
            self.dcm_kf.setText(f"Kf:{kf:.2f} | Kp:{kp:.2f}")
        except: pass

    # ==============================================================================
    # Tab 2: 矩形与阶梯波族
    # ==============================================================================
    def init_rect_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("本页针对常见的 <b>PWM 矩形方波、双极性对称方波、以及全桥移相时的准方波</b>。用于快速分析驱动信号与原边脉冲。")
        info.setStyleSheet("color: #34495e; margin-bottom: 15px;")
        layout.addWidget(info)
        
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        # 输入区
        self.rect_pk = QLineEdit("5"); grid.addWidget(QLabel("脉冲峰值 V_peak/I_pk:"), 0, 0); grid.addWidget(self.rect_pk, 0, 1)
        self.rect_d = QLineEdit("0.45"); self.rect_d.setToolTip("对于单极性和准方波有效。双极性方波忽略此项。")
        grid.addWidget(QLabel("占空比 D (或移相周期比) [0~1]:"), 0, 2); grid.addWidget(self.rect_d, 0, 3)
        
        btn = QPushButton("计算方波与矩形波参数")
        btn.setFixedHeight(40)
        btn.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_rect)
        grid.addWidget(btn, 1, 0, 1, 4)
        layout.addLayout(grid)
        
        # 结果区
        grp_res = QGroupBox("各方波族计算结果对比")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        # Labels
        r_grid.addWidget(QLabel("<b>波形类型</b>"), 0, 0)
        r_grid.addWidget(QLabel("<b>直流平均值 (AVG)</b>"), 0, 1)
        r_grid.addWidget(QLabel("<b>均方根有效值 (RMS)</b>"), 0, 2)
        r_grid.addWidget(QLabel("<b>峰值因数 (Kp)</b>"), 0, 3)
        
        # 1. 单极性
        self.r1_avg = self._create_result_field(); self.r1_rms = self._create_result_field(); self.r1_kp = self._create_result_field()
        r_grid.addWidget(QLabel("单极性脉冲方波\n(如: 单管PWM, 驱动)"), 1, 0)
        r_grid.addWidget(self.r1_avg, 1, 1); r_grid.addWidget(self.r1_rms, 1, 2); r_grid.addWidget(self.r1_kp, 1, 3)
        
        # 2. 双极性对称
        self.r2_avg = self._create_result_field(); self.r2_rms = self._create_result_field(); self.r2_kp = self._create_result_field()
        r_grid.addWidget(QLabel("双极性对称方波\n(如: 纯全桥逆变输出)"), 2, 0)
        r_grid.addWidget(self.r2_avg, 2, 1); r_grid.addWidget(self.r2_rms, 2, 2); r_grid.addWidget(self.r2_kp, 2, 3)
        
        # 3. 准方波
        self.r3_avg = self._create_result_field(); self.r3_rms = self._create_result_field(); self.r3_kp = self._create_result_field()
        r_grid.addWidget(QLabel("准方波 / 移相方波\n(如: PSFB, 有死区的全桥)"), 3, 0)
        r_grid.addWidget(self.r3_avg, 3, 1); r_grid.addWidget(self.r3_rms, 3, 2); r_grid.addWidget(self.r3_kp, 3, 3)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 公式参考
        f_box = QHBoxLayout()
        f_box.addWidget(QLabel("单极性："))
        lbl_rect1 = QLabel()
        lbl_rect1.setPixmap(render_formula(r'RMS = \sqrt{D} \cdot I_{pk}'))
        f_box.addWidget(lbl_rect1)
        f_box.addStretch()
        f_box.addWidget(QLabel("双极性："))
        lbl_rect2 = QLabel()
        lbl_rect2.setPixmap(render_formula(r'RMS = I_{pk}'))
        f_box.addWidget(lbl_rect2)
        f_box.addStretch()
        f_box.addWidget(QLabel("准方波："))
        lbl_rect3 = QLabel()
        lbl_rect3.setPixmap(render_formula(r'RMS = \sqrt{D} \cdot I_{pk} \quad (\text{Bidirectional } D \in [0,1])'))
        f_box.addWidget(lbl_rect3)
        layout.addLayout(f_box)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_rect(self):
        try:
            ipk = float(self.rect_pk.text())
            d = float(self.rect_d.text())
            if d < 0 or d > 1: raise ValueError
            
            # 单极性
            a1 = d * ipk
            r1 = math.sqrt(d) * ipk
            self.r1_avg.setText(f"{a1:.4f}"); self.r1_rms.setText(f"{r1:.4f}")
            self.r1_kp.setText(f"{ipk/r1:.3f}" if r1>0 else "NaN")
            
            # 双极性
            a2 = 0.0
            r2 = ipk
            self.r2_avg.setText(f"{a2:.4f}"); self.r2_rms.setText(f"{r2:.4f}")
            self.r2_kp.setText(f"{ipk/r2:.3f}" if r2>0 else "NaN")
            
            # 准方波 (正半周占D/2时间，负半周占D/2时间的D为周期比，或者单向导通算作D。根据理论公式都是 sqrt(D)*Ipk)
            a3 = 0.0
            r3 = math.sqrt(d) * ipk
            self.r3_avg.setText(f"{a3:.4f}"); self.r3_rms.setText(f"{r3:.4f}")
            self.r3_kp.setText(f"{ipk/r3:.3f}" if r3>0 else "NaN")
            
        except: pass

    # ==============================================================================
    # Tab 3: 正弦及其衍生波
    # ==============================================================================
    def init_sine_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("<b>衍生波形说明：</b> 全波/半波整流通常存在于 AC/DC 前级；相控截断波常见于晶闸管或 Triac 调光电路。")
        info.setStyleSheet("color: #34495e; margin-bottom: 15px;")
        layout.addWidget(info)
        
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.sin_pk = QLineEdit("311.12"); grid.addWidget(QLabel("正弦波绝对峰值 (V_peak):"), 0, 0); grid.addWidget(self.sin_pk, 0, 1)
        self.sin_alpha = QLineEdit("60"); grid.addWidget(QLabel("相控触发角 α [度°] (0~180):"), 0, 2); grid.addWidget(self.sin_alpha, 0, 3)
        
        btn = QPushButton("计算正弦系列波形"); btn.clicked.connect(self.calc_sine)
        btn.setFixedHeight(40); btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        grid.addWidget(btn, 1, 0, 1, 4)
        layout.addLayout(grid)
        
        # 结果阵列
        grp_res = QGroupBox("各种正弦衍生波对比")
        r = QGridLayout()
        r.setVerticalSpacing(15)
        
        headers = ["波形类型", "直流均值 (AVG)", "有效值 (RMS)", "峰值因数 (Kp)"]
        for i, h in enumerate(headers): r.addWidget(QLabel(f"<b>{h}</b>"), 0, i)
        
        self.s1_avg = self._create_result_field(); self.s1_rms = self._create_result_field(); self.s1_kp = self._create_result_field()
        r.addWidget(QLabel("纯正弦波\n(Pure Sine)"), 1, 0); r.addWidget(self.s1_avg, 1, 1); r.addWidget(self.s1_rms, 1, 2); r.addWidget(self.s1_kp, 1, 3)
        
        self.s2_avg = self._create_result_field(); self.s2_rms = self._create_result_field(); self.s2_kp = self._create_result_field()
        r.addWidget(QLabel("全波整流波\n(Full-Wave)"), 2, 0); r.addWidget(self.s2_avg, 2, 1); r.addWidget(self.s2_rms, 2, 2); r.addWidget(self.s2_kp, 2, 3)
        
        self.s3_avg = self._create_result_field(); self.s3_rms = self._create_result_field(); self.s3_kp = self._create_result_field()
        r.addWidget(QLabel("半波整流波\n(Half-Wave)"), 3, 0); r.addWidget(self.s3_avg, 3, 1); r.addWidget(self.s3_rms, 3, 2); r.addWidget(self.s3_kp, 3, 3)
        
        self.s4_avg = self._create_result_field(); self.s4_rms = self._create_result_field(); self.s4_kp = self._create_result_field()
        r.addWidget(QLabel("相控截断正弦波\n(Phase-Controlled)"), 4, 0); r.addWidget(self.s4_avg, 4, 1); r.addWidget(self.s4_rms, 4, 2); r.addWidget(self.s4_kp, 4, 3)
        
        grp_res.setLayout(r)
        layout.addWidget(grp_res)
        
        # 补充相控公式
        f_lbl = QLabel()
        f_lbl.setPixmap(render_formula(r'RMS_{Triac} = V_{pk} \sqrt{ \frac{\pi-\alpha}{2\pi} + \frac{\sin(2\alpha)}{4\pi} }'))
        f_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(f_lbl)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_sine(self):
        try:
            ipk = float(self.sin_pk.text())
            alpha_deg = float(self.sin_alpha.text())
            if alpha_deg < 0 or alpha_deg > 180: raise ValueError
            
            # Pure Sine
            a1 = 0; r1 = ipk / math.sqrt(2)
            self.s1_avg.setText(f"{a1:.4f}"); self.s1_rms.setText(f"{r1:.4f}"); self.s1_kp.setText(f"{math.sqrt(2):.3f}")
            
            # Full Wave
            a2 = 2 * ipk / math.pi; r2 = r1
            self.s2_avg.setText(f"{a2:.4f}"); self.s2_rms.setText(f"{r2:.4f}"); self.s2_kp.setText(f"{math.sqrt(2):.3f}")
            
            # Half Wave
            a3 = ipk / math.pi; r3 = ipk / 2.0
            self.s3_avg.setText(f"{a3:.4f}"); self.s3_rms.setText(f"{r3:.4f}"); self.s3_kp.setText(f"{2.0:.3f}")
            
            # Phase Controlled
            alpha_rad = math.radians(alpha_deg)
            term1 = (math.pi - alpha_rad) / (2 * math.pi)
            term2 = math.sin(2 * alpha_rad) / (4 * math.pi)
            r4 = ipk * math.sqrt(term1 + term2)
            
            # 相控半周期内平均值: (1/pi)*integral_alpha^pi (Vpk sin t) dt = Vpk/pi * [cos(alpha) + 1] 
            # 双向全波相控的话平均值为0。此处展示绝对均值（如调压桥）
            a4 = (ipk / math.pi) * (math.cos(alpha_rad) + 1.0)
            
            self.s4_avg.setText(f"{a4:.4f}"); self.s4_rms.setText(f"{r4:.4f}"); self.s4_kp.setText(f"{ipk/r4:.3f}" if r4>0 else "NaN")
        except: pass

    # ==============================================================================
    # Tab 4: 交直流解耦与电容纹波 (AC/DC / Ripple)
    # ==============================================================================
    def init_decouple_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel(
            "<b>物理实质：</b> 任意周期波形的均方有效值平方，等于其直流均值的平方 加上 交流纹波有效值的平方。即：$I_{rms}^2 = I_{avg}^2 + I_{ac\\_rms}^2$ <br>"
            "<b>典型应用：</b> 基于输出中心电流与峰峰值计算电容纹波吸收应力。"
        )
        info.setStyleSheet("color: #34495e; margin-bottom: 15px;")
        layout.addWidget(info)
        
        # Part A: 通用交直流分量解耦
        g1 = QGroupBox("A. 通用交直流逆向解耦推导")
        g1.setStyleSheet("QGroupBox { border: 1px solid #16a085; border-radius: 5px; } QGroupBox::title { color: #16a085; font-weight: bold; }")
        gl = QGridLayout()
        gl.setVerticalSpacing(10)
        
        self.dec_total = QLineEdit(); self.dec_avg = QLineEdit()
        gl.addWidget(QLabel("总有效值 (Total RMS):"), 0, 0); gl.addWidget(self.dec_total, 0, 1)
        gl.addWidget(QLabel("直流极性值 (DC AVG):"), 1, 0); gl.addWidget(self.dec_avg, 1, 1)
        
        btn_dec = QPushButton("=> 计算扣除直流后的纯交流热损耗 (AC RMS)")
        btn_dec.clicked.connect(self.calc_decouple)
        gl.addWidget(btn_dec, 2, 0, 1, 2)
        
        self.dec_ac = self._create_result_field()
        self.dec_ac.setStyleSheet("background: #fdf2e9; color: #d35400; font-weight: bold; font-size: 16px;")
        gl.addWidget(QLabel("<b>解耦出交流热应力 (AC_RMS):</b>"), 3, 0); gl.addWidget(self.dec_ac, 3, 1)
        
        g1.setLayout(gl)
        layout.addWidget(g1)
        
        # Part B: 基于工程直觉的纹波有效值生成
        g2 = QGroupBox("B. 直流电感中心电流与交流纹波特征公式")
        g2.setStyleSheet("QGroupBox { border: 1px solid #c0392b; border-radius: 5px; margin-top: 15px;} QGroupBox::title { color: #c0392b; font-weight: bold; }")
        g2l = QGridLayout()
        g2l.setVerticalSpacing(10)
        
        self.rip_center = QLineEdit("10"); g2l.addWidget(QLabel("中心直流分量 (I_p):"), 0, 0); g2l.addWidget(self.rip_center, 0, 1)
        self.rip_pp = QLineEdit("3"); g2l.addWidget(QLabel("峰峰纹波扰动 (\u0394I):"), 1, 0); g2l.addWidget(self.rip_pp, 1, 1)
        
        btn_rip = QPushButton("=> 快速合成各类指标")
        btn_rip.clicked.connect(self.calc_ripple)
        g2l.addWidget(btn_rip, 2, 0, 1, 2)
        
        self.rip_cap = self._create_result_field()
        self.rip_lrms = self._create_result_field()
        
        g2l.addWidget(QLabel("滤波电容器承担交流纹波 RMS (<font color=blue>I_cap_rms = \u0394I / 2\u221A3</font>):"), 3, 0); g2l.addWidget(self.rip_cap, 3, 1)
        g2l.addWidget(QLabel("磁性元件总体热应力计算 RMS (<font color=red>\u221A(I_p² + \u0394I²/12)</font>):"), 4, 0); g2l.addWidget(self.rip_lrms, 4, 1)
        
        g2.setLayout(g2l)
        layout.addWidget(g2)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_decouple(self):
        try:
            total = float(self.dec_total.text())
            avg = float(self.dec_avg.text())
            if avg > total: raise ValueError
            ac = math.sqrt(total**2 - avg**2)
            self.dec_ac.setText(f"{ac:.4f}")
        except: pass

    def calc_ripple(self):
        try:
            ip = float(self.rip_center.text())
            delta = float(self.rip_pp.text())
            
            icap = delta / (2 * math.sqrt(3))
            ilrms = math.sqrt(ip**2 + (delta**2)/12.0)
            
            self.rip_cap.setText(f"{icap:.4f}")
            self.rip_lrms.setText(f"{ilrms:.4f}")
            
            self.dec_total.setText(f"{ilrms:.4f}")
            self.dec_avg.setText(f"{ip:.4f}")
        except: pass

    # ==============================================================================
    # 理论指南弹窗
    # ==============================================================================
    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("波形公式推导理论指引")
        dialog.resize(900, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #fcfcfc; padding: 10px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;")
        
        # 严格使用用户传入的 Markdown 原件转换为格式良好的 HTML
        html = r"""
        <style>
            body { font-size: 14px; line-height: 1.6; color: #333;}
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #2980b9; margin-top: 25px; border-bottom: 1px dotted #ccc; }
            h3 { color: #e67e22; margin-top: 20px; }
            p { margin: 10px 0; }
            .math { font-family: 'Cambria Math', serif; background: #f1f2f6; padding: 2px 5px; border-radius: 4px; color: #c0392b; font-size: 15px;}
            pre { background-color: #f1f2f6; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: Consolas, monospace;}
            table { width: 100%; border-collapse: collapse; margin-top: 15px; }
            th, td { border: 1px solid #bdc3c7; padding: 8px 12px; text-align: left; }
            th { background-color: #ecf0f1; color: #2c3e50; font-weight: bold;}
            td { font-size: 13.5px; }
        </style>
        
        <h1>波形公式推导原理</h1>
        
        <h2>电力电子波形</h2>
        <p>在电力电子变换器中，所有的电流波形演变均源于电磁元件的物理特性。以电感元件为例，其两端电压 <span class="math">V_L</span> 与流过电流 <span class="math">i</span> 的关系满足法拉第定律：</p>
        <p><span class="math">V_L = L \frac{di}{dt} \quad \implies \quad i(t) = \int \frac{V_L}{L} dt = K \cdot t + I_{initial}</span></p>
        <p>稳态下开关阶段的 <span class="math">V_L</span> 为常数，由此奠定了电力电子电流波形是<b>线性分段斜坡</b>的数学本质。</p>
        
        <h2>线性分段波形数学模型与梯形脉冲</h2>
        <p>一个从 <span class="math">I_{min}</span> 线性变化到 <span class="math">I_{max}</span> 的时段 <span class="math">T_{on}</span>，对其平方积分得出均方值为：</p>
        <p><span class="math">Mean\ Square = \frac{I_{max}^2 + I_{max} \cdot I_{min} + I_{min}^2}{3}</span></p>
        
        <h3>工程常用变体公式推导：</h3>
        <p>将导通中心电流 <span class="math">I_p</span> 和纹波峰峰值 <span class="math">\Delta I</span> 引入，代入后极大地精简了数学模型：</p>
        <p><span class="math">I_{rms} = \sqrt{D \cdot \left(I_p^2 + \frac{\Delta I^2}{12}\right)}</span></p>
        <p>这个公式直观地说明了：<br><b>总有效值的平方 = 直流均值的平方 + 纯交流发热能量的平方</b>，即著名的 <span class="math">\Delta I / 2\sqrt{3}</span> 定律在此生根发芽。</p>

        <h2>交直流解耦与复合波形</h2>
        <p>任意周期波形均有： <span class="math">F_{rms}^2 = F_{avg}^2 + F_{ac\_rms}^2</span></p>
        <p>在 DC-DC 中，由于电容器不能流过直流，其吃下的纹波完全等同于总波形中的交流分量！</p>
        
        <h2>常用波形参数极限速查表</h2>
        <table>
            <tr><th>波形类型</th><th>平均值 (AVG)</th><th>有效值 (RMS)</th><th>交流有效值 (AC)</th><th>备注</th></tr>
            <tr><td><b>纯直流</b></td><td><span class="math">I_{dc}</span></td><td><span class="math">I_{dc}</span></td><td>0</td><td>电池、负载特性</td></tr>
            <tr><td><b>梯形脉冲波</b></td><td><span class="math">D \frac{I_{max}+I_{min}}{2}</span></td><td><span class="math">\sqrt{D \frac{I_{max}^2+I_{max}I_{min}+I_{min}^2}{3}}</span></td><td><span class="math">\sqrt{D \frac{\Delta I^2}{12}}</span></td><td>MOS管导通电流</td></tr>
            <tr><td><b>矩形脉冲</b></td><td><span class="math">D \cdot I_{pk}</span></td><td><span class="math">\sqrt{D} \cdot I_{pk}</span></td><td>-</td><td>方波近似</td></tr>
            <tr><td><b>连续三角波 (CCM)</b></td><td><span class="math">\frac{I_{max}+I_{min}}{2}</span></td><td><span class="math">\sqrt{ \frac{I_{max}^2+I_{max}I_{min}+I_{min}^2}{3} }</span></td><td><span class="math">\frac{\Delta I}{2\sqrt{3}}</span></td><td>CCM电感电流</td></tr>
            <tr><td><b>断续三角波 (DCM)</b></td><td><span class="math">\frac{D+D_2}{2}I_{pk}</span></td><td><span class="math">I_{pk} \sqrt{\frac{D+D_2}{3}}</span></td><td>-</td><td>DCM电感电流</td></tr>
            <tr><td><b>全波整流波</b></td><td><span class="math">\frac{2I_{pk}}{\pi}</span></td><td><span class="math">\frac{I_{pk}}{\sqrt{2}}</span></td><td>-</td><td>PFC/整流桥后</td></tr>
        </table>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        btn_close = QPushButton("已阅")
        btn_close.clicked.connect(dialog.close)
        btn_close.setStyleSheet("background-color: #34495e; color: white; padding: 5px;")
        layout.addWidget(btn_close)
        
        dialog.exec_()