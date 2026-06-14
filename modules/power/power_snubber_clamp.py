from modules.base_module import BaseModule
# rc_snubber_window.py

import math
import matplotlib.pyplot as plt
from io import BytesIO

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class RcSnubberWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "RC 吸收与钳位"
    description = "理论计算 / 实测计算 / RCD钳位"
    window_id = "power_snubber"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('吸收与钳位电路设计助手 (Snubber & Clamp)')
        self.setGeometry(350, 350, 1050, 750) # 稍微加宽窗口以容纳公式
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部：教程按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("使用教程 / 上下管布局疑问")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(220)
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

        self.estimate_tab = QWidget()
        self.measure_tab = QWidget()
        self.rcd_tab = QWidget() # 新增 RCD 标签页

        self.init_estimate_ui(self.estimate_tab)
        self.init_measure_ui(self.measure_tab)
        self.init_rcd_ui(self.rcd_tab) # 初始化 RCD 界面

        self.tabs.addTab(self.estimate_tab, "RC 吸收: 理论估算")
        self.tabs.addTab(self.measure_tab, "RC 吸收: 实测计算")
        self.tabs.addTab(self.rcd_tab, "RCD 钳位设计 (反激 Flyback)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 理论估算模式 (设计初期)
    # ==============================================================================
    def init_estimate_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 输入
        input_group = QGroupBox("Datasheet 参数与 PCB 预估")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        self.est_coss_input = QLineEdit("200")
        self.est_l_loop_input = QLineEdit("5")
        self.est_vin_input = QLineEdit("12")
        self.est_fsw_input = QLineEdit("500")

        self.est_coss_unit = QComboBox()
        self.est_coss_unit.addItems(["pF", "nF"])
        
        inputs = [
            ("MOSFET 输出电容 (Coss) @Vin:", self.est_coss_input, "查规格书 C_oss 曲线图"),
            ("预估回路寄生电感 (L_loop) [nH]:", self.est_l_loop_input, "经验值: 紧凑布局取 2~5nH"),
            ("工作电压 (Vin) [V]:", self.est_vin_input, "用于计算功耗"),
            ("开关频率 (f_sw) [kHz]:", self.est_fsw_input, "用于计算功耗")
        ]
        
        for i, (label_txt, widget, tip) in enumerate(inputs):
            lbl = QLabel(label_txt)
            input_layout.addWidget(lbl, i, 0)
            
            # 特殊处理 Coss 的单位组合
            if widget == self.est_coss_input:
                h_lay = QHBoxLayout()
                h_lay.setContentsMargins(0,0,0,0)
                h_lay.addWidget(widget)
                h_lay.addWidget(self.est_coss_unit)
                container = QWidget()
                container.setLayout(h_lay)
                input_layout.addWidget(container, i, 1)
            else:
                input_layout.addWidget(widget, i, 1)
            
            tip_lbl = QLabel(tip)
            tip_lbl.setStyleSheet("color: #7f8c8d; font-size: 12px; font-style: italic;")
            input_layout.addWidget(tip_lbl, i, 2)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 按钮
        btn = QPushButton("估算 RC 参数范围")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.on_estimate)
        layout.addWidget(btn)

        # 结果 (使用 Grid 布局确保公式对齐)
        res_group = QGroupBox("推荐设计值 (Design Guide)")
        # 3列：[标签] [数值结果] [公式图片]
        res_layout = QGridLayout()
        res_layout.setVerticalSpacing(15)
        res_layout.setHorizontalSpacing(20)
        res_layout.setColumnStretch(1, 1) # 中间结果列拉伸

        self.est_csnub_out = QLineEdit()
        self.est_rsnub_out = QLineEdit()
        self.est_ploss_out = QLineEdit()

        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 15px;"
        style_power = "background-color: #fff5f5; font-weight: bold; color: #c0392b;"
        
        # Row 0: C_snub
        res_layout.addWidget(QLabel("推荐吸收电容 (C_snub):"), 0, 0)
        res_layout.addWidget(self.est_csnub_out, 0, 1)
        l_c = QLabel(); l_c.setPixmap(self.render_formula(r'C_{snub} \approx 3 \cdot C_{oss} \quad (2 \sim 4 \times C_{oss})'))
        res_layout.addWidget(l_c, 0, 2)
        
        # Row 1: R_snub
        res_layout.addWidget(QLabel("推荐吸收电阻 (R_snub):"), 1, 0)
        res_layout.addWidget(self.est_rsnub_out, 1, 1)
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'R_{snub} \approx \sqrt{\frac{L_{loop}}{C_{oss}}} \quad (Z_0)'))
        res_layout.addWidget(l_r, 1, 2)
        
        # Row 2: P_loss
        res_layout.addWidget(QLabel("电阻功耗预估 (P_loss):"), 2, 0)
        res_layout.addWidget(self.est_ploss_out, 2, 1)
        l_p = QLabel(); l_p.setPixmap(self.render_formula(r'P_{loss} \approx C_{snub} \cdot V_{in}^2 \cdot f_{sw}'))
        res_layout.addWidget(l_p, 2, 2)
        
        # 应用样式
        self.est_csnub_out.setReadOnly(True); self.est_csnub_out.setStyleSheet(style_res)
        self.est_rsnub_out.setReadOnly(True); self.est_rsnub_out.setStyleSheet(style_res)
        self.est_ploss_out.setReadOnly(True); self.est_ploss_out.setStyleSheet(style_power)

        res_group.setLayout(res_layout)
        layout.addWidget(res_group)
        
        # 底部提示
        info_lbl = QLabel("提示：此模式用于设计初期备料。建议在板子上预留 RC 焊盘 (0603/0805)，实物回来后再用“实测模式”微调。")
        info_lbl.setStyleSheet("color: #2980b9; padding: 10px; background: #eaf2f8; border-radius: 5px;")
        layout.addWidget(info_lbl)
        layout.addStretch()

        tab.setLayout(layout)
        self.on_estimate() 

    def on_estimate(self):
        try:
            coss_val = float(self.est_coss_input.text())
            l_loop_nh = float(self.est_l_loop_input.text())
            vin = float(self.est_vin_input.text())
            fsw_khz = float(self.est_fsw_input.text())

            if coss_val <= 0 or l_loop_nh <= 0: raise ValueError

            # 单位换算
            if self.est_coss_unit.currentText() == "nF":
                coss_pf = coss_val * 1000
            else:
                coss_pf = coss_val

            # 计算
            # 1. 特征阻抗 Z0 = sqrt(L/C)
            # L in nH (1e-9), C in pF (1e-12) -> sqrt(1e3 * L/C)
            z0 = math.sqrt(l_loop_nh / (coss_pf * 1e-3)) # 简化计算
            
            # 2. 推荐 R_snub = Z0 ~ 0.5*Z0 (欠阻尼到临界阻尼)
            r_min = 0.5 * z0
            r_max = z0
            
            # 3. 推荐 C_snub = 2*Coss ~ 4*Coss
            c_min = 2 * coss_pf
            c_max = 4 * coss_pf
            
            # 4. 功耗 (按最大C算)
            p_loss = (c_max * 1e-12) * (vin**2) * (fsw_khz * 1e3)

            # 显示
            self.est_csnub_out.setText(f"{c_min:.0f} pF ~ {c_max:.0f} pF")
            self.est_rsnub_out.setText(f"{r_min:.1f} Ω ~ {r_max:.1f} Ω")
            self.est_ploss_out.setText(f"约 {p_loss:.3f} W (请选 1/4W 或更大)")

        except:
            pass # 忽略输入不完整的错误

    # ==============================================================================
    # Tab 2: 实测计算模式 (原功能) - 修复布局对齐
    # ==============================================================================
    def init_measure_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 输入
        input_group = QGroupBox("实验测量数据 (频率偏移法)")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        self.f_ring_input = QLineEdit("100")
        self.c_add_input = QLineEdit("100")
        self.f_shift_input = QLineEdit("70")
        self.vin_input = QLineEdit("12")
        self.f_sw_input = QLineEdit("500")
        
        inputs = [
            ("原始振铃频率 (f_ring) [MHz]:", self.f_ring_input),
            ("并联测试电容 (C_add) [pF]:", self.c_add_input),
            ("并联后振铃频率 (f_shift) [MHz]:", self.f_shift_input),
            ("开关电压/耐压 (V_sw/Vin) [V]:", self.vin_input),
            ("工作开关频率 (f_sw) [kHz]:", self.f_sw_input)
        ]
        
        for i, (txt, widget) in enumerate(inputs):
            row = i // 2
            col = (i % 2) * 2
            input_layout.addWidget(QLabel(txt), row, col)
            input_layout.addWidget(widget, row, col + 1)
            
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 按钮
        btn = QPushButton("计算精确 RC 参数")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(45) 
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.on_calculate)
        layout.addWidget(btn)
        
        # 结果 - 【改为 3 列 Grid 布局以解决错位】
        output_group = QGroupBox("计算结果")
        # Column 0: Label, Column 1: Input, Column 2: Formula Image
        results_layout = QGridLayout()
        results_layout.setVerticalSpacing(12)
        results_layout.setHorizontalSpacing(20)
        results_layout.setColumnStretch(1, 1) # 让中间的输入框拉伸
        
        self.cp_output = QLineEdit()
        self.lp_output = QLineEdit()
        self.z0_output = QLineEdit()
        self.c_snub_output = QLineEdit()
        self.r_snub_output = QLineEdit()
        self.p_loss_output = QLineEdit()
        
        style_gray = "background-color: #f8f9fa; color: #555;"
        style_highlight = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 15px;"
        
        # 定义每一行的数据： (标签, 控件, 样式, 公式LaTeX)
        rows_data = [
            ("寄生电容 (C_p):", self.cp_output, style_gray, r'C_p = \frac{C_{add}}{(f_{ring}/f_{shift})^2 - 1}'),
            ("寄生电感 (L_p):", self.lp_output, style_gray, r'L_p = \frac{1}{(2\pi f_{ring})^2 C_p}'),
            ("特征阻抗 (Z_0):", self.z0_output, style_gray, r'Z_0 = \sqrt{L_p / C_p}'),
            ("推荐吸收电容 (C_snub):", self.c_snub_output, style_highlight, r'C_{snub} \approx 3 \cdot C_p'),
            ("推荐吸收电阻 (R_snub):", self.r_snub_output, style_highlight, r'R_{snub} = Z_0'),
            ("电阻功耗估算 (P_loss):", self.p_loss_output, "background-color: #fff5f5; font-weight: bold; color: #c0392b;", r'P_{loss} \approx C_{snub} V^2 f_{sw}')
        ]
        
        for i, (txt, widget, style, latex) in enumerate(rows_data):
            # 1. Label
            results_layout.addWidget(QLabel(txt), i, 0)
            
            # 2. Value Widget
            widget.setReadOnly(True)
            widget.setStyleSheet(style)
            results_layout.addWidget(widget, i, 1)
            
            # 3. Formula Pixmap (生成对应的公式图)
            formula_label = QLabel()
            formula_label.setPixmap(self.render_formula(latex))
            results_layout.addWidget(formula_label, i, 2)

        output_group.setLayout(results_layout)
        layout.addWidget(output_group)
        layout.addStretch()
        
        tab.setLayout(layout)

    def on_calculate(self):
        try:
            f1_mhz = float(self.f_ring_input.text())
            c_add_pf = float(self.c_add_input.text())
            f2_mhz = float(self.f_shift_input.text())
            vin = float(self.vin_input.text())
            fsw_khz = float(self.f_sw_input.text())
            
            if f1_mhz <= 0 or c_add_pf <= 0 or f2_mhz <= 0: raise ValueError
            if f2_mhz >= f1_mhz:
                QMessageBox.warning(self, "错误", "并联电容后的频率必须小于原始频率")
                return

            # 计算寄生参数
            ratio_sq = (f1_mhz / f2_mhz) ** 2
            cp_pf = c_add_pf / (ratio_sq - 1)
            
            f1_hz = f1_mhz * 1e6
            cp_f = cp_pf * 1e-12
            lp_h = 1 / (4 * math.pi**2 * f1_hz**2 * cp_f)
            lp_nh = lp_h * 1e9
            
            z0 = math.sqrt(lp_h / cp_f)
            
            c_snub_pf = 3 * cp_pf
            r_snub = z0
            
            p_loss = (c_snub_pf * 1e-12) * (vin ** 2) * (fsw_khz * 1e3)
            
            self.cp_output.setText(f"{cp_pf:.2f} pF")
            self.lp_output.setText(f"{lp_nh:.2f} nH")
            self.z0_output.setText(f"{z0:.2f} Ω")
            self.c_snub_output.setText(f"{c_snub_pf:.0f} pF")
            self.r_snub_output.setText(f"{r_snub:.2f} Ω")
            self.p_loss_output.setText(f"{p_loss:.3f} W")
            
        except:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    # ==============================================================================
    # Tab 3: RCD 钳位设计 (Flyback RCD Clamp) - 新增功能
    # ==============================================================================
    def init_rcd_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 1. Flyback 参数输入
        input_group = QGroupBox("反激变压器参数 (Flyback Parameters)")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        self.rcd_l_lk = QLineEdit("5"); self.rcd_l_lk.setToolTip("变压器原边漏感")
        self.rcd_i_pk = QLineEdit("2.0"); self.rcd_i_pk.setToolTip("原边峰值电流")
        self.rcd_vor = QLineEdit("80"); self.rcd_vor.setToolTip("反射电压 n*Vo")
        self.rcd_fsw = QLineEdit("65"); self.rcd_fsw.setToolTip("开关频率")
        
        input_layout.addWidget(QLabel("原边漏感 (L_lk) [uH]:"), 0, 0); input_layout.addWidget(self.rcd_l_lk, 0, 1)
        input_layout.addWidget(QLabel("原边峰值电流 (I_pk) [A]:"), 0, 2); input_layout.addWidget(self.rcd_i_pk, 0, 3)
        input_layout.addWidget(QLabel("反射电压 (Vor) [V]:"), 1, 0); input_layout.addWidget(self.rcd_vor, 1, 1)
        input_layout.addWidget(QLabel("开关频率 (f_sw) [kHz]:"), 1, 2); input_layout.addWidget(self.rcd_fsw, 1, 3)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 2. 设计目标
        target_group = QGroupBox("钳位设计目标 (Design Targets)")
        target_layout = QGridLayout()
        
        self.rcd_v_spike = QLineEdit("50"); self.rcd_v_spike.setToolTip("允许漏感引起的电压过冲幅度。\n钳位电压 Vc = Vor + V_spike。")
        self.rcd_ripple = QLineEdit("10"); self.rcd_ripple.setToolTip("钳位电容上的电压纹波比例，通常取 5%~20%。")
        
        target_layout.addWidget(QLabel("允许过冲电压 (V_spike) [V]:"), 0, 0); target_layout.addWidget(self.rcd_v_spike, 0, 1)
        target_layout.addWidget(QLabel("钳位电容纹波率 (Ripple) [%]:"), 0, 2); target_layout.addWidget(self.rcd_ripple, 0, 3)
        
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 按钮
        btn = QPushButton("计算 RCD 参数")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_rcd)
        layout.addWidget(btn)
        
        # 3. 结果显示
        res_group = QGroupBox("RCD 计算结果")
        res_layout = QGridLayout()
        res_layout.setVerticalSpacing(15)
        res_layout.setColumnStretch(1, 1)
        
        self.rcd_vc_out = QLineEdit()
        self.rcd_r_out = QLineEdit()
        self.rcd_p_out = QLineEdit()
        self.rcd_c_out = QLineEdit()
        
        # Total Clamp Voltage
        res_layout.addWidget(QLabel("总钳位电压 (V_clamp):"), 0, 0)
        res_layout.addWidget(self.rcd_vc_out, 0, 1)
        res_layout.addWidget(QLabel("= Vor + V_spike (Mos承受电压需加Vin)"), 0, 2)
        
        # Power Loss
        res_layout.addWidget(QLabel("电阻功耗 (P_loss):"), 1, 0)
        res_layout.addWidget(self.rcd_p_out, 1, 1)
        l_p = QLabel(); l_p.setPixmap(self.render_formula(r'P_{loss} = \frac{1}{2} L_{lk} I_{pk}^2 f_{sw} \frac{V_{clamp}}{V_{clamp}-V_{or}}'))
        res_layout.addWidget(l_p, 1, 2)
        
        # Resistance
        res_layout.addWidget(QLabel("泄放电阻 (R_clamp):"), 2, 0)
        res_layout.addWidget(self.rcd_r_out, 2, 1)
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'R_{clamp} = \frac{V_{clamp}^2}{P_{loss}}'))
        res_layout.addWidget(l_r, 2, 2)
        
        # Capacitance
        res_layout.addWidget(QLabel("钳位电容 (C_clamp):"), 3, 0)
        res_layout.addWidget(self.rcd_c_out, 3, 1)
        res_layout.addWidget(QLabel("基于纹波要求计算"), 3, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_pow = "background-color: #fff5f5; font-weight: bold; color: #c0392b;"
        
        self.rcd_vc_out.setReadOnly(True); self.rcd_vc_out.setStyleSheet(style_res)
        self.rcd_r_out.setReadOnly(True); self.rcd_r_out.setStyleSheet(style_res)
        self.rcd_p_out.setReadOnly(True); self.rcd_p_out.setStyleSheet(style_pow)
        self.rcd_c_out.setReadOnly(True); self.rcd_c_out.setStyleSheet(style_res)
        
        res_group.setLayout(res_layout)
        layout.addWidget(res_group)
        layout.addStretch()
        
        tab.setLayout(layout)

    def calc_rcd(self):
        try:
            # Inputs
            llk = float(self.rcd_l_lk.text()) * 1e-6
            ipk = float(self.rcd_i_pk.text())
            vor = float(self.rcd_vor.text())
            fsw = float(self.rcd_fsw.text()) * 1000
            v_spike = float(self.rcd_v_spike.text())
            ripple_pct = float(self.rcd_ripple.text()) / 100.0
            
            if llk <= 0 or ipk <= 0 or fsw <= 0 or v_spike <= 0:
                raise ValueError("参数必须大于0")
                
            # 1. Total Clamp Voltage
            vc = vor + v_spike
            
            # 2. Energy Transfer Ratio K = Vc / (Vc - Vor)
            # When Vc approaches Vor, power goes to infinity (voltage source clamping)
            k_ratio = vc / v_spike 
            
            # 3. Leakage Energy per cycle
            e_lk = 0.5 * llk * (ipk ** 2)
            
            # 4. Power Dissipated
            p_loss = e_lk * fsw * k_ratio
            
            # 5. Resistance
            # P = Vc^2 / R
            r_clamp = (vc ** 2) / p_loss
            
            # 6. Capacitance
            # To maintain ripple: C = Vc / (dV * R * f) approx
            # V(t) decays exp(-t/RC).
            # V_end = V_start * exp(-T/RC). T = 1/f.
            # V_start - V_end = V_ripple.
            # V_ripple ~ Vc * (1 - exp(-1/RCf)) ~ Vc * (1/(RCf)) for large RC
            # So C = Vc / (V_ripple * R * f) = 1 / (ripple_pct * R * f)
            c_clamp = 1.0 / (ripple_pct * r_clamp * fsw)
            
            self.rcd_vc_out.setText(f"{vc:.1f} V")
            self.rcd_p_out.setText(f"{p_loss:.2f} W")
            
            # Format R
            if r_clamp >= 1000:
                self.rcd_r_out.setText(f"{r_clamp/1000:.2f} kΩ")
            else:
                self.rcd_r_out.setText(f"{r_clamp:.1f} Ω")
                
            # Format C
            if c_clamp < 1e-6:
                self.rcd_c_out.setText(f"{c_clamp*1e9:.1f} nF")
            else:
                self.rcd_c_out.setText(f"{c_clamp*1e6:.2f} uF")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效，请检查数值")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("RC Snubber 教程 & 常见疑问")
        dialog.resize(700, 550)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 10px;")
        html_content = """
        <style>
            h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h3 { color: #e67e22; margin-top: 15px; }
            .ans { color: #27ae60; font-weight: bold; }
            .note { background-color: #fff9c4; padding: 8px; border-left: 4px solid #f1c40f; color: #333; margin: 10px 0; }
        </style>
        <h2>常见疑问：上下管都需要加吗？</h2>
        <p><b>Q: 我看到有些电路图只在下管加了 Snubber，上管需要加吗？</b></p>
        <p class="ans">A: 通常只需要并联在下管 (Low-side) 的 DS 两端。</p>
        <ul>
            <li>Buck 电路的振铃主要发生在 <b>SW (开关节点)</b>。</li>
            <li>下管的 Source 是直接接地的 (GND)，Drain 接 SW。在下管并联 RC，等效于直接在 SW 和 GND 之间加了吸收电路。</li>
            <li>这是路径最短、效果最好、散热最方便的布局方式。</li>
            <li>上管并联（Vin 到 SW）虽然也有用，但不如对地吸收直接，且 Vin 走线通常较长。</li>
        </ul>
        <div class="note"><b>结论：</b> 优先在下管 DS 两端预留 RC 焊盘。除非振铃极其严重搞不定，才考虑上管。</div>

        <h2>设计初期如何估算？(理论模式)</h2>
        <p>在 PCB 没回来之前，可以通过以下方法预估，提前备料：</p>
        <ol>
            <li><b>查 Datasheet：</b> 找到 MOSFET 的输出电容 <code>Coss</code> (注意查看 Vin 电压下的值，Coss 随电压变化)。</li>
            <li><b>估算寄生电感：</b> 一个紧凑的 Buck 布局，回路电感通常在 <code>2nH ~ 10nH</code> 之间。</li>
            <li><b>经验公式：</b>
                <ul>
                    <li><code>C_snub</code> 取 2~4 倍的 Coss。</li>
                    <li><code>R_snub</code> 取特征阻抗 √(L/Coss)，通常在 2Ω ~ 10Ω 之间。</li>
                </ul>
            </li>
        </ol>
        
        <h2>关于 RCD 钳位电路 (反激)</h2>
        <p>RCD 电路用于吸收反激变压器的漏感能量，防止 MOS 管过压击穿。</p>
        <ul>
            <li><b>R 的作用：</b> 消耗漏感能量。R 越小，钳位电压越低（MOS管更安全），但损耗越大。</li>
            <li><b>C 的作用：</b> 维持钳位电压平稳。C 值需足够大以保证纹波较小，通常选 nF 到 uF 级别。</li>
            <li><b>选型权衡：</b> 必须在 MOS 管耐压裕量和电阻发热之间做权衡。通常设定 V_spike 为 Vor 的 50%~100%。</li>
        </ul>
        """
        text.setHtml(html_content)
        layout.addWidget(text)
        dialog.exec_()