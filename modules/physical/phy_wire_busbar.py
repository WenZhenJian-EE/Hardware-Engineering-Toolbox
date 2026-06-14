from modules.base_module import BaseModule
# wire_calculator_window.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from io import BytesIO

# ==============================================================================
# Helper Dialogs
# ==============================================================================

class MTLCalculatorDialog(QDialog):
    """单圈平均长度 (MTL) 计算助手"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MTL (单圈平均长度) 计算器")
        self.setGeometry(400, 400, 500, 350)
        self.result_val = 0.0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 骨架类型选择
        self.tabs = QTabWidget()
        self.tab_round = QWidget()
        self.tab_rect = QWidget()
        
        self.init_round_ui(self.tab_round)
        self.init_rect_ui(self.tab_rect)
        
        self.tabs.addTab(self.tab_round, "圆形中柱 (EC/ETD/PQ/RM)")
        self.tabs.addTab(self.tab_rect, "矩形中柱 (EE/EI/EF)")
        
        layout.addWidget(self.tabs)
        
        # 结果显示区
        res_group = QGroupBox("计算结果")
        res_layout = QHBoxLayout()
        self.lbl_res = QLabel("MTL = 0.00 mm")
        self.lbl_res.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60;")
        res_layout.addWidget(self.lbl_res)
        res_group.setLayout(res_layout)
        
        # 确定按钮
        btn_ok = QPushButton("使用此结果")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)
        
        self.setLayout(layout)

    def init_round_ui(self, tab):
        form = QGridLayout()
        self.r_d = QLineEdit("10.0"); self.r_d.setPlaceholderText("骨架中柱直径")
        self.r_h = QLineEdit("2.0"); self.r_h.setPlaceholderText("绕组厚度 (Build)")
        
        form.addWidget(QLabel("骨架中柱直径 (D) [mm]:"), 0, 0); form.addWidget(self.r_d, 0, 1)
        form.addWidget(QLabel("绕组厚度/层厚 (H) [mm]:"), 1, 0); form.addWidget(self.r_h, 1, 1)
        
        btn_calc = QPushButton("计算"); btn_calc.clicked.connect(self.calc_round)
        form.addWidget(btn_calc, 2, 0, 1, 2)
        
        # 图示说明
        lbl_tip = QLabel("公式: MTL ≈ π * (D + H)\n(假设绕组处于中间位置平均值)")
        lbl_tip.setStyleSheet("color: gray; font-style: italic;")
        form.addWidget(lbl_tip, 3, 0, 1, 2)
        
        tab.setLayout(form)

    def init_rect_ui(self, tab):
        form = QGridLayout()
        self.sq_a = QLineEdit("10.0"); self.sq_a.setPlaceholderText("骨架长边")
        self.sq_b = QLineEdit("10.0"); self.sq_b.setPlaceholderText("骨架短边")
        self.sq_h = QLineEdit("2.0"); self.sq_h.setPlaceholderText("绕组厚度")
        
        form.addWidget(QLabel("骨架长边 (A) [mm]:"), 0, 0); form.addWidget(self.sq_a, 0, 1)
        form.addWidget(QLabel("骨架短边 (B) [mm]:"), 1, 0); form.addWidget(self.sq_b, 1, 1)
        form.addWidget(QLabel("绕组厚度 (H) [mm]:"), 2, 0); form.addWidget(self.sq_h, 2, 1)
        
        btn_calc = QPushButton("计算"); btn_calc.clicked.connect(self.calc_rect)
        form.addWidget(btn_calc, 3, 0, 1, 2)
        
        lbl_tip = QLabel("公式: MTL ≈ 2*(A + B) + π*H\n(考虑转角处的圆弧效应)")
        lbl_tip.setStyleSheet("color: gray; font-style: italic;")
        form.addWidget(lbl_tip, 4, 0, 1, 2)
        
        tab.setLayout(form)

    def calc_round(self):
        try:
            d = float(self.r_d.text()); h = float(self.r_h.text())
            mtl = math.pi * (d + h)
            self.result_val = mtl
            self.lbl_res.setText(f"MTL = {mtl:.2f} mm")
        except: pass

    def calc_rect(self):
        try:
            a = float(self.sq_a.text()); b = float(self.sq_b.text()); h = float(self.sq_h.text())
            mtl = 2 * (a + b) + math.pi * h
            self.result_val = mtl
            self.lbl_res.setText(f"MTL = {mtl:.2f} mm")
        except: pass


class LitzOptimizerDialog(QDialog):
    """利兹线频率-线径扫描优化器"""
    def __init__(self, freq_khz, i_rms, temp, litz_options, parent=None):
        super().__init__(parent)
        self.freq_khz = freq_khz
        self.i_rms = i_rms
        self.temp = temp
        self.litz_options = litz_options
        self.setWindowTitle(f"利兹线径优化扫描 (f={freq_khz}kHz, I={i_rms}A)")
        self.resize(1000, 700)
        self.init_ui()
        self.run_optimization()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 说明
        info_label = QLabel("优化逻辑：固定目标电流密度(总铜截面)，扫描不同单股线径下的 AC损耗(趋肤) 与 填充损耗(漆皮占比)。\n"
                            "目标：寻找总损耗最低的 'Sweet Spot' 线径。")
        info_label.setStyleSheet("background-color: #e8f8f5; padding: 10px; border-radius: 5px; color: #2c3e50;")
        layout.addWidget(info_label)

        # 图表区域
        self.figure = plt.figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["单股线径 (mm)", "AWG", "需要股数", "AC系数 (Fr)", "总损耗 (相对)", "评价"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def run_optimization(self):
        f = self.freq_khz * 1000
        rho_20 = 1.7241e-8
        rho_cu_t = rho_20 * (1 + 0.00393 * (self.temp - 20))
        mu0 = 4 * math.pi * 1e-7
        
        # 趋肤深度
        delta = math.sqrt(rho_cu_t / (math.pi * f * mu0)) # m
        delta_mm = delta * 1000
        
        # 目标总铜截面 (假设 J = 4A/mm2 作为基准，实际上只要固定截面，比较相对值即可)
        # 为了让比较有意义，我们固定总铜截面 A_total
        j_target = 4.0 # A/mm2
        a_total_target = self.i_rms / j_target # mm2
        
        results = []
        d_list = []
        loss_list = []
        
        # 遍历线径
        # self.litz_options 结构: [(0.511, "AWG 24"), ...] 从粗到细
        # 我们反转一下，让图表从左到右是线径从小到大，或者保持线径从大到小
        sorted_options = sorted(self.litz_options, key=lambda x: x[0], reverse=True) 

        best_loss = float('inf')
        best_cfg = None

        self.table.setRowCount(len(sorted_options))

        for row, (d_mm, name) in enumerate(sorted_options):
            # 1. 计算股数
            a_strand = math.pi * (d_mm / 2)**2
            n_strands = math.ceil(a_total_target / a_strand)
            
            # 2. 修正 DC 电阻 (漆皮效应)
            # 线越细，漆皮占比越大，为了达到同样的纯铜截面，实际线束更粗，
            # 或者说在同样空间内，细线能放进去的纯铜更少。
            # 这里简单模拟：假设绝缘层厚度固定 (例如 0.005mm)，计算铜占比因子
            insulation_thk = 0.003 + 0.0005 * (0.5/d_mm) # 简易模型：越细漆皮相对越厚
            d_over = d_mm + 2*insulation_thk
            fill_factor = (d_mm / d_over)**2 # 仅考虑单根线的漆皮损失
            
            # Rdc = rho * L / (N * A_strand)
            # 我们比较单位长度损耗 P_dc_unit ~ 1/A_total_real
            # 但这里 A_total_real = n_strands * a_strand ≈ a_total_target
            # 所以基础 DC 损耗主要受 "股数取整" 影响，差异不大。
            # 为了体现细线的劣势，我们引入 "成本/绞合 因子" 或者 "填充率惩罚"
            # 实际上：极细的线 Rdc 是一样的，但 AC 损耗低。
            # 现实是：极细线 (0.04mm) 极贵且难焊。我们仅计算物理损耗。
            
            # AC Resistance Factor
            # x = d / (sqrt(2) * delta)
            x_val = d_mm / (math.sqrt(2) * delta_mm)
            fr = 1.0 + (x_val**4) / (48.0 + 0.8 * (x_val**4))
            
            # Total Loss proportional to Fr
            # P_total = I^2 * Rdc * Fr
            # 假设 Rdc 相同 (忽略微小差异)，则 P_total ~ Fr
            
            # 但等等，如果 d >> delta，Fr 会暴增。
            # 如果 d << delta，Fr ~ 1。
            # 那岂不是线越细越好？是的，物理上是这样。
            # 所谓 "甜点" 通常是 "损耗够低" 且 "线径不太细(便于加工)" 的平衡点。
            # 或者当考虑 "邻近效应" 时，细线并不总是最好，因为股数太多导致线圈整体变大，场强变强。
            # 简单的单根趋肤模型无法完全反映利兹线优势，需要加上 "邻近效应 (Proximity Effect)"。
            # 简易邻近效应估算：G * (d/delta)^4 * ...
            # 我们可以加一个简单的惩罚项来模拟工程上的 "过细惩罚" (比如填充率下降导致 Rdc 实际增加)
            
            # 修正 Rdc：越细的线，编织后的空隙越大，实际 Rdc 会比理论值高 
            # 假设填充系数罚函数: penalty = 1 + 0.01 / d_mm
            rdc_penalty = 1.0 + (0.02 / d_mm) 
            
            loss_score = rdc_penalty * fr
            
            results.append((d_mm, name, n_strands, fr, loss_score))
            d_list.append(d_mm)
            loss_list.append(loss_score)
            
            if loss_score < best_loss:
                best_loss = loss_score
                best_cfg = (d_mm, n_strands, name)

            # Fill Table
            self.table.setItem(row, 0, QTableWidgetItem(f"{d_mm:.3f}"))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(n_strands)))
            self.table.setItem(row, 3, QTableWidgetItem(f"{fr:.3f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{loss_score:.3f}"))
            
            eval_str = ""
            if d_mm > 2 * delta_mm:
                eval_str = "❌ 严重趋肤"
                item_color = Qt.red
            elif d_mm < 0.05:
                eval_str = "⚠️ 加工困难"
                item_color = Qt.darkYellow
            else:
                eval_str = "✅ 可用"
                item_color = Qt.black
                
            item = QTableWidgetItem(eval_str)
            item.setForeground(item_color)
            self.table.setItem(row, 5, item)

        # Plot
        ax = self.figure.add_subplot(111)
        ax.plot(d_list, loss_list, 'b-o', label='Relative Loss Index')
        ax.set_xlabel('Strand Diameter (mm)')
        ax.set_ylabel('Loss Index (DC penalty * AC factor)')
        ax.set_title(f'Optimization: Best @ {best_cfg[0]}mm ({best_cfg[2]})\nDelta={delta_mm:.3f}mm')
        ax.grid(True)
        ax.invert_xaxis() # 大线径在左，小线径在右 (符合 AWG 习惯)
        
        # Mark Best
        ax.plot(best_cfg[0], best_loss, 'r*', markersize=15, label='Sweet Spot')
        ax.legend()
        
        self.canvas.draw()
        
        # Highlight best in table
        # (Optional implementation)


# ==============================================================================
# Main Window
# ==============================================================================

class WireCalculatorWindow(BaseModule):
    category = "5. 无源器件与物理连接 (Passives & Physical)"
    display_name = "线缆与铜排"
    description = "磁芯中柱 / 利兹线 / AWG / 铜排"
    window_id = "phy_wire"

    def init_module_ui(self):
        
        # 定义利兹线常用的 AWG 规格数据 (线径 mm, 名称)
        self.litz_awg_options = [
            (0.511, "AWG 24"), (0.455, "AWG 25"),
            (0.404, "AWG 26"), (0.361, "AWG 27"),
            (0.321, "AWG 28"), (0.286, "AWG 29"),
            (0.254, "AWG 30"), (0.227, "AWG 31"),
            (0.203, "AWG 32"), (0.180, "AWG 33"),
            (0.160, "AWG 34"), (0.143, "AWG 35"),
            (0.127, "AWG 36"), (0.113, "AWG 37"),
            (0.102, "AWG 38"), (0.089, "AWG 39"),
            (0.079, "AWG 40"), (0.071, "AWG 41"),
            (0.063, "AWG 42"), (0.056, "AWG 43"),
            (0.051, "AWG 44"), (0.045, "AWG 45"),
            (0.040, "AWG 46")
        ]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('导线/铜排/利兹线 & 线损计算工具')
        self.setGeometry(350, 350, 950, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("载流、趋肤效应与损耗计算指南")
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

        self.tab_litz = QWidget()
        self.tab_awg = QWidget()
        self.tab_busbar = QWidget()

        self.init_litz_ui(self.tab_litz)
        self.init_awg_ui(self.tab_awg)
        self.init_busbar_ui(self.tab_busbar)

        self.tabs.addTab(self.tab_litz, "利兹线设计 (Litz & Coil Loss)")
        self.tabs.addTab(self.tab_awg, "AWG/圆导线载流 (低频/DC)")
        self.tabs.addTab(self.tab_busbar, "铜排 (Busbar) 载流估算")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: 利兹线设计 (Litz Wire Design) & 线损计算
    # ==============================================================================
    def init_litz_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 输入参数
        grp_in = QGroupBox(" 1. 设计条件")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.lz_freq = QLineEdit("100"); grid.addWidget(QLabel("工作频率 (f) [kHz]:"), 0, 0); grid.addWidget(self.lz_freq, 0, 1)
        self.lz_curr = QLineEdit("5.0"); grid.addWidget(QLabel("总有效电流 (I_rms) [A]:"), 0, 2); grid.addWidget(self.lz_curr, 0, 3)
        
        self.lz_j = QLineEdit("4.0"); 
        self.lz_j.setToolTip("电流密度。风冷通常 3~5 A/mm²，自然冷却 2~3 A/mm²")
        grid.addWidget(QLabel("电流密度 (J) [A/mm²]:"), 1, 0); grid.addWidget(self.lz_j, 1, 1)
        
        grid.addWidget(QLabel("材质: 铜 (Copper @ 100°C)"), 1, 2, 1, 2)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        
        self.btn_auto_calc = QPushButton("自动推荐 (Basic)")
        self.btn_auto_calc.setFixedHeight(45)
        self.btn_auto_calc.clicked.connect(self.calc_litz_auto)
        
        # New Optimizer Button
        self.btn_optimizer = QPushButton("频率-线径扫描优化 (Optimizer)")
        self.btn_optimizer.setFixedHeight(45)
        self.btn_optimizer.setFont(QFont('Arial', 10, QFont.Bold))
        self.btn_optimizer.setStyleSheet("background-color: #8e44ad; color: white;")
        self.btn_optimizer.clicked.connect(self.open_optimizer)
        
        self.btn_recalc = QPushButton("刷新计算 (Refresh)")
        self.btn_recalc.setFixedHeight(45)
        self.btn_recalc.clicked.connect(self.update_strand_calculation)
        
        btn_layout.addWidget(self.btn_auto_calc, 1)
        btn_layout.addWidget(self.btn_optimizer, 2)
        btn_layout.addWidget(self.btn_recalc, 1)
        layout.addLayout(btn_layout)
        
        # 2. 选型结果
        grp_res = QGroupBox(" 2. 选型结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        r_grid.setColumnStretch(1, 1)
        
        # 趋肤深度
        self.lz_depth = QLineEdit(); r_grid.addWidget(QLabel("趋肤深度 (Skin Depth):"), 0, 0); r_grid.addWidget(self.lz_depth, 0, 1)
        l_form = QLabel(); l_form.setPixmap(self.render_formula(r'\delta \approx \frac{66 \sim 72}{\sqrt{f}} \text{ (mm)}'))
        r_grid.addWidget(l_form, 0, 2)
        
        # 最大建议线径
        self.lz_max_rec = QLineEdit(); self.lz_max_rec.setStyleSheet("color: #e67e22; font-weight: bold; background-color: #fdf2e9;")
        r_grid.addWidget(QLabel("最大建议单股线径 (2δ):"), 1, 0); r_grid.addWidget(self.lz_max_rec, 1, 1)
        r_grid.addWidget(QLabel("物理限制，请勿超过此值"), 1, 2)

        # 单股线径选择
        self.lz_strand_combo = QComboBox()
        for dia, name in self.litz_awg_options:
            self.lz_strand_combo.addItem(f"{name} ({dia}mm)", dia)
        self.lz_strand_combo.addItem("自定义...", -1)
        self.lz_strand_combo.currentIndexChanged.connect(self.on_combo_changed)
        
        r_grid.addWidget(QLabel("选择单股线径 (Strand):"), 2, 0); r_grid.addWidget(self.lz_strand_combo, 2, 1)
        
        # 自定义直径输入框
        self.lz_custom_dia = QLineEdit()
        self.lz_custom_dia.setPlaceholderText("输入直径(mm)")
        self.lz_custom_dia.setVisible(False)
        self.lz_custom_dia.textChanged.connect(self.update_strand_calculation)
        r_grid.addWidget(self.lz_custom_dia, 2, 1)
        
        # 状态警告标签
        self.lz_warn_label = QLabel("Waiting...")
        r_grid.addWidget(self.lz_warn_label, 2, 2)
        
        # 总截面
        self.lz_total_area = QLineEdit(); r_grid.addWidget(QLabel("所需总铜截面积:"), 3, 0); r_grid.addWidget(self.lz_total_area, 3, 1)
        
        # 股数建议
        self.lz_strands_count = QLineEdit(); r_grid.addWidget(QLabel("需要股数 (Strands):"), 4, 0); r_grid.addWidget(self.lz_strands_count, 4, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_count = "background-color: #fff8e1; font-weight: bold; color: #d35400; font-size: 16px;"
        
        for w in [self.lz_depth, self.lz_max_rec, self.lz_total_area]: w.setReadOnly(True); w.setStyleSheet(style)
        self.lz_strands_count.setReadOnly(True); self.lz_strands_count.setStyleSheet(style_count)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 3. 线圈损耗估算
        grp_loss = QGroupBox(" 3. 线圈损耗估算 (Coil Loss Estimation)")
        l_grid = QGridLayout()
        l_grid.setVerticalSpacing(12) 
        
        # --- 3.1 绕组长度计算助手 ---
        helper_frame = QGroupBox("3.1 绕组长度计算助手 (Length Helper)")
        helper_frame.setStyleSheet("""
            QGroupBox { border: 1px dashed #bdc3c7; margin-top: 20px; padding-top: 15px; } 
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 10px; padding: 0 3px; color: #7f8c8d; }
        """)
        
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(10, 15, 10, 10) 
        
        self.lz_help_mtl = QLineEdit("35"); self.lz_help_mtl.setPlaceholderText("单圈平均长度(mm)")
        self.lz_help_n = QLineEdit("40"); self.lz_help_n.setPlaceholderText("匝数 (Turns)")
        
        btn_open_mtl = QPushButton("不知道MTL? 计算器")
        btn_open_mtl.setStyleSheet("background-color: #f39c12; color: white; border-radius: 3px; padding: 3px 8px; font-weight: bold;")
        btn_open_mtl.clicked.connect(self.open_mtl_calculator)
        
        btn_calc_len = QPushButton("计算总长 ->")
        btn_calc_len.setStyleSheet("background-color: #3498db; color: white; border-radius: 3px; padding: 3px 8px;")
        btn_calc_len.clicked.connect(self.calc_len_from_turns)
        
        h_layout.addWidget(QLabel("单圈长(MTL) [mm]:")); h_layout.addWidget(self.lz_help_mtl)
        h_layout.addWidget(btn_open_mtl)
        h_layout.addWidget(QLabel("匝数:")); h_layout.addWidget(self.lz_help_n)
        h_layout.addWidget(btn_calc_len)
        helper_frame.setLayout(h_layout)
        l_grid.addWidget(helper_frame, 0, 0, 1, 4)
        
        # --- 3.2 损耗计算 ---
        self.lz_len = QLineEdit("1.4"); l_grid.addWidget(QLabel("绕组总长度 [m]:"), 1, 0); l_grid.addWidget(self.lz_len, 1, 1)
        self.lz_temp = QLineEdit("100"); l_grid.addWidget(QLabel("工作温度 [°C]:"), 1, 2); l_grid.addWidget(self.lz_temp, 1, 3)
        
        # --- AC Factor Calculation ---
        l_grid.addWidget(QLabel("AC系数 (Rac/Rdc):"), 2, 0)
        
        h_ac_box = QHBoxLayout()
        self.lz_ac_factor = QLineEdit("1.2")
        self.lz_ac_factor.setToolTip("交流电阻系数。点击右侧按钮可自动计算单根导线的趋肤效应系数。")
        h_ac_box.addWidget(self.lz_ac_factor)
        
        self.lz_calc_skin_btn = QPushButton("计算趋肤系数")
        self.lz_calc_skin_btn.setStyleSheet("background-color: #e67e22; color: white; border-radius: 3px; padding: 2px 5px;")
        self.lz_calc_skin_btn.setFixedWidth(90)
        self.lz_calc_skin_btn.clicked.connect(self.auto_calc_skin_factor)
        h_ac_box.addWidget(self.lz_calc_skin_btn)
        
        l_grid.addLayout(h_ac_box, 2, 1)
        
        self.lz_skin_res_lbl = QLabel("(Fr = ?)")
        self.lz_skin_res_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        l_grid.addWidget(self.lz_skin_res_lbl, 2, 2)
        
        btn_calc_loss = QPushButton("计算损耗 (P_loss)")
        btn_calc_loss.setFixedHeight(35)
        btn_calc_loss.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_calc_loss.clicked.connect(self.update_strand_calculation)
        l_grid.addWidget(btn_calc_loss, 2, 3)
        
        self.lz_rdc = QLineEdit(); self.lz_rdc.setReadOnly(True)
        self.lz_p_loss = QLineEdit(); self.lz_p_loss.setReadOnly(True)
        self.lz_p_loss.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold; font-size: 14px;")
        
        l_grid.addWidget(QLabel("直流电阻 R_dc [Ω]:"), 3, 0); l_grid.addWidget(self.lz_rdc, 3, 1)
        l_grid.addWidget(QLabel("总损耗 P_loss [W]:"), 3, 2); l_grid.addWidget(self.lz_p_loss, 3, 3)
        
        l_grid.addWidget(QLabel("注：P_loss = I_rms² × R_dc × AC系数 (AC系数建议包含邻近效应余量)"), 4, 0, 1, 4)
        
        grp_loss.setLayout(l_grid)
        layout.addWidget(grp_loss)
        
        layout.addStretch()
        tab.setLayout(layout)

    def open_mtl_calculator(self):
        """打开 MTL 计算弹窗"""
        dlg = MTLCalculatorDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.lz_help_mtl.setText(f"{dlg.result_val:.2f}")
            self.calc_len_from_turns()

    def open_optimizer(self):
        """打开优化扫描器"""
        try:
            f = float(self.lz_freq.text())
            i = float(self.lz_curr.text())
            t = float(self.lz_temp.text())
            dlg = LitzOptimizerDialog(f, i, t, self.litz_awg_options, self)
            dlg.exec_()
        except Exception as e:
            QMessageBox.warning(self, "Input Error", "请先输入有效的频率和电流值")

    def calc_len_from_turns(self):
        try:
            mtl = float(self.lz_help_mtl.text())
            n = float(self.lz_help_n.text())
            total_len_m = mtl * n / 1000.0
            self.lz_len.setText(f"{total_len_m:.3f}")
            self.update_strand_calculation() 
        except: pass

    def on_combo_changed(self):
        if self.lz_strand_combo.currentData() == -1:
            self.lz_custom_dia.setVisible(True)
            self.lz_warn_label.setText("请输入直径")
        else:
            self.lz_custom_dia.setVisible(False)
            self.update_strand_calculation()

    def auto_calc_skin_factor(self):
        self.update_strand_calculation(update_ac_input=True)

    def calc_litz_auto(self):
        try:
            f_khz = float(self.lz_freq.text())
            f = f_khz * 1000
            
            delta_mm = 72.0 / math.sqrt(f)
            max_rec_dia = 2 * delta_mm
            
            self.lz_depth.setText(f"{delta_mm:.4f} mm")
            self.lz_max_rec.setText(f"{max_rec_dia:.4f} mm")
            
            found_idx = -1
            # 列表可能未排序，但通常是粗到细
            # 找第一个满足 dia <= max_rec 的
            for i, (dia, name) in enumerate(self.litz_awg_options):
                if dia <= max_rec_dia:
                    found_idx = i
                    break
            
            if found_idx == -1: found_idx = len(self.litz_awg_options) - 1
            
            self.lz_strand_combo.blockSignals(True)
            self.lz_strand_combo.setCurrentIndex(found_idx)
            self.lz_strand_combo.blockSignals(False)
            
            self.lz_custom_dia.setVisible(False)
            self.update_strand_calculation()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def update_strand_calculation(self, update_ac_input=False):
        try:
            i_rms = float(self.lz_curr.text())
            j = float(self.lz_j.text())
            f_khz = float(self.lz_freq.text())
            length = float(self.lz_len.text())
            temp = float(self.lz_temp.text())
            
            if i_rms <= 0 or j <= 0: return
            
            a_total = i_rms / j
            self.lz_total_area.setText(f"{a_total:.3f} mm²")
            
            if self.lz_strand_combo.currentData() == -1:
                try:
                    strand_dia = float(self.lz_custom_dia.text())
                except: return
            else:
                idx = self.lz_strand_combo.currentIndex()
                strand_dia = self.litz_awg_options[idx][0]
            
            if strand_dia <= 0: return

            delta_mm_disp = 72.0 / math.sqrt(f_khz * 1000)
            max_dia = 2 * delta_mm_disp
            self.lz_depth.setText(f"{delta_mm_disp:.4f} mm")
            self.lz_max_rec.setText(f"{max_dia:.4f} mm")
            
            if strand_dia > max_dia:
                self.lz_warn_label.setText("❌ 线径过粗！")
                self.lz_warn_label.setStyleSheet("color: red; font-weight: bold;")
                self.lz_strands_count.setStyleSheet("background-color: #ffebee; color: red;") 
            else:
                self.lz_warn_label.setText("✅ 线径合适")
                self.lz_warn_label.setStyleSheet("color: green; font-weight: bold;")
                self.lz_strands_count.setStyleSheet("background-color: #fff8e1; color: #d35400;") 

            a_strand = math.pi * (strand_dia / 2)**2
            n_strands = math.ceil(a_total / a_strand)
            self.lz_strands_count.setText(f"{n_strands} 股")
            
            # Skin Factor
            rho_cu_t = 1.7241e-8 * (1 + 0.00393 * (temp - 20))
            f_hz = f_khz * 1000
            mu0 = 4 * math.pi * 1e-7
            
            delta_m = math.sqrt(rho_cu_t / (math.pi * f_hz * mu0))
            delta_mm_real = delta_m * 1000.0
            
            x_val = strand_dia / (math.sqrt(2) * delta_mm_real)
            fr_skin = 1.0 + (x_val**4) / (48.0 + 0.8 * (x_val**4))
            
            self.lz_skin_res_lbl.setText(f"(Fr_skin ≈ {fr_skin:.3f})")
            
            if update_ac_input:
                self.lz_ac_factor.setText(f"{fr_skin:.3f}")
            
            real_total_area = n_strands * a_strand
            rdc = rho_cu_t * length / (real_total_area * 1e-6)
            
            ac_k_user = float(self.lz_ac_factor.text())
            ploss = (i_rms ** 2) * rdc * ac_k_user
            
            self.lz_rdc.setText(f"{rdc:.4f}")
            self.lz_p_loss.setText(f"{ploss:.3f}")
                    
        except:
            pass 

    # ==============================================================================
    # Tab 2: AWG / Wire Calculator
    # ==============================================================================
    def init_awg_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # AWG Selection
        grp_sel = QGroupBox(" 1. 导线规格选择") # 加了空格
        grid = QGridLayout()
        
        self.awg_combo = QComboBox()
        # Common AWG sizes
        awgs = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
        for a in awgs: self.awg_combo.addItem(f"AWG {a}", a)
        self.awg_combo.addItem("自定义直径 (mm)", -1)
        self.awg_combo.setCurrentText("AWG 18")
        self.awg_combo.currentIndexChanged.connect(self.on_awg_changed)
        
        grid.addWidget(QLabel("标准线规:"), 0, 0); grid.addWidget(self.awg_combo, 0, 1)
        
        self.w_dia = QLineEdit("1.024")
        self.w_area = QLineEdit("0.823")
        self.w_area.setReadOnly(True); self.w_area.setStyleSheet("background-color: #f0f0f0;")
        
        grid.addWidget(QLabel("直径 (Diameter) [mm]:"), 1, 0); grid.addWidget(self.w_dia, 1, 1)
        grid.addWidget(QLabel("截面积 (Area) [mm²]:"), 1, 2); grid.addWidget(self.w_area, 1, 3)
        
        grp_sel.setLayout(grid)
        layout.addWidget(grp_sel)
        
        # Conditions
        grp_cond = QGroupBox(" 2. 工作条件") # 加了空格
        c_grid = QGridLayout()
        
        self.w_curr = QLineEdit("5.0"); c_grid.addWidget(QLabel("工作电流 [A]:"), 0, 0); c_grid.addWidget(self.w_curr, 0, 1)
        self.w_len = QLineEdit("1.0"); c_grid.addWidget(QLabel("导线长度 [m]:"), 0, 2); c_grid.addWidget(self.w_len, 0, 3)
        self.w_temp = QLineEdit("25"); c_grid.addWidget(QLabel("环境温度 [°C]:"), 1, 0); c_grid.addWidget(self.w_temp, 1, 1)
        self.w_mat = QComboBox(); self.w_mat.addItems(["铜 (Copper)", "铝 (Aluminum)"])
        c_grid.addWidget(QLabel("材质:"), 1, 2); c_grid.addWidget(self.w_mat, 1, 3)
        
        grp_cond.setLayout(c_grid)
        layout.addWidget(grp_cond)
        
        btn = QPushButton("计算压降与功率")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_wire)
        layout.addWidget(btn)
        
        # Results
        grp_res = QGroupBox(" 3. 结果与安规参考") # 加了空格
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.w_res = QLineEdit(); r_grid.addWidget(QLabel("导线总电阻 R [Ω]:"), 0, 0); r_grid.addWidget(self.w_res, 0, 1)
        self.w_vdrop = QLineEdit(); r_grid.addWidget(QLabel("电压降 Vdrop [V]:"), 1, 0); r_grid.addWidget(self.w_vdrop, 1, 1)
        self.w_ploss = QLineEdit(); r_grid.addWidget(QLabel("功率损耗 Ploss [W]:"), 2, 0); r_grid.addWidget(self.w_ploss, 2, 1)
        
        # Ampacity Info
        self.w_amp_chassis = QLineEdit(); self.w_amp_trans = QLineEdit()
        r_grid.addWidget(QLabel("参考载流 (机箱布线):"), 0, 2); r_grid.addWidget(self.w_amp_chassis, 0, 3)
        r_grid.addWidget(QLabel("参考载流 (电力传输):"), 1, 2); r_grid.addWidget(self.w_amp_trans, 1, 3)
        
        lbl_tip = QLabel("注：参考载流基于 NEC 标准估算 (Chassis保守/Transmission多芯)。\n压降建议控制在工作电压的 3% 以内。")
        lbl_tip.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        r_grid.addWidget(lbl_tip, 2, 2, 1, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #2980b9;"
        for w in [self.w_res, self.w_vdrop, self.w_ploss, self.w_amp_chassis, self.w_amp_trans]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)
        
        self.w_dia.textChanged.connect(self.on_dia_changed)

    def on_awg_changed(self):
        data = self.awg_combo.currentData()
        if data != -1: # Standard AWG
            awg = int(data)
            dia = 0.127 * (92 ** ((36 - awg) / 39))
            self.w_dia.setText(f"{dia:.4f}")
            
    def on_dia_changed(self):
        try:
            d = float(self.w_dia.text())
            area = math.pi * (d/2)**2
            self.w_area.setText(f"{area:.4f}")
        except:
            self.w_area.setText("0")

    def calc_wire(self):
        try:
            area = float(self.w_area.text())
            length = float(self.w_len.text())
            curr = float(self.w_curr.text())
            temp = float(self.w_temp.text())
            
            if area <= 0: raise ValueError
            
            rho_20 = 1.724e-8 if self.w_mat.currentIndex() == 0 else 2.82e-8
            alpha = 0.00393 if self.w_mat.currentIndex() == 0 else 0.0039
            rho_t = rho_20 * (1 + alpha * (temp - 20))
            
            r_total = rho_t * length / (area * 1e-6)
            v_drop = curr * r_total
            p_loss = curr**2 * r_total
            
            self.w_res.setText(f"{r_total:.4f}")
            self.w_vdrop.setText(f"{v_drop:.4f}")
            self.w_ploss.setText(f"{p_loss:.4f}")
            
            i_chassis = 15 * (area ** 0.7) 
            i_trans = 4 * (area ** 0.8) 
            
            self.w_amp_chassis.setText(f"~ {i_chassis:.1f} A")
            self.w_amp_trans.setText(f"~ {i_trans:.1f} A")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 3: Busbar Calculator
    # ==============================================================================
    def init_busbar_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 修复：在标题前加空格，防止第一个中文字符显示不全
        grp_in = QGroupBox(" 铜排尺寸 (Rectangular Busbar)") 
        grid = QGridLayout()
        
        self.bb_width = QLineEdit("10"); grid.addWidget(QLabel("宽度 (W) [mm]:"), 0, 0); grid.addWidget(self.bb_width, 0, 1)
        self.bb_thick = QLineEdit("2"); grid.addWidget(QLabel("厚度 (T) [mm]:"), 0, 2); grid.addWidget(self.bb_thick, 0, 3)
        self.bb_len = QLineEdit("100"); grid.addWidget(QLabel("长度 (L) [mm]:"), 1, 0); grid.addWidget(self.bb_len, 1, 1)
        self.bb_curr = QLineEdit("50"); grid.addWidget(QLabel("设计电流 [A]:"), 1, 2); grid.addWidget(self.bb_curr, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算温升与载流能力")
        btn.setFixedHeight(45)
        btn.clicked.connect(self.calc_busbar)
        layout.addWidget(btn)
        
        # 修复：在标题前加空格
        grp_res = QGroupBox(" 估算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.bb_area = QLineEdit()
        self.bb_density = QLineEdit()
        self.bb_temp_rise = QLineEdit()
        self.bb_vdrop = QLineEdit()
        
        r_grid.addWidget(QLabel("截面积 (Area):"), 0, 0); r_grid.addWidget(self.bb_area, 0, 1)
        r_grid.addWidget(QLabel("电流密度 (J):"), 0, 2); r_grid.addWidget(self.bb_density, 0, 3)
        
        r_grid.addWidget(QLabel("估算温升 (ΔT):"), 1, 0); r_grid.addWidget(self.bb_temp_rise, 1, 1)
        l_t = QLabel(); l_t.setPixmap(self.render_formula(r'\Delta T \propto (I/Area)^{1.7}'))
        r_grid.addWidget(l_t, 1, 2)
        
        r_grid.addWidget(QLabel("压降 (Vdrop):"), 2, 0); r_grid.addWidget(self.bb_vdrop, 2, 1)
        r_grid.addWidget(QLabel("基于铜电阻率计算"), 2, 2)
        
        for w in [self.bb_area, self.bb_density, self.bb_temp_rise, self.bb_vdrop]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        info = QLabel("经验法则：设计电流密度建议控制在 2~3 A/mm² (自然冷却)。\n温升估算基于 DIN 43671 简化公式，仅供参考。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_busbar(self):
        try:
            w = float(self.bb_width.text())
            t = float(self.bb_thick.text())
            l = float(self.bb_len.text())
            i = float(self.bb_curr.text())
            
            area = w * t
            if area <= 0: raise ValueError
            
            j = i / area
            
            dt_est = 10 * ((j / 1.2) ** 2.0)
            
            r_val = 0.01724 * (l * 1e-3) / area
            v_drop = i * r_val
            
            self.bb_area.setText(f"{area:.2f} mm²")
            self.bb_density.setText(f"{j:.2f} A/mm²")
            self.bb_temp_rise.setText(f"~ {dt_est:.1f} °C")
            self.bb_vdrop.setText(f"{v_drop*1000:.2f} mV")
            
            if j > 4:
                self.bb_density.setStyleSheet("background-color: #fff5f5; font-weight: bold; color: #c0392b;")
            else:
                self.bb_density.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("导线与损耗计算指南")
        dialog.resize(700, 600)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        html = r"""
        <style>
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
            h2 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
        </style>
        
        <h1>导线与线圈损耗计算</h1>
        
        <h2>1. MTL (Mean Turn Length) 估算</h2>
        <p><b>MTL</b> 是指绕组中所有匝数的平均单圈长度。准确的 MTL 对计算直流电阻 (DCR) 至关重要。</p>
        <ul>
            <li><b>圆柱形骨架 (Round):</b> <code>MTL ≈ π * (D_bobbin + H_winding)</code></li>
            <li><b>矩形骨架 (Rectangular):</b> <code>MTL ≈ 2 * (A + B) + π * H_winding</code></li>
            <li><b>注：</b> D_bobbin 为骨架中柱直径，A/B 为骨架长宽，H_winding 为绕组厚度。</li>
        </ul>

        <h2>2. 利兹线损耗估算 (Coil Loss)</h2>
        <p>变压器或电感的线圈损耗主要由直流损耗 ($I^2R_{dc}$) 和交流损耗 (邻近效应/趋肤效应) 组成。</p>
        <ul>
            <li><b>计算步骤:</b>
                <ol>
                    <li>根据线径和股数计算总有效截面积 $A_{total}$。</li>
                    <li><b>估算总长 (Length):</b> 根据单圈平均长度 (MTL) 和匝数 (N) 计算，$L = MTL \times N$。</li>
                    <li>根据总长度和温度计算直流电阻：$R_{dc} = \rho(T) \cdot L / A_{total}$。</li>
                    <li>根据频率和绕法估算 AC 系数 ($F_r = R_{ac}/R_{dc}$)。一般优化良好的利兹线取 1.2~1.5。</li>
                    <li>总损耗 $P_{loss} = I_{rms}^2 \cdot R_{dc} \cdot F_r$。</li>
                </ol>
            </li>
        </ul>

        <h2>3. 趋肤效应系数自动计算</h2>
        <p>对于高频交流电流，电流趋向于在导线表面流动，导致有效截面积减小，电阻增加。</p>
        <ul>
            <li><b>趋肤深度 ($\delta$):</b> $\delta \approx 66 / \sqrt{f}$ (mm)，其中 f 为频率 (Hz)。</li>
            <li><b>单根导线 AC 系数 ($F_{skin}$):</b> 
                <br>令 $x = d_{strand} / (\sqrt{2} \cdot \delta)$
                <br>$F_{skin} \approx 1 + \frac{x^4}{48 + 0.8x^4}$
            </li>
            <li><b>判据：</b> 为了避免 $R_{ac}$ 暴增，我们选择的利兹线单股直径 $d$ 必须小于 $2\delta$ (最好小于 $\delta$)。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()