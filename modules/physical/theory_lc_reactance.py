from modules.base_module import BaseModule
# lc_basic_window.py

import math
from io import BytesIO
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class LcBasicWindow(BaseModule):
    category = "5. 无源器件与物理连接 (Passives & Physical)"
    display_name = "L/C 基础理论"
    description = "时域特性 / 阻容感抗计算"
    window_id = "theory_lc"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('L/C 基础定义与阻抗计算 (Basic L/C & Reactance)')
        self.setGeometry(350, 350, 950, 750)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部栏
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("时域定义 vs 频域阻抗指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; border-radius: 4px; }
            QTabBar::tab { background: #f0f0f0; border: 1px solid #c0c0c0; padding: 8px 20px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #0078d7; }
        """)

        self.tab_time = QWidget()
        self.tab_react = QWidget() 

        self.init_time_domain_ui(self.tab_time)
        self.init_react_ui(self.tab_react)

        self.tabs.addTab(self.tab_time, "L/C 时域特性")
        self.tabs.addTab(self.tab_react, "阻抗/容抗/感抗计算器 (Reactance)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def _create_label(self, text):
        """统一的标签样式，右对齐"""
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return lbl

    def _create_input(self, text="", read_only=False, color=None):
        """统一的输入框样式，固定宽度"""
        le = QLineEdit(text)
        le.setFixedWidth(110) # 关键：固定宽度防止布局错位
        if read_only:
            le.setReadOnly(True)
            if color:
                le.setStyleSheet(f"background-color: {color}; font-weight: bold; color: #333;")
        return le

    # =========================================================================
    # 1. 统一时域特性页面 (L/C Time Domain UI)
    # =========================================================================
    def init_time_domain_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- 导通/关断时间辅助计算部分 ---
        grp_pwm = QGroupBox("辅助：桥臂中点方波/脉冲时间计算")
        grp_pwm.setStyleSheet("QGroupBox { border: 1px solid #e67e22; border-radius: 4px; margin-top: 10px;} QGroupBox::title { color: #d35400; font-weight: bold; }")
        v_pwm = QVBoxLayout(grp_pwm)
        
        g_in_pwm = QGridLayout()
        self.pwm_fsw = self._create_input("100.0"); self.pwm_fsw.setPlaceholderText("f_sw")
        g_in_pwm.addWidget(self._create_label("开关频率 f_sw [kHz]:"), 0, 0); g_in_pwm.addWidget(self.pwm_fsw, 0, 1)
        self.pwm_d = self._create_input("50.0"); self.pwm_d.setPlaceholderText("D")
        g_in_pwm.addWidget(self._create_label("占空比 D [%]:"), 0, 2); g_in_pwm.addWidget(self.pwm_d, 0, 3)
        
        self.pwm_t = self._create_input(color="#fdf2e9")
        g_in_pwm.addWidget(self._create_label("周期 T [s]:"), 1, 0); g_in_pwm.addWidget(self.pwm_t, 1, 1)
        self.pwm_ton = self._create_input(color="#fdf2e9")
        g_in_pwm.addWidget(self._create_label("导通时间 t_on [s]:"), 1, 2); g_in_pwm.addWidget(self.pwm_ton, 1, 3)
        self.pwm_toff = self._create_input(color="#fdf2e9")
        g_in_pwm.addWidget(self._create_label("关断时间 t_off [s]:"), 1, 4); g_in_pwm.addWidget(self.pwm_toff, 1, 5)
        
        v_pwm.addLayout(g_in_pwm)
        
        btn_pwm = QPushButton("根据频率与占空比计算方波持续时间"); btn_pwm.clicked.connect(self.calc_square_wave_time)
        btn_pwm.setStyleSheet("background-color: #fcece0; color: #d35400; border: 1px solid #edaf7e; border-radius:3px; padding: 5px;")
        v_pwm.addWidget(btn_pwm)
        layout.addWidget(grp_pwm)
        
        # --- 电感部分 ---
        grp_ind = QGroupBox("电感时域计算 (Inductor V = L·di/dt)")
        grp_ind.setStyleSheet("QGroupBox { border: 1px solid #3498db; border-radius: 4px; margin-top: 10px;} QGroupBox::title { color: #2980b9; font-weight: bold; }")
        v_ind = QVBoxLayout(grp_ind)
        
        g_in_ind = QGridLayout()
        self.ind_l = self._create_input("100"); self.ind_l.setPlaceholderText("L")
        g_in_ind.addWidget(self._create_label("电感 L [uH]:"), 0, 0); g_in_ind.addWidget(self.ind_l, 0, 1)
        self.ind_di = self._create_input("2.0"); self.ind_di.setPlaceholderText("di")
        g_in_ind.addWidget(self._create_label("电流变化量 di [A]:"), 0, 2); g_in_ind.addWidget(self.ind_di, 0, 3)
        self.ind_dt = self._create_input("10e-6"); self.ind_dt.setPlaceholderText("dt")
        g_in_ind.addWidget(self._create_label("变化时间 dt [s]:"), 1, 0); g_in_ind.addWidget(self.ind_dt, 1, 1)
        self.ind_i_inst = self._create_input("5.0")
        g_in_ind.addWidget(self._create_label("瞬时电流 I [A]:"), 1, 2); g_in_ind.addWidget(self.ind_i_inst, 1, 3)
        
        self.ind_v_out = self._create_input(color="#e8f8f5"); self.ind_v_out.setPlaceholderText("V_L")
        g_in_ind.addWidget(self._create_label("感应电压 V_L [V]:"), 2, 0); g_in_ind.addWidget(self.ind_v_out, 2, 1)
        self.ind_e_out = self._create_input(read_only=True, color="#e8f8f5")
        g_in_ind.addWidget(self._create_label("磁场储能 E [mJ]:"), 2, 2); g_in_ind.addWidget(self.ind_e_out, 2, 3)
        v_ind.addLayout(g_in_ind)
        
        h_btn_ind = QHBoxLayout()
        btn_ind_v = QPushButton("计算 V_L"); btn_ind_v.clicked.connect(lambda: self.calc_ind_time("V"))
        btn_ind_l = QPushButton("反推 L"); btn_ind_l.clicked.connect(lambda: self.calc_ind_time("L"))
        btn_ind_di = QPushButton("反推 di"); btn_ind_di.clicked.connect(lambda: self.calc_ind_time("DI"))
        btn_ind_dt = QPushButton("反推 dt"); btn_ind_dt.clicked.connect(lambda: self.calc_ind_time("DT"))
        for b in [btn_ind_v, btn_ind_l, btn_ind_di, btn_ind_dt]:
            b.setStyleSheet("background-color: #ebf5fb; color: #2980b9; border: 1px solid #a9cce3; border-radius:3px; padding: 5px;")
            h_btn_ind.addWidget(b)
        h_btn_ind.addStretch()
        v_ind.addLayout(h_btn_ind)
        layout.addWidget(grp_ind)
        
        # --- 电容部分 ---
        grp_cap = QGroupBox("电容时域计算 (Capacitor I = C·dv/dt)")
        grp_cap.setStyleSheet("QGroupBox { border: 1px solid #9b59b6; border-radius: 4px; margin-top: 10px;} QGroupBox::title { color: #8e44ad; font-weight: bold; }")
        v_cap = QVBoxLayout(grp_cap)
        
        g_in_cap = QGridLayout()
        self.cap_c = self._create_input("10"); self.cap_c.setPlaceholderText("C")
        g_in_cap.addWidget(self._create_label("电容 C [uF]:"), 0, 0); g_in_cap.addWidget(self.cap_c, 0, 1)
        self.cap_dv = self._create_input("5.0"); self.cap_dv.setPlaceholderText("dv")
        g_in_cap.addWidget(self._create_label("电压变化量 dv [V]:"), 0, 2); g_in_cap.addWidget(self.cap_dv, 0, 3)
        self.cap_dt = self._create_input("10e-6"); self.cap_dt.setPlaceholderText("dt")
        g_in_cap.addWidget(self._create_label("变化时间 dt [s]:"), 1, 0); g_in_cap.addWidget(self.cap_dt, 1, 1)
        self.cap_v_inst = self._create_input("12.0")
        g_in_cap.addWidget(self._create_label("瞬时电压 V [V]:"), 1, 2); g_in_cap.addWidget(self.cap_v_inst, 1, 3)
        
        self.cap_i_out = self._create_input(color="#f4ecf7"); self.cap_i_out.setPlaceholderText("I_C")
        g_in_cap.addWidget(self._create_label("位移电流 I_C [A]:"), 2, 0); g_in_cap.addWidget(self.cap_i_out, 2, 1)
        self.cap_e_out = self._create_input(read_only=True, color="#f4ecf7")
        g_in_cap.addWidget(self._create_label("电场储能 E [mJ]:"), 2, 2); g_in_cap.addWidget(self.cap_e_out, 2, 3)
        v_cap.addLayout(g_in_cap)
        
        h_btn_cap = QHBoxLayout()
        btn_cap_i = QPushButton("计算 I_C"); btn_cap_i.clicked.connect(lambda: self.calc_cap_time("I"))
        btn_cap_c = QPushButton("反推 C"); btn_cap_c.clicked.connect(lambda: self.calc_cap_time("C"))
        btn_cap_dv = QPushButton("反推 dv"); btn_cap_dv.clicked.connect(lambda: self.calc_cap_time("DV"))
        btn_cap_dt = QPushButton("反推 dt"); btn_cap_dt.clicked.connect(lambda: self.calc_cap_time("DT"))
        for b in [btn_cap_i, btn_cap_c, btn_cap_dv, btn_cap_dt]:
            b.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; border: 1px solid #d2b4de; border-radius:3px; padding: 5px;")
            h_btn_cap.addWidget(b)
        h_btn_cap.addStretch()
        v_cap.addLayout(h_btn_cap)
        layout.addWidget(grp_cap)
        
        # --- 公式图片 ---
        h_form = QHBoxLayout()
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'V_L = L \frac{di}{dt},\; E_L = \frac{1}{2} L I^2 \quad \quad I_C = C \frac{dv}{dt},\; E_C = \frac{1}{2} C V^2'))
        l_form.setAlignment(Qt.AlignCenter)
        h_form.addWidget(l_form)
        layout.addLayout(h_form)

        layout.addStretch()
        tab.setLayout(layout)

    def calc_square_wave_time(self):
        try:
            fsw_khz = float(self.pwm_fsw.text()) if self.pwm_fsw.text() else 0
            d_perc = float(self.pwm_d.text()) if self.pwm_d.text() else 0
            
            if fsw_khz <= 0: raise ValueError("频率必须大于 0")
            if d_perc < 0 or d_perc > 100: raise ValueError("占空比必须在 0 - 100 之间")
            
            t_s = 1.0 / (fsw_khz * 1e3)
            t_on = t_s * (d_perc / 100.0)
            t_off = t_s - t_on
            
            self.pwm_t.setText(f"{t_s:.3e}")
            self.pwm_ton.setText(f"{t_on:.3e}")
            self.pwm_toff.setText(f"{t_off:.3e}")
        except Exception as e: QMessageBox.warning(self, "错误", f"输入有误: {e}")

    def calc_ind_time(self, mode):
        try:
            l = float(self.ind_l.text()) * 1e-6 if self.ind_l.text() else 0
            di = float(self.ind_di.text()) if self.ind_di.text() else 0
            dt = float(self.ind_dt.text()) if self.ind_dt.text() else 0
            v = float(self.ind_v_out.text().replace('V', '').strip()) if self.ind_v_out.text() else 0
            
            i_curr = float(self.ind_i_inst.text()) if self.ind_i_inst.text() else 0

            if mode == "V":
                if dt <= 0: raise ValueError
                self.ind_v_out.setText(f"{l * di / dt:.2f}")
            elif mode == "L":
                if di == 0: raise ValueError
                l_new = (v * dt / di) * 1e6 # Back to uH
                self.ind_l.setText(f"{l_new:.2f}")
            elif mode == "DI":
                if l == 0: raise ValueError
                self.ind_di.setText(f"{v * dt / l:.2f}")
            elif mode == "DT":
                if v == 0: raise ValueError
                self.ind_dt.setText(f"{l * di / v:.3e}")
            
            l = float(self.ind_l.text()) if self.ind_l.text() else 0
            e_mj = 0.5 * l * (i_curr ** 2) / 1000.0
            self.ind_e_out.setText(f"{e_mj:.3f} mJ")
            
        except Exception as e: QMessageBox.warning(self, "错误", "缺少足够参数或者运算错误(除0等)")

    def calc_cap_time(self, mode):
        try:
            c = float(self.cap_c.text()) * 1e-6 if self.cap_c.text() else 0
            dv = float(self.cap_dv.text()) if self.cap_dv.text() else 0
            dt = float(self.cap_dt.text()) if self.cap_dt.text() else 0
            i_c = float(self.cap_i_out.text().replace('A', '').strip()) if self.cap_i_out.text() else 0
            
            v_curr = float(self.cap_v_inst.text()) if self.cap_v_inst.text() else 0

            if mode == "I":
                if dt <= 0: raise ValueError
                self.cap_i_out.setText(f"{c * dv / dt:.2f}")
            elif mode == "C":
                if dv == 0: raise ValueError
                c_new = (i_c * dt / dv) * 1e6 # Back to uF
                self.cap_c.setText(f"{c_new:.2f}")
            elif mode == "DV":
                if c == 0: raise ValueError
                self.cap_dv.setText(f"{i_c * dt / c:.2f}")
            elif mode == "DT":
                if i_c == 0: raise ValueError
                self.cap_dt.setText(f"{c * dv / i_c:.3e}")
            
            c = float(self.cap_c.text()) if self.cap_c.text() else 0
            e_mj = 0.5 * c * (v_curr ** 2) / 1000.0
            self.cap_e_out.setText(f"{e_mj:.3f} mJ")
            
        except Exception as e: QMessageBox.warning(self, "错误", "缺少足够参数或者运算错误(除0等)")

    # =========================================================================
    # 3. 阻抗计算 (Reactance UI)
    # =========================================================================
    def init_react_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 频率设置
        grp_freq = QGroupBox("1. 工作频率设定 (Frequency)")
        f_layout = QHBoxLayout()
        f_layout.addWidget(QLabel("频率 f:"))
        self.react_freq = self._create_input("100")
        f_layout.addWidget(self.react_freq)
        self.react_freq_unit = QComboBox()
        self.react_freq_unit.addItems(["kHz", "Hz", "MHz"])
        self.react_freq_unit.setFixedWidth(70)
        f_layout.addWidget(self.react_freq_unit)
        f_layout.addStretch()
        grp_freq.setLayout(f_layout)
        layout.addWidget(grp_freq)
        
        # --- 电感感抗 ---
        grp_ind = QGroupBox("2. 感抗计算 (Inductive Reactance)")
        grp_ind.setStyleSheet("QGroupBox { border: 1px solid #aab7b8; border-radius: 4px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { color: #2e86c1; font-weight: bold; }")
        
        # 容器布局：左侧表格，右侧图片
        h_ind_container = QHBoxLayout()
        
        # 左侧：输入 + 按钮
        v_ind_left = QVBoxLayout()
        g_ind = QGridLayout()
        g_ind.setVerticalSpacing(10)
        
        self.react_l = self._create_input("22")
        self.react_l.setPlaceholderText("L")
        g_ind.addWidget(self._create_label("电感 L [uH]:"), 0, 0); g_ind.addWidget(self.react_l, 0, 1)
        
        self.react_xl = self._create_input()
        self.react_xl.setPlaceholderText("XL")
        g_ind.addWidget(self._create_label("感抗 X_L [Ω]:"), 0, 2); g_ind.addWidget(self.react_xl, 0, 3)
        g_ind.setColumnStretch(4, 1)
        v_ind_left.addLayout(g_ind)
        
        h_btns = QHBoxLayout()
        btn_xl = QPushButton("计算 X_L"); btn_xl.clicked.connect(lambda: self.calc_reactance("XL"))
        btn_l = QPushButton("反推 L"); btn_l.clicked.connect(lambda: self.calc_reactance("L"))
        btn_f = QPushButton("反推 f"); btn_f.clicked.connect(lambda: self.calc_reactance("F_L"))
        btn_c_from_l = QPushButton("等效 C"); btn_c_from_l.clicked.connect(lambda: self.calc_reactance("C_from_L"))
        
        for b in [btn_xl, btn_l, btn_f, btn_c_from_l]:
            b.setStyleSheet("background-color: #ebf5fb; color: #2e86c1; border: 1px solid #a9cce3; border-radius:3px; padding: 4px 10px;")
            h_btns.addWidget(b)
        h_btns.addStretch()
        v_ind_left.addLayout(h_btns)
        
        h_ind_container.addLayout(v_ind_left, stretch=2)
        
        # 右侧：公式
        l_form_ind = QLabel()
        l_form_ind.setPixmap(self.render_formula(r'X_L = 2 \pi f L'))
        l_form_ind.setAlignment(Qt.AlignCenter)
        h_ind_container.addWidget(l_form_ind, stretch=1)
        
        grp_ind.setLayout(h_ind_container)
        layout.addWidget(grp_ind)
        
        # --- 电容容抗 ---
        grp_cap = QGroupBox("3. 容抗计算 (Capacitive Reactance)")
        grp_cap.setStyleSheet("QGroupBox { border: 1px solid #aab7b8; border-radius: 4px; margin-top: 10px; padding-top: 10px; } QGroupBox::title { color: #884ea0; font-weight: bold; }")
        
        h_cap_container = QHBoxLayout()
        
        v_cap_left = QVBoxLayout()
        g_cap = QGridLayout()
        g_cap.setVerticalSpacing(10)
        
        self.react_c = self._create_input("1")
        self.react_c.setPlaceholderText("C")
        g_cap.addWidget(self._create_label("电容 C [nF]:"), 0, 0); g_cap.addWidget(self.react_c, 0, 1)
        
        self.react_xc = self._create_input()
        self.react_xc.setPlaceholderText("XC")
        g_cap.addWidget(self._create_label("容抗 X_C [Ω]:"), 0, 2); g_cap.addWidget(self.react_xc, 0, 3)
        g_cap.setColumnStretch(4, 1)
        v_cap_left.addLayout(g_cap)
        
        h_btns_c = QHBoxLayout()
        btn_xc = QPushButton("计算 X_C"); btn_xc.clicked.connect(lambda: self.calc_reactance("XC"))
        btn_c = QPushButton("反推 C"); btn_c.clicked.connect(lambda: self.calc_reactance("C"))
        btn_fc = QPushButton("反推 f"); btn_fc.clicked.connect(lambda: self.calc_reactance("F_C"))
        btn_l_from_c = QPushButton("等效 L"); btn_l_from_c.clicked.connect(lambda: self.calc_reactance("L_from_C"))
        
        for b in [btn_xc, btn_c, btn_fc, btn_l_from_c]:
            b.setStyleSheet("background-color: #f4ecf7; color: #884ea0; border: 1px solid #d2b4de; border-radius:3px; padding: 4px 10px;")
            h_btns_c.addWidget(b)
        h_btns_c.addStretch()
        v_cap_left.addLayout(h_btns_c)
        
        h_cap_container.addLayout(v_cap_left, stretch=2)
        
        l_form_cap = QLabel()
        l_form_cap.setPixmap(self.render_formula(r'X_C = \frac{1}{2 \pi f C}'))
        l_form_cap.setAlignment(Qt.AlignCenter)
        h_cap_container.addWidget(l_form_cap, stretch=1)
        
        grp_cap.setLayout(h_cap_container)
        layout.addWidget(grp_cap)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_reactance(self, mode):
        try:
            f_val = float(self.react_freq.text())
            f_unit = self.react_freq_unit.currentText()
            if f_unit == "kHz": f = f_val * 1e3
            elif f_unit == "MHz": f = f_val * 1e6
            else: f = f_val
            
            if f <= 0 and "F_" not in mode: raise ValueError("频率必须大于0")
            
            if mode == "XL":
                l_uh = float(self.react_l.text()); l = l_uh * 1e-6
                xl = 2 * math.pi * f * l
                self.react_xl.setText(f"{xl:.2f}")
            elif mode == "L":
                xl = float(self.react_xl.text()); l = xl / (2 * math.pi * f)
                self.react_l.setText(f"{l*1e6:.2f}")
            elif mode == "F_L":
                l_uh = float(self.react_l.text()); xl = float(self.react_xl.text())
                f_res = xl / (2 * math.pi * l_uh * 1e-6)
                self.update_freq_display(f_res)
            elif mode == "C_from_L":
                xl = float(self.react_xl.text())
                c = 1 / (2 * math.pi * f * xl)
                self.react_c.setText(f"{c*1e9:.2f}")
                self.react_xc.setText(f"{xl:.2f}")
            elif mode == "XC":
                c_nf = float(self.react_c.text()); c = c_nf * 1e-9
                xc = 1 / (2 * math.pi * f * c)
                self.react_xc.setText(f"{xc:.2f}")
            elif mode == "C":
                xc = float(self.react_xc.text()); c = 1 / (2 * math.pi * f * xc)
                self.react_c.setText(f"{c*1e9:.2f}")
            elif mode == "F_C":
                c_nf = float(self.react_c.text()); xc = float(self.react_xc.text())
                f_res = 1 / (2 * math.pi * c_nf * 1e-9 * xc)
                self.update_freq_display(f_res)
            elif mode == "L_from_C":
                xc = float(self.react_xc.text())
                l = xc / (2 * math.pi * f)
                self.react_l.setText(f"{l*1e6:.2f}")
                self.react_xl.setText(f"{xc:.2f}")
        except Exception as e: QMessageBox.warning(self, "错误", "输入数值无效")

    def update_freq_display(self, f_hz):
        if f_hz >= 1e6: self.react_freq.setText(f"{f_hz/1e6:.3f}"); self.react_freq_unit.setCurrentIndex(2) 
        elif f_hz >= 1e3: self.react_freq.setText(f"{f_hz/1e3:.3f}"); self.react_freq_unit.setCurrentIndex(0) 
        else: self.react_freq.setText(f"{f_hz:.2f}"); self.react_freq_unit.setCurrentIndex(1)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("基础 L/C 定义与阻抗指南")
        dialog.resize(750, 600)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        html = """
        <style>
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h3 { color: #e67e22; margin-top: 15px; }
            li { margin-bottom: 5px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
        </style>
        <h2>1. 时域特性 (Time Domain)</h2>
        <p>这是电感和电容最本质的定义，描述它们如何响应电压或电流的<b>变化率</b>。</p>
        <ul>
            <li><b>电感 (L):</b> 阻碍电流变化。公式 <code>V = L * di/dt</code>。
                <br>应用：计算 Buck 电感的纹波电流、MOSFET 关断时的电压尖峰 ($V_{spike}$).
            </li>
            <li><b>电容 (C):</b> 阻碍电压变化。公式 <code>I = C * dv/dt</code>。
                <br>应用：计算电容的充放电时间、米勒效应的等效电容电流。
            </li>
        </ul>
        <h2>2. 频域特性 (Frequency Domain - Reactance)</h2>
        <p>当电路工作在稳态正弦波（或开关频率基波）下时，我们用<b>阻抗 (Reactance)</b> 来描述。</p>
        <ul>
            <li><b>感抗 (X_L):</b> 频率越高，阻抗越大。<code>X_L = 2π * f * L</code></li>
            <li><b>容抗 (X_C):</b> 频率越高，阻抗越小。<code>X_C = 1 / (2π * f * C)</code></li>
        </ul>
        <h3>工程速算经验：</h3>
        <ul>
            <li><b>100uH @ 100kHz:</b> 感抗约为 63Ω。</li>
            <li><b>1uF @ 100kHz:</b> 容抗约为 1.6Ω。</li>
            <li><b>谐振点:</b> 当 X_L = X_C 时发生谐振，此时 <code>f = 1 / (2π√LC)</code>。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()