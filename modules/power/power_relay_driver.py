from modules.base_module import BaseModule
# power_relay_driver.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QTabWidget, QComboBox, QDialog, QTextBrowser)
from PyQt5.QtCore import Qt, QBuffer, QByteArray, QIODevice
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

class RelayDriverWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "继电器驱动"
    description = "RC节电器 / PWM保持"
    window_id = "power_relay"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('继电器/接触器 驱动优化工具 (Relay Economizer)')
        self.setGeometry(350, 350, 950, 700)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- 顶部栏：教程按钮 ---
        top_bar = QHBoxLayout()
        header = QLabel("用于设计继电器/接触器的节能驱动电路，降低线圈发热与功耗。")
        header.setStyleSheet("font-style: italic; color: #555;")
        top_bar.addWidget(header)
        
        top_bar.addStretch()
        
        self.help_btn = QPushButton("设计原理：RC曲线与PWM纹波")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
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

        self.tab_rc = QWidget()
        self.tab_pwm = QWidget()

        self.init_rc_ui(self.tab_rc)
        self.init_pwm_ui(self.tab_pwm)

        self.tabs.addTab(self.tab_rc, "RC 节电器 (R-C Economizer)")
        self.tabs.addTab(self.tab_pwm, "PWM 保持 (PWM Holding)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: RC Economizer (Kickstart)
    # ==============================================================================
    def init_rc_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 原理图示说明
        desc_lbl = QLabel("电路拓扑：电源 Vcc -> (并联 R_eco // C_start) -> 线圈 R_coil -> GND\n"
                          "原理：电容提供瞬间吸合高压，电阻提供稳态保持低压。")
        desc_lbl.setStyleSheet("color: #2980b9; margin-bottom: 10px;")
        layout.addWidget(desc_lbl)

        # 输入参数
        grp_in = QGroupBox("1. 继电器参数与设计目标")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.rc_vcc = QLineEdit("24"); grid.addWidget(QLabel("驱动电压 Vcc [V]:"), 0, 0); grid.addWidget(self.rc_vcc, 0, 1)
        self.rc_r_coil = QLineEdit("200"); grid.addWidget(QLabel("线圈电阻 R_coil [Ω]:"), 0, 2); grid.addWidget(self.rc_r_coil, 0, 3)
        
        self.rc_v_hold = QLineEdit("12"); self.rc_v_hold.setToolTip("稳态保持电压，通常取额定电压的 50% 左右")
        grid.addWidget(QLabel("目标保持电压 V_hold [V]:"), 1, 0); grid.addWidget(self.rc_v_hold, 1, 1)
        
        self.rc_v_pull_min = QLineEdit("17"); self.rc_v_pull_min.setToolTip("线圈两端电压必须高于此值才能保证吸合。\n查阅 Datasheet 'Must Operate Voltage'，通常为 70%-80% Unom。")
        grid.addWidget(QLabel("最小吸合电压 V_pull_min [V]:"), 1, 2); grid.addWidget(self.rc_v_pull_min, 1, 3)
        
        self.rc_t_pull = QLineEdit("50"); self.rc_t_pull.setToolTip("需要维持高电压的时间。\n应大于 Datasheet 'Operate Time' (如 15ms)，建议留 2-3 倍裕量。")
        grid.addWidget(QLabel("所需吸合时间 t_pull [ms]:"), 2, 0); grid.addWidget(self.rc_t_pull, 2, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算 R_eco 和 C_start")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_rc)
        layout.addWidget(btn)
        
        # 结果
        grp_res = QGroupBox("2. 推荐元件参数")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_r_eco = QLineEdit()
        self.res_c_start = QLineEdit()
        self.res_p_save = QLineEdit()
        
        r_grid.addWidget(QLabel("串联节电电阻 R_eco:"), 0, 0); r_grid.addWidget(self.res_r_eco, 0, 1)
        l_r = QLabel(); l_r.setPixmap(render_formula(r'R_{eco} = R_{coil} (\frac{V_{cc}}{V_{hold}} - 1)'))
        r_grid.addWidget(l_r, 0, 2)
        
        r_grid.addWidget(QLabel("并联启动电容 C_start:"), 1, 0); r_grid.addWidget(self.res_c_start, 1, 1)
        l_c = QLabel(); l_c.setPixmap(render_formula(r'C = \frac{-t_{pull}}{(R_{coil} // R_{eco}) \ln(\frac{V_{min} - V_{hold}}{V_{cc} - V_{hold}})}'))
        r_grid.addWidget(l_c, 1, 2)
        
        r_grid.addWidget(QLabel("功耗节省比例 (Power Saving):"), 2, 0); r_grid.addWidget(self.res_p_save, 2, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_r_eco, self.res_c_start, self.res_p_save]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 提示
        tips = QLabel("注意：电容 C_start 需选用耐压高于 Vcc 的电解电容。\n"
                      "R_eco 的功率需满足 (Vcc-Vhold)^2 / R_eco。")
        tips.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(tips)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_rc(self):
        try:
            vcc = float(self.rc_vcc.text())
            r_coil = float(self.rc_r_coil.text())
            v_hold = float(self.rc_v_hold.text())
            v_min = float(self.rc_v_pull_min.text())
            t_ms = float(self.rc_t_pull.text())
            
            if v_hold >= vcc or v_min >= vcc:
                QMessageBox.warning(self, "电压错误", "保持电压和最小吸合电压必须小于电源电压 Vcc")
                return
            if v_hold >= v_min:
                QMessageBox.warning(self, "逻辑错误", "保持电压应设计得比最小吸合电压低 (否则不需要电容)")
                return
                
            # 1. Calculate Resistor
            # V_hold = Vcc * R_coil / (R_coil + R_eco)
            r_eco = r_coil * (vcc / v_hold - 1)
            
            # 2. Calculate Capacitor
            # V_coil(t) = V_hold + (Vcc - V_hold) * exp(-t / tau)
            # tau = C * (R_coil || R_eco)
            # We need V_coil(t_pull) >= V_min
            # exp(...) = (V_min - V_hold) / (Vcc - V_hold)
            # -t/tau = ln(...)
            
            ratio = (v_min - v_hold) / (vcc - v_hold)
            if ratio <= 0: ratio = 0.001
            
            r_par = (r_coil * r_eco) / (r_coil + r_eco)
            t_sec = t_ms / 1000.0
            
            tau = -t_sec / math.log(ratio)
            c_farad = tau / r_par
            c_uf = c_farad * 1e6
            
            # Power Saving
            p_orig = vcc**2 / r_coil
            p_new = vcc**2 / (r_coil + r_eco)
            saving = (1 - p_new / p_orig) * 100
            
            # Resistor Power
            p_r_eco = ((vcc - v_hold) ** 2) / r_eco
            
            self.res_r_eco.setText(f"{r_eco:.1f} Ω (P > {p_r_eco:.2f}W)")
            self.res_c_start.setText(f"{c_uf:.1f} uF")
            self.res_p_save.setText(f"{saving:.1f}%")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 2: PWM Holding
    # ==============================================================================
    def init_pwm_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        desc_lbl = QLabel("原理：利用电感的续流特性，使用 PWM 驱动线圈。\n"
                          "通过降低占空比 D，使平均电压降低到保持电压，从而大幅降低功耗。")
        desc_lbl.setStyleSheet("color: #8e44ad; margin-bottom: 10px;")
        layout.addWidget(desc_lbl)
        
        # 输入
        grp_in = QGroupBox("1. PWM 参数设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.pwm_vcc = QLineEdit("24"); grid.addWidget(QLabel("电源电压 Vcc [V]:"), 0, 0); grid.addWidget(self.pwm_vcc, 0, 1)
        self.pwm_r_coil = QLineEdit("200"); grid.addWidget(QLabel("线圈电阻 R_coil [Ω]:"), 0, 2); grid.addWidget(self.pwm_r_coil, 0, 3)
        
        self.pwm_l_coil = QLineEdit("500"); self.pwm_l_coil.setToolTip("线圈电感量。若未知，可根据电流上升时间估算，或填 0 忽略纹波计算。")
        grid.addWidget(QLabel("线圈电感 L_coil [mH]:"), 1, 0); grid.addWidget(self.pwm_l_coil, 1, 1)
        
        self.pwm_freq = QLineEdit("20"); self.pwm_freq.setToolTip("建议 > 20kHz 以避免人耳听到啸叫")
        grid.addWidget(QLabel("PWM 频率 [kHz]:"), 1, 2); grid.addWidget(self.pwm_freq, 1, 3)
        
        self.pwm_v_hold = QLineEdit("12"); self.pwm_v_hold.setToolTip("目标线圈两端平均电压")
        grid.addWidget(QLabel("目标保持电压 [V]:"), 2, 0); grid.addWidget(self.pwm_v_hold, 2, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算 PWM 占空比与纹波")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_pwm)
        layout.addWidget(btn)
        
        # 结果
        grp_res = QGroupBox("2. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_duty = QLineEdit()
        self.res_i_avg = QLineEdit()
        self.res_ripple = QLineEdit()
        self.res_p_coil = QLineEdit()
        
        # Duty
        r_grid.addWidget(QLabel("推荐占空比 (Duty):"), 0, 0); r_grid.addWidget(self.res_duty, 0, 1)
        l_d = QLabel(); l_d.setPixmap(render_formula(r'D = V_{hold} / V_{cc}'))
        r_grid.addWidget(l_d, 0, 2)
        
        # Current
        r_grid.addWidget(QLabel("平均保持电流 (I_avg):"), 1, 0); r_grid.addWidget(self.res_i_avg, 1, 1)
        
        # Power
        r_grid.addWidget(QLabel("线圈保持功耗 (P_hold):"), 2, 0); r_grid.addWidget(self.res_p_coil, 2, 1)
        l_p = QLabel(); l_p.setPixmap(render_formula(r'P \approx D^2 \frac{V_{cc}^2}{R_{coil}}'))
        r_grid.addWidget(l_p, 2, 2)
        
        # Ripple
        r_grid.addWidget(QLabel("电流纹波 (ΔI):"), 3, 0); r_grid.addWidget(self.res_ripple, 3, 1)
        l_rip = QLabel(); l_rip.setPixmap(render_formula(r'\Delta I \approx \frac{V_{cc}(1-D)D}{f \cdot L}'))
        r_grid.addWidget(l_rip, 3, 2)
        
        style = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad;"
        for w in [self.res_duty, self.res_i_avg, self.res_p_coil, self.res_ripple]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_pwm(self):
        try:
            vcc = float(self.pwm_vcc.text())
            r_coil = float(self.pwm_r_coil.text())
            l_mh = float(self.pwm_l_coil.text())
            f_khz = float(self.pwm_freq.text())
            v_hold = float(self.pwm_v_hold.text())
            
            if vcc <= 0 or r_coil <= 0: raise ValueError
            
            # 1. Duty Cycle
            if v_hold > vcc: v_hold = vcc
            duty = v_hold / vcc
            
            # 2. Avg Current
            i_avg = v_hold / r_coil
            
            # 3. Power
            # For PWM driving inductive load with freewheeling, 
            # Coil sees Vcc during D, 0 during (1-D). Avg V = D*Vcc.
            # RMS voltage is sqrt(D)*Vcc.
            # BUT, for magnetic holding force, Average Current matters most.
            # Power loss in coil = I_rms^2 * R.
            # I_rms approx I_avg (if ripple is small).
            # So P approx (D*Vcc/R)^2 * R = D^2 * Vcc^2 / R.
            p_hold = (i_avg ** 2) * r_coil
            
            # 4. Ripple
            # Buck formula: dI = (Vin - Vout) * D / (L * f)
            # Vout = V_hold
            if l_mh > 0 and f_khz > 0:
                l = l_mh * 1e-3
                f = f_khz * 1e3
                d_i = (vcc - v_hold) * duty / (l * f)
                self.res_ripple.setText(f"{d_i*1000:.1f} mA ({d_i/i_avg*100:.1f}%)")
                
                if d_i > i_avg * 2:
                    self.res_ripple.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
                    self.res_ripple.setToolTip("纹波过大！电流可能断续，继电器会释放或异响。请提高频率或电压。")
                else:
                    self.res_ripple.setStyleSheet("background-color: #f4ecf7; font-weight: bold; color: #8e44ad;")
            else:
                self.res_ripple.setText("---")
            
            self.res_duty.setText(f"{duty*100:.1f} %")
            self.res_i_avg.setText(f"{i_avg*1000:.1f} mA")
            self.res_p_coil.setText(f"{p_hold:.3f} W")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def latex_img(self, formula, height=35):
        """Helper to render LaTeX to Base64 Image for HTML"""
        pixmap = render_formula(formula, target_height=height)
        if pixmap.isNull(): return ""
        
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        pixmap.save(buf, "PNG")
        hex_str = ba.toBase64().data().decode()
        return f'<img src="data:image/png;base64,{hex_str}" style="vertical-align: middle;">'

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("继电器驱动设计指南")
        dialog.resize(900, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 使用 f-string 动态嵌入图片
        # 注意: 这里的 r 前缀是针对 Python 字符串转义，LaTeX 字符串内部的反斜杠会被正确处理
        html = f"""
        <style>
            h2 {{ color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }}
            h3 {{ color: #d35400; margin-top: 15px; }}
            li {{ margin-bottom: 8px; }}
            code {{ background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }}
            .box {{ background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }}
        </style>
        
        <h1>继电器驱动优化 (Relay Economizer)</h1>
        
        <h2>1. 为什么要用节电器？</h2>
        <p>继电器在吸合瞬间需要较大的力（大电流），一旦吸合，磁路闭合，维持吸合所需的力（电流）非常小（通常只需额定的 30%~50%）。</p>
        <p>如果一直给额定电压：</p>
        <ul>
            <li>线圈发热严重，温升可能导致绝缘老化。</li>
            <li>浪费电能（特别是电池供电设备）。</li>
        </ul>

        <h2>2. RC 启动电路</h2>
        <p><b>原理：</b> 利用电容两端电压不能突变的特性。</p>
        <ul>
            <li><b>启动瞬间 (t=0)：</b> 电容 <i>C</i> 相当于短路，电源电压 <i>V</i><sub>cc</sub> 全部加在线圈上，提供大电流吸合。</li>
            <li><b>稳态 (t → ∞)：</b> 电容充满电相当于开路，电流流经 <i>R</i><sub>eco</sub> 和 <i>R</i><sub>coil</sub> 分压，线圈电压降至 <i>V</i><sub>hold</sub>。</li>
        </ul>
        <div class="box">
            <b>计算难点：</b> 必须保证电容充电过程中，线圈两端电压在 <i>t</i><sub>pull</sub> 时间内始终高于 <i>V</i><sub>pull_min</sub>。
            <br>
            <b>公式：</b><br>
            {self.latex_img(r'C = \frac{-t_{pull}}{(R_{coil} // R_{eco}) \ln(\frac{V_{min} - V_{hold}}{V_{cc} - V_{hold}})}', 50)}
        </div>

        <h2>3. PWM 保持电路</h2>
        <p><b>原理：</b> 利用电感对电流的积分作用（续流）。</p>
        <ul>
            <li>启动阶段：给 100% 占空比，全压吸合。</li>
            <li>保持阶段：降低占空比 <i>D</i>，使平均电压 {self.latex_img(r'V_{avg} = D \cdot V_{cc} = V_{hold}')}。</li>
            <li><b>注意：</b> 必须配合续流二极管。PWM 频率不能太低，否则电流纹波过大导致继电器发出“滋滋”声或衔铁震动。<br>
            建议频率 <i>f</i> > 20kHz。</li>
        </ul>
        """
        
        text.setHtml(html)
        layout.addWidget(text)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec_()