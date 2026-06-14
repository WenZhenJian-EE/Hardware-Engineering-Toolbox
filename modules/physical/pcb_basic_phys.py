# pcb_basic_phys.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QComboBox, QCheckBox, QStackedWidget, QTabWidget, QSpinBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

# ==============================================================================
# 1. 线宽与载流 (Trace Width & Current)
# ==============================================================================
class TraceCurrentTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        input_group = QGroupBox("设计参数输入")
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        input_layout.setHorizontalSpacing(15)
        
        self.tr_current_input = QLineEdit("5.0")
        self.tr_temp_rise_input = QLineEdit("10")
        self.tr_thickness_input = QLineEdit("1.0")
        self.tr_length_input = QLineEdit("100")
        self.tr_temp_amb_input = QLineEdit("25")
        
        # 多层配置
        self.tr_multi_layer_check = QCheckBox("启用多层并联计算 (Multi-layer Parallel)")
        self.tr_multi_layer_check.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 13px;")
        self.tr_multi_layer_check.toggled.connect(self.on_trace_mode_changed)
        
        self.tr_single_widget = QWidget()
        sm_layout = QHBoxLayout(self.tr_single_widget)
        sm_layout.setContentsMargins(0,0,0,0)
        self.tr_layer_type_combo = QComboBox()
        self.tr_layer_type_combo.addItems(["外层走线 (External)", "内层走线 (Internal)"])
        sm_layout.addWidget(self.tr_layer_type_combo)
        
        self.tr_multi_widget = QWidget()
        mm_layout = QHBoxLayout(self.tr_multi_widget)
        mm_layout.setContentsMargins(0,0,0,0)
        self.tr_layers_ext_input = QLineEdit("1")
        self.tr_layers_ext_input.setPlaceholderText("外层数")
        self.tr_layers_int_input = QLineEdit("1")
        self.tr_layers_int_input.setPlaceholderText("内层数")
        mm_layout.addWidget(QLabel("外层数:"))
        mm_layout.addWidget(self.tr_layers_ext_input)
        mm_layout.addSpacing(10)
        mm_layout.addWidget(QLabel("内层数:"))
        mm_layout.addWidget(self.tr_layers_int_input)
        
        self.tr_stack = QStackedWidget()
        self.tr_stack.addWidget(self.tr_single_widget)
        self.tr_stack.addWidget(self.tr_multi_widget)
        
        inputs = [
            ("总设计电流 (I) [A]:", self.tr_current_input),
            ("允许温升 (ΔT) [°C]:", self.tr_temp_rise_input),
            ("铜箔厚度 [oz] (1oz=35um):", self.tr_thickness_input),
            ("走线长度 [mm]:", self.tr_length_input),
            ("环境温度 [°C]:", self.tr_temp_amb_input)
        ]
        
        for i, (txt, widget) in enumerate(inputs):
            r, c = i // 2, (i % 2) * 2
            input_layout.addWidget(QLabel(txt), r, c)
            input_layout.addWidget(widget, r, c+1)
            
        setting_row = len(inputs)//2 + 1
        input_layout.addWidget(self.tr_multi_layer_check, setting_row, 0, 1, 2)
        input_layout.addWidget(QLabel("层数配置:"), setting_row, 2)
        input_layout.addWidget(self.tr_stack, setting_row, 3)
        
        # New: IPC-2152 Option
        self.tr_ipc2152_check = QCheckBox("启用 IPC-2152 增强 (含参考平面)")
        self.tr_ipc2152_check.setToolTip("IPC-2152 标准考虑了 PCB 导热和参考平面的散热作用。\n勾选此项表示板上有大面积铜皮或地平面 (Plane)，载流能力通常比 2221 更强。")
        self.tr_ipc2152_check.setStyleSheet("color: #27ae60; font-weight: bold; margin-top: 10px;")
        input_layout.addWidget(self.tr_ipc2152_check, setting_row + 1, 0, 1, 2)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算线宽与压降 (IPC-2221 vs IPC-2152)")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(45)
        btn.clicked.connect(self.on_calculate_trace)
        layout.addWidget(btn)
        
        out_group = QGroupBox("计算结果")
        out_layout = QHBoxLayout()
        
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(12)
        
        self.tr_area_out = QLineEdit() 
        self.tr_width_mil_out = QLineEdit()
        self.tr_width_mm_out = QLineEdit()
        self.tr_res_out = QLineEdit()
        self.tr_drop_out = QLineEdit()
        self.tr_width_2152_out = QLineEdit()
        
        style = "background-color: #f8f9fa; font-weight: bold; color: #2980b9;"
        style_2152 = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        
        # IPC-2221 Results
        res_grid.addWidget(QLabel("IPC-2221 (保守) 线宽 [mm]:"), 0, 0)
        res_grid.addWidget(self.tr_width_mm_out, 0, 1)
        self.tr_width_mm_out.setReadOnly(True); self.tr_width_mm_out.setStyleSheet(style)
        
        # IPC-2152 Results
        res_grid.addWidget(QLabel("IPC-2152 (有平面) 线宽 [mm]:"), 1, 0)
        res_grid.addWidget(self.tr_width_2152_out, 1, 1)
        self.tr_width_2152_out.setReadOnly(True); self.tr_width_2152_out.setStyleSheet(style_2152)
        self.tr_width_2152_out.setPlaceholderText("需勾选增强选项")
        
        # Common Results
        res_grid.addWidget(QLabel("IPC-2221 所需截面积 [sq mils]:"), 2, 0)
        res_grid.addWidget(self.tr_area_out, 2, 1)
        
        res_grid.addWidget(QLabel("总等效电阻 [Ω] (按2221):"), 3, 0)
        res_grid.addWidget(self.tr_res_out, 3, 1)
        
        res_grid.addWidget(QLabel("总电压降 [V] (按2221):"), 4, 0)
        res_grid.addWidget(self.tr_drop_out, 4, 1)
        
        for w in [self.tr_area_out, self.tr_res_out, self.tr_drop_out]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        form_layout = QVBoxLayout()
        form_layout.setAlignment(Qt.AlignCenter)
        self.tr_info_label = QLabel("模式：单层计算")
        self.tr_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        
        l1 = QLabel()
        l1.setPixmap(render_formula(r'Area = \left( \frac{I_{layer}}{k \cdot \Delta T^{0.44}} \right)^{\frac{1}{0.725}}', 50))
        
        form_layout.addWidget(l1)
        form_layout.addWidget(self.tr_info_label)
        
        out_layout.addLayout(res_grid, 4)
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        out_layout.addWidget(line)
        out_layout.addLayout(form_layout, 5)
        
        out_group.setLayout(out_layout)
        layout.addWidget(out_group)
        self.setLayout(layout)
        self.on_calculate_trace()

    def on_trace_mode_changed(self, checked):
        self.tr_stack.setCurrentIndex(1 if checked else 0)

    def on_calculate_trace(self):
        try:
            i_total = float(self.tr_current_input.text())
            dt = float(self.tr_temp_rise_input.text())
            th_oz = float(self.tr_thickness_input.text())
            l_mm = float(self.tr_length_input.text())
            t_amb = float(self.tr_temp_amb_input.text())
            
            if i_total<=0 or dt<=0 or th_oz<=0 or l_mm<=0: raise ValueError("输入需大于0")
            
            num_layers = 1
            k = 0.048
            mode_text = ""
            is_int_layer = False
            
            if self.tr_multi_layer_check.isChecked():
                n_ext = int(self.tr_layers_ext_input.text())
                n_int = int(self.tr_layers_int_input.text())
                if n_ext+n_int == 0: raise ValueError("层数不能为0")
                num_layers = n_ext + n_int
                if n_int > 0:
                    k = 0.024
                    mode_text = f"多层并联 ({num_layers}层, 含内层)\nIPC-2221: 内层标准 k=0.024"
                    is_int_layer = True
                else:
                    k = 0.048
                    mode_text = f"多层并联 ({num_layers}层, 全外层)\nIPC-2221: 外层标准 k=0.048"
            else:
                is_int = "Internal" in self.tr_layer_type_combo.currentText()
                k = 0.024 if is_int else 0.048
                mode_text = f"单层 ({'内层' if is_int else '外层'})\nIPC-2221: k={k}"
                is_int_layer = is_int
            
            self.tr_info_label.setText(mode_text)
            
            i_layer = i_total / num_layers
            area_sq_mils = (i_layer / (k * (dt**0.44))) ** (1/0.725)
            
            th_mils = th_oz * 1.378
            width_mils = area_sq_mils / th_mils
            width_mm = width_mils * 0.0254
            
            temp_work = t_amb + dt
            rho = 1.724e-8 * (1 + 0.00393*(temp_work-25))
            area_m2 = (width_mm*1e-3) * (th_oz*0.035*1e-3)
            r_single = rho * (l_mm*1e-3) / area_m2
            
            r_total = r_single / num_layers
            v_drop = i_total * r_total
            
            self.tr_area_out.setText(f"{area_sq_mils:.1f} sq mils") 
            self.tr_width_mm_out.setText(f"{width_mm:.3f} mm")
            self.tr_res_out.setText(f"{r_total:.5f} Ω")
            self.tr_drop_out.setText(f"{v_drop:.4f} V")
            
            if self.tr_ipc2152_check.isChecked():
                if is_int_layer:
                    current_capacity_mult = 1.8 
                else:
                    current_capacity_mult = 1.4
                width_factor = (1.0 / current_capacity_mult) ** (1/0.725)
                width_mm_2152 = width_mm * width_factor
                self.tr_width_2152_out.setText(f"{width_mm_2152:.3f} mm (估算)")
                self.tr_width_2152_out.setToolTip(f"基于 IPC-2152 (含平面) 估算。\n相对于 IPC-2221，载流能力约提升 {current_capacity_mult} 倍。")
            else:
                self.tr_width_2152_out.setText("未启用")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

# ==============================================================================
# 2. 过孔综合评估 (Via Comprehensive)
# ==============================================================================
class ViaComprehensiveTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 物理参数
        grp_phy = QGroupBox("1. 物理参数 (Physical Parameters)")
        grid_phy = QGridLayout()
        grid_phy.setVerticalSpacing(12)
        
        self.vc_dia = QLineEdit("0.3"); self.vc_dia.setToolTip("过孔钻孔直径 (Drill Diameter)")
        grid_phy.addWidget(QLabel("钻孔直径 [mm]:"), 0, 0); grid_phy.addWidget(self.vc_dia, 0, 1)
        
        self.vc_plating = QLineEdit("25"); self.vc_plating.setToolTip("孔壁镀铜厚度 (IPC 2级标准通常 ≥20um)")
        grid_phy.addWidget(QLabel("镀铜厚度 [um]:"), 0, 2); grid_phy.addWidget(self.vc_plating, 0, 3)
        
        self.vc_height = QLineEdit("1.6"); self.vc_height.setToolTip("PCB 板厚度 / 过孔长度")
        grid_phy.addWidget(QLabel("PCB 板厚 [mm]:"), 1, 0); grid_phy.addWidget(self.vc_height, 1, 1)
        
        self.vc_fill = QComboBox(); self.vc_fill.addItems(["无填充/空气 (Air)", "灌锡 (Solder Filled)"])
        grid_phy.addWidget(QLabel("孔内填充材料:"), 1, 2); grid_phy.addWidget(self.vc_fill, 1, 3)
        
        self.vc_count = QLineEdit("1"); self.vc_count.setPlaceholderText("计划使用的过孔数量")
        self.vc_count.setStyleSheet("background-color: #eaf2f8; font-weight: bold;")
        grid_phy.addWidget(QLabel("设计过孔数量 (N):"), 2, 0); grid_phy.addWidget(self.vc_count, 2, 1)
        grid_phy.addWidget(QLabel("← 用于计算总载流和总热阻"), 2, 2, 1, 2)
        
        grp_phy.setLayout(grid_phy)
        layout.addWidget(grp_phy)
        
        # 1.5. 阵列配置
        grp_array = QGroupBox("1.5 过孔阵列配置 (Via Array Config)")
        grid_array = QGridLayout()
        self.vc_layout = QComboBox()
        self.vc_layout.addItems(["分散/独立 (Isolated)", "线性排列 (Linear 1xN)", "矩阵排列 (Matrix MxN)"])
        grid_array.addWidget(QLabel("布局方式:"), 0, 0); grid_array.addWidget(self.vc_layout, 0, 1)
        self.vc_pitch_type = QComboBox()
        self.vc_pitch_type.addItems(["常规间距 (>3d)", "紧密间距 (<3d)"])
        grid_array.addWidget(QLabel("间距类型:"), 0, 2); grid_array.addWidget(self.vc_pitch_type, 0, 3)
        grp_array.setLayout(grid_array)
        layout.addWidget(grp_array)
        
        # 2. 载流评估
        grp_elec = QGroupBox("2. 载流能力评估 (Electrical - IPC-2221)")
        grid_elec = QGridLayout()
        self.vc_current = QLineEdit("5.0"); 
        grid_elec.addWidget(QLabel("目标总电流 [A]:"), 0, 0); grid_elec.addWidget(self.vc_current, 0, 1)
        self.vc_temp_rise = QLineEdit("10"); 
        grid_elec.addWidget(QLabel("允许温升 ΔT [°C]:"), 0, 2); grid_elec.addWidget(self.vc_temp_rise, 0, 3)
        self.vc_k_factor = QComboBox(); self.vc_k_factor.addItems(["通用 (k=0.048)", "保守 (k=0.024)"])
        grid_elec.addWidget(QLabel("IPC 系数 k:"), 1, 0); grid_elec.addWidget(self.vc_k_factor, 1, 1)
        grp_elec.setLayout(grid_elec)
        layout.addWidget(grp_elec)
        
        # 计算按钮
        btn_calc = QPushButton("开始综合计算 (载流 & 热阻 & 阵列降额)")
        btn_calc.setFixedHeight(45)
        btn_calc.setFont(QFont('Arial', 11, QFont.Bold))
        btn_calc.setStyleSheet("background-color: #3498db; color: white;")
        btn_calc.clicked.connect(self.calc_via_comprehensive)
        layout.addWidget(btn_calc)
        
        # 3. 结果显示
        grp_res = QGroupBox("3. 评估结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.vc_res_single_i = QLineEdit(); self.vc_res_derating = QLineEdit() 
        self.vc_res_total_i = QLineEdit(); self.vc_res_check = QLineEdit() 
        
        r_grid.addWidget(QLabel("单孔最大载流 (I_single):"), 0, 0); r_grid.addWidget(self.vc_res_single_i, 0, 1)
        r_grid.addWidget(QLabel("阵列降额系数 (Derating):"), 0, 2); r_grid.addWidget(self.vc_res_derating, 0, 3)
        r_grid.addWidget(QLabel("阵列总载流能力 (I_total):"), 1, 0); r_grid.addWidget(self.vc_res_total_i, 1, 1)
        r_grid.addWidget(QLabel("设计数量校验:"), 1, 2); r_grid.addWidget(self.vc_res_check, 1, 3)
        
        line = QFrame(); line.setFrameShape(QFrame.HLine); line.setFrameShadow(QFrame.Sunken)
        r_grid.addWidget(line, 2, 0, 1, 4)
        
        self.vc_res_single_rth = QLineEdit(); self.vc_res_total_rth = QLineEdit()
        r_grid.addWidget(QLabel("单孔热阻 (R_th):"), 3, 0); r_grid.addWidget(self.vc_res_single_rth, 3, 1)
        r_grid.addWidget(QLabel("总热阻 (基于设计数量):"), 3, 2); r_grid.addWidget(self.vc_res_total_rth, 3, 3)
        
        style_res = "background-color: #f0f0f0; font-weight: bold; color: #2c3e50;"
        style_key = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #e67e22;"
        
        self.vc_res_single_i.setReadOnly(True); self.vc_res_single_i.setStyleSheet(style_res)
        self.vc_res_derating.setReadOnly(True); self.vc_res_derating.setStyleSheet(style_warn)
        self.vc_res_total_rth.setReadOnly(True); self.vc_res_total_rth.setStyleSheet(style_res)
        self.vc_res_total_i.setReadOnly(True); self.vc_res_total_i.setStyleSheet(style_key)
        self.vc_res_check.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        l_tips = QLabel()
        l_tips.setPixmap(render_formula(r'I_{total} = N \cdot I_{single} \cdot K_{derating}, \quad R_{th\_total} = R_{th\_single} / N', 35))
        layout.addWidget(l_tips)
        layout.addStretch()
        self.setLayout(layout)

    def calc_via_comprehensive(self):
        try:
            d_mm = float(self.vc_dia.text())
            t_um = float(self.vc_plating.text())
            h_mm = float(self.vc_height.text())
            n_design = int(self.vc_count.text())
            i_target = float(self.vc_current.text())
            dt = float(self.vc_temp_rise.text())
            layout_idx = self.vc_layout.currentIndex() 
            
            if d_mm <= 0 or t_um <= 0 or h_mm <= 0 or n_design <= 0: raise ValueError("物理参数必须大于0")

            # Electrical
            d_mil = d_mm / 0.0254
            t_mil = (t_um / 1000.0) / 0.0254
            area_sq_mils = math.pi * d_mil * t_mil
            k = 0.048 if "0.048" in self.vc_k_factor.currentText() else 0.024
            i_max_single = k * (dt ** 0.44) * (area_sq_mils ** 0.725)
            
            # Derating
            derating = 1.0
            if n_design > 1:
                if layout_idx == 0: derating = 1.0
                elif layout_idx == 1: derating = max(0.7, 1.0 - 0.02 * (n_design - 1))
                else: derating = max(0.5, 1.0 - 0.05 * (n_design - 1))
            if self.vc_pitch_type.currentIndex() == 1 and n_design > 1: derating *= 0.9
                
            i_total_capacity = n_design * i_max_single * derating
            
            self.vc_res_single_i.setText(f"{i_max_single:.3f} A")
            self.vc_res_derating.setText(f"{derating:.2f}")
            self.vc_res_total_i.setText(f"{i_total_capacity:.2f} A")
            
            if i_total_capacity >= i_target:
                self.vc_res_check.setText(f"合格 (余量 {i_total_capacity - i_target:.2f}A)")
                self.vc_res_check.setStyleSheet("background-color: #e8f8f5; color: #27ae60; font-weight: bold;")
            else:
                self.vc_res_check.setText(f"不足! (缺 {i_target - i_total_capacity:.2f}A)")
                self.vc_res_check.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold;")

            # Thermal
            d = d_mm * 1e-3
            t = t_um * 1e-6
            h = h_mm * 1e-3
            d_inner = d - 2*t if d - 2*t > 0 else 0
            area_cu = (math.pi / 4.0) * (d**2 - d_inner**2)
            area_fill = (math.pi / 4.0) * (d_inner**2)
            k_cu = 390.0
            is_solder = (self.vc_fill.currentIndex() == 1)
            k_fill = 50.0 if is_solder else 0.026
            
            g_total_single = (k_cu * area_cu + k_fill * area_fill) / h
            r_single = 1.0 / g_total_single if g_total_single > 0 else 0
            r_total = r_single / n_design
            
            self.vc_res_single_rth.setText(f"{r_single:.1f} °C/W")
            self.vc_res_total_rth.setText(f"{r_total:.2f} °C/W")

        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")


# ==============================================================================
# 4. 单位换算 (Unit Converter)
# ==============================================================================
class UnitConverterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        
        grp_len = QGroupBox("1. 长度/距离换算 (mil / mm / inch)")
        grid_len = QGridLayout()
        grid_len.setVerticalSpacing(15)
        self.unit_len_val = QLineEdit("100")
        self.unit_len_from = QComboBox(); self.unit_len_from.addItems(["mil", "mm", "inch"])
        self.unit_len_to = QComboBox(); self.unit_len_to.addItems(["mm", "mil", "inch"])
        self.unit_len_res = QLineEdit(); self.unit_len_res.setReadOnly(True)
        self.unit_len_res.setStyleSheet("background-color: #f0f0f0; font-weight: bold; color: #2980b9; font-size: 14px;")
        btn_len = QPushButton("转换 ->"); btn_len.setFixedHeight(35); btn_len.setStyleSheet("background-color: #3498db; color: white; border-radius: 4px;")
        btn_len.clicked.connect(self.calc_unit_len)
        
        grid_len.addWidget(QLabel("输入数值:"), 0, 0); grid_len.addWidget(self.unit_len_val, 0, 1)
        grid_len.addWidget(self.unit_len_from, 0, 2); grid_len.addWidget(btn_len, 0, 3)
        grid_len.addWidget(self.unit_len_res, 0, 4); grid_len.addWidget(self.unit_len_to, 0, 5)
        grp_len.setLayout(grid_len)
        layout.addWidget(grp_len)
        
        grp_cu = QGroupBox("2. 铜箔厚度换算 (oz / um / mil)")
        grid_cu = QGridLayout()
        grid_cu.setVerticalSpacing(15)
        self.unit_cu_val = QLineEdit("1.0")
        self.unit_cu_from = QComboBox(); self.unit_cu_from.addItems(["oz", "um", "mil", "mm"])
        self.unit_cu_to = QComboBox(); self.unit_cu_to.addItems(["um", "mil", "oz", "mm"])
        self.unit_cu_res = QLineEdit(); self.unit_cu_res.setReadOnly(True)
        self.unit_cu_res.setStyleSheet("background-color: #f0f0f0; font-weight: bold; color: #d35400; font-size: 14px;")
        btn_cu = QPushButton("转换 ->"); btn_cu.setFixedHeight(35); btn_cu.setStyleSheet("background-color: #e67e22; color: white; border-radius: 4px;")
        btn_cu.clicked.connect(self.calc_unit_cu)
        
        grid_cu.addWidget(QLabel("输入数值:"), 0, 0); grid_cu.addWidget(self.unit_cu_val, 0, 1)
        grid_cu.addWidget(self.unit_cu_from, 0, 2); grid_cu.addWidget(btn_cu, 0, 3)
        grid_cu.addWidget(self.unit_cu_res, 0, 4); grid_cu.addWidget(self.unit_cu_to, 0, 5)
        grp_cu.setLayout(grid_cu)
        layout.addWidget(grp_cu)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def calc_unit_len(self):
        try:
            val = float(self.unit_len_val.text())
            u_from = self.unit_len_from.currentText()
            u_to = self.unit_len_to.currentText()
            val_mm = val if u_from == "mm" else (val * 0.0254 if u_from == "mil" else val * 25.4)
            res = val_mm if u_to == "mm" else (val_mm / 0.0254 if u_to == "mil" else val_mm / 25.4)
            self.unit_len_res.setText(f"{res:.4f}")
        except: pass

    def calc_unit_cu(self):
        try:
            val = float(self.unit_cu_val.text())
            u_from = self.unit_cu_from.currentText()
            u_to = self.unit_cu_to.currentText()
            oz_to_um = 34.79 
            val_um = val if u_from == "um" else (val * 1000 if u_from == "mm" else (val * oz_to_um if u_from == "oz" else val * 25.4))
            res = val_um if u_to == "um" else (val_um / 1000 if u_to == "mm" else (val_um / oz_to_um if u_to == "oz" else val_um / 25.4))
            self.unit_cu_res.setText(f"{res:.4f}")
        except: pass

# ==============================================================================
# 5. 方块电阻计算 (Trace Resistance - Square Counting) [NEW]
# ==============================================================================
class TraceSquareResistanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：基于“方块数 (Number of Squares)”快速估算 PCB 铜箔电阻。适用于不规则形状大电流铜皮压降估算。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. 铜箔方阻 (Sheet Resistance)
        grp_sheet = QGroupBox("1. 铜箔方阻 (Sheet Resistance)")
        grid_sheet = QGridLayout()
        grid_sheet.setVerticalSpacing(12)
        
        self.sq_thick = QLineEdit("1.0")
        self.sq_thick_unit = QComboBox(); self.sq_thick_unit.addItems(["oz", "um", "mm", "mil"])
        h_th = QHBoxLayout(); h_th.addWidget(self.sq_thick); h_th.addWidget(self.sq_thick_unit); h_th.setContentsMargins(0,0,0,0)
        grid_sheet.addWidget(QLabel("铜厚:"), 0, 0); grid_sheet.addLayout(h_th, 0, 1)
        
        self.sq_temp = QLineEdit("25")
        grid_sheet.addWidget(QLabel("工作温度 [°C]:"), 0, 2); grid_sheet.addWidget(self.sq_temp, 0, 3)
        
        self.res_r_sheet = QLineEdit(); self.res_r_sheet.setReadOnly(True)
        self.res_r_sheet.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
        grid_sheet.addWidget(QLabel("计算方阻 R_sq [mΩ/□]:"), 1, 0); grid_sheet.addWidget(self.res_r_sheet, 1, 1, 1, 3)
        
        l_form1 = QLabel()
        l_form1.setPixmap(render_formula(r'R_{sq} = \frac{\rho}{t} \approx \frac{0.5}{T_{oz}} \text{ m}\Omega'))
        grid_sheet.addWidget(l_form1, 2, 0, 1, 4)
        
        grp_sheet.setLayout(grid_sheet)
        layout.addWidget(grp_sheet)
        
        # 2. 走线电阻
        grp_trace = QGroupBox("2. 走线电阻估算")
        grid_tr = QGridLayout()
        grid_tr.setVerticalSpacing(12)
        
        # 模式选择
        self.rb_count = QRadioButton("直接输入方块数 N"); self.rb_count.setChecked(True)
        self.rb_dim = QRadioButton("输入长宽 L/W")
        bg = QButtonGroup(self); bg.addButton(self.rb_count); bg.addButton(self.rb_dim)
        bg.buttonClicked.connect(self.update_calc_mode)
        
        h_rb = QHBoxLayout(); h_rb.addWidget(self.rb_count); h_rb.addWidget(self.rb_dim)
        grid_tr.addLayout(h_rb, 0, 0, 1, 4)
        
        self.sq_n = QLineEdit("5"); self.sq_n.setPlaceholderText("方块数")
        self.lbl_n = QLabel("方块数量 N (L/W):")
        grid_tr.addWidget(self.lbl_n, 1, 0); grid_tr.addWidget(self.sq_n, 1, 1)
        
        self.sq_l = QLineEdit("10"); self.sq_l.setPlaceholderText("长度 mm")
        self.sq_w = QLineEdit("2"); self.sq_w.setPlaceholderText("宽度 mm")
        self.lbl_l = QLabel("长度 L:"); self.lbl_w = QLabel("宽度 W:")
        
        grid_tr.addWidget(self.lbl_l, 1, 0); grid_tr.addWidget(self.sq_l, 1, 1)
        grid_tr.addWidget(self.lbl_w, 1, 2); grid_tr.addWidget(self.sq_w, 1, 3)
        
        # 结果
        btn_calc = QPushButton("计算总电阻")
        btn_calc.setFixedHeight(40); btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_resistance)
        grid_tr.addWidget(btn_calc, 2, 0, 1, 4)
        
        self.res_r_total = QLineEdit(); self.res_r_total.setReadOnly(True)
        self.res_r_total.setStyleSheet("background-color: #f4ecf7; font-weight: bold; color: #8e44ad; font-size: 16px;")
        grid_tr.addWidget(QLabel("总电阻 R_trace [mΩ]:"), 3, 0); grid_tr.addWidget(self.res_r_total, 3, 1, 1, 3)
        
        grp_trace.setLayout(grid_tr)
        layout.addWidget(grp_trace)
        
        # 3. 采样电阻误差估算
        grp_shunt = QGroupBox("3. 采样电阻(Shunt) 焊盘误差分析")
        grid_sh = QGridLayout()
        grid_sh.setVerticalSpacing(12)
        
        self.sh_r = QLineEdit("1.0"); grid_sh.addWidget(QLabel("采样电阻阻值 [mΩ]:"), 0, 0); grid_sh.addWidget(self.sh_r, 0, 1)
        self.sh_w = QLineEdit("5.0"); grid_sh.addWidget(QLabel("焊盘/走线宽度 [mm]:"), 0, 2); grid_sh.addWidget(self.sh_w, 0, 3)
        
        self.sh_l_err = QLineEdit("2.0"); self.sh_l_err.setToolTip("开尔文接线点偏移距离，即误包含了多少长度的铜箔")
        grid_sh.addWidget(QLabel("接线偏移长度 L_err [mm]:"), 1, 0); grid_sh.addWidget(self.sh_l_err, 1, 1)
        
        btn_sh = QPushButton("计算误差")
        btn_sh.setFixedHeight(40); btn_sh.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        btn_sh.clicked.connect(self.calc_shunt_error)
        grid_sh.addWidget(btn_sh, 1, 2, 1, 2)
        
        self.res_sh_err_r = QLineEdit(); self.res_sh_err_pct = QLineEdit()
        self.res_sh_err_r.setReadOnly(True); self.res_sh_err_pct.setReadOnly(True)
        self.res_sh_err_pct.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold;")
        
        grid_sh.addWidget(QLabel("引入寄生电阻:"), 2, 0); grid_sh.addWidget(self.res_sh_err_r, 2, 1)
        grid_sh.addWidget(QLabel("测量误差百分比:"), 2, 2); grid_sh.addWidget(self.res_sh_err_pct, 2, 3)
        
        grp_shunt.setLayout(grid_sh)
        layout.addWidget(grp_shunt)
        
        layout.addStretch()
        self.setLayout(layout)
        self.update_calc_mode()
        
    def update_calc_mode(self):
        is_count = self.rb_count.isChecked()
        self.sq_n.setVisible(is_count); self.lbl_n.setVisible(is_count)
        self.sq_l.setVisible(not is_count); self.lbl_l.setVisible(not is_count)
        self.sq_w.setVisible(not is_count); self.lbl_w.setVisible(not is_count)

    def get_sheet_resistance(self):
        try:
            t_val = float(self.sq_thick.text())
            u = self.sq_thick_unit.currentText()
            temp = float(self.sq_temp.text())
            
            # Convert to meters
            if u == "oz": t_m = t_val * 35e-6
            elif u == "um": t_m = t_val * 1e-6
            elif u == "mm": t_m = t_val * 1e-3
            else: t_m = t_val * 25.4e-6
            
            if t_m <= 0: return None
            
            rho_25 = 1.724e-8
            rho = rho_25 * (1 + 0.00393 * (temp - 25))
            
            r_sq = rho / t_m
            return r_sq # Ohm/sq
        except: return None

    def calc_resistance(self):
        r_sq = self.get_sheet_resistance()
        if r_sq is None:
            QMessageBox.warning(self, "错误", "参数无效")
            return
        
        self.res_r_sheet.setText(f"{r_sq*1000:.4f}") # mOhm
        
        try:
            n = 0
            if self.rb_count.isChecked():
                n = float(self.sq_n.text())
            else:
                l = float(self.sq_l.text())
                w = float(self.sq_w.text())
                if w <= 0: raise ValueError
                n = l / w
            
            r_total = r_sq * n
            self.res_r_total.setText(f"{r_total*1000:.4f} mΩ")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的几何尺寸")

    def calc_shunt_error(self):
        r_sq = self.get_sheet_resistance()
        if r_sq is None:
            # Force update sheet res if user didn't click top button
            try:
                # Mock calc to update R_sheet field only
                pass 
            except: pass
            
        # Recalculate R_sheet locally to be safe
        try:
            t_val = float(self.sq_thick.text())
            u = self.sq_thick_unit.currentText()
            # Convert to meters
            if u == "oz": t_m = t_val * 35e-6
            elif u == "um": t_m = t_val * 1e-6
            elif u == "mm": t_m = t_val * 1e-3
            else: t_m = t_val * 25.4e-6
            rho = 1.724e-8 * (1 + 0.00393 * (float(self.sq_temp.text()) - 25))
            r_sq = rho / t_m
            
            self.res_r_sheet.setText(f"{r_sq*1000:.4f}")
            
            r_shunt = float(self.sh_r.text()) * 1e-3 # Ohm
            l_err = float(self.sh_l_err.text())
            w_trace = float(self.sh_w.text())
            
            if w_trace <= 0 or r_shunt <= 0: raise ValueError
            
            n_err = l_err / w_trace
            r_parasitic = r_sq * n_err
            
            err_pct = (r_parasitic / r_shunt) * 100
            
            self.res_sh_err_r.setText(f"{r_parasitic*1000:.4f} mΩ")
            self.res_sh_err_pct.setText(f"+{err_pct:.2f}%")
            
        except Exception as e:
             QMessageBox.warning(self, "错误", "输入无效")