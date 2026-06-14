from modules.base_module import BaseModule
# emc_calculator_window.py

import math
import matplotlib.pyplot as plt
from io import BytesIO
import numpy as np

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class EmcCalculatorWindow(BaseModule):
    category = "3. 环路控制与滤波 (Control & Filter)"
    display_name = "EMC 计算工具"
    description = "单位换算 / 衰减 / 场强 / 限值"
    window_id = "emc_calc"

    def init_module_ui(self):
        
        # 定义 EMC 标准数据库 (频率单位 MHz, 限值单位 dBuV 或 dBuV/m)
        # 格式: [(freq_start, freq_end, limit_val), ...]
        self.standards_db = {
            "CISPR 32 Class B 传导 (Conducted QP)": {
                'type': 'Conducted',
                'unit': 'dBµV',
                'data': [
                    (0.15, 0.50, "66-56"), # 斜率
                    (0.50, 5.0,  56),
                    (5.0,  30.0, 60)
                ]
            },
            "CISPR 32 Class B 传导 (Conducted AVG)": {
                'type': 'Conducted',
                'unit': 'dBµV',
                'data': [
                    (0.15, 0.50, "56-46"), # 斜率
                    (0.50, 5.0,  46),
                    (5.0,  30.0, 50)
                ]
            },
            "CISPR 32 Class B 辐射 (Radiated 3m QP)": {
                'type': 'Radiated',
                'unit': 'dBµV/m',
                'data': [
                    (30, 230, 40),
                    (230, 1000, 47)
                ]
            },
            "CISPR 32 Class A 辐射 (Radiated 3m QP)": { # Class A 工业
                'type': 'Radiated',
                'unit': 'dBµV/m',
                'data': [
                    (30, 230, 50),
                    (230, 1000, 57)
                ]
            },
            "CISPR 25 Class 3 传导 (Voltage QP)": { # 汽车
                'type': 'Conducted',
                'unit': 'dBµV',
                'data': [
                    (0.15, 0.3, 70), (0.53, 1.8, 56), (5.9, 6.2, 50), (26, 28, 50),
                    (30, 54, 34), (68, 87, 34), (76, 108, 34) # 简化版，截取主要频段
                ]
            },
            "FCC Part 15 Class B 辐射 (Radiated 3m)": {
                'type': 'Radiated',
                'unit': 'dBµV/m',
                'data': [
                    (30, 88, 40),
                    (88, 216, 43.5),
                    (216, 960, 46),
                    (960, 10000, 54)
                ]
            }
        }
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('EMC 综合计算工具 (EMC Pro Max)')
        self.setGeometry(350, 350, 1000, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("EMC 标准与设计指南")
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

        self.tab_conv = QWidget()
        self.tab_att = QWidget()
        self.tab_rad = QWidget() 
        self.tab_limits = QWidget() # New: Limits Lookup
        self.tab_filter_sizing = QWidget() # New: CM/DM Filter Design
        self.tab_fix = QWidget()

        self.init_conv_ui(self.tab_conv)
        self.init_att_ui(self.tab_att)
        self.init_rad_ui(self.tab_rad)
        self.init_limits_ui(self.tab_limits) # Init New
        self.init_filter_sizing_ui(self.tab_filter_sizing) # Init Sizing
        self.init_conducted_fix_ui(self.tab_fix)

        self.tabs.addTab(self.tab_conv, "1. 单位换算 (dBµV/dBm)")
        self.tabs.addTab(self.tab_att, "2. 滤波器衰减 & 谐振")
        self.tabs.addTab(self.tab_rad, "3. 辐射 & 波长")
        self.tabs.addTab(self.tab_limits, "4. 标准限值速查 (Limits)")
        self.tabs.addTab(self.tab_filter_sizing, "5. 共模/差模滤波参数设计")
        self.tabs.addTab(self.tab_fix, "6. 传导EMI整改速算")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: EMC 单位换算 (保留原功能)
    # ==============================================================================
    def init_conv_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_in = QGroupBox("1. 输入参数 (基于 50Ω 系统)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.conv_mode = QComboBox()
        self.conv_mode.addItems(["dBµV (干扰电压分贝)", "mV/V (线性电压)", "dBm (功率分贝)", "dBµA (电流分贝)"])
        self.conv_mode.currentIndexChanged.connect(self.clear_conv_res)
        grid.addWidget(QLabel("已知单位类型:"), 0, 0); grid.addWidget(self.conv_mode, 0, 1)
        
        self.conv_val = QLineEdit("60")
        grid.addWidget(QLabel("输入数值:"), 0, 2); grid.addWidget(self.conv_val, 0, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("一键全单位换算")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_conversion)
        layout.addWidget(btn)
        
        # 结果
        grp_res = QGroupBox("2. 换算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.res_dbuv = QLineEdit(); r_grid.addWidget(QLabel("dBµV (电压):"), 0, 0); r_grid.addWidget(self.res_dbuv, 0, 1)
        self.res_mv = QLineEdit(); r_grid.addWidget(QLabel("mV (电压):"), 1, 0); r_grid.addWidget(self.res_mv, 1, 1)
        self.res_dbm = QLineEdit(); r_grid.addWidget(QLabel("dBm (功率):"), 2, 0); r_grid.addWidget(self.res_dbm, 2, 1)
        self.res_dbua = QLineEdit(); r_grid.addWidget(QLabel("dBµA (电流 @50Ω):"), 3, 0); r_grid.addWidget(self.res_dbua, 3, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.res_dbuv, self.res_mv, self.res_dbm, self.res_dbua]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'dB\mu V = dBm + 107 \quad (50\Omega System)'))
        r_grid.addWidget(l_form, 4, 0, 1, 2)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def clear_conv_res(self):
        for w in [self.res_dbuv, self.res_mv, self.res_dbm, self.res_dbua]: w.clear()

    def calc_conversion(self):
        try:
            val = float(self.conv_val.text())
            mode = self.conv_mode.currentIndex()
            
            dbuv = 0.0
            
            if mode == 0: # dBµV
                dbuv = val
            elif mode == 1: # mV
                uv = val * 1000
                if uv <= 0: raise ValueError
                dbuv = 20 * math.log10(uv)
            elif mode == 2: # dBm
                dbuv = val + 107
            elif mode == 3: # dBµA
                dbuv = val + 34
                
            uv = 10**(dbuv/20)
            mv = uv / 1000
            dbm = dbuv - 107
            dbua = dbuv - 34
                
            self.res_dbuv.setText(f"{dbuv:.2f} dBµV")
            self.res_mv.setText(f"{mv:.4f} mV")
            self.res_dbm.setText(f"{dbm:.2f} dBm")
            self.res_dbua.setText(f"{dbua:.2f} dBµA")
            
        except Exception:
            QMessageBox.warning(self, "错误", "请输入有效数值")

    # ==============================================================================
    # Tab 2: 插入损耗与谐振计算 (保留原功能)
    # ==============================================================================
    def init_att_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_in = QGroupBox("1. 滤波器参数 (LC Low Pass)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.att_l = QLineEdit("10"); grid.addWidget(QLabel("电感 L [uH]:"), 0, 0); grid.addWidget(self.att_l, 0, 1)
        self.att_c = QLineEdit("100"); grid.addWidget(QLabel("电容 C [nF]:"), 0, 2); grid.addWidget(self.att_c, 0, 3)
        self.att_freq = QLineEdit("150"); grid.addWidget(QLabel("噪声频率 [kHz]:"), 1, 0); grid.addWidget(self.att_freq, 1, 1)
        self.att_z = QLineEdit("50"); grid.addWidget(QLabel("系统阻抗 Z [Ω]:"), 1, 2); grid.addWidget(self.att_z, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算衰减量 & 自谐振频率")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_attenuation)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("2. 分析结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_att = QLineEdit()
        self.res_f_res = QLineEdit() 
        
        r_grid.addWidget(QLabel("插入损耗 (Insertion Loss):"), 0, 0)
        r_grid.addWidget(self.res_att, 0, 1)
        l_att = QLabel(); l_att.setPixmap(self.render_formula(r'IL_{dB} \approx 40 \log_{10}(f / f_c)'))
        r_grid.addWidget(l_att, 0, 2)
        
        r_grid.addWidget(QLabel("LC 谐振频率 (f_res):"), 1, 0)
        r_grid.addWidget(self.res_f_res, 1, 1)
        l_res = QLabel(); l_res.setPixmap(self.render_formula(r'f_{res} = \frac{1}{2\pi \sqrt{LC}}'))
        r_grid.addWidget(l_res, 1, 2)
        
        style = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad; font-size: 16px;"
        self.res_att.setReadOnly(True); self.res_att.setStyleSheet(style)
        self.res_f_res.setReadOnly(True); self.res_f_res.setStyleSheet(style)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        info = QLabel("提示：谐振频率 f_res 处阻抗最低。滤波器在 f_res 之后效果最好，但需注意寄生参数导致的高频失效。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_attenuation(self):
        try:
            l = float(self.att_l.text()) * 1e-6
            c = float(self.att_c.text()) * 1e-9
            f = float(self.att_freq.text()) * 1e3
            
            if l*c <= 0: return

            fc = 1 / (2 * math.pi * math.sqrt(l * c))
            
            if f < fc:
                att = 0.0
            else:
                att = 40 * math.log10(f / fc)
            
            self.res_att.setText(f"- {att:.2f} dB")
            
            if fc >= 1e6:
                self.res_f_res.setText(f"{fc/1e6:.2f} MHz")
            elif fc >= 1e3:
                self.res_f_res.setText(f"{fc/1e3:.2f} kHz")
            else:
                self.res_f_res.setText(f"{fc:.1f} Hz")
            
        except Exception:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 3: 辐射场强与波长 (保留原功能)
    # ==============================================================================
    def init_rad_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_wave = QGroupBox("1. 波长与缝隙计算 (用于屏蔽效能评估)")
        w_grid = QGridLayout()
        
        self.rad_freq = QLineEdit("100"); w_grid.addWidget(QLabel("干扰频率 f [MHz]:"), 0, 0); w_grid.addWidget(self.rad_freq, 0, 1)
        btn_wave = QPushButton("计算波长 λ"); btn_wave.clicked.connect(self.calc_wavelength)
        btn_wave.setStyleSheet("background-color: #f39c12; color: white;")
        w_grid.addWidget(btn_wave, 0, 2)
        
        self.res_lambda = QLineEdit(); self.res_lambda_20 = QLineEdit()
        self.res_lambda.setReadOnly(True); self.res_lambda_20.setReadOnly(True)
        w_grid.addWidget(QLabel("波长 λ [m]:"), 1, 0); w_grid.addWidget(self.res_lambda, 1, 1)
        w_grid.addWidget(QLabel("安全缝隙 (λ/20) [mm]:"), 1, 2); w_grid.addWidget(self.res_lambda_20, 1, 3)
        
        grp_wave.setLayout(w_grid)
        layout.addWidget(grp_wave)
        
        grp_field = QGroupBox("2. 辐射发射场强计算 (Radiated Emission)")
        f_grid = QGridLayout()
        f_grid.setVerticalSpacing(12)
        
        self.rad_vrx = QLineEdit("30"); f_grid.addWidget(QLabel("接收机读数 V_rx [dBµV]:"), 0, 0); f_grid.addWidget(self.rad_vrx, 0, 1)
        self.rad_af = QLineEdit("10"); self.rad_af.setToolTip("Antenna Factor，查天线校准报告")
        f_grid.addWidget(QLabel("天线系数 AF [dB/m]:"), 0, 2); f_grid.addWidget(self.rad_af, 0, 3)
        self.rad_cable = QLineEdit("2.5"); f_grid.addWidget(QLabel("线缆损耗 Cable Loss [dB]:"), 1, 0); f_grid.addWidget(self.rad_cable, 1, 1)
        self.rad_amp = QLineEdit("0"); self.rad_amp.setToolTip("如果有前置放大器，填增益(正数)")
        f_grid.addWidget(QLabel("前置放大器增益 [dB]:"), 1, 2); f_grid.addWidget(self.rad_amp, 1, 3)
        
        btn_field = QPushButton("计算最终场强 (E)")
        btn_field.setFixedHeight(45)
        btn_field.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_field.clicked.connect(self.calc_field_strength)
        f_grid.addWidget(btn_field, 2, 0, 1, 4)
        
        self.res_field = QLineEdit()
        self.res_field.setReadOnly(True); self.res_field.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 16px;")
        f_grid.addWidget(QLabel("实际场强 E [dBµV/m]:"), 3, 0); f_grid.addWidget(self.res_field, 3, 1)
        
        l_field = QLabel()
        l_field.setPixmap(self.render_formula(r'E = V_{rx} + AF + Cable_{loss} - Gain_{amp}'))
        f_grid.addWidget(l_field, 3, 2, 1, 2)
        
        grp_field.setLayout(f_grid)
        layout.addWidget(grp_field)
        
        layout.addWidget(QLabel("说明：屏蔽机箱的缝隙、开孔最大尺寸建议小于 λ/20，以保证屏蔽效能 > 20dB。"))
        layout.addStretch()
        tab.setLayout(layout)

    def calc_wavelength(self):
        try:
            f_mhz = float(self.rad_freq.text())
            if f_mhz <= 0: return
            
            lam = 300.0 / f_mhz
            lam_20_mm = (lam / 20.0) * 1000
            
            self.res_lambda.setText(f"{lam:.3f} m")
            self.res_lambda_20.setText(f"{lam_20_mm:.2f} mm")
        except: pass

    def calc_field_strength(self):
        try:
            vrx = float(self.rad_vrx.text())
            af = float(self.rad_af.text())
            loss = float(self.rad_cable.text())
            gain = float(self.rad_amp.text())
            
            e = vrx + af + loss - gain
            self.res_field.setText(f"{e:.2f} dBµV/m")
        except: pass

    # ==============================================================================
    # Tab 4: 标准限值速查 (New Feature)
    # ==============================================================================
    def init_limits_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能：查询常用 EMC 标准在指定频率下的限制值 (Limit Line)。")
        info.setStyleSheet("color: #555; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # 1. 选择标准
        grp_sel = QGroupBox("1. 标准选择")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.std_combo = QComboBox()
        self.std_combo.addItems(list(self.standards_db.keys()))
        self.std_combo.currentIndexChanged.connect(self.update_limits_info)
        grid.addWidget(QLabel("EMC 标准:"), 0, 0); grid.addWidget(self.std_combo, 0, 1)
        
        self.std_info_lbl = QLabel("信息: ---")
        self.std_info_lbl.setStyleSheet("color: #7f8c8d;")
        grid.addWidget(self.std_info_lbl, 1, 0, 1, 2)
        
        grp_sel.setLayout(grid)
        layout.addWidget(grp_sel)
        
        # 2. 查询工具
        grp_query = QGroupBox("2. 频率点查询")
        q_grid = QGridLayout()
        
        self.query_freq = QLineEdit("150"); self.query_freq.setPlaceholderText("MHz")
        q_grid.addWidget(QLabel("输入频率 [MHz]:"), 0, 0); q_grid.addWidget(self.query_freq, 0, 1)
        
        btn_check = QPushButton("查询限值")
        btn_check.clicked.connect(self.check_limit)
        btn_check.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        q_grid.addWidget(btn_check, 0, 2)
        
        self.res_limit = QLineEdit(); self.res_limit.setReadOnly(True)
        self.res_limit.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c; background-color: #fdedec;")
        q_grid.addWidget(QLabel("标准限值:"), 1, 0); q_grid.addWidget(self.res_limit, 1, 1)
        self.res_unit_lbl = QLabel("dBµV")
        q_grid.addWidget(self.res_unit_lbl, 1, 2)
        
        grp_query.setLayout(q_grid)
        layout.addWidget(grp_query)
        
        # 3. 绘图按钮
        btn_plot = QPushButton("显示完整限值曲线 (Plot)")
        btn_plot.setFixedHeight(45)
        btn_plot.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_plot.clicked.connect(self.plot_limit_curve)
        layout.addWidget(btn_plot)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        self.update_limits_info() # Init

    def update_limits_info(self):
        key = self.std_combo.currentText()
        db = self.standards_db.get(key)
        if db:
            self.std_info_lbl.setText(f"类型: {db['type']} | 单位: {db['unit']}")
            self.res_unit_lbl.setText(db['unit'])
            # Auto set default freq for convenience
            if db['type'] == 'Conducted':
                self.query_freq.setText("0.15") # 150kHz
            else:
                self.query_freq.setText("100") # 100MHz

    def get_limit_at_freq(self, freq_mhz, data_list):
        for (f_start, f_end, limit) in data_list:
            if f_start <= freq_mhz <= f_end:
                if isinstance(limit, (int, float)):
                    return float(limit)
                elif isinstance(limit, str) and '-' in limit:
                    # Linear decay in Log-freq scale (Slope)
                    # Limit = L_start - slope * log10(f/f_start)
                    # Usually specific formula for CISPR.
                    # CISPR 32 Class B Cond: 0.15-0.5 MHz, 66 -> 56 dBuV
                    # It's linear on log-freq scale.
                    l_start, l_end = map(float, limit.split('-'))
                    # Interpolation: Y = Y1 + (x - x1) * (y2 - y1)/(x2 - x1)
                    # where x = log10(f)
                    log_f = math.log10(freq_mhz)
                    log_f1 = math.log10(f_start)
                    log_f2 = math.log10(f_end)
                    val = l_start + (log_f - log_f1) * (l_end - l_start) / (log_f2 - log_f1)
                    return val
        return None

    def check_limit(self):
        try:
            f = float(self.query_freq.text())
            key = self.std_combo.currentText()
            db = self.standards_db.get(key)
            
            val = self.get_limit_at_freq(f, db['data'])
            
            if val is not None:
                self.res_limit.setText(f"{val:.2f}")
            else:
                self.res_limit.setText("无定义 (Out of Range)")
        except Exception as e:
            QMessageBox.warning(self, "错误", "频率无效")

    def plot_limit_curve(self):
        key = self.std_combo.currentText()
        db = self.standards_db.get(key)
        data = db['data']
        
        freqs = []
        limits = []
        
        # Construct points for plotting (Step function handling)
        for (f_start, f_end, limit) in data:
            # Start point
            freqs.append(f_start)
            if isinstance(limit, str):
                l_start, _ = map(float, limit.split('-'))
                limits.append(l_start)
            else:
                limits.append(limit)
            
            # End point
            freqs.append(f_end)
            if isinstance(limit, str):
                _, l_end = map(float, limit.split('-'))
                limits.append(l_end)
            else:
                limits.append(limit)
                
        # Plot
        try:
            # 修改字体设置以支持中文
            plt.rcParams.update({
                'font.size': 10,
                'font.family': 'Microsoft YaHei',  # 优先使用微软雅黑
                'axes.unicode_minus': False        # 解决负号显示问题
            })
            
            fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
            
            # Use step-like plot but manually connected because of slopes
            # Matplotlib 'plot' connects points linearly, which is correct for log-x scale slopes if we sample enough points?
            # No, standard 'plot' is linear-linear interpolation.
            # EMC limits are usually straight lines on Semilog-X graph.
            # So simple plot(freqs, limits) is fine if x-axis is log.
            
            ax.semilogx(freqs, limits, 'r-', linewidth=2, label='Limit Line')
            
            ax.set_title(f"EMC Limit: {key}")
            ax.set_xlabel("Frequency (MHz)")
            ax.set_ylabel(f"Level ({db['unit']})")
            ax.grid(True, which="both", linestyle='--', alpha=0.6)
            ax.legend()
            
            # Show Dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"限值曲线 - {key}")
            dialog.resize(850, 600)
            layout = QVBoxLayout(dialog)
            
            scroll = QScrollArea()
            content = QWidget()
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
            l_layout = QVBoxLayout(content)
            
            canvas_lbl = QLabel()
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            canvas_lbl.setPixmap(pixmap)
            l_layout.addWidget(canvas_lbl)
            layout.addWidget(scroll)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "绘图错误", str(e))
            
    def init_filter_sizing_ui(self, tab):
        outer_layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        info = QLabel("功能说明：根据安全漏电流限制及滤波衰减目标，计算共模 (CM) 与差模 (DM) 滤波器的关键感值与容值。\n"
                      "考虑共模电感自身的漏感作为差模滤波一部分，给出极具工程实用价值的额外差模电感设计值。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. 规格输入
        grp_in = QGroupBox("1. 滤波器输入工况与指标")
        g_in = QGridLayout()
        g_in.setVerticalSpacing(12)
        
        self.flt_vline = QLineEdit("220")
        g_in.addWidget(QLabel("电网额定电压 V_line [Vrms]:"), 0, 0)
        g_in.addWidget(self.flt_vline, 0, 1)
        
        self.flt_fline = QLineEdit("50")
        g_in.addWidget(QLabel("电网额定频率 f_line [Hz]:"), 0, 2)
        g_in.addWidget(self.flt_fline, 0, 3)

        self.flt_ileak = QLineEdit("0.5")
        self.flt_ileak.setToolTip("根据安规标准：手持式设备通常 < 0.5mA，固定式IT/工业设备通常 < 3.5mA")
        g_in.addWidget(QLabel("最大漏电流限值 I_leak [mA]:"), 1, 0)
        g_in.addWidget(self.flt_ileak, 1, 1)

        self.flt_fnoise = QLineEdit("150")
        self.flt_fnoise.setToolTip("滤波目标频率，如传导EMI起点150kHz")
        g_in.addWidget(QLabel("目标噪声频率 f_noise [kHz]:"), 1, 2)
        g_in.addWidget(self.flt_fnoise, 1, 3)

        self.flt_att_cm = QLineEdit("40")
        g_in.addWidget(QLabel("共模目标衰减量 Att_cm [dB]:"), 2, 0)
        g_in.addWidget(self.flt_att_cm, 2, 1)

        self.flt_att_dm = QLineEdit("45")
        g_in.addWidget(QLabel("差模目标衰减量 Att_dm [dB]:"), 2, 2)
        g_in.addWidget(self.flt_att_dm, 2, 3)

        self.flt_cx = QLineEdit("0.22")
        g_in.addWidget(QLabel("差模电容 X-Cap C_x [uF]:"), 3, 0)
        g_in.addWidget(self.flt_cx, 3, 1)

        self.flt_kleak = QLineEdit("1.0")
        self.flt_kleak.setToolTip("共模电感的差模漏感比例，一般取 0.5% ~ 2.0%")
        g_in.addWidget(QLabel("共模电感漏感比例 k_leak [%]:"), 3, 2)
        g_in.addWidget(self.flt_kleak, 3, 3)

        grp_in.setLayout(g_in)
        layout.addWidget(grp_in)

        # Calculate Button
        btn = QPushButton("设计滤波器参数")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.calc_filter_sizing)
        layout.addWidget(btn)

        # 2. 计算结果
        grp_res = QGroupBox("2. 设计推荐与计算结果")
        g_res = QGridLayout()
        g_res.setVerticalSpacing(12)
        self.res_cy_max = QLineEdit()
        g_res.addWidget(QLabel("最大允许 Y 电容 Cy_max [nF]:"), 0, 0)
        g_res.addWidget(self.res_cy_max, 0, 1)

        self.res_cy_rec = QLineEdit()
        self.res_cy_rec.setToolTip("根据标称值推荐略小的安规电容值，以留足余量")
        g_res.addWidget(QLabel("推荐标称 Y 电容 C_y [nF]:"), 0, 2)
        g_res.addWidget(self.res_cy_rec, 0, 3)

        self.res_fc_cm = QLineEdit()
        g_res.addWidget(QLabel("共模截止频率 fc_cm [kHz]:"), 1, 0)
        g_res.addWidget(self.res_fc_cm, 1, 1)

        self.res_lcm = QLineEdit()
        g_res.addWidget(QLabel("共模电感量 L_cm [mH]:"), 1, 2)
        g_res.addWidget(self.res_lcm, 1, 3)

        self.res_fc_dm = QLineEdit()
        g_res.addWidget(QLabel("差模截止频率 fc_dm [kHz]:"), 2, 0)
        g_res.addWidget(self.res_fc_dm, 2, 1)

        self.res_ldm = QLineEdit()
        g_res.addWidget(QLabel("所需总差模电感 L_dm [uH]:"), 2, 2)
        g_res.addWidget(self.res_ldm, 2, 3)

        self.res_ldm_leak = QLineEdit()
        g_res.addWidget(QLabel("共模电感提供漏感 L_leak [uH]:"), 3, 0)
        g_res.addWidget(self.res_ldm_leak, 3, 1)

        self.res_ldm_add = QLineEdit()
        self.res_ldm_add.setToolTip("正数表示需要额外放置的差模扼流圈感值；0 表示仅靠共模电感的漏感已足够")
        g_res.addWidget(QLabel("需额外增加差模电感 L_add [uH]:"), 3, 2)
        g_res.addWidget(self.res_ldm_add, 3, 3)

        for w in [self.res_cy_max, self.res_cy_rec, self.res_fc_cm, self.res_lcm, self.res_fc_dm, self.res_ldm, self.res_ldm_leak, self.res_ldm_add]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #16a085;")

        grp_res.setLayout(g_res)
        layout.addWidget(grp_res)

        # 3. 设计公式原理
        grp_formula = QGroupBox("3. 滤波器设计公式与原理")
        g_form = QGridLayout()
        g_form.setVerticalSpacing(10)
        
        self.flt_form_leak = QLabel()
        self.flt_form_leak.setAlignment(Qt.AlignCenter)
        self.flt_form_leak.setPixmap(self.render_formula(r'C_{y\_max} = \frac{I_{leak\_max}}{2\pi \cdot f_{line} \cdot V_{line}}'))
        g_form.addWidget(QLabel("Y电容最大容量限制:"), 0, 0)
        g_form.addWidget(self.flt_form_leak, 0, 1)

        self.flt_form_lcm = QLabel()
        self.flt_form_lcm.setAlignment(Qt.AlignCenter)
        self.flt_form_lcm.setPixmap(self.render_formula(r'f_{c\_cm} = \frac{f_{noise}}{10^{Att_{cm}/40}}, \quad L_{cm} = \frac{1}{2 \cdot (2\pi f_{c\_cm})^2 \cdot C_y}'))
        g_form.addWidget(QLabel("共模滤波感值设计:"), 1, 0)
        g_form.addWidget(self.flt_form_lcm, 1, 1)

        self.flt_form_ldm = QLabel()
        self.flt_form_ldm.setAlignment(Qt.AlignCenter)
        self.flt_form_ldm.setPixmap(self.render_formula(r'f_{c\_dm} = \frac{f_{noise}}{10^{Att_{dm}/40}}, \quad L_{dm} = \frac{1}{(2\pi f_{c\_dm})^2 \cdot C_x}'))
        g_form.addWidget(QLabel("差模滤波感值设计:"), 2, 0)
        g_form.addWidget(self.flt_form_ldm, 2, 1)

        self.flt_form_add = QLabel()
        self.flt_form_add.setAlignment(Qt.AlignCenter)
        self.flt_form_add.setPixmap(self.render_formula(r'L_{dm\_add} = \max(0, L_{dm} - k_{leak} \cdot L_{cm})'))
        g_form.addWidget(QLabel("差模补偿电感计算:"), 3, 0)
        g_form.addWidget(self.flt_form_add, 3, 1)

        grp_formula.setLayout(g_form)
        layout.addWidget(grp_formula)

        layout.addStretch()
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def calc_filter_sizing(self):
        try:
            vline = float(self.flt_vline.text())
            fline = float(self.flt_fline.text())
            ileak = float(self.flt_ileak.text()) * 1e-3
            fnoise = float(self.flt_fnoise.text()) * 1e3
            att_cm = float(self.flt_att_cm.text())
            att_dm = float(self.flt_att_dm.text())
            cx = float(self.flt_cx.text()) * 1e-6
            kleak = float(self.flt_kleak.text()) / 100.0

            if vline <= 0 or fline <= 0 or ileak <= 0 or fnoise <= 0 or cx <= 0:
                raise ValueError

            # 1. Cy_max
            cy_max = ileak / (2 * math.pi * fline * vline)
            cy_max_nf = cy_max * 1e9
            self.res_cy_max.setText(f"{cy_max_nf:.3f}")

            # 2. Recommend Y-cap
            std_y_caps = [0.1, 0.22, 0.33, 0.47, 1.0, 1.5, 2.2, 3.3, 4.7, 6.8, 10.0, 22.0]
            cy_rec_nf = 0.0
            for val in std_y_caps:
                if val <= cy_max_nf:
                    cy_rec_nf = val
                else:
                    break
            
            if cy_rec_nf == 0.0:
                cy_rec_nf = cy_max_nf * 0.9
            
            self.res_cy_rec.setText(f"{cy_rec_nf:.2f}")
            cy_val = cy_rec_nf * 1e-9

            # 3. CM Cutoff & Inductance
            fc_cm = fnoise / (10 ** (att_cm / 40.0))
            self.res_fc_cm.setText(f"{fc_cm/1e3:.2f}")

            lcm = 1.0 / (2.0 * ((2 * math.pi * fc_cm) ** 2) * cy_val)
            self.res_lcm.setText(f"{lcm*1e3:.2f}")

            # 4. DM Cutoff & Inductance
            fc_dm = fnoise / (10 ** (att_dm / 40.0))
            self.res_fc_dm.setText(f"{fc_dm/1e3:.2f}")

            ldm = 1.0 / (((2 * math.pi * fc_dm) ** 2) * cx)
            self.res_ldm.setText(f"{ldm*1e6:.1f}")

            # 5. Leakage inductance
            ldm_leak = lcm * kleak
            self.res_ldm_leak.setText(f"{ldm_leak*1e6:.1f}")

            # 6. Additional DM Inductor
            ldm_add = max(0.0, ldm - ldm_leak)
            self.res_ldm_add.setText(f"{ldm_add*1e6:.1f}")

            if ldm_add == 0:
                self.res_ldm_add.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.res_ldm_add.setStyleSheet("background-color: #e8f8f5; color: #16a085; font-weight: bold;")

        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数字参数。并确保 Y 电容量非零。")

    def init_conducted_fix_ui(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            "Fast conducted-EMI debug helper: measured level -> over-limit margin -> first-pass CM/DM filter changes."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #566573; font-style: italic;")
        layout.addWidget(info)

        grp = QGroupBox("1. Failed frequency point")
        g = QGridLayout()
        self.fix_std = QComboBox()
        conducted_keys = [k for k, v in self.standards_db.items() if v.get("type") == "Conducted"]
        self.fix_std.addItems(conducted_keys)
        self.fix_freq = QLineEdit("0.15")
        self.fix_meas = QLineEdit("76")
        self.fix_margin = QLineEdit("6")
        self.fix_cm_pct = QLineEdit("60")
        self.fix_vline = QLineEdit("220")
        self.fix_fline = QLineEdit("50")
        self.fix_ileak = QLineEdit("0.5")
        self.fix_cx = QLineEdit("0.22")
        self.fix_kleak = QLineEdit("1.0")

        fields = [
            ("Conducted standard:", self.fix_std),
            ("Fail frequency [MHz]:", self.fix_freq),
            ("Measured level [dBuV]:", self.fix_meas),
            ("Design margin [dB]:", self.fix_margin),
            ("Assumed CM share [%]:", self.fix_cm_pct),
            ("Line voltage [Vrms]:", self.fix_vline),
            ("Line frequency [Hz]:", self.fix_fline),
            ("Leakage current limit [mA]:", self.fix_ileak),
            ("Existing/target X cap [uF]:", self.fix_cx),
            ("CMC leakage [%]:", self.fix_kleak),
        ]
        for i, (label, widget) in enumerate(fields):
            r, c = i // 2, (i % 2) * 2
            g.addWidget(QLabel(label), r, c)
            g.addWidget(widget, r, c + 1)
        grp.setLayout(g)
        layout.addWidget(grp)

        btn = QPushButton("Calculate EMI fix")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_conducted_fix)
        layout.addWidget(btn)

        grp_res = QGroupBox("2. First-pass fix recommendation")
        r = QGridLayout()
        self.fix_res = {}
        labels = [
            ("Limit at frequency:", "limit"),
            ("Over limit:", "over"),
            ("Required attenuation:", "need"),
            ("CM target attenuation:", "cm_att"),
            ("DM target attenuation:", "dm_att"),
            ("Recommended Y cap:", "cy"),
            ("Recommended CMC:", "lcm"),
            ("Recommended DM inductance:", "ldm"),
            ("Extra DM inductance:", "ldm_add"),
            ("Damping estimate:", "damp"),
        ]
        for i, (label, key) in enumerate(labels):
            w = QLineEdit()
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #1e8449;")
            self.fix_res[key] = w
            rr, cc = i // 2, (i % 2) * 2
            r.addWidget(QLabel(label), rr, cc)
            r.addWidget(w, rr, cc + 1)
        grp_res.setLayout(r)
        layout.addWidget(grp_res)

        self.fix_note = QTextBrowser()
        self.fix_note.setMinimumHeight(120)
        self.fix_note.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d5d8dc;")
        layout.addWidget(self.fix_note)
        layout.addStretch()

    def calc_conducted_fix(self):
        try:
            key = self.fix_std.currentText()
            db = self.standards_db[key]
            freq_mhz = float(self.fix_freq.text())
            measured = float(self.fix_meas.text())
            margin = float(self.fix_margin.text())
            cm_share = float(self.fix_cm_pct.text()) / 100.0
            vline = float(self.fix_vline.text())
            fline = float(self.fix_fline.text())
            ileak = float(self.fix_ileak.text()) * 1e-3
            cx = float(self.fix_cx.text()) * 1e-6
            kleak = float(self.fix_kleak.text()) / 100.0
            if not (0 <= cm_share <= 1) or min(freq_mhz, vline, fline, ileak, cx) <= 0:
                raise ValueError

            limit = self.get_limit_at_freq(freq_mhz, db["data"])
            if limit is None:
                self.fix_res["limit"].setText("Out of range")
                return
            over = measured - limit
            need = max(0.0, over + margin)
            cm_att = need * cm_share
            dm_att = need * (1.0 - cm_share)
            fnoise = freq_mhz * 1e6

            cy_max = ileak / (2 * math.pi * fline * vline)
            std_y_nf = [0.1, 0.22, 0.33, 0.47, 1.0, 1.5, 2.2, 3.3, 4.7, 6.8, 10.0]
            cy_nf = max([v for v in std_y_nf if v <= cy_max * 1e9] or [cy_max * 1e9 * 0.8])
            cy = cy_nf * 1e-9

            fc_cm = fnoise / (10 ** (cm_att / 40.0)) if cm_att > 0 else fnoise
            lcm = 1.0 / (2.0 * ((2.0 * math.pi * fc_cm) ** 2) * cy)
            fc_dm = fnoise / (10 ** (dm_att / 40.0)) if dm_att > 0 else fnoise
            ldm = 1.0 / (((2.0 * math.pi * fc_dm) ** 2) * cx)
            ldm_leak = lcm * kleak
            ldm_add = max(0.0, ldm - ldm_leak)
            rdamp = math.sqrt(max(ldm, 1e-12) / cx)
            cdamp = 3.0 * cx

            self.fix_res["limit"].setText(f"{limit:.1f} dBuV")
            self.fix_res["over"].setText(f"{over:.1f} dB")
            self.fix_res["need"].setText(f"{need:.1f} dB")
            self.fix_res["cm_att"].setText(f"{cm_att:.1f} dB")
            self.fix_res["dm_att"].setText(f"{dm_att:.1f} dB")
            self.fix_res["cy"].setText(f"{cy_nf:.2f} nF max-safe pick")
            self.fix_res["lcm"].setText(f"{lcm * 1e3:.2f} mH")
            self.fix_res["ldm"].setText(f"{ldm * 1e6:.1f} uH")
            self.fix_res["ldm_add"].setText(f"{ldm_add * 1e6:.1f} uH")
            self.fix_res["damp"].setText(f"R~{rdamp:.1f} ohm, C~{cdamp * 1e6:.2f} uF")

            self.fix_note.setHtml(
                "Use this as a bench starting point, not a compliance guarantee.<br>"
                "Low-frequency conducted failures are often DM-heavy; high-frequency or PE-referenced failures are often CM-heavy. "
                "Change the CM share field after LISN/CM-current-probe diagnosis."
            )
        except Exception:
            QMessageBox.warning(self, "Input error", "Please check EMI fix inputs.")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("EMC 标准与设计指南")
        dialog.resize(900, 750)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px; font-size: 13px;")
        
        html = """
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 20px;}
            h3 { color: #d35400; margin-top: 15px; }
            .box { background-color: #ecf0f1; padding: 10px; border-left: 5px solid #bdc3c7; margin: 10px 0; }
            .warn { background-color: #fdedec; padding: 10px; border-left: 5px solid #c0392b; color: #c0392b;}
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
        </style>
        
        <h1>EMC 设计与整改指南</h1>
        
        <h2>1. 标准限值速查</h2>
        <p><b>传导发射 (Conducted Emission):</b> 关注频段 150kHz ~ 30MHz。主要通过电源线传播。</p>
        <ul>
            <li><b>QP (Quasi-Peak):</b> 准峰值，模拟人耳对脉冲噪声的主观感受。</li>
            <li><b>AVG (Average):</b> 平均值，衡量连续噪声。</li>
            <li><i>整改提示：</i> 150k~500k 超标通常是差模噪声（加大 X 电容/差模电感）；5M~30M 超标通常是共模噪声（加大 Y 电容/共模电感）。</li>
        </ul>
        
        <p><b>辐射发射 (Radiated Emission):</b> 关注频段 30MHz ~ 1GHz (或更高)。通过空间传播。</p>
        <ul>
            <li><b>3m 法 vs 10m 法：</b> CISPR 32 Class A/B 常用 3m 或 10m 距离测试。距离越远，限值通常越低（需换算）。本工具默认使用 3m 限值。</li>
            <li><i>整改提示：</i> 30M~200M 往往与线缆（作为天线）有关；200M 以上往往与 PCB 布局、时钟、开孔缝隙有关。</li>
        </ul>

        <h2>2. 核心单位换算 (50Ω 系统)</h2>
        <div class="box">
            <p><b>dBµV (电压):</b> 参考 1µV。 0 dBµV = 1µV。</p>
            <p><b>dBm (功率):</b> 参考 1mW。 0 dBm = 1mW。</p>
            <p><b>换算公式:</b> <code>dBµV = dBm + 107</code></p>
            <p><b>记忆锚点:</b> 0 dBm = 107 dBµV (约 0.224V)</p>
        </div>

        <h2>3. 滤波器设计要点</h2>
        <h3>共模干扰 (Common Mode)</h3>
        <p>噪声同时存在于 L 和 N 线，对地（PE）同相流动。</p>
        <ul>
            <li><b>抑制手段：</b> 共模电感 (CMC) + Y 电容。</li>
            <li><b>Y 电容限制：</b> 受安规漏电流限制，通常小于 4.7nF。</li>
        </ul>

        <h3>差模干扰 (Differential Mode)</h3>
        <p>噪声在 L 和 N 线之间反相流动。</p>
        <ul>
            <li><b>抑制手段：</b> 差模电感 (L_dm) + X 电容。</li>
            <li><b>X 电容优势：</b> 不涉及漏电流，容值可以选很大 (uF级)。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()
