from modules.base_module import BaseModule
# comp_resistor_tool.py
# (Renamed from comp_resistor_finder.py to reflect expanded functionality)

import math
import bisect
import itertools

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QGridLayout, QGroupBox, QRadioButton, QPushButton,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QButtonGroup,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils import ResistorDividerCalculator, render_formula

# ==============================================================================
# Main Window: Resistor & Capacitor Comprehensive Tool
# ==============================================================================
class ResistorToolWindow(BaseModule):
    category = "5. 无源器件与物理连接 (Passives & Physical)"
    display_name = "电阻综合工具箱"
    description = "分压/WCA/凑值/查询/脉冲"
    window_id = "comp_r_tool"

    def init_module_ui(self):
        
        # 共享工具类实例
        self.calculator = ResistorDividerCalculator()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('电阻综合工具箱 (Divider, Combiner, WCA, Pulse)')
        self.setGeometry(350, 350, 950, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部栏
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("电阻选型与凑值指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(200)
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

        self.tab_theoretical = TheoreticalDividerTab()
        self.tab_divider_find = DividerFinderTab(self.calculator)
        self.tab_divider_wca = DividerWcaTab()
        self.tab_combiner = CombinerTab(self.calculator) # New Feature
        self.tab_finder = StandardFinderTab(self.calculator) # Existing
        self.tab_pulse = PulseWithstandTab() # Existing

        self.tabs.addTab(self.tab_theoretical, "1. 理论分压计算 (Theory)")
        self.tabs.addTab(self.tab_divider_find, "2. 分压电阻寻找 (Divider)")
        self.tabs.addTab(self.tab_divider_wca, "3. 最坏情况分析 (WCA)")
        self.tabs.addTab(self.tab_combiner, "4. R/C 串并联凑值 (Combiner)")
        self.tabs.addTab(self.tab_finder, "5. 标准阻值查询 (E96/E192)")
        self.tabs.addTab(self.tab_pulse, "6. 电阻脉冲耐受评估 (Pulse)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("电阻选型与凑值工程指南")
        dialog.resize(850, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 8px; }
            .box { background-color: #fffde7; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
            .code { background-color: #e8f8f5; color: #27ae60; font-weight: bold; padding: 2px 5px; border-radius: 3px; }
        </style>
        
        <h1>电阻选型与应用工程指南</h1>
        
        <h2>1. 分压电阻计算器 & WCA</h2>
        <p><b>寻找标准电阻 (Find R):</b> 寻找两个规范电阻（E96系列），使其分压比例最接近目标电压。</p>
        <p><b>最坏情况分析 (WCA):</b> 由于电阻精度、温漂、Vref 精度以及 FB 引脚偏置电流的影响，批量生产时的输出电压会在一定范围内波动。建议设计分压极值时，预留 WCA 计算出的误差裕量。</p>

        <h2>2. R/C 串并联凑值 (Combiner)</h2>
        <div class="box">
            <b>痛点：</b> 在调节 LDO 输出电压、DC-DC 环路补偿或 OVP 保护点时，计算出的理想电阻值（如 13.47kΩ）往往不是标准值。定制电阻成本高且周期长。
        </div>
        <p><b>解决方案：</b> 使用两个常见的标准电阻（E24/E96系列）进行串联或并联，可以极高精度地逼近目标值。</p>
        <ul>
            <li><b>串联 (Series):</b> $R_{total} = R1 + R2$。增加阻值，常用于高压分压微调。</li>
            <li><b>并联 (Parallel):</b> $R_{total} = (R1 \cdot R2) / (R1 + R2)$。减小阻值，常用于大电流采样微调或获得非标阻值。</li>
            <li><b>技巧：</b> 尽量选择通过库存中已有的阻值（如 10k, 100k）组合，减少 BOM 种类。</li>
        </ul>

        <h2>2. 标准阻值 (Standard Values)</h2>
        <p>电阻值遵循 IEC 标准系列：</p>
        <ul>
            <li><b>E24 (5%):</b> 成本最低，常用于上拉、限流。如 4.7k, 10k, 51k。</li>
            <li><b>E96 (1%):</b> 信号处理、电源反馈最常用。如 4.99k, 10.0k, 13.7k。</li>
            <li><b>E192 (0.1%~0.5%):</b> 高精度仪表、精密采样。</li>
        </ul>

        <h2>3. 脉冲功率耐受 (Pulse Withstand)</h2>
        <div class="box">
            <b>误区：</b> 0603 电阻标称 0.1W，是指<b>稳态</b>散热能力。在 ESD 或浪涌瞬间，电阻需靠自身热容吸收能量，耐受力远小于稳态。
        </div>
        
        <h3>单次脉冲能量限制 (Single Pulse Energy)</h3>
        <ul>
            <li><b>普通厚膜 (Thick Film):</b> 耐脉冲能力差。0603 约 <b>0.01J</b>。</li>
            <li><b>抗浪涌厚膜 (Anti-Surge):</b> 特殊设计，耐受能力提升 5~10 倍。</li>
            <li><b>绕线电阻 (Wirewound):</b> 耐脉冲能力最强（几十焦耳），适合预充电阻。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        close_btn = QPushButton("关闭指南")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec_()

# ==============================================================================
# Tab 0: 理论分压计算 (Theoretical Divider)
# ==============================================================================
class TheoreticalDividerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：输入源电压、分压目标、上偏与下偏电阻中的任意3项，自动计算第4项，并同步输出电阻功耗与回路电流。")
        info.setStyleSheet("color: #555; font-style: italic; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. Parameter Input Group
        grp_in = QGroupBox("1. 分压参数设定 (输入3项，计算第4项)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        grid.setHorizontalSpacing(15)
        
        self.inp_vin = QLineEdit("12.0")
        self.inp_vout = QLineEdit("3.3")
        self.inp_r1 = QLineEdit("10.0")
        self.inp_r2 = QLineEdit("3.793")
        
        # Buttons
        btn_calc_vin = QPushButton("计算 Vin")
        btn_calc_vout = QPushButton("计算 Vout")
        btn_calc_r1 = QPushButton("计算 R1")
        btn_calc_r2 = QPushButton("计算 R2")
        
        for btn in [btn_calc_vin, btn_calc_vout, btn_calc_r1, btn_calc_r2]:
            btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
            btn.setCursor(Qt.PointingHandCursor)
        
        btn_calc_vin.clicked.connect(lambda: self.calc_target('vin'))
        btn_calc_vout.clicked.connect(lambda: self.calc_target('vout'))
        btn_calc_r1.clicked.connect(lambda: self.calc_target('r1'))
        btn_calc_r2.clicked.connect(lambda: self.calc_target('r2'))
        
        for inp in [self.inp_vin, self.inp_vout, self.inp_r1, self.inp_r2]:
            inp.textChanged.connect(self.update_power)
            
        grid.addWidget(QLabel("源电压 (Vin) [V]:"), 0, 0)
        grid.addWidget(self.inp_vin, 0, 1)
        grid.addWidget(btn_calc_vin, 0, 2)
        
        grid.addWidget(QLabel("中点电压 (Vout) [V]:"), 1, 0)
        grid.addWidget(self.inp_vout, 1, 1)
        grid.addWidget(btn_calc_vout, 1, 2)
        
        grid.addWidget(QLabel("上偏电阻 (R1) [kΩ]:"), 2, 0)
        grid.addWidget(self.inp_r1, 2, 1)
        grid.addWidget(btn_calc_r1, 2, 2)
        
        grid.addWidget(QLabel("下偏电阻 (R2) [kΩ]:"), 3, 0)
        grid.addWidget(self.inp_r2, 3, 1)
        grid.addWidget(btn_calc_r2, 3, 2)
        
        grid.setColumnStretch(1, 1)
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. Results Group
        grp_out = QGroupBox("2. 功耗与电流分析")
        out_grid = QGridLayout()
        out_grid.setVerticalSpacing(15)
        
        self.out_i = QLineEdit()
        self.out_p1 = QLineEdit()
        self.out_p2 = QLineEdit()
        
        for w in [self.out_i, self.out_p1, self.out_p2]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #f0f0f0; font-weight: bold; color: #2c3e50;")
            
        out_grid.addWidget(QLabel("分压回路电流 (I) [mA]:"), 0, 0)
        out_grid.addWidget(self.out_i, 0, 1)
        
        out_grid.addWidget(QLabel("上偏 R1 功耗 (P1) [W]:"), 1, 0)
        out_grid.addWidget(self.out_p1, 1, 1)
        
        out_grid.addWidget(QLabel("下偏 R2 功耗 (P2) [W]:"), 2, 0)
        out_grid.addWidget(self.out_p2, 2, 1)
        
        grp_out.setLayout(out_grid)
        layout.addWidget(grp_out)
        
        # 3. 附注信息与功率校验
        grp_info = QGroupBox("3. 贴片电阻功率校验与参考")
        info_layout = QVBoxLayout()
        info_table = QLabel(
            "<table border='1' cellspacing='0' cellpadding='4' style='border-collapse: collapse; text-align: center; width: 100%; border-color: #ddd;'>"
            "<tr style='background-color: #f4f6f9;'><th>封装</th><th>0402</th><th>0603</th><th>0805</th><th>1206</th></tr>"
            "<tr><td><b>额定功耗</b></td><td>1/16 W<br>(0.0625 W)</td><td>1/10 W<br>(0.1 W)</td><td>1/8 W<br>(0.125 W)</td><td>1/4 W<br>(0.25 W)</td></tr>"
            "</table>"
        )
        info_table.setStyleSheet("font-size: 13px; color: #333;")
        info_layout.addWidget(info_table)
        
        # 功率校验区
        chk_layout = QHBoxLayout()
        chk_layout.addWidget(QLabel("拟采用封装:"))
        self.pkg_combo = QComboBox()
        self.pkg_combo.addItems(["0402 (1/16W)", "0603 (1/10W)", "0805 (1/8W)", "1206 (1/4W)"])
        self.pkg_combo.setCurrentText("0603 (1/10W)")
        chk_layout.addWidget(self.pkg_combo)
        
        chk_layout.addWidget(QLabel("R1 拟用数量:"))
        self.pkg_qty_r1 = QLineEdit("1")
        self.pkg_qty_r1.setFixedWidth(50)
        chk_layout.addWidget(self.pkg_qty_r1)

        chk_layout.addWidget(QLabel("R2 拟用数量:"))
        self.pkg_qty_r2 = QLineEdit("1")
        self.pkg_qty_r2.setFixedWidth(50)
        chk_layout.addWidget(self.pkg_qty_r2)
        
        chk_layout.addStretch()
        
        info_layout.addLayout(chk_layout)
        
        # 校验结果
        self.lbl_verify_r1 = QLabel("R1 校验: -")
        self.lbl_verify_r2 = QLabel("R2 校验: -")
        self.lbl_verify_r1.setTextFormat(Qt.RichText)
        self.lbl_verify_r2.setTextFormat(Qt.RichText)
        self.lbl_verify_r1.setStyleSheet("font-size: 13px; margin-top: 5px;")
        self.lbl_verify_r2.setStyleSheet("font-size: 13px; margin-bottom: 5px;")
        
        info_layout.addWidget(self.lbl_verify_r1)
        info_layout.addWidget(self.lbl_verify_r2)
        
        grp_info.setLayout(info_layout)
        layout.addWidget(grp_info)
        
        # 连接事件
        self.pkg_combo.currentIndexChanged.connect(self.update_power)
        self.pkg_qty_r1.textChanged.connect(self.update_power)
        self.pkg_qty_r2.textChanged.connect(self.update_power)
        
        layout.addStretch()
        self.setLayout(layout)
        self.update_power()

    def calc_target(self, target):
        try:
            if target != 'vin':
                vin = float(self.inp_vin.text())
            if target != 'vout':
                vout = float(self.inp_vout.text())
            if target != 'r1':
                r1 = float(self.inp_r1.text())
            if target != 'r2':
                r2 = float(self.inp_r2.text())
                
            if target == 'vin':
                vin = vout * (r1 + r2) / r2
                self.inp_vin.setText(f"{vin:.4f}")
            elif target == 'vout':
                vout = vin * r2 / (r1 + r2)
                self.inp_vout.setText(f"{vout:.4f}")
            elif target == 'r1':
                if vout <= 0 or vout >= vin: raise ValueError("Vout 必须在 0 和 Vin 之间")
                r1 = r2 * (vin / vout - 1.0)
                self.inp_r1.setText(f"{r1:.4f}")
            elif target == 'r2':
                if vout <= 0 or vout >= vin: raise ValueError("Vout 必须在 0 和 Vin 之间")
                r2 = vout * r1 / (vin - vout)
                self.inp_r2.setText(f"{r2:.4f}")
                
            self.update_power()
            
        except ZeroDivisionError:
            QMessageBox.warning(self, "计算错误", "除数为零，检查输入的电阻或电压值。")
        except ValueError as ve:
            QMessageBox.warning(self, "计算错误", f"计算错误: {ve}")
        except Exception as e:
            QMessageBox.warning(self, "计算错误", f"输入不合法: {e}")
            
    def update_power(self):
        p1_w = 0.0
        p2_w = 0.0
        success = False
        try:
            vin = float(self.inp_vin.text())
            r1 = float(self.inp_r1.text())
            r2 = float(self.inp_r2.text())
            
            if r1 + r2 > 0:
                i_ma = vin / (r1 + r2) # V / kOhm = mA
                p1_w = (i_ma * i_ma * r1) / 1000.0 # mA^2 * kOhm = mW -> W
                p2_w = (i_ma * i_ma * r2) / 1000.0
                
                self.out_i.setText(f"{i_ma:.5f}")
                self.out_p1.setText(f"{p1_w:.5f}")
                self.out_p2.setText(f"{p2_w:.5f}")
                success = True
            else:
                self.out_i.clear(); self.out_p1.clear(); self.out_p2.clear()
        except:
            self.out_i.clear()
            self.out_p1.clear()
            self.out_p2.clear()
            
        if not success:
            if hasattr(self, 'lbl_verify_r1'):
                self.lbl_verify_r1.setText("R1 校验: -")
                self.lbl_verify_r2.setText("R2 校验: -")
            return
            
        try:
            qty1_text = self.pkg_qty_r1.text()
            qty1 = int(qty1_text) if qty1_text.isdigit() else 1
            if qty1 < 1: qty1 = 1
            
            qty2_text = self.pkg_qty_r2.text()
            qty2 = int(qty2_text) if qty2_text.isdigit() else 1
            if qty2 < 1: qty2 = 1
            
            pkg_idx = self.pkg_combo.currentIndex()
            pkg_powers = [0.0625, 0.1, 0.125, 0.25]
            single_power = pkg_powers[pkg_idx]
            
            def eval_power(calc_w, role, qty):
                if calc_w <= 0: return f"{role} 评估: -"
                needed_qty = math.ceil(calc_w / single_power)
                per_p = calc_w / qty
                color = "#e74c3c" if per_p > single_power else "#27ae60"
                status = "超标" if per_p > single_power else "安全"
                return f"{role} 评估: 该封装至少需要 <b>{needed_qty}</b> 个。当使用 <b>{qty}</b> 个时，每颗分配功耗：<b><span style='color:{color};'>{per_p:.5f} W ({status})</span></b>"

            self.lbl_verify_r1.setText(eval_power(p1_w, "R1", qty1))
            self.lbl_verify_r2.setText(eval_power(p2_w, "R2", qty2))
        except:
            if hasattr(self, 'lbl_verify_r1'):
                self.lbl_verify_r1.setText("R1 评估: 数量设置无效")
                self.lbl_verify_r2.setText("R2 评估: -")


# ==============================================================================
# Tab 1: R/C 串并联凑值 (New Feature)
# ==============================================================================
class CombinerTab(QWidget):
    def __init__(self, calculator):
        super().__init__()
        self.calculator = calculator
        self.e24_base = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
                         3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 目标设置
        grp_in = QGroupBox("1. 凑值目标")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["电阻 (Resistor)", "电容 (Capacitor)"])
        self.combo_type.currentIndexChanged.connect(self.update_units)
        grid.addWidget(QLabel("器件类型:"), 0, 0); grid.addWidget(self.combo_type, 0, 1)
        
        self.target_val = QLineEdit("13.47")
        self.target_val.setPlaceholderText("例如 13.47 或 1200")
        self.target_unit = QLabel("kΩ")
        h_val = QHBoxLayout(); h_val.addWidget(self.target_val); h_val.addWidget(self.target_unit)
        grid.addWidget(QLabel("目标值:"), 0, 2); grid.addLayout(h_val, 0, 3)
        
        self.combo_series = QComboBox()
        self.combo_series.addItems(["E24 (常用 5%)", "E96 (精密 1%)", "E12 (电容常用)"])
        self.combo_series.setCurrentIndex(1) # Default E96
        grid.addWidget(QLabel("使用系列:"), 1, 0); grid.addWidget(self.combo_series, 1, 1)
        
        btn_calc = QPushButton("寻找最佳组合")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.find_combinations)
        grid.addWidget(btn_calc, 1, 2, 1, 2)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. 结果显示
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["组合方式", "元件 1", "元件 2", "误差 (%)"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setAlternatingRowColors(True)
        
        layout.addWidget(QLabel("<b>推荐方案 (按误差排序):</b>"))
        layout.addWidget(self.result_table)
        
        # Tips
        tip = QLabel("说明：\n1. 电容并联 = 阻值串联公式；电容串联 = 阻值并联公式。\n2. 搜索范围覆盖 7 个数量级，计算可能需要几毫秒。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px;")
        layout.addWidget(tip)
        
        self.setLayout(layout)

    def update_units(self):
        if self.combo_type.currentIndex() == 0: # Resistor
            self.target_unit.setText("kΩ") # Default input unit assumption for logic
            self.target_val.setPlaceholderText("例如 13.47 (即 13.47k)")
        else: # Capacitor
            self.target_unit.setText("nF")
            self.target_val.setPlaceholderText("例如 4.7 (即 4.7nF)")

    def get_series_list(self):
        s_idx = self.combo_series.currentIndex()
        if s_idx == 0: # E24
            base = self.e24_base
        elif s_idx == 1: # E96
            # Use calculator's E96 base but we need to generate full range locally for speed control
            base = self.calculator.e96_series
        else: # E12 (Subset of E24)
            base = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
            
        # Generate full decades: 1R to 10M (Res) or 1pF to 10uF (Cap)
        # Simplified: Generate 1e-1 to 1e4 range relative to input unit
        # Actually standard finder uses 1e0 to 1e6. Let's cover reasonable range.
        full_list = []
        # Multipliers: 0.01, 0.1, 1, 10, 100, 1000
        multipliers = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
        
        for m in multipliers:
            for b in base:
                full_list.append(round(b * m, 5))
        
        # Sort and remove duplicates
        return sorted(list(set(full_list)))

    def find_combinations(self):
        try:
            target = float(self.target_val.text())
            if target <= 0: return
            
            # Decide mode
            is_resistor = (self.combo_type.currentIndex() == 0)
            
            # Get values (normalized to input unit)
            vals = self.get_series_list()
            
            # Filter values reasonably close to target (e.g., 0.01x to 100x)
            # To optimize speed for E96
            vals = [v for v in vals if v >= target/100.0 and v <= target*100.0]
            
            results = []
            
            # Single Component Match
            idx = bisect.bisect_left(vals, target)
            if idx < len(vals):
                err = abs(vals[idx] - target) / target * 100
                results.append( ("单颗 (Single)", vals[idx], 0, err) )
            if idx > 0:
                err = abs(vals[idx-1] - target) / target * 100
                results.append( ("单颗 (Single)", vals[idx-1], 0, err) )
                
            # Combinations
            # Series (R+R or C_par) and Parallel (R||R or C_ser)
            
            # Logic:
            # Resistor Series = v1 + v2
            # Resistor Parallel = (v1*v2)/(v1+v2)
            # Capacitor Series = (v1*v2)/(v1+v2)
            # Capacitor Parallel = v1 + v2
            
            # Define operations based on component type
            if is_resistor:
                op_add_name = "串联 (Series)"
                op_par_name = "并联 (Parallel)"
            else:
                op_add_name = "并联 (Parallel)"
                op_par_name = "串联 (Series)"
                
            # We can just iterate once and check both
            # Optimization: 
            # For Add: v1 + v2 = target. Iterate v1 < target. v2 approx target - v1. Find closest v2.
            # For Par: (v1*v2)/(v1+v2) = target. 1/v1 + 1/v2 = 1/target. 
            
            # 1. Addition Logic (R_ser or C_par)
            # v1 + v2 = T.  v1 < T.
            for v1 in vals:
                if v1 >= target: break # Cannot add positive to get target
                v2_ideal = target - v1
                # Find closest v2 in vals
                idx2 = bisect.bisect_left(vals, v2_ideal)
                
                # Check neighbors
                candidates = []
                if idx2 < len(vals): candidates.append(vals[idx2])
                if idx2 > 0: candidates.append(vals[idx2-1])
                
                for v2 in candidates:
                    total = v1 + v2
                    err = abs(total - target) / target * 100
                    if err < 2.0: # Only save reasonable results
                        results.append( (op_add_name, v1, v2, err) )

            # 2. Parallel Logic (R_par or C_ser)
            # (v1*v2)/(v1+v2) = T  =>  v2 = (T*v1) / (v1 - T)
            # Condition: v1 > T
            for v1 in vals:
                if v1 <= target: continue # Must be larger than target to parallel down
                
                v2_ideal = (target * v1) / (v1 - target)
                
                # Find closest v2
                idx2 = bisect.bisect_left(vals, v2_ideal)
                candidates = []
                if idx2 < len(vals): candidates.append(vals[idx2])
                if idx2 > 0: candidates.append(vals[idx2-1])
                
                for v2 in candidates:
                    total = (v1 * v2) / (v1 + v2)
                    err = abs(total - target) / target * 100
                    if err < 2.0:
                        results.append( (op_par_name, v1, v2, err) )
                        
            # Sort and Display
            # Dedup based on (v1, v2) set
            seen = set()
            unique_results = []
            for r in results:
                # normalize key
                key = tuple(sorted((r[1], r[2]))) + (r[0],)
                if key not in seen:
                    seen.add(key)
                    unique_results.append(r)
            
            unique_results.sort(key=lambda x: x[3]) # Sort by error
            
            self.display_results(unique_results[:20]) # Top 20
            
        except Exception as e:
            QMessageBox.warning(self, "计算错误", str(e))

    def display_results(self, data):
        self.result_table.setRowCount(len(data))
        unit = self.target_unit.text()
        
        for r, (mode, v1, v2, err) in enumerate(data):
            self.result_table.setItem(r, 0, QTableWidgetItem(mode))
            self.result_table.setItem(r, 1, QTableWidgetItem(f"{v1:g} {unit}"))
            
            if v2 > 0:
                self.result_table.setItem(r, 2, QTableWidgetItem(f"{v2:g} {unit}"))
            else:
                self.result_table.setItem(r, 2, QTableWidgetItem("-"))
                
            item_err = QTableWidgetItem(f"{err:.4f} %")
            if err < 0.1:
                item_err.setForeground(Qt.darkGreen)
                item_err.setFont(QFont("Arial", 9, QFont.Bold))
            self.result_table.setItem(r, 3, item_err)

# ==============================================================================
# Tab 2: 标准阻值查询 (原功能封装)
# ==============================================================================
class StandardFinderTab(QWidget):
    def __init__(self, calculator):
        super().__init__()
        self.calculator = calculator
        self.init_ui()
        self.find_closest_resistors()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 系列选择
        series_group = QGroupBox("选择电阻系列")
        series_layout = QHBoxLayout()
        self.e96_radio = QRadioButton("E96 (1% 精度)")
        self.e96_radio.setChecked(True)
        self.e96_radio.toggled.connect(self.on_series_change)
        
        self.e192_radio = QRadioButton("E192 (≤0.5% 精度)")
        self.e192_radio.toggled.connect(self.on_series_change)
        
        series_layout.addWidget(self.e96_radio)
        series_layout.addSpacing(20)
        series_layout.addWidget(self.e192_radio)
        series_layout.addStretch()
        series_group.setLayout(series_layout)
        
        # 输入
        input_group = QGroupBox("输入查询值")
        input_layout = QHBoxLayout()
        
        label = QLabel("电阻值:")
        label.setFont(QFont('Arial', 12))
        
        self.resistor_input = QLineEdit()
        self.resistor_input.setPlaceholderText("支持格式: 46k, 4.7M, 100")
        self.resistor_input.setFont(QFont('Arial', 12))
        self.resistor_input.setFixedHeight(40)
        self.resistor_input.textChanged.connect(self.find_closest_resistors)
        
        input_layout.addWidget(label)
        input_layout.addWidget(self.resistor_input)
        input_group.setLayout(input_layout)
        
        # 结果
        output_group = QGroupBox("查询结果")
        output_layout = QGridLayout()
        output_layout.setVerticalSpacing(15)
        
        self.lower_label = QLabel("向下取值 (较小值)")
        self.lower_output = QLineEdit()
        self.lower_output.setReadOnly(True)
        self.lower_output.setStyleSheet("font-size: 16px; font-weight: bold; color: #e67e22;") 
        self.lower_output.setAlignment(Qt.AlignCenter)
        self.lower_output.setFixedHeight(40)
        
        self.upper_label = QLabel("向上取值 (较大值)")
        self.upper_output = QLineEdit()
        self.upper_output.setReadOnly(True)
        self.upper_output.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        self.upper_output.setAlignment(Qt.AlignCenter)
        self.upper_output.setFixedHeight(40)
        
        output_layout.addWidget(self.lower_label, 0, 0)
        output_layout.addWidget(self.lower_output, 0, 1)
        output_layout.addWidget(self.upper_label, 1, 0)
        output_layout.addWidget(self.upper_output, 1, 1)
        
        output_group.setLayout(output_layout)
        
        self.status_label = QLabel("请选择系列并输入电阻值进行查询。")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 10px; font-size: 13px;")
        
        layout.addWidget(series_group)
        layout.addWidget(input_group)
        layout.addWidget(output_group)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)

    def on_series_change(self):
        self.find_closest_resistors()

    def parse_input(self, text):
        text = text.strip().lower()
        if not text: return None
        try:
            if text.endswith('mω') or text.endswith('m'):
                value = float(text.replace('mω', '').replace('m', '')) * 1_000_000
            elif text.endswith('kω') or text.endswith('k'):
                value = float(text.replace('kω', '').replace('k', '')) * 1_000
            elif text.endswith('ω'):
                value = float(text.replace('ω', ''))
            else:
                value = float(text)
            return value
        except: return None

    def find_closest_resistors(self):
        if self.e96_radio.isChecked():
            current_series_list = self.calculator.full_e96_resistors
            series_name = "E96"
        else:
            current_series_list = self.calculator.full_e192_resistors
            series_name = "E192"
            
        input_text = self.resistor_input.text()
        target_value = self.parse_input(input_text)
        
        if target_value is None:
            self.lower_output.clear()
            self.upper_output.clear()
            self.status_label.setText(f"当前系列: {series_name}。请输入有效的电阻值。")
            self.status_label.setStyleSheet("color: #95a5a6;")
            return
            
        idx = bisect.bisect_left(current_series_list, target_value)
        
        if idx < len(current_series_list) and math.isclose(current_series_list[idx], target_value):
            formatted_val = self.calculator.format_resistor_value(target_value)
            self.lower_output.setText(formatted_val)
            self.upper_output.setText(formatted_val)
            self.status_label.setText(f"输入值是标准的 {series_name} 电阻值！")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            
        elif 0 < idx < len(current_series_list):
            lower_val = current_series_list[idx - 1]
            upper_val = current_series_list[idx]
            self.lower_output.setText(self.calculator.format_resistor_value(lower_val))
            self.upper_output.setText(self.calculator.format_resistor_value(upper_val))
            self.status_label.setText(f"已找到 {series_name} 系列中最接近的两个标准值。")
            self.status_label.setStyleSheet("color: #2980b9;")
            
        elif idx == 0:
            self.lower_output.setText("---")
            self.upper_output.setText(self.calculator.format_resistor_value(current_series_list[0]))
            self.status_label.setText(f"{series_name} 系列: 输入值小于最小标准值。")
            self.status_label.setStyleSheet("color: #e67e22;")
        else:
            self.lower_output.setText(self.calculator.format_resistor_value(current_series_list[-1]))
            self.upper_output.setText("---")
            self.status_label.setText(f"{series_name} 系列: 输入值大于最大标准值。")
            self.status_label.setStyleSheet("color: #e67e22;")

# ==============================================================================
# Tab 3: 脉冲耐受评估 (Original Feature)
# ==============================================================================
class PulseWithstandTab(QWidget):
    def __init__(self):
        super().__init__()
        # 脉冲能量耐受数据 (Conservative Engineering Guess)
        # Unit: Joules (Single Pulse < 2ms)
        self.pulse_limits = {
            "0402": {"std": 0.005, "surge": 0.05, "power": 0.063},
            "0603": {"std": 0.01,  "surge": 0.1,  "power": 0.1},
            "0805": {"std": 0.03,  "surge": 0.3,  "power": 0.125},
            "1206": {"std": 0.15,  "surge": 1.2,  "power": 0.25},
            "1210": {"std": 0.30,  "surge": 2.0,  "power": 0.5},
            "2010": {"std": 0.50,  "surge": 3.0,  "power": 0.75},
            "2512": {"std": 1.50,  "surge": 5.0,  "power": 1.0},
            "Wirewound 3W": {"std": 20.0, "surge": 50.0, "power": 3.0}, # 绕线电阻
            "Cement 5W":    {"std": 50.0, "surge": 100.0, "power": 5.0} # 水泥电阻
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：评估电阻在瞬态脉冲（如电容预充、浪涌）下的耐受能力。\n"
                      "模型基于短脉冲绝热模型 (E = P*t)，对比经验失效阈值。")
        info.setStyleSheet("color: #555; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 脉冲参数
        grp_in = QGroupBox("1. 脉冲参数 (Pulse Specs)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.mode_group = QButtonGroup(self)
        self.rb_energy = QRadioButton("已知脉冲能量 (Energy)")
        self.rb_power = QRadioButton("已知 功率 & 时间 (Power & Time)")
        self.rb_power.setChecked(True)
        self.mode_group.addButton(self.rb_energy)
        self.mode_group.addButton(self.rb_power)
        self.mode_group.buttonClicked.connect(self.update_inputs)
        
        h_mode = QHBoxLayout(); h_mode.addWidget(self.rb_power); h_mode.addWidget(self.rb_energy); h_mode.addStretch()
        grid.addLayout(h_mode, 0, 0, 1, 4)
        
        # 动态输入
        self.lbl_p = QLabel("脉冲峰值功率 P_peak [W]:")
        self.inp_p = QLineEdit("100")
        self.lbl_t = QLabel("脉冲持续时间 t [ms]:")
        self.inp_t = QLineEdit("1.0")
        
        self.lbl_e = QLabel("总脉冲能量 E [Joule]:")
        self.inp_e = QLineEdit("0.1")
        self.inp_e.setVisible(False); self.lbl_e.setVisible(False)
        
        grid.addWidget(self.lbl_p, 1, 0); grid.addWidget(self.inp_p, 1, 1)
        grid.addWidget(self.lbl_t, 1, 2); grid.addWidget(self.inp_t, 1, 3)
        grid.addWidget(self.lbl_e, 2, 0); grid.addWidget(self.inp_e, 2, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. 选型
        grp_sel = QGroupBox("2. 拟选电阻封装")
        h_sel = QHBoxLayout()
        self.pkg_combo = QComboBox()
        self.pkg_combo.addItems(list(self.pulse_limits.keys()))
        self.pkg_combo.setCurrentText("0805")
        
        h_sel.addWidget(QLabel("封装尺寸:")); h_sel.addWidget(self.pkg_combo)
        h_sel.addStretch()
        
        btn_calc = QPushButton("评估风险")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_pulse)
        h_sel.addWidget(btn_calc)
        
        grp_sel.setLayout(h_sel)
        layout.addWidget(grp_sel)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_energy = QLineEdit()
        self.res_std_limit = QLineEdit()
        self.res_surge_limit = QLineEdit()
        self.res_status = QLineEdit()
        
        r_grid.addWidget(QLabel("实际脉冲能量:"), 0, 0); r_grid.addWidget(self.res_energy, 0, 1)
        r_grid.addWidget(QLabel("普通厚膜极限 (Standard):"), 1, 0); r_grid.addWidget(self.res_std_limit, 1, 1)
        r_grid.addWidget(QLabel("抗浪涌厚膜极限 (Anti-Surge):"), 2, 0); r_grid.addWidget(self.res_surge_limit, 2, 1)
        
        r_grid.addWidget(QLabel("综合判定:"), 3, 0); r_grid.addWidget(self.res_status, 3, 1)
        
        style_res = "background-color: #f0f0f0; font-weight: bold;"
        for w in [self.res_energy, self.res_std_limit, self.res_surge_limit]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
        self.res_status.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        
        self.setLayout(layout)
        self.update_inputs()

    def update_inputs(self):
        is_pwr = self.rb_power.isChecked()
        self.lbl_p.setVisible(is_pwr); self.inp_p.setVisible(is_pwr)
        self.lbl_t.setVisible(is_pwr); self.inp_t.setVisible(is_pwr)
        self.lbl_e.setVisible(not is_pwr); self.inp_e.setVisible(not is_pwr)

    def calc_pulse(self):
        try:
            energy = 0.0
            if self.rb_power.isChecked():
                p = float(self.inp_p.text())
                t_ms = float(self.inp_t.text())
                if p < 0 or t_ms < 0: raise ValueError
                energy = p * (t_ms / 1000.0)
            else:
                energy = float(self.inp_e.text())
                if energy < 0: raise ValueError
            
            pkg = self.pkg_combo.currentText()
            limits = self.pulse_limits[pkg]
            lim_std = limits['std']
            lim_surge = limits['surge']
            
            self.res_energy.setText(f"{energy:.4f} J")
            self.res_std_limit.setText(f"{lim_std:.3f} J")
            self.res_surge_limit.setText(f"{lim_surge:.3f} J")
            
            # Status
            if energy < lim_std * 0.5:
                self.res_status.setText("非常安全 (普通电阻即可)")
                self.res_status.setStyleSheet("background-color: #d4edda; color: green; font-weight: bold;")
            elif energy < lim_std:
                self.res_status.setText("安全 (普通电阻可用，建议降额)")
                self.res_status.setStyleSheet("background-color: #e8f8f5; color: #27ae60; font-weight: bold;")
            elif energy < lim_surge:
                self.res_status.setText("警告：需选用【抗浪涌/Anti-Surge】系列")
                self.res_status.setStyleSheet("background-color: #fff3cd; color: #d35400; font-weight: bold;")
            else:
                self.res_status.setText("危险！必然烧毁 (需更大封装)")
                self.res_status.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

# ==============================================================================
# Tab 4: 分压电阻寻找 (Divider Find)
# ==============================================================================
class DividerFinderTab(QWidget):
    def __init__(self, calculator):
        super().__init__()
        self.calculator = calculator
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入设置区域
        input_group = QGroupBox("参数设置")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        input_layout.setHorizontalSpacing(10)
        
        self.vin_input = QLineEdit()
        self.vin_input.setPlaceholderText('例如: 12')
        self.vout_input = QLineEdit()
        self.vout_input.setPlaceholderText('例如: 3.3')
        self.error_input = QLineEdit('1.0')
        
        input_layout.addWidget(QLabel('源电压 (Vin) [V]:'), 0, 0)
        input_layout.addWidget(self.vin_input, 0, 1)
        input_layout.addWidget(QLabel('目标电压 (Vout) [V]:'), 0, 2)
        input_layout.addWidget(self.vout_input, 0, 3)
        
        input_layout.addWidget(QLabel('最大误差 (%):'), 1, 0)
        input_layout.addWidget(self.error_input, 1, 1)
        
        series_label = QLabel('电阻系列: E96 (1%)')
        series_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        input_layout.addWidget(series_label, 1, 2, 1, 2)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.calculate_button = QPushButton('计算电阻组合')
        self.calculate_button.setCursor(Qt.PointingHandCursor)
        self.calculate_button.setFixedHeight(45)
        self.calculate_button.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.calculate_button.clicked.connect(self.on_calculate)
        
        btn_layout.addWidget(self.calculate_button)
        btn_layout.addSpacing(10)
        layout.addLayout(btn_layout)

        # 结果表格
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(['R1 (上偏)', 'R2 (下偏)', '实际输出 (V)', '误差 (%)'])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.results_table.setAlternatingRowColors(True) 
        
        layout.addWidget(self.results_table)
        self.setLayout(layout)

    def on_calculate(self):
        try:
            v_in_text = self.vin_input.text()
            v_out_text = self.vout_input.text()
            error_text = self.error_input.text()

            if not v_in_text or not v_out_text:
                raise ValueError("电压输入不能为空")

            v_in = float(v_in_text)
            v_out = float(v_out_text)
            max_error = float(error_text) / 100.0
            
            results = self.calculator.find_resistors(v_in, v_out, max_error=max_error)
            self.populate_table(results)
        except Exception as e:
            QMessageBox.warning(self, '输入错误', f'请输入有效的数值！\n详细信息: {e}')
        except Exception as e:
            QMessageBox.critical(self, '发生错误', f'程序出现未知错误: {e}')

    def populate_table(self, results):
        self.results_table.setRowCount(0)
        if not results:
            QMessageBox.information(self, '提示', '在当前误差范围内未找到合适的电阻组合。\n请尝试增大最大误差值。')
            return
            
        MAX_ROWS = 100
        total_results = len(results)
        display_results = results[:MAX_ROWS]
        
        self.results_table.setRowCount(len(display_results))
        for row, res_data in enumerate(display_results):
            r1_str = self.calculator.format_resistor_value(res_data['R1'])
            r2_str = self.calculator.format_resistor_value(res_data['R2'])
            vout_actual_str = f"{res_data['V_out_actual']:.4f}"
            error_str = f"{res_data['error_percent']:.4f}"
            
            self.results_table.setItem(row, 0, QTableWidgetItem(r1_str))
            self.results_table.setItem(row, 1, QTableWidgetItem(r2_str))
            self.results_table.setItem(row, 2, QTableWidgetItem(vout_actual_str))
            self.results_table.setItem(row, 3, QTableWidgetItem(error_str))
            
            for col in range(4):
                item = self.results_table.item(row, col)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 3 and res_data['error_percent'] < 0.1:
                     item.setForeground(Qt.darkGreen)
                     item.setFont(QFont("Arial", 9, QFont.Bold))
        
        if total_results > MAX_ROWS:
            pass # Removed warning popup per user request

# ==============================================================================
# Tab 5: 最坏情况分析 (WCA)
# ==============================================================================
class DividerWcaTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能：已知电阻和基准的误差范围，计算输出电压在最坏情况下的最大/最小值。\n"
                      "适用：电源 FB 分压、OVP/UVP 阈值设定。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # 输入区
        grp_in = QGroupBox("1. 元件参数与精度")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.wca_vref = QLineEdit("0.8"); self.wca_vref.setPlaceholderText("V")
        self.wca_vref_tol = QLineEdit("1.0"); self.wca_vref_tol.setPlaceholderText("%")
        grid.addWidget(QLabel("基准电压 Vref [V]:"), 0, 0)
        grid.addWidget(self.wca_vref, 0, 1)
        grid.addWidget(QLabel("Vref 精度 [%]:"), 0, 2)
        grid.addWidget(self.wca_vref_tol, 0, 3)
        
        self.wca_ib = QLineEdit("0.1"); self.wca_ib.setPlaceholderText("uA")
        grid.addWidget(QLabel("FB 偏置电流 I_bias [uA]:"), 1, 0)
        grid.addWidget(self.wca_ib, 1, 1)
        grid.addWidget(QLabel("(注: 流入FB填正，流出填负，详见教学)"), 1, 2, 1, 2)
        
        self.wca_r1 = QLineEdit("10"); self.wca_r1.setPlaceholderText("kΩ")
        self.wca_r1_tol = QLineEdit("1.0"); self.wca_r1_tol.setPlaceholderText("%")
        grid.addWidget(QLabel("上分压电阻 R1 [kΩ]:"), 2, 0)
        grid.addWidget(self.wca_r1, 2, 1)
        grid.addWidget(QLabel("R1 精度 (含温漂) [%]:"), 2, 2)
        grid.addWidget(self.wca_r1_tol, 2, 3)
        
        self.wca_r2 = QLineEdit("10"); self.wca_r2.setPlaceholderText("kΩ")
        self.wca_r2_tol = QLineEdit("1.0"); self.wca_r2_tol.setPlaceholderText("%")
        grid.addWidget(QLabel("下分压电阻 R2 [kΩ]:"), 3, 0)
        grid.addWidget(self.wca_r2, 3, 1)
        grid.addWidget(QLabel("R2 精度 (含温漂) [%]:"), 3, 2)
        grid.addWidget(self.wca_r2_tol, 3, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_calc = QPushButton("执行最坏情况分析 (WCA)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_wca)
        
        btn_help = QPushButton("参数填写教学")
        btn_help.setFixedHeight(45)
        btn_help.setFixedWidth(150)
        btn_help.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_help.clicked.connect(self.show_wca_tutorial)
        
        btn_layout.addWidget(btn_calc)
        btn_layout.addWidget(btn_help)
        layout.addLayout(btn_layout)
        
        # 结果区
        grp_res = QGroupBox("2. 分析结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_vout_nom = QLineEdit()
        self.res_vout_min = QLineEdit()
        self.res_vout_max = QLineEdit()
        self.res_total_err = QLineEdit()
        
        r_grid.addWidget(QLabel("标称输出 Vout_nom [V]:"), 0, 0); r_grid.addWidget(self.res_vout_nom, 0, 1)
        
        l_form = QLabel()
        l_form.setPixmap(render_formula(r'V_{out} = V_{ref} \left(1 + \frac{R_1}{R_2}\right) + I_{bias} R_1'))
        r_grid.addWidget(l_form, 0, 2, 4, 1)
        
        r_grid.addWidget(QLabel("最小值 Vout_min [V]:"), 1, 0); r_grid.addWidget(self.res_vout_min, 1, 1)
        r_grid.addWidget(QLabel("最大值 Vout_max [V]:"), 2, 0); r_grid.addWidget(self.res_vout_max, 2, 1)
        
        r_grid.addWidget(QLabel("总误差范围 Total Error:"), 3, 0); r_grid.addWidget(self.res_total_err, 3, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400;"
        
        self.res_vout_nom.setReadOnly(True); self.res_vout_nom.setStyleSheet(style)
        self.res_vout_min.setReadOnly(True); self.res_vout_min.setStyleSheet(style_warn)
        self.res_vout_max.setReadOnly(True); self.res_vout_max.setStyleSheet(style_warn)
        self.res_total_err.setReadOnly(True); 
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)

    def calc_wca(self):
        try:
            vref = float(self.wca_vref.text())
            vref_tol = float(self.wca_vref_tol.text()) / 100.0
            
            ib_ua = float(self.wca_ib.text())
            
            r1 = float(self.wca_r1.text()) # kOhm
            r1_tol = float(self.wca_r1_tol.text()) / 100.0
            
            r2 = float(self.wca_r2.text()) # kOhm
            r2_tol = float(self.wca_r2_tol.text()) / 100.0
            
            if r2 <= 0: raise ValueError
            
            # Helper to calc Vout
            def get_vout(v_r, r_1, r_2, i_b):
                # Vout = Vref * (1 + R1/R2) + I_bias * R1
                # I_bias * R1 unit: uA * kOhm = mV = 1e-3 V
                term_bias = i_b * r_1 * 1e-3 
                return v_r * (1 + r_1 / r_2) + term_bias
            
            # Nominal
            v_nom = get_vout(vref, r1, r2, ib_ua)
            
            vref_max = vref * (1 + vref_tol)
            vref_min = vref * (1 - vref_tol)
            
            r1_max = r1 * (1 + r1_tol)
            r1_min = r1 * (1 - r1_tol)
            
            r2_max = r2 * (1 + r2_tol)
            r2_min = r2 * (1 - r2_tol)
            
            ib_effect_pos = abs(ib_ua) 
            v_max = get_vout(vref_max, r1_max, r2_min, ib_effect_pos)
            
            ib_effect_neg = -abs(ib_ua)
            v_min = get_vout(vref_min, r1_min, r2_max, ib_effect_neg) 
            
            # Error %
            err_pos = (v_max - v_nom) / v_nom * 100
            err_neg = (v_min - v_nom) / v_nom * 100
            
            self.res_vout_nom.setText(f"{v_nom:.4f} V")
            self.res_vout_max.setText(f"{v_max:.4f} V")
            self.res_vout_min.setText(f"{v_min:.4f} V")
            self.res_total_err.setText(f"{err_neg:.2f}% ~ +{err_pos:.2f}%")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def show_wca_tutorial(self):
        """显示 WCA 参数填写教学"""
        dialog = QDialog(self)
        dialog.setWindowTitle("WCA 参数填写与误差分析指南")
        dialog.resize(800, 650)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; font-weight: bold; }
            .box { background-color: #ecf0f1; padding: 10px; border-left: 5px solid #bdc3c7; margin: 10px 0; }
            .warn { background-color: #fff3cd; padding: 10px; border-left: 5px solid #ffc107; color: #856404;}
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
        </style>
        
        <h1>最坏情况分析 (WCA) 填写指南</h1>
        <p>在电源设计中，OVP（过压保护）和 UVP（欠压锁定）的阈值精度至关重要。WCA 能帮你计算出批量生产时电压可能偏离的极限范围。</p>

        <h3>1. Vref 精度 (Reference Tolerance)</h3>
        <p><b>陷阱：</b> 不要只看 Datasheet 首页的 "1%" 或 "0.5%"。</p>
        <div class="box">
            <b>正确填法：</b> 查看规格书中的 "Total Accuracy" 或 "Over Temperature" 数据。<br>
            例如 TL431：
            <ul>
                <li>常温 (25°C) 精度可能是 0.5%。</li>
                <li>全温范围 (-40~125°C) 精度可能变成 <b>1.5% 或 2.0%</b>。</li>
            </ul>
            <i>建议填写全温范围内的最大误差值。</i>
        </div>

        <h3>2. FB 偏置电流 (I_bias)</h3>
        <p>FB 引脚并不是理想断路，它有微小的漏电流。对于 MΩ 级的大电阻分压，这个电流会产生显著的电压误差。</p>
        <ul>
            <li><b>电流方向与符号：</b>
                <ul>
                    <li><b>流入 FB (Sink/In):</b> 电流从分压点流入芯片。这会分流 R1 的电流，导致分压点电压被拉低。为了维持 Vref，电源会提升输出电压。<b>(本工具按正值计算叠加)</b></li>
                    <li><b>流出 FB (Source/Out):</b> 电流从芯片流出到分压点。这会给 R2 额外充入电流，抬高分压点电压。电源会降低输出电压。</li>
                </ul>
            </li>
            <li><b>填法建议：</b> 查阅芯片手册的 $I_{FB}$ 或 $I_{bias}$ 参数。通常填写最大值 (Max)。本工具会自动按 +/- 双向极限计算最坏情况。</li>
        </ul>

        <h3>3. 电阻精度 (Resistor Tolerance)</h3>
        <p>除了标称精度 (1%, 0.1%)，还必须考虑<b>温漂 (TCR)</b> 和<b>老化</b>。</p>
        <div class="warn">
            <b>计算公式：</b> Total_Tol = Initial_Tol + (TCR * ΔT) + Aging<br>
            <b>案例：</b> 一个 1% 的电阻，TCR 为 100ppm/°C，温升 50°C。<br>
            误差 = 1% + (100e-6 * 50 * 100)% = 1% + 0.5% = <b>1.5%</b>。<br>
            <i>建议：WCA 分析时，电阻精度建议填 <b>1.5% ~ 2.0%</b> (针对普通厚膜电阻)。</i>
        </div>

        <h3>4. 计算原理</h3>
        <p>工具会排列组合以下极端情况，寻找 Vout 的最大值和最小值：</p>
        <ul>
            <li><b>Vout_max:</b> Vref(Max) + R1(Max) + R2(Min) + Ibias(Positive effect)</li>
            <li><b>Vout_min:</b> Vref(Min) + R1(Min) + R2(Max) + Ibias(Negative effect)</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        btn_close = QPushButton("我明白了")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec_()