# modules/signal/opamp_circuit.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QRadioButton, 
                             QButtonGroup, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

from modules.base_module import BaseModule
from core.formula_opamp import (
    calc_basic_opamp, calc_diff_opamp, calc_summing_opamp,
    calc_hysteresis_comparator, calc_error_budget, calc_opamp_selection
)

class OpampCalculatorWindow(BaseModule):
    """
    运放与比较器计算工具
    """
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "运放与比较器"
    description = "基础 / 差分 / 加法 / 迟滞 / 误差"
    window_id = "analog_opamp"

    def init_module_ui(self):
        self.setWindowTitle('运放电路计算工具 (Op-Amp Calculator)')
        self.setGeometry(350, 350, 1000, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton(" 运放原理 & 误差分析指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(260)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        # 移除了 self.tabs.setStyleSheet(...) 样式，直接沿用 gui/styles.py 中的全局 QTabWidget 样式

        self.tab_basic = QWidget()
        self.tab_diff = QWidget()
        self.tab_sum = QWidget()
        self.tab_hyst = QWidget() 
        self.tab_error = QWidget()
        self.tab_select = QWidget()

        self.init_basic_ui(self.tab_basic)
        self.init_diff_ui(self.tab_diff)
        self.init_sum_ui(self.tab_sum)
        self.init_hysteresis_ui(self.tab_hyst) 
        self.init_error_ui(self.tab_error)
        self.init_selection_ui(self.tab_select)

        self.tabs.addTab(self.tab_basic, "基础放大器")
        self.tabs.addTab(self.tab_diff, "差分放大器")
        self.tabs.addTab(self.tab_sum, "加法器")
        self.tabs.addTab(self.tab_hyst, "迟滞比较器 (Hysteresis)")
        self.tabs.addTab(self.tab_error, "误差预算 (Error Budget)") 
        self.tabs.addTab(self.tab_select, "选型指南")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: Basic
    # ==============================================================================
    def init_basic_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_cfg = QGroupBox("1. 电路配置")
        grid = QGridLayout()
        self.rb_noninv = QRadioButton("同相放大器 (Non-Inverting)")
        self.rb_inv = QRadioButton("反相放大器 (Inverting)")
        self.rb_follower = QRadioButton("电压跟随器 (Follower)")
        self.rb_noninv.setChecked(True)
        
        bg = QButtonGroup(self)
        bg.addButton(self.rb_noninv); bg.addButton(self.rb_inv); bg.addButton(self.rb_follower)
        bg.buttonClicked.connect(self.update_basic_ui)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.rb_noninv); hbox.addWidget(self.rb_inv); hbox.addWidget(self.rb_follower)
        grid.addLayout(hbox, 0, 0, 1, 4)
        grp_cfg.setLayout(grid)
        layout.addWidget(grp_cfg)
        
        grp_param = QGroupBox("2. 元件与信号")
        p_grid = QGridLayout()
        p_grid.setVerticalSpacing(12)
        
        self.b_rin = QLineEdit("10"); self.b_rin.setToolTip("输入电阻 R1 (或 Rin)")
        p_grid.addWidget(QLabel("输入电阻 Rin [kΩ]:"), 0, 0); p_grid.addWidget(self.b_rin, 0, 1)
        self.b_rf = QLineEdit("100"); self.b_rf.setToolTip("反馈电阻 Rf")
        p_grid.addWidget(QLabel("反馈电阻 Rf [kΩ]:"), 0, 2); p_grid.addWidget(self.b_rf, 0, 3)
        self.b_vin = QLineEdit("0.1"); p_grid.addWidget(QLabel("输入电压 Vin [V]:"), 1, 0); p_grid.addWidget(self.b_vin, 1, 1)
        self.b_gbp = QLineEdit("1"); self.b_gbp.setToolTip("增益带宽积。查Datasheet。")
        p_grid.addWidget(QLabel("运放 GBP [MHz]:"), 1, 2); p_grid.addWidget(self.b_gbp, 1, 3)
        grp_param.setLayout(p_grid)
        layout.addWidget(grp_param)
        
        btn = QPushButton("计算增益与带宽")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_basic)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("3. 计算结果")
        r_grid = QGridLayout()
        
        self.b_res_gain = QLineEdit()
        self.b_res_vout = QLineEdit()
        self.b_res_bw = QLineEdit()
        
        r_grid.addWidget(QLabel("闭环增益 (Gain):"), 0, 0); r_grid.addWidget(self.b_res_gain, 0, 1)
        self.b_lbl_formula = QLabel()
        self.b_lbl_formula.setPixmap(self.render_formula(r'V_{out} = V_{in} (1 + \frac{R_f}{R_{in}})'))
        r_grid.addWidget(self.b_lbl_formula, 0, 2, 2, 1)
        
        r_grid.addWidget(QLabel("输出电压 (Vout):"), 1, 0); r_grid.addWidget(self.b_res_vout, 1, 1)
        r_grid.addWidget(QLabel("截止频率 (-3dB BW):"), 2, 0); r_grid.addWidget(self.b_res_bw, 2, 1)
        r_grid.addWidget(QLabel("注：BW = GBP / Noise_Gain"), 2, 2)
        
        for w in [self.b_res_gain, self.b_res_vout, self.b_res_bw]:
            w.setReadOnly(True)
            # 移除了手写的 style 字符串，直接使用全局 QSS 设置
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.update_basic_ui()

    def update_basic_ui(self):
        if self.rb_noninv.isChecked():
            self.b_rin.setEnabled(True); self.b_rf.setEnabled(True)
            self.b_lbl_formula.setPixmap(self.render_formula(r'V_{out} = V_{in} (1 + \frac{R_f}{R_{in}})'))
        elif self.rb_inv.isChecked():
            self.b_rin.setEnabled(True); self.b_rf.setEnabled(True)
            self.b_lbl_formula.setPixmap(self.render_formula(r'V_{out} = - V_{in} \frac{R_f}{R_{in}}'))
        else:
            self.b_rin.setEnabled(False); self.b_rf.setEnabled(False)
            self.b_rin.setText("∞"); self.b_rf.setText("0")
            self.b_lbl_formula.setPixmap(self.render_formula(r'V_{out} = V_{in}'))

    def calc_basic(self):
        try:
            vin = float(self.b_vin.text())
            gbp = float(self.b_gbp.text()) * 1e6
            
            if self.rb_follower.isChecked():
                mode = 'follower'
                rin, rf = None, None
            else:
                rin = float(self.b_rin.text())
                rf = float(self.b_rf.text())
                mode = 'noninv' if self.rb_noninv.isChecked() else 'inv'
            
            res = calc_basic_opamp(vin, gbp, mode, rin, rf)
            self.b_res_gain.setText(f"{res['gain_vv']:.2f} V/V ({res['gain_db']:.2f} dB)")
            self.b_res_vout.setText(f"{res['vout_v']:.3f} V")
            self.b_res_bw.setText(f"{res['bw_hz']/1000:.2f} kHz")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {e}")

    # ==============================================================================
    # Tab 2: Differential Amplifier
    # ==============================================================================
    def init_diff_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Resistors
        grp_r = QGroupBox("1. 电阻网络")
        grid = QGridLayout()
        self.d_r1 = QLineEdit("10"); self.d_r2 = QLineEdit("100")
        self.d_r3 = QLineEdit("10"); self.d_r4 = QLineEdit("100")
        
        grid.addWidget(QLabel("R1 (In-) [kΩ]:"), 0, 0); grid.addWidget(self.d_r1, 0, 1)
        grid.addWidget(QLabel("R2 (Fb) [kΩ]:"), 0, 2); grid.addWidget(self.d_r2, 0, 3)
        grid.addWidget(QLabel("R3 (In+) [kΩ]:"), 1, 0); grid.addWidget(self.d_r3, 1, 1)
        grid.addWidget(QLabel("R4 (Gnd) [kΩ]:"), 1, 2); grid.addWidget(self.d_r4, 1, 3)
        
        btn_match = QPushButton("自动匹配电阻 (R3=R1, R4=R2)")
        btn_match.setStyleSheet("background-color: #f39c12; color: white;")
        btn_match.clicked.connect(self.match_resistors)
        grid.addWidget(btn_match, 2, 0, 1, 4)
        grp_r.setLayout(grid)
        layout.addWidget(grp_r)
        
        # Inputs
        grp_in = QGroupBox("2. 输入信号")
        grid_in = QGridLayout()
        self.d_v1 = QLineEdit("2.5"); grid_in.addWidget(QLabel("V1 (反相) [V]:"), 0, 0); grid_in.addWidget(self.d_v1, 0, 1)
        self.d_v2 = QLineEdit("2.6"); grid_in.addWidget(QLabel("V2 (同相) [V]:"), 0, 2); grid_in.addWidget(self.d_v2, 0, 3)
        
        btn_calc = QPushButton("计算输出 Vout")
        btn_calc.setFixedHeight(40); btn_calc.setFont(QFont('Arial', 11, QFont.Bold))
        btn_calc.clicked.connect(self.calc_diff)
        grid_in.addWidget(btn_calc, 1, 0, 1, 4)
        grp_in.setLayout(grid_in)
        layout.addWidget(grp_in)
        
        # Result
        grp_res = QGroupBox("3. 结果")
        r_grid = QGridLayout()
        self.d_res_vout = QLineEdit(); r_grid.addWidget(QLabel("输出电压 Vout:"), 0, 0); r_grid.addWidget(self.d_res_vout, 0, 1)
        self.d_res_gain = QLineEdit(); r_grid.addWidget(QLabel("差模增益 Gain:"), 1, 0); r_grid.addWidget(self.d_res_gain, 1, 1)
        self.d_res_cmrr = QLineEdit(); r_grid.addWidget(QLabel("匹配状态:"), 2, 0); r_grid.addWidget(self.d_res_cmrr, 2, 1)
        
        # Formula Label
        self.d_lbl_form = QLabel()
        self.d_lbl_form.setPixmap(self.render_formula(r'V_{out} = V_2 (\frac{R_4}{R_3+R_4})(1+\frac{R_2}{R_1}) - V_1 (\frac{R_2}{R_1})', target_height=50))
        r_grid.addWidget(self.d_lbl_form, 3, 0, 1, 2)
        
        for w in [self.d_res_vout, self.d_res_gain, self.d_res_cmrr]:
            w.setReadOnly(True)
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        
        tab.setLayout(layout)

    def match_resistors(self):
        self.d_r3.setText(self.d_r1.text())
        self.d_r4.setText(self.d_r2.text())

    def calc_diff(self):
        try:
            r1 = float(self.d_r1.text())
            r2 = float(self.d_r2.text())
            r3 = float(self.d_r3.text())
            r4 = float(self.d_r4.text())
            v1 = float(self.d_v1.text())
            v2 = float(self.d_v2.text())
            
            res = calc_diff_opamp(r1, r2, r3, r4, v1, v2)
            self.d_res_vout.setText(f"{res['vout_v']:.4f} V")
            self.d_res_gain.setText(f"{res['gain_vv']:.2f} V/V")
            
            if res['is_matched']:
                self.d_res_cmrr.setText(" 匹配 (理想CMRR)")
                self.d_res_cmrr.setStyleSheet("background-color: #e8f8f5; color: #27ae60; font-weight: bold;")
                self.d_lbl_form.setPixmap(self.render_formula(r'V_{out} = \frac{R_2}{R_1}(V_2 - V_1)'))
            else:
                self.d_res_cmrr.setText(" 不匹配 (CMRR差)")
                self.d_res_cmrr.setStyleSheet("background-color: #fff5f5; color: #c0392b; font-weight: bold;")
                self.d_lbl_form.setPixmap(self.render_formula(r'V_{out} = V_2 (\frac{R_4}{R_3+R_4})(1+\frac{R_2}{R_1}) - V_1 (\frac{R_2}{R_1})', target_height=50))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {e}")

    # ==============================================================================
    # Tab 3: Summing
    # ==============================================================================
    def init_sum_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        h_fb = QHBoxLayout()
        self.s_rf = QLineEdit("10")
        h_fb.addWidget(QLabel("反馈电阻 Rf [kΩ]:")); h_fb.addWidget(self.s_rf); h_fb.addStretch()
        layout.addLayout(h_fb)
        
        grp_ch = QGroupBox("输入通道")
        grid = QGridLayout()
        self.s_r1 = QLineEdit("10"); self.s_v1 = QLineEdit("1.0")
        grid.addWidget(QLabel("R1 [kΩ]:"), 0, 0); grid.addWidget(self.s_r1, 0, 1); grid.addWidget(QLabel("V1 [V]:"), 0, 2); grid.addWidget(self.s_v1, 0, 3)
        self.s_r2 = QLineEdit("10"); self.s_v2 = QLineEdit("0.5")
        grid.addWidget(QLabel("R2 [kΩ]:"), 1, 0); grid.addWidget(self.s_r2, 1, 1); grid.addWidget(QLabel("V2 [V]:"), 1, 2); grid.addWidget(self.s_v2, 1, 3)
        self.s_r3 = QLineEdit("10"); self.s_v3 = QLineEdit("0")
        grid.addWidget(QLabel("R3 [kΩ]:"), 2, 0); grid.addWidget(self.s_r3, 2, 1); grid.addWidget(QLabel("V3 [V]:"), 2, 2); grid.addWidget(self.s_v3, 2, 3)
        grp_ch.setLayout(grid)
        layout.addWidget(grp_ch)
        
        btn = QPushButton("计算加法结果")
        btn.setFixedHeight(40)
        btn.clicked.connect(self.calc_sum)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("结果")
        h_res = QHBoxLayout()
        self.s_res_vout = QLineEdit(); self.s_res_vout.setReadOnly(True)
        h_res.addWidget(QLabel("输出电压 Vout:")); h_res.addWidget(self.s_res_vout)
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'V_{out} = -R_f (\frac{V_1}{R_1} + \frac{V_2}{R_2} + \frac{V_3}{R_3})'))
        h_res.addWidget(l_form)
        grp_res.setLayout(h_res)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_sum(self):
        try:
            rf = float(self.s_rf.text())
            channels = []
            for r_w, v_w in [(self.s_r1, self.s_v1), (self.s_r2, self.s_v2), (self.s_r3, self.s_v3)]:
                r = float(r_w.text())
                v = float(v_w.text())
                channels.append((r, v))
            vout = calc_summing_opamp(rf, channels)
            self.s_res_vout.setText(f"{vout:.4f} V")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {e}")

    # ==============================================================================
    # Tab 4: Hysteresis Comparator
    # ==============================================================================
    def init_hysteresis_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Topology Selection
        grp_topo = QGroupBox("1. 拓扑结构 (Topology)")
        topo_layout = QHBoxLayout()
        self.hys_rb_noninv = QRadioButton("同相迟滞 (Non-Inverting)")
        self.hys_rb_inv = QRadioButton("反相迟滞 (Inverting) [OVP]")
        self.hys_rb_noninv.setChecked(True)
        self.hys_rb_noninv.toggled.connect(self.update_hys_desc)
        
        bg = QButtonGroup(self)
        bg.addButton(self.hys_rb_noninv); bg.addButton(self.hys_rb_inv)
        topo_layout.addWidget(self.hys_rb_noninv); topo_layout.addWidget(self.hys_rb_inv); topo_layout.addStretch()
        grp_topo.setLayout(topo_layout)
        layout.addWidget(grp_topo)

        # 1. 阈值与电平设置
        grp_spec = QGroupBox("2. 阈值与电平设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.hys_v_high = QLineEdit("12.0"); self.hys_v_high.setToolTip("开启阈值 (Rising Threshold)")
        grid.addWidget(QLabel("上限阈值 V_high [V]:"), 0, 0); grid.addWidget(self.hys_v_high, 0, 1)
        
        self.hys_v_low = QLineEdit("10.0"); self.hys_v_low.setToolTip("关断阈值 (Falling Threshold)")
        grid.addWidget(QLabel("下限阈值 V_low [V]:"), 0, 2); grid.addWidget(self.hys_v_low, 0, 3)
        
        self.hys_v_out_h = QLineEdit("5.0"); self.hys_v_out_h.setToolTip("比较器输出高电平 (通常为 Vcc 或上拉电压)")
        grid.addWidget(QLabel("输出高电平 V_oh [V]:"), 1, 0); grid.addWidget(self.hys_v_out_h, 1, 1)
        
        self.hys_v_out_l = QLineEdit("0.0"); self.hys_v_out_l.setToolTip("比较器输出低电平 (通常为 GND)")
        grid.addWidget(QLabel("输出低电平 V_ol [V]:"), 1, 2); grid.addWidget(self.hys_v_out_l, 1, 3)
        
        self.hys_v_ref = QLineEdit("2.5"); self.hys_v_ref.setToolTip("基准电压 (TL431等)")
        grid.addWidget(QLabel("基准电压 V_ref [V]:"), 2, 0); grid.addWidget(self.hys_v_ref, 2, 1)
        
        self.hys_r_top = QLineEdit("100"); self.hys_r_top.setToolTip("上分压电阻 R1 (同相) 或 源端电阻 R1 (反相)")
        grid.addWidget(QLabel("预设电阻 R1 [kΩ]:"), 2, 2); grid.addWidget(self.hys_r_top, 2, 3)
        
        grp_spec.setLayout(grid)
        layout.addWidget(grp_spec)
        
        # 按钮
        btn_calc = QPushButton("计算反馈电阻与迟滞量")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_hysteresis)
        layout.addWidget(btn_calc)
        
        # 2. 结果
        grp_res = QGroupBox("3. 推荐电阻网络")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.hys_r2 = QLineEdit()
        self.hys_rf = QLineEdit()
        self.hys_actual_high = QLineEdit()
        self.hys_actual_low = QLineEdit()
        
        # R2
        r_grid.addWidget(QLabel("对地电阻 R2 (R_gnd):"), 0, 0); r_grid.addWidget(self.hys_r2, 0, 1)
        self.hys_lbl_r2_loc = QLabel("Location info")
        r_grid.addWidget(self.hys_lbl_r2_loc, 0, 2)
        
        # Rf
        r_grid.addWidget(QLabel("反馈电阻 Rf (Feedback):"), 1, 0); r_grid.addWidget(self.hys_rf, 1, 1)
        self.hys_lbl_rf_loc = QLabel("Location info")
        r_grid.addWidget(self.hys_lbl_rf_loc, 1, 2)
        
        # Verify
        r_grid.addWidget(QLabel("校验 V_high:"), 2, 0); r_grid.addWidget(self.hys_actual_high, 2, 1)
        r_grid.addWidget(QLabel("校验 V_low:"), 3, 0); r_grid.addWidget(self.hys_actual_low, 3, 1)
        
        # 错误/提示信息显示区域
        self.hys_msg = QLabel("")
        self.hys_msg.setWordWrap(True)
        r_grid.addWidget(self.hys_msg, 4, 0, 1, 3)

        for w in [self.hys_r2, self.hys_rf]: 
            w.setReadOnly(True)
        self.hys_actual_high.setReadOnly(True); self.hys_actual_low.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 拓扑说明
        self.hys_lbl_desc = QLabel()
        self.hys_lbl_desc.setStyleSheet("color: #555; background-color: #f9f9f9; padding: 10px; border: 1px dashed #ccc;")
        layout.addWidget(self.hys_lbl_desc)
        
        self.update_hys_desc()
        layout.addStretch()
        tab.setLayout(layout)

    def update_hys_desc(self):
        if self.hys_rb_noninv.isChecked():
            self.hys_lbl_desc.setText("同相迟滞拓扑 (Non-Inverting):\n"
                                      "  - 输入信号 Vin -> R1 -> In+\n"
                                      "  - 比较器 In- 接 V_ref (固定)\n"
                                      "  - 反馈 Rf 接 Output -> In+\n"
                                      "  - R2 接 In+ -> GND\n"
                                      "逻辑: Vin > V_high, Output High; Vin < V_low, Output Low.")
            self.hys_lbl_r2_loc.setText("连接 In+ 到 GND")
            self.hys_lbl_rf_loc.setText("连接 Output 到 In+")
        else:
            self.hys_lbl_desc.setText("反相迟滞拓扑 (Inverting) [OVP 常用]:\n"
                                      "  - 输入信号 Vin 直接接 In-\n"
                                      "  - 比较器 In+ 为参考端 (叠加 Vref 和 Feedback)\n"
                                      "  - R1 接 V_ref -> In+\n"
                                      "  - Rf 接 Output -> In+\n"
                                      "  - R2 接 In+ -> GND\n"
                                      "逻辑: Vin > V_high, Output Low (保护触发); Vin < V_low, Output High (恢复).")
            self.hys_lbl_r2_loc.setText("连接 In+ 到 GND")
            self.hys_lbl_rf_loc.setText("连接 Output 到 In+")

    def calc_hysteresis(self):
        self.hys_msg.setText("")
        self.hys_msg.setStyleSheet("")
        
        try:
            vh = float(self.hys_v_high.text())
            vl = float(self.hys_v_low.text())
            voh = float(self.hys_v_out_h.text())
            vol = float(self.hys_v_out_l.text())
            vref = float(self.hys_v_ref.text())
            r1 = float(self.hys_r_top.text()) # kOhm
            is_noninv = self.hys_rb_noninv.isChecked()
            
            res = calc_hysteresis_comparator(vh, vl, voh, vol, vref, r1, is_noninv)
            
            self.hys_r2.setText(f"{res['r2_k']:.2f} kΩ")
            self.hys_rf.setText(f"{res['rf_k']:.2f} kΩ")
            self.hys_actual_high.setText(f"{res['vh_calc_v']:.3f} V")
            self.hys_actual_low.setText(f"{res['vl_calc_v']:.3f} V")
        except Exception as e:
            self.hys_r2.setText("无法实现")
            self.hys_rf.setText("无法实现")
            self.hys_actual_high.setText("---")
            self.hys_actual_low.setText("---")
            self.hys_msg.setText(f"计算失败: {e}")
            self.hys_msg.setStyleSheet("color: red; font-weight: bold;")

    # ==============================================================================
    # Tab 5: Error Budget
    # ==============================================================================
    def init_error_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        layout.addWidget(QLabel("功能说明：估算同相放大电路在最坏情况下的总输出误差。\n考虑失调(Vos)、偏置(Ib)、共模(CMRR)、电源(PSRR)、温漂及电阻精度。"))

        # 1. Input Layout
        g_in = QGroupBox("1. 运放与电路参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(10)

        # OpAmp Specs
        self.err_vos = QLineEdit("1.0"); grid.addWidget(QLabel("失调电压 Vos (max) [mV]:"), 0, 0); grid.addWidget(self.err_vos, 0, 1)
        self.err_drift = QLineEdit("5.0"); grid.addWidget(QLabel("温漂 Drift [uV/°C]:"), 0, 2); grid.addWidget(self.err_drift, 0, 3)
        self.err_ib = QLineEdit("10"); grid.addWidget(QLabel("偏置电流 Ib (max) [nA]:"), 1, 0); grid.addWidget(self.err_ib, 1, 1)
        self.err_cmrr = QLineEdit("80"); grid.addWidget(QLabel("共模抑制比 CMRR [dB]:"), 1, 2); grid.addWidget(self.err_cmrr, 1, 3)
        self.err_psrr = QLineEdit("80"); grid.addWidget(QLabel("电源抑制比 PSRR [dB]:"), 2, 0); grid.addWidget(self.err_psrr, 2, 1)

        # Circuit Specs
        self.err_rin = QLineEdit("10"); grid.addWidget(QLabel("输入电阻 Rin [kΩ]:"), 3, 0); grid.addWidget(self.err_rin, 3, 1)
        self.err_rf = QLineEdit("90"); grid.addWidget(QLabel("反馈电阻 Rf [kΩ]:"), 3, 2); grid.addWidget(self.err_rf, 3, 3)
        self.err_rs = QLineEdit("0"); grid.addWidget(QLabel("信号源阻抗 Rs [kΩ]:"), 4, 0); grid.addWidget(self.err_rs, 4, 1)
        self.err_tol = QLineEdit("1.0"); grid.addWidget(QLabel("电阻精度 [%]:"), 4, 2); grid.addWidget(self.err_tol, 4, 3)
        
        # Environment
        self.err_dt = QLineEdit("50"); grid.addWidget(QLabel("温升 ΔT [°C]:"), 5, 0); grid.addWidget(self.err_dt, 5, 1)
        self.err_vin = QLineEdit("2.5"); grid.addWidget(QLabel("输入信号 Vin [V]:"), 5, 2); grid.addWidget(self.err_vin, 5, 3)
        self.err_vcm = QLineEdit("2.5"); grid.addWidget(QLabel("共模电压 Vcm [V]:"), 6, 0); grid.addWidget(self.err_vcm, 6, 1)
        self.err_dvcc = QLineEdit("0.1"); grid.addWidget(QLabel("电源波动 ΔVcc [V]:"), 6, 2); grid.addWidget(self.err_dvcc, 6, 3)

        g_in.setLayout(grid)
        layout.addWidget(g_in)

        btn = QPushButton("计算误差预算 (Calculate Error Budget)")
        btn.setFixedHeight(40)
        btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_error)
        layout.addWidget(btn)

        # 2. Result Table
        self.err_table = QTableWidget(7, 3)
        self.err_table.setHorizontalHeaderLabels(["误差源 (Source)", "输出误差 (mV)", "占比 (%)"])
        self.err_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.err_table.verticalHeader().setVisible(False)
        layout.addWidget(self.err_table)

        # Summary
        g_sum = QGroupBox("总误差汇总")
        h_sum = QHBoxLayout()
        self.err_rss = QLineEdit(); self.err_rss.setPlaceholderText("RSS Root-Sum-Square")
        self.err_worst = QLineEdit(); self.err_worst.setPlaceholderText("Worst Case (Sum)")
        h_sum.addWidget(QLabel("均方根误差 (RSS) [mV]:")); h_sum.addWidget(self.err_rss)
        h_sum.addWidget(QLabel("最坏情况误差 (Worst Case) [mV]:")); h_sum.addWidget(self.err_worst)
        g_sum.setLayout(h_sum)
        layout.addWidget(g_sum)

        self.err_rss.setReadOnly(True)
        self.err_worst.setReadOnly(True)
        tab.setLayout(layout)

    def calc_error(self):
        try:
            vos = float(self.err_vos.text()) # mV
            drift = float(self.err_drift.text()) # uV/C
            ib = float(self.err_ib.text()) # nA
            cmrr_db = float(self.err_cmrr.text())
            psrr_db = float(self.err_psrr.text())
            
            rin = float(self.err_rin.text()) * 1e3
            rf = float(self.err_rf.text()) * 1e3
            rs = float(self.err_rs.text()) * 1e3
            tol = float(self.err_tol.text()) / 100.0
            
            dt = float(self.err_dt.text())
            vin = float(self.err_vin.text())
            vcm = float(self.err_vcm.text())
            dvcc = float(self.err_dvcc.text())

            res = calc_error_budget(
                vos, drift, ib, cmrr_db, psrr_db, rin, rf, rs, tol, dt, vin, vcm, dvcc
            )
            
            errors = res['errors']
            total_worst = res['total_worst_mv']
            total_rss = res['total_rss_mv']
            
            # Populate Table
            self.err_table.setRowCount(len(errors))
            for i, (name, val) in enumerate(errors):
                self.err_table.setItem(i, 0, QTableWidgetItem(name))
                self.err_table.setItem(i, 1, QTableWidgetItem(f"{val:.3f}"))
                ratio = (val / total_worst * 100) if total_worst > 0 else 0
                self.err_table.setItem(i, 2, QTableWidgetItem(f"{ratio:.1f}%"))
                
            self.err_rss.setText(f"{total_rss:.3f}")
            self.err_worst.setText(f"{total_worst:.3f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数值无效: {e}")

    # ==============================================================================
    # Tab 6: 选型指南
    # ==============================================================================
    def init_selection_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_in = QGroupBox("1. 电路应用场景参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.sel_fsw = QLineEdit("20"); self.sel_fsw.setToolTip("系统开关频率 (Switching Frequency)")
        grid.addWidget(QLabel("开关频率 f_sw [kHz]:"), 0, 0); grid.addWidget(self.sel_fsw, 0, 1)
        
        self.sel_gain = QLineEdit("10"); self.sel_gain.setToolTip("目标闭环增益 (Closed Loop Gain)")
        grid.addWidget(QLabel("目标增益 Gain [V/V]:"), 0, 2); grid.addWidget(self.sel_gain, 0, 3)
        
        self.sel_vout_pp = QLineEdit("3.3"); self.sel_vout_pp.setToolTip("运放输出电压峰峰值 (通常为ADC满量程)")
        grid.addWidget(QLabel("输出摆幅 Vout_pp [V]:"), 1, 0); grid.addWidget(self.sel_vout_pp, 1, 1)
        
        self.sel_bits = QLineEdit("12"); self.sel_bits.setToolTip("ADC 位数，决定了需要的建立精度")
        grid.addWidget(QLabel("ADC 精度 [Bits]:"), 1, 2); grid.addWidget(self.sel_bits, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算运放关键指标 (GBP / SR / Offset)")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.setStyleSheet("background-color: #3498db; color: white;")
        btn.clicked.connect(self.calc_selection)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("2. 选型参考指标")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        
        self.sel_res_gbp = QLineEdit()
        res_grid.addWidget(QLabel("推荐最小 GBP:"), 0, 0); res_grid.addWidget(self.sel_res_gbp, 0, 1)
        l_gbp = QLabel(); l_gbp.setPixmap(self.render_formula(r'GBP \geq Gain \cdot f_{sw} \cdot 10 \sim 50'))
        res_grid.addWidget(l_gbp, 0, 2)
        
        self.sel_res_sr = QLineEdit()
        res_grid.addWidget(QLabel("推荐最小 SR:"), 1, 0); res_grid.addWidget(self.sel_res_sr, 1, 1)
        l_sr = QLabel(); l_sr.setPixmap(self.render_formula(r'SR \geq \frac{V_{pp}}{t_{settle}} \quad (t_{settle} \approx 5\% T_{sw})'))
        res_grid.addWidget(l_sr, 1, 2)
        
        self.sel_res_vos = QLineEdit()
        res_grid.addWidget(QLabel("最大允许 Vos:"), 2, 0); res_grid.addWidget(self.sel_res_vos, 2, 1)
        res_grid.addWidget(QLabel("基于 1/2 LSB 估算 (输入端)"), 2, 2)
        
        style_rec = "font-weight: bold; color: #d35400; font-size: 14px;"
        for w in [self.sel_res_gbp, self.sel_res_sr, self.sel_res_vos]:
            w.setReadOnly(True); w.setStyleSheet(style_rec)
            
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        
        layout.addWidget(QLabel(" 说明：建议值为理论下限，工程选型时建议再留 1.5 倍裕量。"))
        layout.addStretch()
        tab.setLayout(layout)

    def calc_selection(self):
        try:
            fsw = float(self.sel_fsw.text()) * 1e3 
            gain = float(self.sel_gain.text())
            v_pp = float(self.sel_vout_pp.text())
            bits = int(self.sel_bits.text())
            
            res = calc_opamp_selection(fsw, gain, v_pp, bits)
            
            self.sel_res_gbp.setText(f"> {res['gbp_min_hz']/1e6:.2f} MHz")
            self.sel_res_sr.setText(f"> {res['sr_min_v_s']/1e6:.2f} V/μs")
            self.sel_res_vos.setText(f"< {res['vos_max_input_v']*1e3:.3f} mV")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {e}")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("运放与比较器指南")
        dialog.resize(800, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        html = """
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
        </style>
        <h1>运放与比较器设计指南</h1>
        
        <h2>1. 迟滞比较器 (Hysteresis)</h2>
        <div class="box">
            <b>应用场景：</b> 防止信号在阈值附近抖动导致的输出震荡。
        </div>
        <ul>
            <li><b>同相迟滞 (Non-Inverting):</b> 输入接 In+。逻辑：Vin 高 -> Output 高。阈值计算较简单。</li>
            <li><b>反相迟滞 (Inverting):</b> 输入接 In-。逻辑：Vin 高 -> Output 低。
                <br>常用于 <b>过压保护 (OVP)</b>：检测到高电压时，拉低 Enable 信号关断电路。
                <br><i>注意：反相迟滞的阈值计算依赖于 Output 的高低电平状态，计算较复杂，本工具已内置求解器。</i>
            </li>
        </ul>

        <h2>2. 误差预算 (Error Budget)</h2>
        <div class="box">
            <b>设计痛点：</b> 许多工程师只看 Vos，忽略了电阻温漂和 Ib 带来的误差。
        </div>
        <p>本工具采用了 "Worst Case"（最坏情况直接相加）和 "RSS"（均方根）两种统计方式供参考。</p>

        <h2>3. 选型指南</h2>
        <ul>
            <li><b>GBP：</b> 确保 $GBP > Gain \times f_{signal} \times 20$。</li>
            <li><b>SR (压摆率)：</b> 对于大信号，SR 决定了能否不失真地输出波形。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()
