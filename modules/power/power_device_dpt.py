from modules.base_module import BaseModule
# power_device_dpt.py
import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QTabWidget, QDialog, QTextBrowser, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

class DoublePulseTestWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "双脉冲实验 (DPT)"
    description = "开关与损耗评估"
    window_id = "power_dpt"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('双脉冲测试仪 (Double Pulse Test - DPT)')
        self.setGeometry(350, 350, 950, 650)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部栏：标题与教程
        top_bar = QHBoxLayout()
        header_lbl = QLabel("SiC/GaN/IGBT 双脉冲实验：脉宽发生器计算与开关特性评估。")
        header_lbl.setStyleSheet("color: #7f8c8d; font-style: italic; font-weight: bold;")
        top_bar.addWidget(header_lbl)
        
        top_bar.addStretch()
        
        self.help_btn = QPushButton("DPT 实验指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(180)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        
        main_layout.addLayout(top_bar)

        # Tab 页签
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_generator = QWidget()
        self.tab_evaluator = QWidget()

        self.init_generator_ui(self.tab_generator)
        self.init_evaluator_ui(self.tab_evaluator)

        self.tabs.addTab(self.tab_generator, "1. 脉宽发生器速算 (Pulse Width Calc)")
        self.tabs.addTab(self.tab_evaluator, "2. 损耗与开关速度评估 (Switching Eval)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 脉宽计算
    # ==============================================================================
    def init_generator_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_in = QGroupBox("输入实验条件")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.dpt_vdc = QLineEdit("400")
        grid.addWidget(QLabel("母线测试电压 V_DC [V]:"), 0, 0); grid.addWidget(self.dpt_vdc, 0, 1)
        
        self.dpt_imax = QLineEdit("50")
        grid.addWidget(QLabel("目标关断电流 I_max [A]:"), 0, 2); grid.addWidget(self.dpt_imax, 0, 3)
        
        self.dpt_l = QLineEdit("100")
        grid.addWidget(QLabel("负载电感 L [uH]:"), 1, 0); grid.addWidget(self.dpt_l, 1, 1)
        
        self.dpt_r = QLineEdit("50")
        self.dpt_r.setToolTip("电感寄生电阻与回路电阻之和。如果不清楚可填较小值，如50mΩ")
        grid.addWidget(QLabel("回路总电阻 R [mΩ]:"), 1, 2); grid.addWidget(self.dpt_r, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算双脉冲 T1, T2, T3")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_pulse_widths)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("脉冲时间结果 (理想模型与LR指数模型校准)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_t1 = QLineEdit()
        self.res_t2 = QLineEdit()
        self.res_t3 = QLineEdit()
        
        r_grid.addWidget(QLabel("T1 (首次充电脉宽):"), 0, 0); r_grid.addWidget(self.res_t1, 0, 1)
        r_grid.addWidget(QLabel("用于让电感电流爬升至目标 I_max\n(近似 T1 = L*I/V)"), 0, 2)
        
        r_grid.addWidget(QLabel("T2 (关断观测间隔):"), 1, 0); r_grid.addWidget(self.res_t2, 1, 1)
        r_grid.addWidget(QLabel("抓取关断波形，让电感电流在二极管续流。\n设为 T1 的 10%~20%"), 1, 2)
        
        r_grid.addWidget(QLabel("T3 (二次开通脉宽):"), 2, 0); r_grid.addWidget(self.res_t3, 2, 1)
        r_grid.addWidget(QLabel("抓取开通波形。此时二极管有反向恢复。\n设为 T1 的约 5%"), 2, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.res_t1, self.res_t2, self.res_t3]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_pulse_widths(self):
        try:
            vdc = float(self.dpt_vdc.text())
            imax = float(self.dpt_imax.text())
            l_uh = float(self.dpt_l.text())
            r_mohm = float(self.dpt_r.text())
            
            if vdc <= 0 or imax <= 0 or l_uh <= 0: raise ValueError
            
            l_h = l_uh * 1e-6
            r_ohm = r_mohm * 1e-3
            
            # T1 Calculation:
            # Ideal: T1 = L * I_max / Vdc
            # Real (LR circuit): I(t) = (Vdc/R) * (1 - e^(-Rt/L))
            # 1 - I*R/Vdc = e^(-Rt/L) => -Rt/L = ln(1 - I*R/Vdc) => t = -L/R * ln(1 - I*R/Vdc)
            
            if r_ohm > 1e-6 and (imax * r_ohm / vdc) < 1:
                t1 = -(l_h / r_ohm) * math.log(1 - (imax * r_ohm / vdc))
            else:
                t1 = l_h * imax / vdc
                
            # Rule of thumb for DPT:
            # T2 is off time, needs to be long enough for switching to settle, but short enough that current doesn't decay much.
            # Usually 1us to 5us is enough, or 10% of T1. Let's provide a safe default of 2us minimum.
            t2 = max(2e-6, t1 * 0.1)
            
            # T3 is second pulse, just long enough to capture turn-on transients.
            t3 = max(1e-6, t1 * 0.05)
            
            self.res_t1.setText(f"{t1*1e6:.1f} us")
            self.res_t2.setText(f"{t2*1e6:.1f} us (建议)")
            self.res_t3.setText(f"{t3*1e6:.1f} us (建议)")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效！请检查。")

    # ==============================================================================
    # Tab 2: 损耗与速度评估
    # ==============================================================================
    def init_evaluator_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info_lbl = QLabel(
            "<b>辅助对齐示波器积分：</b> 根据示波器上读到的 10%~90% 电压时间变化，快速计算 dv/dt 与开关能量 Eon/Eoff 面值估算。"
        )
        info_lbl.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info_lbl)
        
        h_main = QHBoxLayout()
        
        # Turn-on Box
        grp_on = QGroupBox("开通过程评估 (Turn-on)")
        g_on = QGridLayout()
        self.ev_on_v = QLineEdit("400"); g_on.addWidget(QLabel("电压摆幅 V_sw [V]:"), 0, 0); g_on.addWidget(self.ev_on_v, 0, 1)
        self.ev_on_i = QLineEdit("50"); g_on.addWidget(QLabel("电流摆幅 I_sw [A]:"), 1, 0); g_on.addWidget(self.ev_on_i, 1, 1)
        self.ev_on_dtv = QLineEdit("20"); g_on.addWidget(QLabel("电压下降时间 tvf [ns]:"), 2, 0); g_on.addWidget(self.ev_on_dtv, 2, 1)
        self.ev_on_dti = QLineEdit("15"); g_on.addWidget(QLabel("电流上升时间 tir [ns]:"), 3, 0); g_on.addWidget(self.ev_on_dti, 3, 1)
        
        btn_on = QPushButton("评估 T-ON")
        btn_on.clicked.connect(self.eval_turn_on)
        btn_on.setStyleSheet("background-color: #3498db; color: white;")
        g_on.addWidget(btn_on, 4, 0, 1, 2)
        
        self.res_on_dvdt = QLineEdit(); g_on.addWidget(QLabel("dv/dt [V/ns]:"), 5, 0); g_on.addWidget(self.res_on_dvdt, 5, 1)
        self.res_on_didt = QLineEdit(); g_on.addWidget(QLabel("di/dt [A/ns]:"), 6, 0); g_on.addWidget(self.res_on_didt, 6, 1)
        self.res_on_eon = QLineEdit(); g_on.addWidget(QLabel("预估 E_on [uJ]:"), 7, 0); g_on.addWidget(self.res_on_eon, 7, 1)
        
        grp_on.setLayout(g_on)
        h_main.addWidget(grp_on)
        
        # Turn-off Box
        grp_off = QGroupBox("关断过程评估 (Turn-off)")
        g_off = QGridLayout()
        self.ev_off_v = QLineEdit("400"); g_off.addWidget(QLabel("电压摆幅 V_sw [V]:"), 0, 0); g_off.addWidget(self.ev_off_v, 0, 1)
        self.ev_off_i = QLineEdit("50"); g_off.addWidget(QLabel("电流摆幅 I_sw [A]:"), 1, 0); g_off.addWidget(self.ev_off_i, 1, 1)
        self.ev_off_dtv = QLineEdit("15"); g_off.addWidget(QLabel("电压上升时间 tvr [ns]:"), 2, 0); g_off.addWidget(self.ev_off_dtv, 2, 1)
        self.ev_off_dti = QLineEdit("25"); g_off.addWidget(QLabel("电流下降时间 tif [ns]:"), 3, 0); g_off.addWidget(self.ev_off_dti, 3, 1)
        
        btn_off = QPushButton("评估 T-OFF")
        btn_off.clicked.connect(self.eval_turn_off)
        btn_off.setStyleSheet("background-color: #e67e22; color: white;")
        g_off.addWidget(btn_off, 4, 0, 1, 2)
        
        self.res_off_dvdt = QLineEdit(); g_off.addWidget(QLabel("dv/dt [V/ns]:"), 5, 0); g_off.addWidget(self.res_off_dvdt, 5, 1)
        self.res_off_didt = QLineEdit(); g_off.addWidget(QLabel("di/dt [A/ns]:"), 6, 0); g_off.addWidget(self.res_off_didt, 6, 1)
        self.res_off_eoff = QLineEdit(); g_off.addWidget(QLabel("预估 E_off [uJ]:"), 7, 0); g_off.addWidget(self.res_off_eoff, 7, 1)

        grp_off.setLayout(g_off)
        h_main.addWidget(grp_off)
        
        layout.addLayout(h_main)
        
        for w in [self.res_on_dvdt, self.res_on_didt, self.res_on_eon,
                  self.res_off_dvdt, self.res_off_didt, self.res_off_eoff]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #fdf2e9; font-weight: bold;")
            
        layout.addStretch()
        tab.setLayout(layout)

    def eval_turn_on(self):
        try:
            v = float(self.ev_on_v.text())
            i = float(self.ev_on_i.text())
            dtv = float(self.ev_on_dtv.text())
            dti = float(self.ev_on_dti.text())
            
            if dtv <= 0 or dti <= 0: raise ValueError
            
            # Using 10%-90% means amplitude is 80% for the dt span.
            # True derivative involves dividing by the time.
            # Standard definition: dv/dt = 0.8*V / dt
            dv_dt = (0.8 * v) / dtv
            di_dt = (0.8 * i) / dti
            
            # Simplified E_on estimation (Triangle approximation of VI overlap)
            # Area = 1/2 * V * I * (tir + tvf) 
            e_on = 0.5 * v * i * (dtv + dti) 
            # Note: actual formula usually assumes 10-90 times imply larger total overlap time.
            # But roughly this is often within 20% of scope integration excluding Qrr.
            
            self.res_on_dvdt.setText(f"{dv_dt:.1f}")
            self.res_on_didt.setText(f"{di_dt:.1f}")
            self.res_on_eon.setText(f"{e_on/1000:.1f}") # scaled ns*V*A = uJ / 1000? No, V*A*ns = 1e-9 J = 1e-3 uJ
            # Correct: V * A * ns = W * ns = 1e-9 J = 1 nJ. 
            # So e_on is in nJ.
            self.res_on_eon.setText(f"{e_on/1000:.2f} uJ")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效！请检查。")

    def eval_turn_off(self):
        try:
            v = float(self.ev_off_v.text())
            i = float(self.ev_off_i.text())
            dtv = float(self.ev_off_dtv.text())
            dti = float(self.ev_off_dti.text())
            
            if dtv <= 0 or dti <= 0: raise ValueError
            
            dv_dt = (0.8 * v) / dtv
            di_dt = (0.8 * i) / dti
            
            # Simplified E_off estimation
            e_off = 0.5 * v * i * (dtv + dti) 
            
            self.res_off_dvdt.setText(f"{dv_dt:.1f}")
            self.res_off_didt.setText(f"{di_dt:.1f}")
            self.res_off_eoff.setText(f"{e_off/1000:.2f} uJ")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效！请检查。")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("双脉冲实验 (DPT) 指南")
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
        </style>
        
        <h2>双脉冲实验 (DPT) 目标</h2>
        <div class="box">
            <b>1. 获取真实开关损耗 (Eon, Eoff, Err)：</b> 验证损耗预估在实际杂散电感、不同门极电阻下的真实值。<br>
            <b>2. 评估开关速度与超调：</b> 测量 dv/dt, di/dt, 以及关断电压尖峰 (V_peak)，防止过压击穿。
        </div>

        <h2>脉冲时序解释</h2>
        <ul>
            <li><b>T1 (第一次长脉冲)：</b> 目标是给电感充能，让电流通过 L 和下管 MOS 上升到测试目标电流 I_max。这个期间不做测量。</li>
            <li><b>T2 (关断时间)：</b> MOS 关断，此时可以抓取 <b>关断波形 (Turn-off)</b>，电流在续流二极管中流通。T2 不能太长，否则电流会掉太多。</li>
            <li><b>T3 (第二次短脉冲)：</b> MOS 再次开通，此时可以抓取 <b>开通波形 (Turn-on)</b>。此过程包含了上管二极管的反向恢复电流。</li>
        </ul>

        <h2>为什么 Eon 一般比 Eoff 大？</h2>
        <p>因为在 T3 开通时，上管（或续流二极管）带有反向恢复电荷 (Qrr) 和结电容 (Coss) 充电电流。这些额外的电流尖峰会叠加在导通电流上，导致 Eon 和开启损耗剧增。对于 SiC 来说反向恢复很小，但结电容充电依然存在。</p>
        
        <h2>dv/dt 测量与对齐</h2>
        <p>示波器上的积分受到探头延时 (Deskew) 影响很大。如果你读到的时间和电压，用本工具的积分预估和示波器差异超过 50%，请务必检查电流电压探头是否对齐！</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()
