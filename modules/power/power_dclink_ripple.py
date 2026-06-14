from modules.base_module import BaseModule
# power_dclink_ripple.py
import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QTabWidget, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

class DcLinkRippleWindow(BaseModule):
    category = "1. 磁性元件与电源拓扑 (Magnetics & Topology)"
    display_name = "母线与交错分析"
    description = "DC-Link纹波 / 交错抵消 / 逆变应力"
    window_id = "power_dclink"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('直流母线电容高级计算 (DC-Link Ripple)')
        self.setGeometry(350, 350, 950, 650)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部栏
        top_bar = QHBoxLayout()
        header_lbl = QLabel("交错并联 (Interleaved) 与 三相逆变 (Inverter) 母线电容纹波应力分析。")
        header_lbl.setStyleSheet("color: #7f8c8d; font-style: italic; font-weight: bold;")
        top_bar.addWidget(header_lbl)
        
        top_bar.addStretch()
        
        self.help_btn = QPushButton("纹波抵消与逆变应力原理")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(200)
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

        self.tab_interleaved = QWidget()
        self.tab_inverter = QWidget()

        self.init_interleaved_ui(self.tab_interleaved)
        self.init_inverter_ui(self.tab_inverter)

        self.tabs.addTab(self.tab_interleaved, "1. N相交错并联纹波抵消 (Interleaved DC-DC)")
        self.tabs.addTab(self.tab_inverter, "2. 三相逆变器母线应力 (3-Phase Inverter)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 交错并联纹波抵消
    # ==============================================================================
    def init_interleaved_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("<b>适用场景:</b> 多相 Buck (如 CPU Vcore)、多相 Boost (大功率 PFC)、交错推挽等。<br>"
                      "利用 N 相相差 360°/N 发波的特性，输入/输出纹波电流大量抵消，大幅减小电容体积。")
        info.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info)
        
        grp_in = QGroupBox("输入条件 (DC-DC Converter)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.intl_n = QLineEdit("2"); grid.addWidget(QLabel("交错相数 N:"), 0, 0); grid.addWidget(self.intl_n, 0, 1)
        self.intl_d = QLineEdit("0.45"); grid.addWidget(QLabel("单相占空比 D [0~1]:"), 0, 2); grid.addWidget(self.intl_d, 0, 3)
        self.intl_iout = QLineEdit("100"); grid.addWidget(QLabel("总输出电流 I_out_total [A]:"), 1, 0); grid.addWidget(self.intl_iout, 1, 1)
        self.intl_ripple = QLineEdit("20"); grid.addWidget(QLabel("单相电感纹波率 [%]:"), 1, 2); grid.addWidget(self.intl_ripple, 1, 3)
        self.intl_ripple.setToolTip("单相电感电流纹波峰峰值占单相直流电流的百分比")
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算抵消系数 (K_ripple) 与 实际电容电流")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_interleaved)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("纹波计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_intl_k = QLineEdit()
        self.res_intl_rms_single = QLineEdit()
        self.res_intl_rms_total = QLineEdit()
        
        r_grid.addWidget(QLabel("纹波抵消系数 K_ripple:"), 0, 0); r_grid.addWidget(self.res_intl_k, 0, 1)
        r_grid.addWidget(QLabel("(K = 0 表示完全抵消，例如双相 D=0.5)"), 0, 2)
        
        r_grid.addWidget(QLabel("未交错时的总应力 (Σ相):"), 1, 0); r_grid.addWidget(self.res_intl_rms_single, 1, 1)
        r_grid.addWidget(QLabel("若采用单相设计所需的吸收电流"), 1, 2)
        
        r_grid.addWidget(QLabel("交错后电容真实有效电流 (I_c_rms):"), 2, 0); r_grid.addWidget(self.res_intl_rms_total, 2, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.res_intl_k, self.res_intl_rms_single, self.res_intl_rms_total]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        l_form = QLabel()
        # simplified K formula placeholder
        l_form.setPixmap(render_formula(r'K_{ripple} = \frac{\Delta I_c}{\Delta I_{L1}} \approx \text{Complex Function of } N, D'))
        l_form.setAlignment(Qt.AlignCenter)
        layout.addWidget(l_form)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_interleaved(self):
        try:
            n = int(self.intl_n.text())
            d = float(self.intl_d.text())
            i_total = float(self.intl_iout.text())
            ripple_pct = float(self.intl_ripple.text()) / 100.0
            
            if n <= 0 or d <= 0 or d >= 1 or i_total <= 0: raise ValueError
            
            # Find floor index m
            m = math.floor(n * d)
            
            # Exact Cancellation Factor K_ripple formula for output capacitor of interleaved multiphase Buck:
            # K = V_out_ripple_interleaved / V_out_ripple_single (which is prop to I_ripple_pp ratio)
            # A well-known normalized peak-to-peak ripple cancellation ratio is:
            # K_pp = (N/D(1-D)) * ( (m+1)/N - d ) * ( d - m/N )
            
            k_pp = (n / (d * (1 - d))) * ((m + 1) / n - d) * (d - m / n)
            
            # RMS current in input capacitor of N-phase buck is different!
            # Let's provide both or clarify. The user asked for "DC-Link capacitor", 
            # In a buck, the input capacitor is the DC-link. In a boost, the output cap is the DC-link.
            # Let's calculate Input RMS for Multiphase Buck:
            # I_in_rms = I_out * sqrt( D * (1 - m/N) - ... ) --> Exact analytical form is complex.
            # We can use a simplified effective duty cycle approach or exact formula:
            # For N phases, D_eff = N*d - m.
            # I_in_rms = (I_total/N) * sqrt( N * D_eff * (1 - D_eff) )  [assuming ripple is small]
            # Let's use this standard approximation for Input RMS in Buck:
            d_eff = n * d - m
            i_phase = i_total / n
            i_in_rms_ideal = i_phase * math.sqrt(n * d_eff * (1 - d_eff))
            
            # If it was a single phase handling i_total with duty d:
            i_in_rms_single = i_total * math.sqrt(d * (1 - d))
            
            self.res_intl_k.setText(f"{k_pp:.4f} (基于峰峰值 K_pp)")
            self.res_intl_rms_single.setText(f"{i_in_rms_single:.2f} A (纯方波近似)")
            self.res_intl_rms_total.setText(f"{i_in_rms_ideal:.2f} A (纯方波近似)")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入参数无效！")

    # ==============================================================================
    # Tab 2: 三相逆变器母线应力
    # ==============================================================================
    def init_inverter_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("<b>适用场景:</b> 伺服驱动器、车载 IGBT/SiC 电机控制器 (MCU)、光伏并网三相逆变。<br>"
                      "利用空间矢量 (SVPWM) 或 SPWM，解析计算支撑母线需要的薄膜/电解电容有效流。")
        info.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info)
        
        grp_in = QGroupBox("输入条件 (3-Phase Inverter)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.inv_iout = QLineEdit("100"); grid.addWidget(QLabel("输出线电流有效值 I_out_rms [A]:"), 0, 0); grid.addWidget(self.inv_iout, 0, 1)
        self.inv_vdc = QLineEdit("600"); grid.addWidget(QLabel("母线电压 V_dc [V]:"), 0, 2); grid.addWidget(self.inv_vdc, 0, 3)
        self.inv_m = QLineEdit("0.8"); grid.addWidget(QLabel("调制系数 M [0~1.15]:"), 1, 0); grid.addWidget(self.inv_m, 1, 1)
        self.inv_m.setToolTip("M = 2 * V_out_peak / V_dc. SVPWM 最大线性调制区可达 1.15。")
        self.inv_pf = QLineEdit("0.85"); grid.addWidget(QLabel("负载功率因数 cos(φ):"), 1, 2); grid.addWidget(self.inv_pf, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算 DC-Link 电容电流")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_inverter)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("母线侧电流结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_inv_i_dc_avg = QLineEdit()
        self.res_inv_i_cap_rms = QLineEdit()
        
        r_grid.addWidget(QLabel("母线直流电流平均值 I_dc_avg [A]:"), 0, 0); r_grid.addWidget(self.res_inv_i_dc_avg, 0, 1)
        r_grid.addWidget(QLabel("提供系统有功功率"), 0, 2)
        
        r_grid.addWidget(QLabel("DC-Link 吸收电流有效值 I_c_rms [A]:"), 1, 0); r_grid.addWidget(self.res_inv_i_cap_rms, 1, 1)
        r_grid.addWidget(QLabel("用于电容选型和寿命热设计"), 1, 2)
        
        style = "background-color: #fdf2e9; font-weight: bold; color: #d35400; font-size: 14px;"
        for w in [self.res_inv_i_dc_avg, self.res_inv_i_cap_rms]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        l_form = QLabel()
        l_form.setPixmap(render_formula(r'I_{c(rms)} = I_{out(rms)} \sqrt{2 M \left[\frac{\sqrt{3}}{4\pi} + \cos^2\varphi \left(\frac{\sqrt{3}}{\pi} - \frac{9}{16} M \right) \right]}'))
        l_form.setAlignment(Qt.AlignCenter)
        layout.addWidget(l_form)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_inverter(self):
        try:
            i_out_rms = float(self.inv_iout.text())
            m = float(self.inv_m.text())
            pf = float(self.inv_pf.text())
            
            if i_out_rms <= 0 or m <= 0 or pf < -1 or pf > 1: raise ValueError
            
            # Kolar analytical formula for SPWM DC-link capacitor RMS current
            # I_c_rms = I_out_rms * sqrt( 2*M*(sqrt(3)/(4*pi) + cos_phi^2 * (sqrt(3)/pi - (9/16)*M)) )
            # valid for sinusoidal PWM. For SVPWM, the formula is slightly different but very close.
            
            term1 = math.sqrt(3) / (4 * math.pi)
            term2 = (pf ** 2) * (math.sqrt(3) / math.pi - (9.0 / 16.0) * m)
            
            inside_sqrt = 2 * m * (term1 + term2)
            if inside_sqrt < 0:
                i_c_rms = 0
            else:
                i_c_rms = i_out_rms * math.sqrt(inside_sqrt)
                
            # Power balance for average DC current
            # P_in = P_out => V_dc * I_dc_avg = 3 * V_out_phase_rms * I_out_rms * pf
            # V_out_phase_peak = M * V_dc / 2 => V_out_phase_rms = M * V_dc / (2*sqrt(2))
            # I_dc_avg = 3 * (M / 2 / sqrt(2)) * I_out_rms * pf (approx SPWM relation)
            
            i_dc_avg = 3 * (m / (2 * math.sqrt(2))) * i_out_rms * pf
            
            self.res_inv_i_dc_avg.setText(f"{i_dc_avg:.2f}")
            self.res_inv_i_cap_rms.setText(f"{i_c_rms:.2f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入参数无效，请检查数值。")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("DC-Link 母线电容设计指南")
        dialog.resize(750, 500)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
        </style>
        
        <h2>1. 交错并联抵消效应 (Interleaved Cancellation)</h2>
        <div class="box">
            <b>核心原理：</b> N相变换器，相角错开 $360°/N$。由于各个开关管的脉冲电流在母线上叠加，其基波甚至次谐波会发生向量相互抵消。<br>
            <b>最佳点：</b> 当占空比 $D = m/N$ 时 ($m$ 为整数)，输入电流变成完美的平滑直流（忽略电感纹波），理论纹波电流归零！
        </div>

        <h2>2. 三相逆变器母线电容应力</h2>
        <p>三相全桥逆变器不断从母线切走宽窄不一的方波电流，给负载供电。这些高频脉冲电流的大部分无功分量和高频分量，只能由距离最近的薄膜电容（DC-Link）提供缓冲。</p>
        
        <h3>最恶劣工况 (Worst Case Analysis)：</h3>
        <ul>
            <li><b>功率因数 $\cos\phi \approx 1$ 时：</b> 虽然是纯有功，但调制深度 $M$ 较高时（如 M=0.6~0.8），电流被斩切产生的 RMS 极大。通常在 $M=0.61$ 左右达到最大。此时 RMS 约等于 $0.5 \sim 0.6$ 倍的线电流。</li>
            <li><b>功率因数 $\cos\phi \approx 0$ 时：</b> （感性负载堵转）有功功率为0，电机的无功电流全靠薄膜电容和二极管倒灌回来。此时 RMS 极高！</li>
        </ul>
        <p>结论：薄膜电容（或者电解电容）选型前，必须用此公式核算最大相电流和不同调制比下，电容自身的发热（$P_{loss} = I_{rms}^2 \times ESR$）是否超标导致寿命缩减或爆炸。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()
