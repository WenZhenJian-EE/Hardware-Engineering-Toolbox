from modules.base_module import BaseModule
# pcb_impedance_heat.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
                             QDialog, QTextBrowser, QGroupBox, QGridLayout, QLabel, QLineEdit,
                             QSpinBox, QComboBox, QFrame, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import math
from utils import render_formula

# 导入子模块
# 注意：TraceCurrentTab 等已移动到 modules/physical 目录下
from modules.physical.pcb_basic_phys import TraceCurrentTab, ViaComprehensiveTab, UnitConverterTab, TraceSquareResistanceTab
# 注意：PlanarCapacitanceTab 已移动到 modules/physical 目录下
from modules.physical.pcb_signal_integrity import ImpedanceTab, ParasiticTab, PlanarCapacitanceTab
from modules.physical.pcb_fusing_tool import FusingTab

class PcbCalculatorWindow(BaseModule):
    category = "5. 无源器件与物理连接 (Passives & Physical)"
    display_name = "PCB 工具箱"
    description = "阻抗/载流/方块电阻/平面电容"
    window_id = "pcb_tool"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PCB 设计计算工具箱 (IPC & Impedance & Thermal)')
        self.setGeometry(350, 350, 950, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 教程按钮区
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计指南与标准对比")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)
        
        # 主 Tab 容器 (一级分类)
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; border-radius: 4px; margin-top: 5px; }
            QTabBar::tab { 
                background: #f0f0f0; 
                border: 1px solid #c0c0c0; 
                padding: 10px 20px; 
                margin-right: 2px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                font-size: 14px; 
                min-width: 250px;
            }
            QTabBar::tab:selected { 
                background: #ffffff; 
                border-bottom: 1px solid #ffffff; 
                font-weight: bold; 
                color: #3498db; 
            }
        """)
        
        # --- Group 1: 基础物理参数 ---
        self.group_basic = QWidget()
        self.init_basic_group_ui()
        self.main_tabs.addTab(self.group_basic, "1. 基础物理参数 (Basic Physics)")
        
        # --- Group 2: 信号完整性与阻抗 ---
        self.group_si = QWidget()
        self.init_si_group_ui()
        self.main_tabs.addTab(self.group_si, "2. 信号完整性 (Impedance & SI)")
        
        # --- Group 3: 散热与熔断 (Thermal & Fusing) ---
        self.group_thermal_fusing = QWidget()
        self.init_thermal_fusing_group_ui()
        self.main_tabs.addTab(self.group_thermal_fusing, "3. 散热与熔断 (Thermal & Fusing)")
        
        main_layout.addWidget(self.main_tabs)
        self.setLayout(main_layout)

    def init_basic_group_ui(self):
        """初始化组1：线宽、过孔、单位、方块电阻"""
        layout = QVBoxLayout(self.group_basic)
        layout.setContentsMargins(0, 10, 0, 0)
        
        tabs = QTabWidget()
        tabs.addTab(TraceCurrentTab(), "1. 线宽与载流 ")
        tabs.addTab(ViaComprehensiveTab(), "2. 过孔综合评估 ")
        # 【关键更新】：这里添加了方块电阻的 Tab
        tabs.addTab(TraceSquareResistanceTab(), "4. 方块电阻与采样 ") 
        tabs.addTab(UnitConverterTab(), "5. 单位换算 ")
        
        layout.addWidget(tabs)

    def init_si_group_ui(self):
        """初始化组2：阻抗、寄生、平面电容"""
        layout = QVBoxLayout(self.group_si)
        layout.setContentsMargins(0, 10, 0, 0)
        
        tabs = QTabWidget()
        tabs.addTab(ImpedanceTab(), "特性阻抗评估 (Impedance)")
        tabs.addTab(ParasiticTab(), "寄生参数估算 (Parasitics)")
        tabs.addTab(PlanarCapacitanceTab(), "PCB 平面电容 (Planar Cap)")
        
        layout.addWidget(tabs)

    def init_thermal_fusing_group_ui(self):
        """初始化组3：散热与熔断"""
        layout = QVBoxLayout(self.group_thermal_fusing)
        layout.setContentsMargins(0, 10, 0, 0)
        
        tabs = QTabWidget()
        tabs.addTab(FusingTab(), "铜箔瞬态熔断 (Trace Fusing)")
        tabs.addTab(PcbHeatsinkTab(), "PCB 铜皮散热 (Copper Heatsink)")
        tabs.addTab(ThermalViaTab(), "热过孔阵列 (Thermal Via Array)")
        
        layout.addWidget(tabs)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("PCB 设计计算与工程指南")
        dialog.resize(900, 800)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html_content = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 25px;}
            h3 { color: #d35400; margin-top: 15px; font-size: 15px; font-weight: bold;}
            .note { background-color: #fff9c4; padding: 10px; border-left: 4px solid #f1c40f; color: #333; margin: 10px 0;}
            .ipc2152 { background-color: #e8f8f5; padding: 10px; border-left: 4px solid #27ae60; color: #333; margin: 10px 0;}
            li { margin-bottom: 5px; }
            code { background-color: #e0e0e0; padding: 2px 4px; border-radius: 3px; font-family: monospace; color: #c0392b; }
        </style>
        
        <h1>PCB 设计工程指南</h1>
        <p>本指南按照软件界面的三个功能分组进行说明。</p>

        <h2>第一组：基础物理参数 (Basic Physics)</h2>
        
        <h3>1. 线宽与载流 (Trace Width)</h3>
        <p><b>IPC-2221 (传统保守):</b> $I = k \cdot \Delta T^{0.44} \cdot A^{0.725}$。内层散热差(k=0.024)，外层散热好(k=0.048)。</p>
        <div class="ipc2152">
            <b>IPC-2152 (现代标准):</b> 引入了物理导热模型，指出 FR-4 和内部铜平面 (Planes) 是极佳的散热器。<br>
            对于含 GND/VCC 层的多层板，IPC-2152 计算出的载流能力通常比 2221 高 30%~50%，能显著节省布线空间。
        </div>

        <h3>2. 方块电阻统计法 (Square Counting)</h3>
        <p><b>原理：</b> PCB 铜箔电阻 $R = R_{sq} \times N$。</p>
        <ul>
            <li>$R_{sq}$ (方阻): 取决于铜厚和温度。1oz 铜在常温下约为 $0.5 m\Omega / \Box$。</li>
            <li>$N$ (方块数): 走线长度 / 宽度 ($L/W$)。</li>
        </ul>
        <p><b>应用：</b> 快速估算大电流路径压降；评估电流采样电阻 (Shunt) 的开尔文接线误差（每多“吃”进一个方块的铜箔，就会引入 0.5mΩ 的误差）。</p>

        <h2>第二组：信号完整性 (Signal Integrity)</h2>
        
        <h3>1. 特性阻抗 (Impedance)</h3>
        <p>高速信号（USB, Ethernet）需控制阻抗匹配（50Ω/90Ω/100Ω）。</p>
        <ul>
            <li><b>微带线 (Microstrip):</b> 表层走线。受绿油厚度影响。</li>
            <li><b>带状线 (Stripline):</b> 内层走线，上下均有参考平面。屏蔽好，但信号传输速度略慢。</li>
        </ul>

        <h3>2. PCB 平面电容 (Planar Capacitance)</h3>
        <p>利用电源层和地层之间的平板电容效应来滤除高频噪声。</p>
        <ul>
            <li><b>高频优势：</b> 与分立 MLCC 相比，平面电容没有引脚 ESL，在高频 (>100MHz) 下阻抗极低。</li>
            <li><b>关键参数：</b> 层间介质厚度 (Dielectric Thickness)。厚度越薄 (如 3mil vs 10mil)，电容越大，去耦效果越好。</li>
            <li><b>公式：</b> $C \approx 0.225 \cdot D_k \cdot \frac{Area}{d}$ (pF)。</li>
        </ul>

        <h2>第三组：散热与熔断 (Thermal & Fusing)</h2>
        
        <h3>1. PCB 铜皮散热 (PCB Heatsink)</h3>
        <p><b>核心概念：</b> 利用多层板的内层铜箔作为“均热板 (Heat Spreader)”。</p>
        <ul>
            <li><b>外层：</b> 直接接触空气对流，效率最高 (权重 1.0)。</li>
            <li><b>内层：</b> 不能直接对流，但能极大降低横向热阻，将热量传导到整板，权重约 0.5。</li>
            <li><b>铜厚：</b> 2oz 铜厚的导热能力是 1oz 的两倍，对于高功率密度设计至关重要。</li>
        </ul>

        <h3>2. 热过孔阵列 (Thermal Vias)</h3>
        <p>对于 QFN/DFN 等底部带有散热焊盘 (EPAD) 的器件，必须打过孔将热量引到背面。</p>
        <ul>
            <li><b>单个过孔瓶颈：</b> 孔壁铜层仅约 25um，热阻很高 (100~200°C/W)。</li>
            <li><b>阵列效应：</b> N 个过孔并联，热阻降为 1/N。建议在 EPAD 区域打满过孔阵列。</li>
        </ul>

        <h3>3. 铜箔瞬态熔断 (Trace Fusing)</h3>
        <p>基于 <b>Onderdonk</b> 公式，评估短路或雷击浪涌下的耐受力。</p>
        <p><b>公式：</b> $I = A \cdot \sqrt{\frac{\log(1 + \Delta T / (234 + T_a))}{33 t}}$</p>
        """
        text.setHtml(html_content)
        layout.addWidget(text)
        dialog.exec_()

# ==============================================================================
# PCB 铜皮散热 Tab 类 (Moved from Heatsink Tool)
# ==============================================================================
class PcbHeatsinkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # 输入：正向计算热阻
        grp_calc = QGroupBox("1. 铺铜配置 & 正向热阻估算 (Forward Calculation)")
        grid_pcb = QGridLayout()
        
        # 面积
        self.pcb_area = QLineEdit("500") # mm^2
        self.pcb_area.setToolTip("每一层的单面铺铜面积。假设多层铺铜大小一致并通过过孔连接。")
        grid_pcb.addWidget(QLabel("单层铺铜面积 [mm²]:"), 0, 0)
        grid_pcb.addWidget(self.pcb_area, 0, 1)

        # 铜厚 (自定义 Float)
        self.pcb_copper = QLineEdit("1.0")
        self.pcb_copper.setPlaceholderText("如 1.0, 1.5, 2.0")
        grid_pcb.addWidget(QLabel("铜厚 [oz]:"), 0, 2)
        grid_pcb.addWidget(self.pcb_copper, 0, 3)

        # 层数配置 (自定义 SpinBox)
        self.lay_out = QSpinBox()
        self.lay_out.setRange(0, 2)
        self.lay_out.setValue(1) # 默认 Top
        self.lay_out.setSuffix(" 层")
        self.lay_out.setToolTip("外层 (Top/Bottom) 铜皮数量。外层不仅均热，还能直接对流散热，效率最高。")

        self.lay_in = QSpinBox()
        self.lay_in.setRange(0, 32)
        self.lay_in.setValue(0) # 默认无内层
        self.lay_in.setSuffix(" 层")
        self.lay_in.setToolTip("内层 (Inner Layer) 铜皮数量。内层主要起到均热板(Heat Spreader)的作用，需通过过孔连接。")

        grid_pcb.addWidget(QLabel("外层用于散热 (0-2):"), 1, 0)
        grid_pcb.addWidget(self.lay_out, 1, 1)
        grid_pcb.addWidget(QLabel("内层用于散热 (0-N):"), 1, 2)
        grid_pcb.addWidget(self.lay_in, 1, 3)

        btn_pcb = QPushButton("估算 PCB 等效热阻 Rθja")
        btn_pcb.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; height: 35px;")
        btn_pcb.clicked.connect(self.calc_pcb_rth)
        grid_pcb.addWidget(btn_pcb, 2, 0, 1, 4)

        self.res_pcb_rth = QLineEdit(); self.res_pcb_rth.setReadOnly(True)
        self.res_pcb_rth.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 16px;")
        grid_pcb.addWidget(QLabel("预估热阻 Rθja [°C/W]:"), 3, 0); grid_pcb.addWidget(self.res_pcb_rth, 3, 1, 1, 3)
        
        grp_calc.setLayout(grid_pcb)
        layout.addWidget(grp_calc)

        # 输入：反向计算面积
        grp_reverse = QGroupBox("2. 反向设计：功耗 -> 所需铺铜面积 (Reverse Calculation)")
        grid_rev = QGridLayout()
        
        lbl_hint = QLabel("(注：计算基于上方设定的层数与铜厚)")
        lbl_hint.setStyleSheet("color: #7f8c8d; font-style: italic;")
        grid_rev.addWidget(lbl_hint, 0, 0, 1, 4)

        self.target_pd = QLineEdit("1.5") # W
        self.target_dt = QLineEdit("50")  # DegC rise
        grid_rev.addWidget(QLabel("耗散功率 [W]:"), 1, 0); grid_rev.addWidget(self.target_pd, 1, 1)
        grid_rev.addWidget(QLabel("允许温升 ΔT [°C]:"), 1, 2); grid_rev.addWidget(self.target_dt, 1, 3)

        btn_rev = QPushButton("反推所需最小占地面积 (Footprint Area)")
        btn_rev.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; height: 35px;")
        btn_rev.clicked.connect(self.calc_pcb_area_needed)
        grid_rev.addWidget(btn_rev, 2, 0, 1, 4)

        self.res_area_needed = QLineEdit(); self.res_area_needed.setReadOnly(True)
        self.res_area_needed.setStyleSheet("background-color: #fef9e7; font-weight: bold; color: #b7950b; font-size: 14px;")
        grid_rev.addWidget(QLabel("所需 PCB 铺铜占地面积:"), 3, 0); grid_rev.addWidget(self.res_area_needed, 3, 1, 1, 3)

        grp_reverse.setLayout(grid_rev)
        layout.addWidget(grp_reverse)

        l_pcb_form = QLabel()
        l_pcb_form.setPixmap(render_formula(r'R_{\theta JA} \approx \frac{850}{\sqrt{Area}} \cdot K_{oz} \cdot K_{layers}'))
        l_pcb_form.setAlignment(Qt.AlignCenter)
        layout.addWidget(l_pcb_form)

        info = QLabel("提示：内层铜皮通过过孔连接后可充当高效均热板。计算结果为工程估算值，实际效果受过孔数量和风道影响。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)

        layout.addStretch()
        self.setLayout(layout)

    def get_pcb_factors(self):
        try:
            t_oz = float(self.pcb_copper.text())
            if t_oz < 0.1: t_oz = 0.5 
        except:
            t_oz = 1.0
        
        k_oz = t_oz ** -0.3

        n_out = self.lay_out.value()
        n_in = self.lay_in.value()
        
        n_eff = n_out + 0.5 * n_in
        if n_eff < 0.5: n_eff = 0.5
        
        k_layers = n_eff ** -0.6
        
        return k_oz, k_layers, n_out, n_in

    def calc_pcb_rth(self):
        try:
            area = float(self.pcb_area.text()) # mm^2
            if area <= 0: return
            base_rth = 850.0 / (area ** 0.5) 
            
            k_oz, k_lay, _, _ = self.get_pcb_factors()
            
            final_rth = base_rth * k_oz * k_lay
            final_rth = max(final_rth, 10.0)
            self.res_pcb_rth.setText(f"{final_rth:.2f} °C/W")
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    def calc_pcb_area_needed(self):
        try:
            pd = float(self.target_pd.text())
            dt = float(self.target_dt.text())
            if pd <= 0 or dt <= 0: return
            
            target_rth = dt / pd
            k_oz, k_lay, n_out, n_in = self.get_pcb_factors()
            
            if target_rth < 10:
                self.res_area_needed.setText("需强迫风冷或大散热器")
                return

            sqrt_area = (850.0 * k_oz * k_lay) / target_rth
            area_needed = sqrt_area ** 2
            
            layer_info_str = f"({n_out}层外 + {n_in}层内)"
            self.res_area_needed.setText(f"{area_needed:.1f} mm² {layer_info_str}")
            self.res_area_needed.setToolTip(f"这代表 PCB 上需要开辟 {area_needed:.1f} mm² 的区域，\n并在所有选定的 {n_out+n_in} 层上铺铜并通过过孔连接。")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的功率和温升")

# ==============================================================================
# 热过孔阵列 Tab 类 (Moved from Heatsink Tool)
# ==============================================================================
class ThermalViaTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：计算 EPAD 下方过孔阵列的等效热阻。用于评估“打多少个孔才够”。")
        info.setStyleSheet("color: #555; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 过孔参数
        grp_in = QGroupBox("1. 过孔参数 (Single Via Params)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.via_dia = QLineEdit("0.3") # mm
        self.via_dia.setToolTip("钻孔直径 (Drill Diameter)")
        grid.addWidget(QLabel("过孔直径 d [mm]:"), 0, 0); grid.addWidget(self.via_dia, 0, 1)
        
        self.via_wall = QLineEdit("25") # um
        self.via_wall.setToolTip("孔壁镀铜厚度，通常为 20~25um")
        grid.addWidget(QLabel("孔壁铜厚 t [um]:"), 0, 2); grid.addWidget(self.via_wall, 0, 3)
        
        self.via_len = QLineEdit("1.6") # mm
        self.via_len.setToolTip("PCB板厚度 (热传导距离)")
        grid.addWidget(QLabel("PCB板厚 L [mm]:"), 1, 0); grid.addWidget(self.via_len, 1, 1)
        
        self.via_fill = QComboBox()
        self.via_fill.addItems(["无填充 (Air)", "灌锡 (Solder Filled)"])
        grid.addWidget(QLabel("孔内填充材料:"), 1, 2); grid.addWidget(self.via_fill, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. 阵列配置
        grp_array = QGroupBox("2. 阵列配置 (Array Config)")
        g_arr = QGridLayout()
        
        self.via_count = QSpinBox()
        self.via_count.setRange(1, 1000)
        self.via_count.setValue(10)
        g_arr.addWidget(QLabel("过孔数量 N:"), 0, 0); g_arr.addWidget(self.via_count, 0, 1)
        
        btn_calc = QPushButton("计算阵列热阻")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_via_array)
        g_arr.addWidget(btn_calc, 0, 2, 1, 2)
        
        grp_array.setLayout(g_arr)
        layout.addWidget(grp_array)
        
        # 3. 结果
        grp_res = QGroupBox("3. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_via_single = QLineEdit()
        self.res_via_total = QLineEdit()
        
        # Single Rth
        r_grid.addWidget(QLabel("单孔热阻 R_via:"), 0, 0); r_grid.addWidget(self.res_via_single, 0, 1)
        l_single = QLabel(); l_single.setPixmap(render_formula(r'R_{via} = \frac{L}{k_{cu} A_{cu} + k_{fill} A_{fill}}'))
        r_grid.addWidget(l_single, 0, 2)
        
        # Total Rth
        r_grid.addWidget(QLabel("阵列总热阻 R_total:"), 1, 0); r_grid.addWidget(self.res_via_total, 1, 1)
        l_total = QLabel(); l_total.setPixmap(render_formula(r'R_{total} = R_{via} / N'))
        r_grid.addWidget(l_total, 1, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        for w in [self.res_via_single, self.res_via_total]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        self.setLayout(layout)

    def calc_via_array(self):
        try:
            d_mm = float(self.via_dia.text())
            t_um = float(self.via_wall.text())
            l_mm = float(self.via_len.text())
            n = self.via_count.value()
            is_solder = (self.via_fill.currentIndex() == 1)
            
            if d_mm <= 0 or l_mm <= 0: return
            
            # Convert to meters
            d = d_mm * 1e-3
            t = t_um * 1e-6
            length = l_mm * 1e-3
            
            # Inner diameter
            d_in = d - 2*t
            if d_in < 0: d_in = 0
            
            # Areas
            area_cu = (math.pi / 4.0) * (d**2 - d_in**2)
            area_fill = (math.pi / 4.0) * (d_in**2)
            
            # Thermal Conductivities (W/mK)
            k_cu = 390.0 # Copper
            k_fill = 50.0 if is_solder else 0.026 # Air
            
            # Thermal Conductance G = k*A / L
            g_cu = k_cu * area_cu / length
            g_fill = k_fill * area_fill / length
            
            g_total_single = g_cu + g_fill
            if g_total_single == 0: return
            
            r_single = 1.0 / g_total_single
            r_array = r_single / n
            
            self.res_via_single.setText(f"{r_single:.1f} °C/W")
            self.res_via_total.setText(f"{r_array:.2f} °C/W")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")