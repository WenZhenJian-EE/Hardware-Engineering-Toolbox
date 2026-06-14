from modules.base_module import BaseModule
# battery_pack_bms.py

import math
from io import BytesIO
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QRadioButton, 
                             QButtonGroup, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class BatteryBmsWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "电池包 & BMS"
    description = "串并联配置 / 压降 / 均衡"
    window_id = "battery_pack"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('电池包与 BMS 设计工具 (Battery Pack & BMS)')
        self.setGeometry(350, 350, 1000, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Top Bar
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计指南：S/P配置与均衡原理")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(250)
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

        self.tab_pack = QWidget()
        self.tab_load = QWidget()
        self.tab_balance = QWidget()

        self.init_pack_ui(self.tab_pack)
        self.init_load_ui(self.tab_load)
        self.init_balance_ui(self.tab_balance)

        self.tabs.addTab(self.tab_pack, "1. 模组配置 (Series/Parallel)")
        self.tabs.addTab(self.tab_load, "2. 负载压降与温升 (Voltage Drop)")
        self.tabs.addTab(self.tab_balance, "3. 均衡电流估算 (Balancing)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 模组配置 (Pack Configuration)
    # ==============================================================================
    def init_pack_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 单体电芯参数
        grp_cell = QGroupBox("1. 单体电芯参数 (Cell Specs)")
        grid_c = QGridLayout()
        grid_c.setVerticalSpacing(12)
        
        self.cell_type = QComboBox()
        self.cell_type.addItems(["三元锂 (NMC) - 3.7V", "磷酸铁锂 (LFP) - 3.2V", "铅酸 (Lead-Acid) - 2V/12V", "钛酸锂 (LTO) - 2.4V", "自定义"])
        self.cell_type.currentIndexChanged.connect(self.on_cell_type_changed)
        grid_c.addWidget(QLabel("电芯类型:"), 0, 0); grid_c.addWidget(self.cell_type, 0, 1)
        
        self.cell_v_nom = QLineEdit("3.7"); grid_c.addWidget(QLabel("标称电压 [V]:"), 1, 0); grid_c.addWidget(self.cell_v_nom, 1, 1)
        self.cell_v_min = QLineEdit("2.8"); grid_c.addWidget(QLabel("放电截止 [V]:"), 1, 2); grid_c.addWidget(self.cell_v_min, 1, 3)
        self.cell_v_max = QLineEdit("4.2"); grid_c.addWidget(QLabel("充电截止 [V]:"), 1, 4); grid_c.addWidget(self.cell_v_max, 1, 5)
        
        self.cell_cap = QLineEdit("2.5"); self.cell_cap.setPlaceholderText("Ah")
        grid_c.addWidget(QLabel("单体容量 [Ah]:"), 2, 0); grid_c.addWidget(self.cell_cap, 2, 1)
        
        self.cell_ir = QLineEdit("20"); self.cell_ir.setToolTip("单体交流内阻 ACIR 或 直流内阻 DCIR")
        grid_c.addWidget(QLabel("单体内阻 [mΩ]:"), 2, 2); grid_c.addWidget(self.cell_ir, 2, 3)
        
        grp_cell.setLayout(grid_c)
        layout.addWidget(grp_cell)
        
        # 2. 模组目标与配置
        grp_conf = QGroupBox("2. 模组配置 (Pack Configuration)")
        grid_cf = QGridLayout()
        
        # 模式选择
        self.calc_mode = QButtonGroup()
        self.rb_sp = QRadioButton("已知 S/P -> 算总电压/容量"); self.rb_sp.setChecked(True)
        self.rb_target = QRadioButton("已知 目标电压/能量 -> 算 S/P")
        self.calc_mode.addButton(self.rb_sp); self.calc_mode.addButton(self.rb_target)
        self.calc_mode.buttonClicked.connect(self.update_pack_mode)
        
        hbox_mode = QHBoxLayout()
        hbox_mode.addWidget(self.rb_sp); hbox_mode.addWidget(self.rb_target); hbox_mode.addStretch()
        grid_cf.addLayout(hbox_mode, 0, 0, 1, 4)
        
        # S/P Inputs
        self.inp_s = QLineEdit("10"); self.lbl_s = QLabel("串联数 (S):")
        self.inp_p = QLineEdit("4");  self.lbl_p = QLabel("并联数 (P):")
        
        grid_cf.addWidget(self.lbl_s, 1, 0); grid_cf.addWidget(self.inp_s, 1, 1)
        grid_cf.addWidget(self.lbl_p, 1, 2); grid_cf.addWidget(self.inp_p, 1, 3)
        
        # Target Inputs (Hidden by default)
        self.inp_target_v = QLineEdit("48"); self.lbl_tv = QLabel("目标电压 [V]:")
        self.inp_target_e = QLineEdit("1000"); self.lbl_te = QLabel("目标能量 [Wh]:")
        
        grid_cf.addWidget(self.lbl_tv, 2, 0); grid_cf.addWidget(self.inp_target_v, 2, 1)
        grid_cf.addWidget(self.lbl_te, 2, 2); grid_cf.addWidget(self.inp_target_e, 2, 3)
        
        grp_conf.setLayout(grid_cf)
        layout.addWidget(grp_conf)
        
        btn_calc = QPushButton("计算模组参数")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn_calc.clicked.connect(self.calc_pack)
        layout.addWidget(btn_calc)
        
        # 3. 结果
        grp_res = QGroupBox("3. 电池包规格 (Pack Specification)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.res_v_range = QLineEdit(); r_grid.addWidget(QLabel("总电压范围 (Min-Nom-Max):"), 0, 0); r_grid.addWidget(self.res_v_range, 0, 1)
        self.res_cap = QLineEdit(); r_grid.addWidget(QLabel("总容量 (Capacity):"), 1, 0); r_grid.addWidget(self.res_cap, 1, 1)
        self.res_energy = QLineEdit(); r_grid.addWidget(QLabel("总能量 (Total Energy):"), 2, 0); r_grid.addWidget(self.res_energy, 2, 1)
        self.res_ir = QLineEdit(); r_grid.addWidget(QLabel("模组总内阻 (Pack IR):"), 3, 0); r_grid.addWidget(self.res_ir, 3, 1)
        self.res_config = QLineEdit(); r_grid.addWidget(QLabel("推荐构型 (Configuration):"), 4, 0); r_grid.addWidget(self.res_config, 4, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.res_v_range, self.res_cap, self.res_energy, self.res_ir, self.res_config]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.update_pack_mode()

    def on_cell_type_changed(self):
        txt = self.cell_type.currentText()
        if "3.7V" in txt:
            self.cell_v_nom.setText("3.7"); self.cell_v_min.setText("2.8"); self.cell_v_max.setText("4.2")
        elif "3.2V" in txt:
            self.cell_v_nom.setText("3.2"); self.cell_v_min.setText("2.5"); self.cell_v_max.setText("3.65")
        elif "Lead-Acid" in txt:
            self.cell_v_nom.setText("12.0"); self.cell_v_min.setText("10.5"); self.cell_v_max.setText("14.4")
        elif "2.4V" in txt:
            self.cell_v_nom.setText("2.3"); self.cell_v_min.setText("1.5"); self.cell_v_max.setText("2.8")

    def update_pack_mode(self):
        is_target = self.rb_target.isChecked()
        # S/P Input visibility
        self.inp_s.setVisible(not is_target); self.lbl_s.setVisible(not is_target)
        self.inp_p.setVisible(not is_target); self.lbl_p.setVisible(not is_target)
        # Target Input visibility
        self.inp_target_v.setVisible(is_target); self.lbl_tv.setVisible(is_target)
        self.inp_target_e.setVisible(is_target); self.lbl_te.setVisible(is_target)

    def calc_pack(self):
        try:
            v_nom = float(self.cell_v_nom.text())
            v_min = float(self.cell_v_min.text())
            v_max = float(self.cell_v_max.text())
            cap = float(self.cell_cap.text())
            ir = float(self.cell_ir.text()) / 1000.0 # mOhm -> Ohm
            
            s = 0; p = 0
            
            if self.rb_sp.isChecked():
                s = int(self.inp_s.text())
                p = int(self.inp_p.text())
            else:
                target_v = float(self.inp_target_v.text())
                target_wh = float(self.inp_target_e.text())
                if target_v <= 0 or target_wh <= 0: raise ValueError
                
                s = round(target_v / v_nom)
                if s < 1: s = 1
                
                # Total Ah needed = Wh / V_pack
                total_ah = target_wh / (s * v_nom)
                p = math.ceil(total_ah / cap)
                
            # Calculation
            pack_v_nom = s * v_nom
            pack_v_min = s * v_min
            pack_v_max = s * v_max
            
            pack_ah = p * cap
            pack_wh = pack_v_nom * pack_ah
            
            # Pack IR = (Cell_IR / P) * S (Simplified, neglecting busbars)
            pack_ir = (ir / p) * s
            
            self.res_v_range.setText(f"{pack_v_min:.1f}V - {pack_v_nom:.1f}V - {pack_v_max:.1f}V")
            self.res_cap.setText(f"{pack_ah:.2f} Ah")
            self.res_energy.setText(f"{pack_wh/1000:.2f} kWh ({pack_wh:.1f} Wh)")
            self.res_ir.setText(f"{pack_ir*1000:.2f} mΩ")
            self.res_config.setText(f"{s}S {p}P")
            
            # Pass data to other tabs
            self.current_pack_data = {
                's': s, 'p': p, 'v_nom': pack_v_nom, 'v_min': pack_v_min,
                'ah': pack_ah, 'ir': pack_ir
            }
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 2: 负载与压降分析 (Load Analysis)
    # ==============================================================================
    def init_load_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("提示：请先在 Tab 1 完成模组配置计算。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)
        
        grp_load = QGroupBox("1. 负载工况")
        grid = QGridLayout()
        
        self.load_curr = QLineEdit("50"); grid.addWidget(QLabel("负载电流 [A]:"), 0, 0); grid.addWidget(self.load_curr, 0, 1)
        self.load_power = QLineEdit("2000"); grid.addWidget(QLabel("或 负载功率 [W]:"), 0, 2); grid.addWidget(self.load_power, 0, 3)
        
        self.load_busbar_r = QLineEdit("5.0"); self.load_busbar_r.setToolTip("线束、铜排、接触器、熔断器等的总阻抗")
        grid.addWidget(QLabel("线束/连接总阻抗 [mΩ]:"), 1, 0); grid.addWidget(self.load_busbar_r, 1, 1)
        
        self.btn_use_curr = QRadioButton("按电流计算"); self.btn_use_curr.setChecked(True)
        self.btn_use_pwr = QRadioButton("按功率计算")
        bg = QButtonGroup(self); bg.addButton(self.btn_use_curr); bg.addButton(self.btn_use_pwr)
        
        hbox = QHBoxLayout(); hbox.addWidget(self.btn_use_curr); hbox.addWidget(self.btn_use_pwr); hbox.addStretch()
        grid.addLayout(hbox, 2, 0, 1, 4)
        
        grp_load.setLayout(grid)
        layout.addWidget(grp_load)
        
        btn = QPushButton("计算压降与C-Rate")
        btn.setFixedHeight(45); btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_load)
        layout.addWidget(btn)
        
        # Results
        grp_res = QGroupBox("2. 分析结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_crate = QLineEdit()
        self.res_v_drop_total = QLineEdit()
        self.res_v_terminal = QLineEdit()
        self.res_heat = QLineEdit()
        
        r_grid.addWidget(QLabel("放电倍率 (C-Rate):"), 0, 0); r_grid.addWidget(self.res_crate, 0, 1)
        r_grid.addWidget(QLabel("总压降 V_drop (内阻+线束):"), 1, 0); r_grid.addWidget(self.res_v_drop_total, 1, 1)
        r_grid.addWidget(QLabel("带载端口电压 V_terminal:"), 2, 0); r_grid.addWidget(self.res_v_terminal, 2, 1)
        r_grid.addWidget(QLabel("回路总发热功率 P_loss:"), 3, 0); r_grid.addWidget(self.res_heat, 3, 1)
        
        # Formula
        l_f = QLabel(); l_f.setPixmap(self.render_formula(r'V_{term} = V_{ocv} - I_{load} \cdot (R_{pack\_int} + R_{busbar})'))
        r_grid.addWidget(l_f, 0, 2, 4, 1)
        
        style = "background-color: #f4ecf7; font-weight: bold; color: #8e44ad;"
        for w in [self.res_crate, self.res_v_drop_total, self.res_v_terminal, self.res_heat]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_load(self):
        if not hasattr(self, 'current_pack_data'):
            QMessageBox.warning(self, "提示", "请先在 Tab 1 计算模组配置")
            return
            
        try:
            pack_ir = self.current_pack_data['ir'] # Ohm
            pack_ah = self.current_pack_data['ah']
            v_nom = self.current_pack_data['v_nom']
            
            r_bus = float(self.load_busbar_r.text()) / 1000.0 # Ohm
            
            current = 0.0
            if self.btn_use_curr.isChecked():
                current = float(self.load_curr.text())
            else:
                pwr = float(self.load_power.text())
                # Est current at nominal voltage
                current = pwr / v_nom 
            
            if current <= 0: return
            
            c_rate = current / pack_ah
            
            r_total = pack_ir + r_bus
            v_drop = current * r_total
            v_term = v_nom - v_drop
            
            p_heat = (current ** 2) * r_total
            
            self.res_crate.setText(f"{c_rate:.2f} C")
            self.res_v_drop_total.setText(f"{v_drop:.3f} V")
            self.res_v_terminal.setText(f"{v_term:.2f} V (Nominal)")
            self.res_heat.setText(f"{p_heat:.2f} W")
            
            if v_term < self.current_pack_data['v_min']:
                self.res_v_terminal.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
                self.res_v_terminal.setToolTip("警告：带载电压低于放电截止电压！")
            else:
                self.res_v_terminal.setStyleSheet("background-color: #f4ecf7; font-weight: bold; color: #8e44ad;")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    # ==============================================================================
    # Tab 3: 均衡计算 (Balancing)
    # ==============================================================================
    def init_balance_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_in = QGroupBox("1. 均衡需求 (Passive Balancing)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.bal_dv = QLineEdit("50"); self.bal_dv.setToolTip("电芯间最大电压差")
        grid.addWidget(QLabel("电压不平衡量 dV [mV]:"), 0, 0); grid.addWidget(self.bal_dv, 0, 1)
        
        self.bal_q = QLineEdit("5"); self.bal_q.setToolTip("估算的不平衡容量比例，通常 2~5%")
        grid.addWidget(QLabel("不平衡容量 Q_diff [%]:"), 0, 2); grid.addWidget(self.bal_q, 0, 3)
        
        self.bal_time = QLineEdit("5"); self.bal_time.setToolTip("期望在多少小时内完成均衡")
        grid.addWidget(QLabel("目标均衡时间 [Hours]:"), 1, 0); grid.addWidget(self.bal_time, 1, 1)
        
        self.bal_v_cell = QLineEdit("4.2"); self.bal_v_cell.setToolTip("均衡开启电压，通常为充电末端电压")
        grid.addWidget(QLabel("均衡开启电压 [V]:"), 1, 2); grid.addWidget(self.bal_v_cell, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算均衡电流与电阻")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_balance)
        layout.addWidget(btn)
        
        # Results
        grp_res = QGroupBox("2. 设计建议")
        r_grid = QGridLayout()
        
        self.res_ibal_req = QLineEdit()
        self.res_r_bleed = QLineEdit()
        self.res_p_bleed = QLineEdit()
        
        r_grid.addWidget(QLabel("所需均衡电流 I_bal:"), 0, 0); r_grid.addWidget(self.res_ibal_req, 0, 1)
        l_i = QLabel(); l_i.setPixmap(self.render_formula(r'I_{bal} = \frac{C_{pack} \cdot Q_{diff}\%}{Time}'))
        r_grid.addWidget(l_i, 0, 2)
        
        r_grid.addWidget(QLabel("推荐放电电阻 R_bleed:"), 1, 0); r_grid.addWidget(self.res_r_bleed, 1, 1)
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'R_{bleed} = \frac{V_{cell}}{I_{bal}}'))
        r_grid.addWidget(l_r, 1, 2)
        
        r_grid.addWidget(QLabel("电阻功率 P_res:"), 2, 0); r_grid.addWidget(self.res_p_bleed, 2, 1)
        r_grid.addWidget(QLabel("注意：此功率将在 PCB 上发热"), 2, 2)
        
        style = "background-color: #fdf2e9; font-weight: bold; color: #d35400;"
        for w in [self.res_ibal_req, self.res_r_bleed, self.res_p_bleed]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_balance(self):
        try:
            # Need Pack Capacity
            if not hasattr(self, 'current_pack_data'):
                # Try to read from Tab 1 if simple calc
                try:
                    cap = float(self.cell_cap.text()) * int(self.inp_p.text())
                except:
                    cap = float(self.cell_cap.text()) # Default to 1P if error
            else:
                cap = self.current_pack_data['ah']
            
            q_diff_pct = float(self.bal_q.text()) / 100.0
            time_h = float(self.bal_time.text())
            v_cell = float(self.bal_v_cell.text())
            
            if time_h <= 0: raise ValueError
            
            # Ah needed to bleed
            ah_bleed = cap * q_diff_pct
            
            # Current needed
            i_bal = ah_bleed / time_h # Amps
            
            # Resistor
            r_bleed = v_cell / i_bal if i_bal > 0 else 0
            
            # Power
            p_bleed = i_bal * v_cell
            
            self.res_ibal_req.setText(f"{i_bal*1000:.1f} mA")
            self.res_r_bleed.setText(f"{r_bleed:.1f} Ω")
            self.res_p_bleed.setText(f"{p_bleed:.2f} W")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("电池包设计原理")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        html = """
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
        </style>
        <h1>电池包 (Battery Pack) 设计基础</h1>
        
        <h2>1. 串并联配置 (S & P)</h2>
        <ul>
            <li><b>串联 (Series, S):</b> 增加电压。Pack Voltage = Cell Voltage * S。容量 (Ah) 不变。</li>
            <li><b>并联 (Parallel, P):</b> 增加容量。Pack Capacity = Cell Capacity * P。电压不变。</li>
            <li><b>总能量 (Wh):</b> Wh = V * Ah = (V_cell * S) * (Ah_cell * P)。</li>
        </ul>

        <h2>2. 内阻与压降</h2>
        <p>电池包不仅是理想电压源，它有内阻。大电流放电时，内阻会导致端电压下降 (Voltage Sag) 和发热。</p>
        <p><code>V_terminal = V_ocv - I_load * (R_cells + R_busbars)</code></p>
        <p>设计时必须考虑 Busbar (铜排) 和连接器接触电阻，它们往往占据总内阻的 30%~50%。</p>

        <h2>3. 均衡 (Balancing)</h2>
        <p>由于制造工艺差异，电芯容量和自放电率不可能完全一致。随着充放电循环，串联电芯会出现电压不一致。</p>
        <ul>
            <li><b>被动均衡 (Passive):</b> 利用电阻将电压高的电芯能量消耗掉（发热）。简单、成本低，适用于小电流均衡 (通常 < 100mA)。</li>
            <li><b>均衡电流计算：</b> 假设电芯差异为 5%，希望在充电末端的 2小时内平衡掉差异。
                <br><code>I_bal = (Capacity * 5%) / 2h</code>。
                <br>例如 100Ah 电池，差异 5Ah，2小时平衡需要 2.5A 电流！这对于被动均衡是不现实的，大容量电池通常需要主动均衡或更严格的电芯配对。
            </li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()