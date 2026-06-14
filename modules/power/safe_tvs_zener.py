from modules.base_module import BaseModule
# safe_tvs_zener.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QTabWidget, QComboBox, QDialog, QTextBrowser, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula  # 使用工具箱统一的公式渲染器

class TvsZenerWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "TVS / Zener 选型"
    description = "稳压电阻设计 / TVS 浪涌选型"
    window_id = "safe_tvs"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('TVS & 稳压管 (Zener) 选型计算器')
        self.setGeometry(350, 350, 950, 750)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("选型原理与降额指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(220)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_zener = QWidget()
        self.tab_tvs = QWidget()

        self.init_zener_ui(self.tab_zener)
        self.init_tvs_ui(self.tab_tvs)

        self.tabs.addTab(self.tab_zener, "Zener 稳压电阻设计 (LDO前级/钳位)")
        self.tabs.addTab(self.tab_tvs, "TVS 浪涌选型 (8/20μs Surge)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: Zener 稳压电阻设计
    # ==============================================================================
    def init_zener_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 工况参数
        grp_in = QGroupBox("1. 电路工况输入 (Input Conditions)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.zn_vin_min = QLineEdit("10"); grid.addWidget(QLabel("最小输入电压 Vin_min [V]:"), 0, 0); grid.addWidget(self.zn_vin_min, 0, 1)
        self.zn_vin_max = QLineEdit("24"); grid.addWidget(QLabel("最大输入电压 Vin_max [V]:"), 0, 2); grid.addWidget(self.zn_vin_max, 0, 3)
        
        self.zn_vz = QLineEdit("5.1"); self.zn_vz.setToolTip("稳压管标称稳压值")
        grid.addWidget(QLabel("稳压电压 Vz [V]:"), 1, 0); grid.addWidget(self.zn_vz, 1, 1)
        
        self.zn_iz_min = QLineEdit("5"); self.zn_iz_min.setToolTip("维持稳压所需的最小反向电流，通常取 1mA~5mA")
        grid.addWidget(QLabel("最小偏置电流 Iz_min [mA]:"), 1, 2); grid.addWidget(self.zn_iz_min, 1, 3)
        
        self.zn_iload_min = QLineEdit("0"); grid.addWidget(QLabel("最小负载电流 Iload_min [mA]:"), 2, 0); grid.addWidget(self.zn_iload_min, 2, 1)
        self.zn_iload_max = QLineEdit("50"); grid.addWidget(QLabel("最大负载电流 Iload_max [mA]:"), 2, 2); grid.addWidget(self.zn_iload_max, 2, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. 选定电阻
        grp_sel = QGroupBox("2. 电阻选型 (Resistor Selection)")
        h_sel = QHBoxLayout()
        self.zn_r_sel = QLineEdit("100"); self.zn_r_sel.setPlaceholderText("输入电阻值")
        h_sel.addWidget(QLabel("选定限流电阻 R [Ω]:")); h_sel.addWidget(self.zn_r_sel)
        
        btn_calc = QPushButton("计算功率与裕量")
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.setFixedHeight(35)
        btn_calc.clicked.connect(self.calc_zener)
        h_sel.addWidget(btn_calc)
        
        grp_sel.setLayout(h_sel)
        layout.addWidget(grp_sel)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估结果 (Worst Case Analysis)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_r_range = QLineEdit()
        self.res_pz_max = QLineEdit()
        self.res_pr_max = QLineEdit()
        self.res_status = QLineEdit()
        
        # Row 0: R Range
        r_grid.addWidget(QLabel("理论电阻上限 R_max:"), 0, 0); r_grid.addWidget(self.res_r_range, 0, 1)
        l_r = QLabel(); l_r.setPixmap(render_formula(r'R \leq \frac{V_{in\_min} - V_z}{I_{load\_max} + I_{z\_min}}'))
        r_grid.addWidget(l_r, 0, 2)
        
        # Row 1: Zener Power
        r_grid.addWidget(QLabel("稳压管最大功耗 Pz_max:"), 1, 0); r_grid.addWidget(self.res_pz_max, 1, 1)
        l_pz = QLabel(); l_pz.setPixmap(render_formula(r'P_{z\_max} \approx V_z \cdot (\frac{V_{in\_max}-V_z}{R} - I_{load\_min})'))
        r_grid.addWidget(l_pz, 1, 2)
        
        # Row 2: Resistor Power
        r_grid.addWidget(QLabel("电阻最大功耗 Pr_max:"), 2, 0); r_grid.addWidget(self.res_pr_max, 2, 1)
        l_pr = QLabel(); l_pr.setPixmap(render_formula(r'P_{R\_max} = \frac{(V_{in\_max}-V_z)^2}{R}'))
        r_grid.addWidget(l_pr, 2, 2)
        
        # Row 3: Status
        r_grid.addWidget(QLabel("设计状态检查:"), 3, 0); r_grid.addWidget(self.res_status, 3, 1)
        
        # Style
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400;"
        self.res_r_range.setReadOnly(True); self.res_r_range.setStyleSheet(style_res)
        self.res_pz_max.setReadOnly(True); self.res_pz_max.setStyleSheet(style_warn)
        self.res_pr_max.setReadOnly(True); self.res_pr_max.setStyleSheet(style_warn)
        self.res_status.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_zener(self):
        try:
            # Inputs
            vin_min = float(self.zn_vin_min.text())
            vin_max = float(self.zn_vin_max.text())
            vz = float(self.zn_vz.text())
            iz_min = float(self.zn_iz_min.text()) / 1000.0
            iload_min = float(self.zn_iload_min.text()) / 1000.0
            iload_max = float(self.zn_iload_max.text()) / 1000.0
            r_sel = float(self.zn_r_sel.text())
            
            if r_sel <= 0: raise ValueError
            if vin_min < vz: 
                QMessageBox.warning(self, "错误", "最小输入电压必须大于稳压值 Vz")
                return

            # 1. R_max Check (Ensure regulation at Vin_min & Full Load)
            # Ir = (Vin_min - Vz) / R
            # Need Ir >= Iload_max + Iz_min
            r_limit = (vin_min - vz) / (iload_max + iz_min)
            self.res_r_range.setText(f"< {r_limit:.1f} Ω")
            
            # 2. Power Dissipation @ Vin_max
            # Resistor Power (Worst case: Vin_max, Vz fixed)
            pr_max = ((vin_max - vz) ** 2) / r_sel
            
            # Zener Current (Worst case: Vin_max, Min Load)
            # Ir_max = (Vin_max - Vz) / R
            # Iz_max = Ir_max - Iload_min
            ir_max = (vin_max - vz) / r_sel
            iz_max = ir_max - iload_min
            if iz_max < 0: iz_max = 0 # Should not happen if design is valid
            pz_max = vz * iz_max
            
            self.res_pr_max.setText(f"{pr_max:.3f} W")
            self.res_pz_max.setText(f"{pz_max:.3f} W")
            
            # Status
            msgs = []
            is_ok = True
            if r_sel > r_limit:
                msgs.append("R过大: 低压满载时无法稳压")
                is_ok = False
            
            # Warn if power is high (e.g. standard 0.5W zener)
            if pz_max > 0.4:
                msgs.append(f"Pz ({pz_max:.2f}W) 较高! 注意散热")
                
            if is_ok:
                self.res_status.setText("设计合理" if not msgs else f"可用但注意: {'; '.join(msgs)}")
                self.res_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.res_status.setText(f"失败: {'; '.join(msgs)}")
                self.res_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 2: TVS 浪涌选型
    # ==============================================================================
    def init_tvs_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 浪涌源参数
        grp_src = QGroupBox("1. 浪涌源参数 (Surge Source - IEC 61000-4-5)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.tvs_v_surge = QLineEdit("2000"); self.tvs_v_surge.setToolTip("发生器设定电压 (Open Circuit Voltage)")
        grid.addWidget(QLabel("浪涌电压 V_surge [V]:"), 0, 0); grid.addWidget(self.tvs_v_surge, 0, 1)
        
        self.tvs_r_src = QLineEdit("2"); self.tvs_r_src.setToolTip("发生器内阻。\n线-线通常 2Ω，线-地通常 12Ω。")
        grid.addWidget(QLabel("发生器内阻 R_source [Ω]:"), 0, 2); grid.addWidget(self.tvs_r_src, 0, 3)
        
        grp_src.setLayout(grid)
        layout.addWidget(grp_src)
        
        # 2. TVS 参数
        grp_dev = QGroupBox("2. TVS 器件参数 (Datasheet)")
        grid_dev = QGridLayout()
        grid_dev.setVerticalSpacing(12)
        
        self.tvs_vrwm = QLineEdit("24"); grid_dev.addWidget(QLabel("反向截止 VRWM [V]:"), 0, 0); grid_dev.addWidget(self.tvs_vrwm, 0, 1)
        self.tvs_vbr = QLineEdit("26.7"); grid_dev.addWidget(QLabel("击穿电压 Vbr (Min) [V]:"), 0, 2); grid_dev.addWidget(self.tvs_vbr, 0, 3)
        
        self.tvs_vc_spec = QLineEdit("38.9"); self.tvs_vc_spec.setToolTip("规格书中的最大钳位电压 Vc @ Ipp")
        grid_dev.addWidget(QLabel("最大钳位 Vc_max [V]:"), 1, 0); grid_dev.addWidget(self.tvs_vc_spec, 1, 1)
        
        self.tvs_ipp_spec = QLineEdit("15.4"); self.tvs_ipp_spec.setToolTip("规格书中的最大峰值脉冲电流 Ipp (10/1000us 或 8/20us)")
        grid_dev.addWidget(QLabel("测试电流 Ipp_test [A]:"), 1, 2); grid_dev.addWidget(self.tvs_ipp_spec, 1, 3)
        
        self.tvs_pppm = QLineEdit("600"); self.tvs_pppm.setToolTip("峰值脉冲功率 (Peak Pulse Power)")
        grid_dev.addWidget(QLabel("额定功率 P_ppm [W]:"), 2, 0); grid_dev.addWidget(self.tvs_pppm, 2, 1)
        
        grp_dev.setLayout(grid_dev)
        layout.addWidget(grp_dev)
        
        # 按钮
        btn = QPushButton("计算实际钳位与应力")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_tvs)
        layout.addWidget(btn)
        
        # 3. 结果
        grp_res = QGroupBox("3. 实际应力评估 (Actual Stress)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.res_ipp_act = QLineEdit()
        self.res_vc_act = QLineEdit()
        self.res_ppp_act = QLineEdit()
        self.res_tvs_status = QLineEdit()
        
        # Ipp Actual
        r_grid.addWidget(QLabel("实际流过电流 Ipp_act:"), 0, 0); r_grid.addWidget(self.res_ipp_act, 0, 1)
        l_i = QLabel(); l_i.setPixmap(render_formula(r'I_{pp} \approx \frac{V_{surge} - V_{cl}}{R_{source}}'))
        r_grid.addWidget(l_i, 0, 2)
        
        # Vc Actual
        r_grid.addWidget(QLabel("估算钳位电压 Vc_act:"), 1, 0); r_grid.addWidget(self.res_vc_act, 1, 1)
        r_grid.addWidget(QLabel("(线性插值估算)"), 1, 2)
        
        # Power Actual
        r_grid.addWidget(QLabel("实际峰值功率 P_act:"), 2, 0); r_grid.addWidget(self.res_ppp_act, 2, 1)
        l_p = QLabel(); l_p.setPixmap(render_formula(r'P_{pk} = V_{cl\_act} \cdot I_{pp\_act}'))
        r_grid.addWidget(l_p, 2, 2)
        
        # Status
        r_grid.addWidget(QLabel("TVS 状态评估:"), 3, 0); r_grid.addWidget(self.res_tvs_status, 3, 1)
        
        style = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad;"
        for w in [self.res_ipp_act, self.res_vc_act, self.res_ppp_act]:
            w.setReadOnly(True); w.setStyleSheet(style)
        self.res_tvs_status.setReadOnly(True)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        tip = QLabel("注意：Datasheet 中的 P_ppm 通常是基于 10/1000μs 波形的。如果浪涌是 8/20μs，TVS 的耐受功率通常会更高（约 4~5 倍，需查降额曲线）。")
        tip.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(tip)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_tvs(self):
        try:
            v_surge = float(self.tvs_v_surge.text())
            r_src = float(self.tvs_r_src.text())
            
            vc_spec = float(self.tvs_vc_spec.text())
            ipp_spec = float(self.tvs_ipp_spec.text()) # @ Vc_spec
            vbr = float(self.tvs_vbr.text())
            pppm_rated = float(self.tvs_pppm.text())
            
            if r_src <= 0: raise ValueError
            
            # 迭代计算 Ipp 和 Vc (简单的一阶近似)
            # Ipp = (V_surge - Vc) / R_src
            # 假设 Vc 与 Ipp 成线性关系 (斜率电阻 R_dyn)
            # R_dyn approx = (Vc_spec - Vbr) / Ipp_spec
            # Vc = Vbr + Ipp * R_dyn
            # Combine: Ipp = (V_surge - (Vbr + Ipp*R_dyn)) / R_src
            # Ipp * (R_src + R_dyn) = V_surge - Vbr
            # Ipp = (V_surge - Vbr) / (R_src + R_dyn)
            
            if ipp_spec > 0:
                r_dyn = (vc_spec - vbr) / ipp_spec
            else:
                r_dyn = 0.5 # Default fallback
                
            if r_dyn < 0: r_dyn = 0.1 # Vc must > Vbr
            
            if v_surge < vbr:
                ipp_act = 0.0
                vc_act = v_surge
            else:
                ipp_act = (v_surge - vbr) / (r_src + r_dyn)
                vc_act = vbr + ipp_act * r_dyn
            
            # Power
            p_act = vc_act * ipp_act
            
            self.res_ipp_act.setText(f"{ipp_act:.2f} A")
            self.res_vc_act.setText(f"{vc_act:.2f} V")
            self.res_ppp_act.setText(f"{p_act:.2f} W")
            
            # Assessment
            # Check 1: Vc vs 后级耐压? (用户未输入，仅提示)
            # Check 2: Power vs Rated (Simple check, ignoring 8/20 vs 10/1000 difference logic for now, just direct compare or hint)
            
            msgs = []
            if p_act > pppm_rated * 5: # Assuming 8/20us handling is ~4-5x better than 10/1000us Pppm
                msgs.append("功率严重超标")
            elif p_act > pppm_rated:
                msgs.append("功率较高 (注意波形折算)")
                
            # Check Current Limit if specific Ipp spec provided for 8/20us? 
            # Usually Datasheet gives Ipp @ 8/20us for ESD/Surge diodes, or 10/1000us for classic TVS.
            # Assuming user inputs consistent data.
            
            if not msgs:
                self.res_tvs_status.setText("参数在合理范围内 (Safe)")
                self.res_tvs_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.res_tvs_status.setText(f"警告: {'; '.join(msgs)}")
                self.res_tvs_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("TVS 与 Zener 设计指南")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 使用 r""" 原生字符串，避免 \_ 等转义警告
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
        </style>
        
        <h1>设计与选型指南</h1>
        
        <h2>1. 稳压管 (Zener Diode) 选型陷阱</h2>
        <div class="box">
            <b>最大风险点：</b> 高压输入 + 轻载/空载。<br>
            当负载断开时，所有电流都会流过稳压管。此时稳压管的功耗最大。
        </div>
        <ul>
            <li><b>计算核心：</b> 必须同时满足“低压满载能稳住”和“高压空载不烧管”。</li>
            <li><b>功率选型：</b> 计算出的 $P_{z\_max}$ 是稳态功耗，稳压管必须降额使用 (建议 < 50% 额定功率)，因为稳压管发热严重会导致电压漂移。</li>
        </ul>

        <h2>2. TVS 瞬态抑制二极管</h2>
        <p>用于吸收雷击浪涌 (Surge) 或静电 (ESD)。</p>
        
        <h3>关键参数：</h3>
        <ul>
            <li><b>Vrwm (Reverse Working Voltage):</b> 必须大于电路的正常工作电压，否则 TVS 会漏电或长期导通烧毁。</li>
            <li><b>Vc (Clamping Voltage):</b> 钳位电压。<b>这是保护后级电路的关键指标。</b>必须小于后级芯片的绝对最大耐压。</li>
            <li><b>Pppm (Peak Pulse Power):</b> 峰值脉冲功率。注意：600W 的 TVS (如 SMBJ系列) 指的是 10/1000μs 波形。对于 8/20μs 浪涌，其耐受功率通常可达几千瓦。</li>
        </ul>

        <h3>计算逻辑：</h3>
        <p>浪涌源通常被模拟为一个带内阻的电压源 (IEC 61000-4-5)。</p>
        <p><code>I_pp = (V_surge - V_c) / R_source</code></p>
        <p>设计时，应确保计算出的 $I_{pp}$ 小于 TVS 规格书中的最大脉冲电流。如果 $R_{source}$ 很小 (如电源端口)，电流会非常大，此时可能需要前级串联压敏电阻 (MOV) 或气体放电管 (GDT) 来分担能量。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()