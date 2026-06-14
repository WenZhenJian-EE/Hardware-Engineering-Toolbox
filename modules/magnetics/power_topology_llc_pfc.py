from modules.base_module import BaseModule
# power_topology_llc_pfc.py

import sys
# 核心修复：必须在导入 pyplot 之前设置后端为 'Agg'，否则单独运行时会与 PyQt 冲突报错
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

import math
import numpy as np
from io import BytesIO

# 确保导入所有必要的 Qt 组件
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QScrollArea, QFrame, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class AdvancedTopologiesWindow(BaseModule):
    category = "1. 磁性元件与电源拓扑 (Magnetics & Topology)"
    display_name = "LLC / PFC / PSFB"
    description = "LLC设计 / 仿真 / PFC / 移相"
    window_id = "power_topology"

    def init_module_ui(self):
        
        self.init_ui()

    # 内置公式渲染函数
    def init_ui(self):
        self.setWindowTitle('高级拓扑分析与设计 (LLC & PFC & PSFB)')
        self.setGeometry(350, 350, 1150, 900)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计指南 / 参数详解")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(220)
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

        self.tab_llc_design = QWidget() # New Feature
        self.tab_llc_sim = QWidget()    # Existing
        self.tab_pfc = QWidget()
        self.tab_psfb = QWidget() 

        self.init_llc_design_ui(self.tab_llc_design)
        self.init_llc_sim_ui(self.tab_llc_sim)
        self.init_pfc_ui(self.tab_pfc)
        self.init_psfb_ui(self.tab_psfb) 

        self.tabs.addTab(self.tab_llc_design, "LLC 参数正向设计 (Design)")
        self.tabs.addTab(self.tab_llc_sim, "LLC 仿真与验证 (Analysis)")
        self.tabs.addTab(self.tab_pfc, "Boost PFC 电感设计 (CCM/CrM)")
        self.tabs.addTab(self.tab_psfb, "移相全桥 ZVS 范围 (PSFB)") 

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1 (NEW): LLC Forward Design (Synthesizer)
    # ==============================================================================
    def init_llc_design_ui(self, tab):
        outer_layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        info = QLabel("功能说明：根据输入输出规格和目标频率，正向计算谐振腔参数 (Lr, Cr, Lm, n)。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)

        # 1. 规格输入
        grp_spec = QGroupBox("1. 设计规格 (Specifications)")
        g_spec = QGridLayout()
        g_spec.setVerticalSpacing(12)
        
        self.des_vin_nom = QLineEdit("390"); g_spec.addWidget(QLabel("额定输入 Vin_nom [V]:"), 0, 0); g_spec.addWidget(self.des_vin_nom, 0, 1)
        self.des_vin_range = QLineEdit("350, 410"); self.des_vin_range.setPlaceholderText("min, max"); 
        g_spec.addWidget(QLabel("输入范围 Vin_min,max:"), 0, 2); g_spec.addWidget(self.des_vin_range, 0, 3)
        
        self.des_vout = QLineEdit("24"); g_spec.addWidget(QLabel("输出电压 Vout [V]:"), 1, 0); g_spec.addWidget(self.des_vout, 1, 1)
        self.des_pout = QLineEdit("200"); g_spec.addWidget(QLabel("满载功率 Pout [W]:"), 1, 2); g_spec.addWidget(self.des_pout, 1, 3)
        
        self.des_fr = QLineEdit("100"); g_spec.addWidget(QLabel("目标谐振频率 fr [kHz]:"), 2, 0); g_spec.addWidget(self.des_fr, 2, 1)
        
        grp_spec.setLayout(g_spec)
        layout.addWidget(grp_spec)
        
        # 2. 设定目标值
        grp_target = QGroupBox("2. 设定目标参数 (Target K & Q)")
        g_tgt = QGridLayout()
        
        self.des_k = QLineEdit("5.0"); self.des_k.setToolTip("电感比 K = Lm / Lr (推荐 3~7)")
        g_tgt.addWidget(QLabel("电感比 K (Lm/Lr):"), 0, 0); g_tgt.addWidget(self.des_k, 0, 1)
        g_tgt.addWidget(QLabel("推荐值: 5~6 (高效率), 3~4 (宽范围)"), 0, 2)
        
        self.des_q = QLineEdit("0.4"); self.des_q.setToolTip("满载品质因数 Q (推荐 0.3~0.5)")
        g_tgt.addWidget(QLabel("满载品质因数 Q_max:"), 1, 0); g_tgt.addWidget(self.des_q, 1, 1)
        g_tgt.addWidget(QLabel("推荐值: 0.35~0.45"), 1, 2)
        
        grp_target.setLayout(g_tgt)
        layout.addWidget(grp_target)
        
        # Button
        btn_calc = QPushButton("计算谐振腔参数 (Synthesize Tank)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; font-size: 14px;")
        btn_calc.clicked.connect(self.calc_llc_design)
        layout.addWidget(btn_calc)
        
        # 3. 计算结果
        grp_res = QGroupBox("3. 推荐参数 (Calculated Parameters)")
        g_res = QGridLayout()
        g_res.setVerticalSpacing(12)
        
        self.res_n = QLineEdit(); g_res.addWidget(QLabel("变压器匝比 n (Np:Ns):"), 0, 0); g_res.addWidget(self.res_n, 0, 1)
        self.res_rac = QLineEdit(); g_res.addWidget(QLabel("等效阻抗 Rac [Ω]:"), 0, 2); g_res.addWidget(self.res_rac, 0, 3)
        
        self.res_lr = QLineEdit(); g_res.addWidget(QLabel("谐振电感 Lr [uH]:"), 1, 0); g_res.addWidget(self.res_lr, 1, 1)
        self.res_cr = QLineEdit(); g_res.addWidget(QLabel("谐振电容 Cr [nF]:"), 1, 2); g_res.addWidget(self.res_cr, 1, 3)
        
        self.res_lm = QLineEdit(); g_res.addWidget(QLabel("励磁电感 Lm [uH]:"), 2, 0); g_res.addWidget(self.res_lm, 2, 1)
        self.res_z0 = QLineEdit(); g_res.addWidget(QLabel("特征阻抗 Zo [Ω]:"), 2, 2); g_res.addWidget(self.res_z0, 2, 3)

        for w in [self.res_n, self.res_rac, self.res_lr, self.res_cr, self.res_lm, self.res_z0]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #16a085;")
            
        grp_res.setLayout(g_res)
        layout.addWidget(grp_res)
        
        # 4. 增益校核
        grp_check = QGroupBox("4. 增益能力校核 (Gain Check)")
        g_chk = QGridLayout()
        
        self.chk_m_req = QLineEdit(); g_chk.addWidget(QLabel("Vin_min 时所需增益 M_max:"), 0, 0); g_chk.addWidget(self.chk_m_req, 0, 1)
        self.chk_m_peak = QLineEdit(); g_chk.addWidget(QLabel("当前K/Q可达峰值增益 M_peak:"), 0, 2); g_chk.addWidget(self.chk_m_peak, 0, 3)
        self.chk_status = QLineEdit(); g_chk.addWidget(QLabel("校核结果:"), 1, 0); g_chk.addWidget(self.chk_status, 1, 1, 1, 3)
        
        for w in [self.chk_m_req, self.chk_m_peak]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #f4f6f6;")
        
        grp_check.setLayout(g_chk)
        layout.addWidget(grp_check)
        
        layout.addStretch()
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def calc_llc_design(self):
        try:
            # Inputs
            vin_nom = float(self.des_vin_nom.text())
            
            # Parse Vin Range
            vin_range_str = self.des_vin_range.text().replace('，', ',')
            if ',' in vin_range_str:
                parts = vin_range_str.split(',')
                vin_min = float(parts[0])
                vin_max = float(parts[1])
            else:
                vin_min = vin_nom * 0.9
                vin_max = vin_nom * 1.1
                self.des_vin_range.setText(f"{vin_min:.0f}, {vin_max:.0f}")

            vout = float(self.des_vout.text())
            pout = float(self.des_pout.text())
            fr = float(self.des_fr.text()) * 1e3
            k = float(self.des_k.text())
            q = float(self.des_q.text())
            
            if pout <= 0 or fr <= 0 or vin_min <= 0: raise ValueError
            
            # 1. Calculate Turns Ratio n
            # Strategy: Set resonant point at Vin_nom (M=1)
            # M = 1 = n * Vout / Vin_nom  => n = Vin_nom / Vout
            n = vin_nom / vout
            
            # 2. Rac
            # R_load = Vout^2 / Pout
            r_load = (vout ** 2) / pout
            rac = (8 * n**2 / (math.pi**2)) * r_load
            
            # 3. Tank Impedance Zo
            # Q = Zo / Rac => Zo = Q * Rac
            z0 = q * rac
            
            # 4. Lr, Cr
            # Zo = sqrt(Lr/Cr), wr = 1/sqrt(LrCr)
            # Lr = Zo / wr
            # Cr = 1 / (wr * Zo)
            w_r = 2 * math.pi * fr
            lr = z0 / w_r
            cr = 1.0 / (w_r * z0)
            
            # 5. Lm
            lm = k * lr
            
            # Display Results
            self.res_n.setText(f"{n:.2f} : 1")
            self.res_rac.setText(f"{rac:.2f}")
            self.res_lr.setText(f"{lr*1e6:.2f}")
            self.res_cr.setText(f"{cr*1e9:.2f}")
            self.res_lm.setText(f"{lm*1e6:.2f}")
            self.res_z0.setText(f"{z0:.2f}")
            
            # 6. Check Gain Requirement
            # Required Max Gain at Vin_min
            # M_req = n * Vout / Vin_min
            m_req_max = n * vout / vin_min
            
            # Calculate Peak Gain capability of this tank (approximate scan)
            # Scan fn from 0.3 to 1.0
            fn_arr = np.linspace(0.3, 1.0, 200)
            
            def get_gain(f_norm):
                term1 = 1 + (1/k) * (1 - 1/(f_norm**2))
                term2 = q * (f_norm - 1/f_norm)
                return 1 / np.sqrt(term1**2 + term2**2)
            
            gains = get_gain(fn_arr)
            m_peak_avail = np.max(gains)
            
            self.chk_m_req.setText(f"{m_req_max:.3f}")
            self.chk_m_peak.setText(f"{m_peak_avail:.3f}")
            
            if m_peak_avail >= m_req_max * 1.05: # 5% margin
                self.chk_status.setText("PASS (设计合理，增益充足)")
                self.chk_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            elif m_peak_avail >= m_req_max:
                self.chk_status.setText("MARGINAL (增益余量较小，建议减小 Q 或 K)")
                self.chk_status.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold;")
            else:
                self.chk_status.setText(f"FAIL (最大增益不足！需要 < {m_peak_avail:.2f})")
                self.chk_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数字参数")

    # ==============================================================================
    # Tab 2 (Existing): LLC Analysis (Renamed from init_llc_ui)
    # ==============================================================================
    def init_llc_sim_ui(self, tab):
        # 使用 QScrollArea 确保内容过多时可以滚动
        outer_layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)
        
        # 1. 谐振槽参数
        grp_tank = QGroupBox("1. 谐振腔与变压器参数 (Resonant Tank)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.llc_lr = QLineEdit("60"); grid.addWidget(QLabel("谐振电感 Lr [uH]:"), 0, 0); grid.addWidget(self.llc_lr, 0, 1)
        self.llc_cr = QLineEdit("20"); grid.addWidget(QLabel("谐振电容 Cr [nF]:"), 0, 2); grid.addWidget(self.llc_cr, 0, 3)
        self.llc_lm = QLineEdit("200"); grid.addWidget(QLabel("励磁电感 Lm [uH]:"), 1, 0); grid.addWidget(self.llc_lm, 1, 1)
        self.llc_n = QLineEdit("10"); self.llc_n.setToolTip("变压器匝比 Np:Ns"); grid.addWidget(QLabel("匝比 n (Np/Ns):"), 1, 2); grid.addWidget(self.llc_n, 1, 3)
        
        grp_tank.setLayout(grid)
        content_layout.addWidget(grp_tank)
        
        # 2. 工况参数
        grp_op = QGroupBox("2. 输入输出工况 (Operation Conditions)")
        grid_op = QGridLayout()
        
        self.llc_vin = QLineEdit("390"); grid_op.addWidget(QLabel("输入电压 Vin_nom [V]:"), 0, 0); grid_op.addWidget(self.llc_vin, 0, 1)
        self.llc_vout = QLineEdit("24"); grid_op.addWidget(QLabel("输出电压 Vout [V]:"), 0, 2); grid_op.addWidget(self.llc_vout, 0, 3)
        self.llc_pout = QLineEdit("200"); grid_op.addWidget(QLabel("额定功率 Pout [W]:"), 1, 0); grid_op.addWidget(self.llc_pout, 1, 1)
        
        grp_op.setLayout(grid_op)
        content_layout.addWidget(grp_op)
        
        # 按钮布局 (分开计算和绘图)
        btn_layout = QHBoxLayout()
        
        self.btn_calc = QPushButton("1. 计算关键参数 (K, Q, Rac)")
        self.btn_calc.setFixedHeight(45)
        self.btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.btn_calc.clicked.connect(self.calc_llc_params)
        
        self.btn_plot = QPushButton("2. 绘制增益曲线 (Gain Curve)")
        self.btn_plot.setFixedHeight(45)
        self.btn_plot.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        self.btn_plot.clicked.connect(self.plot_llc_curve)
        
        btn_layout.addWidget(self.btn_calc)
        btn_layout.addWidget(self.btn_plot)
        content_layout.addLayout(btn_layout)
        
        # 3. 计算结果 (列表式带公式)
        grp_res = QGroupBox("3. 关键参数结果 (Key Parameters)")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(10)
        res_grid.setColumnStretch(1, 1) # 让数值框拉伸
        
        self.llc_fr = QLineEdit()
        self.llc_k = QLineEdit()
        self.llc_rac = QLineEdit()
        self.llc_q = QLineEdit()
        self.llc_m_req = QLineEdit()
        
        # 定义每一行的数据: (Label, Widget, LaTeX Formula)
        rows_data = [
            ("谐振频率 fr [kHz]:", self.llc_fr, r'f_r = \frac{1}{2\pi \sqrt{L_r C_r}}'),
            ("电感比 K (Lm/Lr):", self.llc_k, r'K = \frac{L_m}{L_r}'),
            ("品质因数 Q (满载):", self.llc_q, r'Q = \frac{\sqrt{L_r/C_r}}{R_{ac}}'),
            ("等效阻抗 Rac [Ω]:", self.llc_rac, r'R_{ac} = \frac{8 n^2}{\pi^2} R_{load}'),
            ("所需增益 M_req:", self.llc_m_req, r'M_{req} = \frac{n V_{out}}{V_{in}}')
        ]
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        
        for i, (label_txt, widget, formula_str) in enumerate(rows_data):
            res_grid.addWidget(QLabel(label_txt), i, 0)
            widget.setReadOnly(True)
            widget.setStyleSheet(style_res)
            res_grid.addWidget(widget, i, 1)
            l_form = QLabel()
            l_form.setPixmap(self.render_formula(formula_str))
            res_grid.addWidget(l_form, i, 2)

        # 底部添加 FHA 增益总公式
        frame_line = QFrame()
        frame_line.setFrameShape(QFrame.HLine)
        frame_line.setFrameShadow(QFrame.Sunken)
        res_grid.addWidget(frame_line, 5, 0, 1, 3)
        
        l_main_form = QLabel()
        l_main_form.setAlignment(Qt.AlignCenter)
        l_main_form.setPixmap(self.render_formula(r'M = \frac{1}{\sqrt{(1+\frac{1}{K}(1-\frac{1}{f_n^2}))^2 + Q^2(f_n - \frac{1}{f_n})^2}}', target_height=50))
        res_grid.addWidget(l_main_form, 6, 0, 1, 3)
            
        grp_res.setLayout(res_grid)
        content_layout.addWidget(grp_res)

        # 4. ZVS 软开关校核 (ZVS Check) - NEW FEATURE
        grp_zvs = QGroupBox("4. ZVS 软开关校核 (ZVS Check Condition)")
        zvs_grid = QGridLayout()
        zvs_grid.setVerticalSpacing(10)
        
        self.llc_zvs_td = QLineEdit("200"); self.llc_zvs_td.setToolTip("死区时间 Deadtime")
        zvs_grid.addWidget(QLabel("死区 T_dead [ns]:"), 0, 0); zvs_grid.addWidget(self.llc_zvs_td, 0, 1)
        
        self.llc_zvs_coss = QLineEdit("150"); self.llc_zvs_coss.setToolTip("MOSFET Co(er) or Coss at high voltage")
        zvs_grid.addWidget(QLabel("MOS Coss(eq) [pF]:"), 0, 2); zvs_grid.addWidget(self.llc_zvs_coss, 0, 3)
        
        self.llc_zvs_fsw = QLineEdit("100"); self.llc_zvs_fsw.setToolTip("实际工作开关频率 (通常校核最高频率或谐振频率)")
        zvs_grid.addWidget(QLabel("校核工作频率 fsw [kHz]:"), 1, 0); zvs_grid.addWidget(self.llc_zvs_fsw, 1, 1)
        
        btn_zvs = QPushButton("校核 ZVS 条件")
        btn_zvs.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        btn_zvs.clicked.connect(self.calc_llc_zvs)
        zvs_grid.addWidget(btn_zvs, 1, 2, 1, 2)
        
        # Results
        self.llc_zvs_imin = QLineEdit()
        self.llc_zvs_imag = QLineEdit()
        self.llc_zvs_res = QLineEdit()
        
        zvs_grid.addWidget(QLabel("所需最小励磁电流 Im_min:"), 2, 0); zvs_grid.addWidget(self.llc_zvs_imin, 2, 1)
        zvs_grid.addWidget(QLabel("实际励磁电流峰值 Im_pk:"), 2, 2); zvs_grid.addWidget(self.llc_zvs_imag, 2, 3)
        zvs_grid.addWidget(QLabel("校核结果:"), 3, 0); zvs_grid.addWidget(self.llc_zvs_res, 3, 1, 1, 3)
        
        # Formula for ZVS
        l_zvs_form = QLabel()
        l_zvs_form.setPixmap(self.render_formula(r'I_{m\_pk} \geq I_{min} = \frac{2 V_{in} C_{oss}}{T_{dead}}'))
        zvs_grid.addWidget(l_zvs_form, 4, 0, 1, 4, Qt.AlignCenter)

        for w in [self.llc_zvs_imin, self.llc_zvs_imag, self.llc_zvs_res]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #fcf3cf; font-weight: bold;")
            
        grp_zvs.setLayout(zvs_grid)
        content_layout.addWidget(grp_zvs)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def get_llc_values(self):
        """辅助函数：获取并计算基础值"""
        lr = float(self.llc_lr.text()) * 1e-6
        cr = float(self.llc_cr.text()) * 1e-9
        lm = float(self.llc_lm.text()) * 1e-6
        n = float(self.llc_n.text())
        vin = float(self.llc_vin.text())
        vout = float(self.llc_vout.text())
        pout = float(self.llc_pout.text())
        
        fr = 1 / (2 * math.pi * math.sqrt(lr * cr))
        k_ratio = lm / lr
        z0 = math.sqrt(lr / cr)
        
        r_load = (vout**2) / pout if pout > 0 else 1e9
        rac = (8 * n**2 / (math.pi**2)) * r_load
        
        q_val = z0 / rac if rac > 0 else 0
        m_req = vout * n / vin
        
        return fr, k_ratio, q_val, rac, m_req

    def calc_llc_params(self):
        try:
            fr, k_ratio, q_val, rac, m_req = self.get_llc_values()
            
            self.llc_fr.setText(f"{fr/1000:.2f}")
            self.llc_k.setText(f"{k_ratio:.2f}")
            self.llc_q.setText(f"{q_val:.3f}")
            self.llc_rac.setText(f"{rac:.2f}")
            self.llc_m_req.setText(f"{m_req:.3f}")

            # 自动填充 ZVS 校核的频率为谐振频率 (作为参考起点)
            self.llc_zvs_fsw.setText(f"{fr/1000:.2f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def calc_llc_zvs(self):
        try:
            vin = float(self.llc_vin.text())
            vout = float(self.llc_vout.text())
            n = float(self.llc_n.text())
            lm = float(self.llc_lm.text()) * 1e-6
            
            td = float(self.llc_zvs_td.text()) * 1e-9
            coss = float(self.llc_zvs_coss.text()) * 1e-12
            fsw = float(self.llc_zvs_fsw.text()) * 1e3
            
            if fsw <= 0 or td <= 0: raise ValueError
            
            # 1. Min required magnetizing current
            im_min = (2 * vin * coss) / td
            
            # 2. Actual peak magnetizing current
            # Approximation assuming near resonance
            im_pk = (n * vout) / (4 * lm * fsw)
            
            self.llc_zvs_imin.setText(f"{im_min:.2f} A")
            self.llc_zvs_imag.setText(f"{im_pk:.2f} A")
            
            if im_pk > im_min:
                self.llc_zvs_res.setText(f"PASS (余量 {(im_pk-im_min):.2f}A)")
                self.llc_zvs_res.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.llc_zvs_res.setText("FAIL (ZVS 丢失! 减小 Lm 或增加死区)")
                self.llc_zvs_res.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
        except Exception as e:
             QMessageBox.warning(self, "错误", "请确保所有LLC参数和ZVS参数（fsw, td, Coss）已正确填写")

    def plot_llc_curve(self):
        try:
            # 重新计算以确保数据最新
            fr, k_ratio, q_val, rac, m_req = self.get_llc_values()
            self.calc_llc_params() # 顺便刷新界面数值
            self.plot_llc_gain_window(k_ratio, q_val, m_req, fr)
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效，无法绘图")

    def plot_llc_gain_window(self, k, q_nom, m_req, fr):
        try:
            # Frequency range: 0.2 fr to 2.0 fr
            fn = np.linspace(0.2, 2.0, 500)
            
            # Gain Formula (FHA)
            def calculate_gain(f_norm, q_val):
                term1 = 1 + (1/k) * (1 - 1/(f_norm**2))
                term2 = q_val * (f_norm - 1/f_norm)
                return 1 / np.sqrt(term1**2 + term2**2)
            
            q_list = [q_nom, q_nom*0.5, q_nom*0.2]
            labels = ["100% Load", "50% Load", "20% Load"]
            colors = ['r', 'g', 'b']
            
            plt.rcParams.update({'font.size': 10})
            fig, ax = plt.subplots(figsize=(9, 6), dpi=100)
            
            for q, lbl, c in zip(q_list, labels, colors):
                m_curve = calculate_gain(fn, q)
                ax.plot(fn, m_curve, label=f"Q={q:.2f} ({lbl})", color=c, linewidth=2)
            ax.axhline(y=m_req, color='orange', linestyle='--', label=f"Req Gain M={m_req:.2f}")
            ax.axvline(x=1.0, color='gray', linestyle=':', label="fr (Resonance)")
            
            ax.set_title(f"LLC Gain Curve (K={k:.1f}, fr={fr/1000:.1f}kHz)")
            ax.set_xlabel("Normalized Frequency (fn = fsw/fr)")
            ax.set_ylabel("Voltage Gain M")
            ax.set_ylim(0, max(2.0, m_req*1.5))
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.legend(loc='best')
            
            # Show Dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("LLC 增益曲线")
            dialog.resize(900, 700)
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

    # ==============================================================================
    # Tab 3: Boost PFC Inductor Design
    # ==============================================================================
    def init_pfc_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.pfc_input_group = QGroupBox("1. PFC 设计参数 (CCM Boost)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        # Mode selector
        self.pfc_mode = QComboBox()
        self.pfc_mode.addItems(["CCM (连续导通模式)", "CrM (临界/边界导通模式)"])
        self.pfc_mode.currentIndexChanged.connect(self.on_pfc_mode_changed)
        grid.addWidget(QLabel("工作模式 Mode:"), 0, 0)
        grid.addWidget(self.pfc_mode, 0, 1, 1, 3)
        
        self.pfc_vac_min = QLineEdit("85"); grid.addWidget(QLabel("最小输入电压 Vac_min [Vrms]:"), 1, 0); grid.addWidget(self.pfc_vac_min, 1, 1)
        self.pfc_vbus = QLineEdit("400"); grid.addWidget(QLabel("输出母线电压 Vbus [Vdc]:"), 1, 2); grid.addWidget(self.pfc_vbus, 1, 3)
        
        self.pfc_pout = QLineEdit("500"); grid.addWidget(QLabel("输出功率 Pout [W]:"), 2, 0); grid.addWidget(self.pfc_pout, 2, 1)
        self.pfc_eff = QLineEdit("0.95"); grid.addWidget(QLabel("效率 Efficiency (0~1):"), 2, 2); grid.addWidget(self.pfc_eff, 2, 3)
        
        self.pfc_fsw_label = QLabel("开关频率 fsw [kHz]:")
        self.pfc_fsw = QLineEdit("65"); grid.addWidget(self.pfc_fsw_label, 3, 0); grid.addWidget(self.pfc_fsw, 3, 1)
        
        self.pfc_ripple_label = QLabel("电流纹波率 Ripple [%]:")
        self.pfc_ripple = QLineEdit("20"); grid.addWidget(self.pfc_ripple_label, 3, 2); grid.addWidget(self.pfc_ripple, 3, 3)
        
        self.pfc_input_group.setLayout(grid)
        layout.addWidget(self.pfc_input_group)
        
        btn = QPushButton("计算 PFC 电感参数")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_pfc)
        layout.addWidget(btn)
        
        self.pfc_res_group = QGroupBox("2. 计算结果")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(10)
        
        self.pfc_iin_pk = QLineEdit(); res_grid.addWidget(QLabel("输入电流峰值 I_in_pk [A]:"), 0, 0); res_grid.addWidget(self.pfc_iin_pk, 0, 1)
        self.pfc_duty = QLineEdit(); res_grid.addWidget(QLabel("峰值处占空比 Duty:"), 0, 2); res_grid.addWidget(self.pfc_duty, 0, 3)
        
        self.pfc_l_min = QLineEdit()
        self.pfc_l_label = QLabel("最小电感量 L_min [uH]:")
        res_grid.addWidget(self.pfc_l_label, 1, 0); res_grid.addWidget(self.pfc_l_min, 1, 1)
        
        self.pfc_i_L_pk = QLineEdit()
        self.pfc_i_L_pk_label = QLabel("电感峰值电流 I_L_pk [A]:")
        res_grid.addWidget(self.pfc_i_L_pk_label, 1, 2); res_grid.addWidget(self.pfc_i_L_pk, 1, 3)
        
        # New fields for CrM
        self.pfc_ton_label = QLabel("导通时间 t_on [us]:")
        self.pfc_ton = QLineEdit()
        res_grid.addWidget(self.pfc_ton_label, 2, 0); res_grid.addWidget(self.pfc_ton, 2, 1)
        
        self.pfc_fsw_max_label = QLabel("最高开关频率 f_max [kHz]:")
        self.pfc_fsw_max = QLineEdit()
        res_grid.addWidget(self.pfc_fsw_max_label, 2, 2); res_grid.addWidget(self.pfc_fsw_max, 2, 3)
        
        self.pfc_ton_label.setVisible(False)
        self.pfc_ton.setVisible(False)
        self.pfc_fsw_max_label.setVisible(False)
        self.pfc_fsw_max.setVisible(False)
        
        # Formulas
        self.pfc_formula_i = QLabel()
        self.pfc_formula_i.setAlignment(Qt.AlignCenter)
        self.pfc_formula_i.setPixmap(self.render_formula(r'I_{pk} = \frac{\sqrt{2} P_{out}}{\eta \cdot V_{ac\_min}}'))
        res_grid.addWidget(self.pfc_formula_i, 3, 0, 1, 2)
        
        self.pfc_formula_l = QLabel()
        self.pfc_formula_l.setAlignment(Qt.AlignCenter)
        self.pfc_formula_l.setPixmap(self.render_formula(r'L = \frac{\sqrt{2} V_{ac\_min} \cdot (1 - \frac{\sqrt{2} V_{ac\_min}}{V_{bus}})}{f_{sw} \cdot \Delta I}'))
        res_grid.addWidget(self.pfc_formula_l, 3, 2, 1, 2)
        
        for w in [self.pfc_iin_pk, self.pfc_duty, self.pfc_l_min, self.pfc_i_L_pk, self.pfc_ton, self.pfc_fsw_max]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #f4ecf7; font-weight: bold; color: #8e44ad;")
            
        self.pfc_res_group.setLayout(res_grid)
        layout.addWidget(self.pfc_res_group)
        layout.addStretch()
        tab.setLayout(layout)

    def on_pfc_mode_changed(self):
        mode = self.pfc_mode.currentIndex()
        if mode == 0: # CCM
            self.pfc_input_group.setTitle("1. PFC 设计参数 (CCM Boost)")
            self.pfc_fsw_label.setText("开关频率 fsw [kHz]:")
            self.pfc_ripple.setEnabled(True)
            self.pfc_ripple.setText("20")
            self.pfc_l_label.setText("最小电感量 L_min [uH]:")
            self.pfc_i_L_pk_label.setText("电感峰值电流 I_L_pk [A]:")
            
            self.pfc_ton_label.setVisible(False)
            self.pfc_ton.setVisible(False)
            self.pfc_fsw_max_label.setVisible(False)
            self.pfc_fsw_max.setVisible(False)
            
            self.pfc_formula_i.setPixmap(self.render_formula(r'I_{pk} = \frac{\sqrt{2} P_{out}}{\eta \cdot V_{ac\_min}}'))
            self.pfc_formula_l.setPixmap(self.render_formula(r'L = \frac{\sqrt{2} V_{ac\_min} \cdot (1 - \frac{\sqrt{2} V_{ac\_min}}{V_{bus}})}{f_{sw} \cdot \Delta I}'))
        else: # CrM
            self.pfc_input_group.setTitle("1. PFC 设计参数 (CrM Boost)")
            self.pfc_fsw_label.setText("最低开关频率 f_min [kHz]:")
            self.pfc_ripple.setEnabled(False)
            self.pfc_ripple.setText("200") # Ripple is fixed in CrM
            self.pfc_l_label.setText("设计电感量 L [uH]:")
            self.pfc_i_L_pk_label.setText("电感峰值电流 I_L_pk [A]:")
            
            self.pfc_ton_label.setVisible(True)
            self.pfc_ton.setVisible(True)
            self.pfc_fsw_max_label.setVisible(True)
            self.pfc_fsw_max.setVisible(True)
            
            self.pfc_formula_i.setPixmap(self.render_formula(r'I_{L\_pk} = \frac{2\sqrt{2} P_{out}}{\eta \cdot V_{ac\_min}}'))
            self.pfc_formula_l.setPixmap(self.render_formula(r'L = \frac{\eta \cdot V_{ac\_min}^2 \cdot (V_{bus} - \sqrt{2} V_{ac\_min})}{2 \cdot P_{out} \cdot f_{min} \cdot V_{bus}}'))

    def calc_pfc(self):
        try:
            vac_min = float(self.pfc_vac_min.text())
            vbus = float(self.pfc_vbus.text())
            pout = float(self.pfc_pout.text())
            eff = float(self.pfc_eff.text())
            
            vin_pk_min = vac_min * math.sqrt(2)
            
            if vin_pk_min >= vbus:
                QMessageBox.warning(self, "参数错误", "Boost PFC 要求 Vin_peak < Vbus")
                return
            
            mode = self.pfc_mode.currentIndex()
            
            if mode == 0: # CCM
                fsw = float(self.pfc_fsw.text()) * 1e3
                ripple_ratio = float(self.pfc_ripple.text()) / 100.0
                
                iin_rms = (pout / eff) / vac_min
                iin_pk_val = iin_rms * math.sqrt(2)
                
                delta_i = ripple_ratio * iin_pk_val
                duty_pk = 1 - (vin_pk_min / vbus)
                l_min = (vin_pk_min * duty_pk) / (fsw * delta_i)
                i_l_pk = iin_pk_val + delta_i / 2
                
                self.pfc_iin_pk.setText(f"{iin_pk_val:.2f}")
                self.pfc_duty.setText(f"{duty_pk:.2f}")
                self.pfc_l_min.setText(f"{l_min*1e6:.1f}")
                self.pfc_i_L_pk.setText(f"{i_l_pk:.2f}")
                self.pfc_ton.clear()
                self.pfc_fsw_max.clear()
            else: # CrM
                fmin = float(self.pfc_fsw.text()) * 1e3
                
                iin_rms = (pout / eff) / vac_min
                iin_pk_val = iin_rms * math.sqrt(2)
                
                # In CrM, peak inductor current is 2 * input peak current
                i_l_pk = 2 * iin_pk_val
                duty_pk = 1 - (vin_pk_min / vbus)
                
                # Inductance L
                l_val = (eff * (vac_min**2) * (vbus - vin_pk_min)) / (2 * pout * fmin * vbus)
                
                # On-time ton
                ton_val = (vbus - vin_pk_min) / (vbus * fmin)
                
                # Max frequency at zero crossing
                fmax_val = 1.0 / ton_val
                
                self.pfc_iin_pk.setText(f"{iin_pk_val:.2f}")
                self.pfc_duty.setText(f"{duty_pk:.2f}")
                self.pfc_l_min.setText(f"{l_val*1e6:.1f}")
                self.pfc_i_L_pk.setText(f"{i_l_pk:.2f}")
                self.pfc_ton.setText(f"{ton_val*1e6:.2f}")
                self.pfc_fsw_max.setText(f"{fmax_val/1e3:.1f}")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 4: Phase Shift Full Bridge (PSFB) ZVS Estimator
    # ==============================================================================
    def init_psfb_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：估算移相全桥(PSFB)滞后臂(Lagging Leg)实现 ZVS 所需的能量和最小电流。\n"
                      "滞后臂 ZVS 依赖谐振电感和漏感的能量，比超前臂更难实现软开关。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. 输入参数
        grp_in = QGroupBox("1. 电路参数 (Circuit Parameters)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.psfb_lr = QLineEdit("20"); self.psfb_lr.setToolTip("外加的谐振电感 (Resonant Inductor)")
        grid.addWidget(QLabel("谐振电感 Lr [uH]:"), 0, 0); grid.addWidget(self.psfb_lr, 0, 1)
        
        self.psfb_llk = QLineEdit("5"); self.psfb_llk.setToolTip("变压器原边漏感 (Transformer Leakage)")
        grid.addWidget(QLabel("变压器漏感 Llk [uH]:"), 0, 2); grid.addWidget(self.psfb_llk, 0, 3)
        
        self.psfb_coss = QLineEdit("200"); self.psfb_coss.setToolTip("MOSFET 的输出电容，查阅 Datasheet (Co(er) 或特定电压下的 Coss)")
        grid.addWidget(QLabel("MOSFET Coss [pF]:"), 1, 0); grid.addWidget(self.psfb_coss, 1, 1)
        
        self.psfb_vin = QLineEdit("390"); grid.addWidget(QLabel("输入电压 Vin [V]:"), 1, 2); grid.addWidget(self.psfb_vin, 1, 3)
        
        self.psfb_dt = QLineEdit("300"); self.psfb_dt.setToolTip("设定的死区时间")
        grid.addWidget(QLabel("死区时间 T_dead [ns]:"), 2, 0); grid.addWidget(self.psfb_dt, 2, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn_calc = QPushButton("计算 ZVS 临界条件")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_psfb_zvs)
        layout.addWidget(btn_calc)
        
        # 2. 结果
        grp_res = QGroupBox("2. 滞后臂 ZVS 评估 (Lagging Leg Analysis)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.psfb_res_imin = QLineEdit()
        self.psfb_res_ecap = QLineEdit()
        self.psfb_res_tmin = QLineEdit()
        self.psfb_status = QLineEdit()
        
        # Row 1: Min Current
        r_grid.addWidget(QLabel("ZVS 最小原边电流 I_min [A]:"), 0, 0); r_grid.addWidget(self.psfb_res_imin, 0, 1)
        l_imin = QLabel(); l_imin.setPixmap(self.render_formula(r'I_{min} = \sqrt{\frac{2 \cdot (2 C_{oss}) \cdot V_{in}^2}{L_r + L_{lk}}}'))
        r_grid.addWidget(l_imin, 0, 2)
        
        # Row 2: Capacitive Energy
        r_grid.addWidget(QLabel("开关节点电容能量 E_cap [uJ]:"), 1, 0); r_grid.addWidget(self.psfb_res_ecap, 1, 1)
        l_ecap = QLabel(); l_ecap.setPixmap(self.render_formula(r'E_{cap} = \frac{1}{2} (2 C_{oss}) V_{in}^2'))
        r_grid.addWidget(l_ecap, 1, 2)
        
        # Row 3: Deadtime Check
        r_grid.addWidget(QLabel("I_min 下的最短死区 T_req [ns]:"), 2, 0); r_grid.addWidget(self.psfb_res_tmin, 2, 1)
        l_time = QLabel(); l_time.setPixmap(self.render_formula(r'T_{req} \approx \frac{2 C_{oss} V_{in}}{I_{min}}'))
        r_grid.addWidget(l_time, 2, 2)
        
        # Row 4: Status
        r_grid.addWidget(QLabel("死区时间校验:"), 3, 0); r_grid.addWidget(self.psfb_status, 3, 1, 1, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.psfb_res_imin, self.psfb_res_ecap, self.psfb_res_tmin]:
            w.setReadOnly(True); w.setStyleSheet(style)
        self.psfb_status.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_psfb_zvs(self):
        try:
            lr = float(self.psfb_lr.text()) * 1e-6
            llk = float(self.psfb_llk.text()) * 1e-6
            coss = float(self.psfb_coss.text()) * 1e-12
            vin = float(self.psfb_vin.text())
            dt_set = float(self.psfb_dt.text()) * 1e-9
            
            # Effective Inductance (Series)
            l_eff = lr + llk
            if l_eff <= 0: raise ValueError
            
            # Equivalent Capacitance of the leg midpoint (2 * Coss)
            c_eq = 2 * coss
            
            # Energy required to charge/discharge C_eq
            e_cap = 0.5 * c_eq * (vin ** 2)
            
            # Inductive Energy E_ind = 0.5 * L_eff * I^2
            # Condition: E_ind > E_cap
            i_min = math.sqrt((c_eq * vin**2) / l_eff)
            
            # Deadtime requirement at this critical current
            t_req = (c_eq * vin) / i_min
            
            self.psfb_res_imin.setText(f"{i_min:.2f} A")
            self.psfb_res_ecap.setText(f"{e_cap*1e6:.2f} uJ")
            self.psfb_res_tmin.setText(f"{t_req*1e9:.0f} ns")
            
            if dt_set > t_req:
                self.psfb_status.setText(f"设定死区 ({dt_set*1e9:.0f}ns) 充足 ( > {t_req*1e9:.0f}ns )")
                self.psfb_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.psfb_status.setText(f"设定死区不足！建议 > {t_req*1e9:.0f}ns")
                self.psfb_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("详细参数填写指南 & 原理")
        dialog.resize(900, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 修复：使用 raw string 防止转义字符问题
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 8px; }
            .box { background-color: #fffde7; padding: 10px; border-left: 4px solid #f1c40f; margin: 10px 0; }
        </style>
        
        <h1>参数填写与设计指南</h1>

        <h2>1. LLC 谐振变换器 - 正向设计 (Design)</h2>
        <div class="box">
            <b>设计逻辑：</b> 设定目标 K 和 Q，正向合成 Lr, Cr, Lm。
        </div>
        <ul>
            <li><b>步骤 1 (匝比 n):</b> 通常设定在 Vin_nom 时谐振腔工作在谐振点 (Gain=1)。即 $n = V_{in\_nom} / V_{out}$。</li>
            <li><b>步骤 2 (Rac):</b> 等效交流阻抗。 $R_{ac} = \frac{8 n^2}{\pi^2} R_{load}$。</li>
            <li><b>步骤 3 (K 值):</b> 电感比 $K = L_m / L_r$。
                <ul>
                    <li>K 越小，增益能力越强，频率变化范围越窄，但励磁电流大，损耗大。推荐 3~5。</li>
                    <li>K 越大，效率高，但需更宽的频率范围来稳压。推荐 5~7。</li>
                </ul>
            </li>
            <li><b>步骤 4 (Q 值):</b> 品质因数 $Q = \sqrt{L_r/C_r} / R_{ac}$。
                <ul>
                    <li>Q 越大，波形越正弦，但在轻载或输入低压时增益可能不足。满载设计推荐 0.3~0.5。</li>
                </ul>
            </li>
        </ul>
        
        <hr>

        <h2>2. LLC 谐振变换器 - 仿真验证 (Analysis)</h2>
        <div class="box">
            <b>核心原理：</b> 利用 FHA (基波近似法) 分析增益曲线。
        </div>
        
        <h3>参数怎么填？</h3>
        <ul>
            <li><b>Lr [uH] (谐振电感):</b> 串联谐振回路中的电感。通常设计时取 leakage = Lr。</li>
            <li><b>Cr [nF] (谐振电容):</b> 与 Lr 串联的电容。决定了第一谐振频率 fr。</li>
            <li><b>Lm [uH] (励磁电感):</b> 变压器原边的励磁电感。Lm 越小，励磁电流越大，ZVS 越容易，但关断损耗增加。</li>
        </ul>

        <h3>关于 ZVS 校核:</h3>
        <p><b>原理：</b>死区时间内，励磁电感 Lm 中的电流必须足够大，才能抽干上下管结电容 ($2 \cdot C_{oss}$) 的电荷，使电压降至 0 实现软开通。</p>
        <p><b>判据：</b> $I_{m\_pk} > \frac{2 \cdot V_{in} \cdot C_{oss}}{T_{dead}}$</p>
        
        <hr>
        
        <h2>3. 移相全桥 (PSFB) ZVS 分析</h2>
        <div class="box">
            <b>滞后臂 (Lagging Leg)：</b> ZVS 极难实现，必须满足 $E_{ind} > E_{cap}$。
        </div>
        <p>本工具估算特定死区下，维持 ZVS 所需的最小原边电流 $I_{min}$。如果实际负载电流小于此值，滞后臂将进入硬开关。</p>

        <hr>
        
        <h2>4. Boost PFC 电感设计</h2>
        <p><b>CCM 模式 (连续导通模式):</b> 适用于中大功率设计。基于电感电流纹波率 (通常取 20%~40%)，在最低输入交流电压峰值处计算最小电感量 $L_{min}$。</p>
        <p><b>CrM 模式 (临界/边界导通模式):</b> 适用于中小功率 (如 <300W) 或者是交错并联 PFC。其电感电流在每个周期都降为零，因此纹波电流峰峰值等于两倍平均输入电流 (Ripple = 200%)。开关频率在电网半周期内动态变化，最低开关频率 $f_{min}$ 发生在交流输入电压峰值处。本工具根据设定的最低开关频率计算所需的电感值 $L$ 以及对应的最大导通时间 $t_{on}$ 和最高工作频率 $f_{max}$ (发生于零交叉点)。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    window = AdvancedTopologiesWindow()
    window.show()
    sys.exit(app.exec_())