from modules.base_module import BaseModule
# ntc_calculator_window.py

import math
from io import BytesIO
import matplotlib.pyplot as plt

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox, QTextEdit, 
                             QRadioButton, QButtonGroup, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class NtcCalculatorWindow(BaseModule):
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "NTC 热敏电阻"
    description = "单点计算 / 查表 / 拟合 / 选型"
    window_id = "sense_ntc"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('NTC 热敏电阻计算工具 (NTC Calculator)')
        self.setGeometry(350, 350, 950, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部说明
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("NTC 深度指南 / 线性化详解")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # Tab
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_calc = QWidget()
        self.tab_table = QWidget()
        self.tab_sh = QWidget()
        self.tab_opt = QWidget() # New: Resistor Optimization

        self.init_calc_ui(self.tab_calc)
        self.init_table_ui(self.tab_table)
        self.init_sh_ui(self.tab_sh)
        self.init_opt_ui(self.tab_opt) # New

        self.tabs.addTab(self.tab_calc, "1. 单点计算 (B值公式)")
        self.tabs.addTab(self.tab_table, "2. 查表生成 (Table Gen)")
        self.tabs.addTab(self.tab_sh, "3. 高精度拟合 (Steinhart-Hart)")
        self.tabs.addTab(self.tab_opt, "4. 分压电阻选型 (R_div Opt)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Common Inputs (NTC Specs & Circuit)
    # ==============================================================================
    def create_param_group(self):
        grp = QGroupBox("1. NTC 参数与电路配置")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        # NTC Specs
        self.ntc_r25 = QLineEdit("10")
        self.ntc_r25.setToolTip("25°C 时的标称阻值 (R25)")
        grid.addWidget(QLabel("R25 [kΩ]:"), 0, 0); grid.addWidget(self.ntc_r25, 0, 1)
        
        self.ntc_beta = QLineEdit("3950")
        self.ntc_beta.setToolTip("B值常数 (Beta Value)\n通常查 Datasheet 的 B25/50 或 B25/85")
        grid.addWidget(QLabel("B值 (Beta) [K]:"), 0, 2); grid.addWidget(self.ntc_beta, 0, 3)
        
        # Circuit
        grid.addWidget(QLabel("-----------------"), 1, 0, 1, 4)
        
        # Circuit Type (Radio)
        self.rb_pullup = QRadioButton("上拉电阻模式 (Pull-up)")
        self.rb_pulldown = QRadioButton("下拉电阻模式 (Pull-down)")
        self.rb_pullup.setChecked(True)
        self.rb_group = QButtonGroup()
        self.rb_group.addButton(self.rb_pullup)
        self.rb_group.addButton(self.rb_pulldown)
        
        hbox_rb = QHBoxLayout()
        hbox_rb.addWidget(self.rb_pullup)
        hbox_rb.addWidget(self.rb_pulldown)
        grid.addLayout(hbox_rb, 2, 0, 1, 4)
        
        # Resistor & Vref
        self.circuit_r = QLineEdit("10")
        self.circuit_r.setToolTip("分压电阻阻值\n通常选与 NTC 常温阻值接近的值 (如 10k)")
        grid.addWidget(QLabel("分压电阻 (R_div) [kΩ]:"), 3, 0); grid.addWidget(self.circuit_r, 3, 1)
        
        self.circuit_vref = QLineEdit("3.3")
        self.circuit_vref.setToolTip("ADC 参考电压 / 供电电压")
        grid.addWidget(QLabel("参考电压 (Vref) [V]:"), 3, 2); grid.addWidget(self.circuit_vref, 3, 3)
        
        grp.setLayout(grid)
        return grp

    # ==============================================================================
    # Tab 1: Single Point Calculation
    # ==============================================================================
    def init_calc_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Add shared params
        self.param_group_1 = self.create_param_group()
        layout.addWidget(self.param_group_1)
        
        # Calculation Mode
        grp_calc = QGroupBox("2. 计算器")
        grid = QGridLayout()
        
        self.calc_mode = QComboBox()
        self.calc_mode.addItems(["已知温度 T -> 求电阻 R & 电压 V", "已知电压 V -> 求温度 T", "已知电阻 R -> 求温度 T"])
        self.calc_mode.currentIndexChanged.connect(self.update_calc_ui)
        grid.addWidget(QLabel(" 计算目标:"), 0, 0); grid.addWidget(self.calc_mode, 0, 1)
        
        self.inp_val = QLineEdit("25")
        self.inp_label = QLabel("输入温度 [°C]:")
        grid.addWidget(self.inp_label, 1, 0); grid.addWidget(self.inp_val, 1, 1)
        
        btn = QPushButton("计算")
        btn.setFixedHeight(40)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.run_calc)
        grid.addWidget(btn, 2, 0, 1, 2)
        
        grp_calc.setLayout(grid)
        layout.addWidget(grp_calc)
        
        # Results
        grp_res = QGroupBox("计算结果")
        res_layout = QGridLayout()
        
        self.res_r = QLineEdit()
        self.res_v = QLineEdit()
        self.res_t = QLineEdit()
        
        res_layout.addWidget(QLabel("NTC 阻值 (R_ntc):"), 0, 0); res_layout.addWidget(self.res_r, 0, 1)
        res_layout.addWidget(QLabel("ADC 电压 (V_adc):"), 1, 0); res_layout.addWidget(self.res_v, 1, 1)
        res_layout.addWidget(QLabel("计算温度 (Temp):"), 2, 0); res_layout.addWidget(self.res_t, 2, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_r, self.res_v, self.res_t]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(res_layout)
        layout.addWidget(grp_res)
        layout.addStretch()
        
        tab.setLayout(layout)

    def update_calc_ui(self):
        idx = self.calc_mode.currentIndex()
        if idx == 0:
            self.inp_label.setText("输入温度 [°C]:")
            self.inp_val.setText("25")
        elif idx == 1:
            self.inp_label.setText("输入 ADC 电压 [V]:")
            self.inp_val.setText("1.65")
        else:
            self.inp_label.setText("输入 NTC 阻值 [kΩ]:")
            self.inp_val.setText("10")
            
        self.res_r.setText(""); self.res_v.setText(""); self.res_t.setText("")

    def get_ntc_r_from_t(self, t_c, r25, beta):
        # R = R25 * exp(B * (1/T - 1/T25))
        t_k = t_c + 273.15
        t25_k = 25.0 + 273.15
        return r25 * math.exp(beta * (1.0/t_k - 1.0/t25_k))

    def get_ntc_t_from_r(self, r_ntc, r25, beta):
        # T = 1 / ( (1/T25) + (1/B)*ln(R/R25) )
        if r_ntc <= 0: return -999
        t25_k = 25.0 + 273.15
        inv_t = (1.0/t25_k) + (1.0/beta) * math.log(r_ntc/r25)
        return (1.0/inv_t) - 273.15

    def run_calc(self):
        try:
            r25 = float(self.ntc_r25.text())
            beta = float(self.ntc_beta.text())
            r_div = float(self.circuit_r.text())
            vref = float(self.circuit_vref.text())
            inp = float(self.inp_val.text())
            is_pullup = self.rb_pullup.isChecked()
            
            idx = self.calc_mode.currentIndex()
            
            if idx == 0: # T -> R, V
                t_c = inp
                r_ntc = self.get_ntc_r_from_t(t_c, r25, beta)
                
                if is_pullup:
                    v_adc = vref * r_ntc / (r_ntc + r_div)
                else:
                    v_adc = vref * r_div / (r_ntc + r_div)
                    
                self.res_t.setText(f"{t_c:.2f} °C")
                self.res_r.setText(f"{r_ntc:.4f} kΩ")
                self.res_v.setText(f"{v_adc:.4f} V")
                
            elif idx == 1: # V -> T
                v_in = inp
                if v_in <= 0 or v_in >= vref: raise ValueError("电压超出范围")
                
                if is_pullup:
                    r_ntc = (v_in * r_div) / (vref - v_in)
                else:
                    r_ntc = r_div * (vref - v_in) / v_in
                    
                t_c = self.get_ntc_t_from_r(r_ntc, r25, beta)
                
                self.res_v.setText(f"{v_in:.4f} V")
                self.res_r.setText(f"{r_ntc:.4f} kΩ")
                self.res_t.setText(f"{t_c:.2f} °C")
                
            else: # R -> T
                r_in = inp
                t_c = self.get_ntc_t_from_r(r_in, r25, beta)
                
                if is_pullup:
                    v_adc = vref * r_in / (r_in + r_div)
                else:
                    v_adc = vref * r_div / (r_in + r_div)
                    
                self.res_r.setText(f"{r_in:.4f} kΩ")
                self.res_t.setText(f"{t_c:.2f} °C")
                self.res_v.setText(f"{v_adc:.4f} V")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算出错: {str(e)}\n请检查输入数值")

    # ==============================================================================
    # Tab 2: Table Generator
    # ==============================================================================
    def init_table_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Settings
        grp_set = QGroupBox("生成设置")
        grid = QGridLayout()
        
        self.tbl_start_t = QLineEdit("-40"); grid.addWidget(QLabel("起始温度 [°C]:"), 0, 0); grid.addWidget(self.tbl_start_t, 0, 1)
        self.tbl_end_t = QLineEdit("125"); grid.addWidget(QLabel("结束温度 [°C]:"), 0, 2); grid.addWidget(self.tbl_end_t, 0, 3)
        self.tbl_step = QLineEdit("1"); grid.addWidget(QLabel("步长 [°C]:"), 1, 0); grid.addWidget(self.tbl_step, 1, 1)
        
        self.tbl_adc_res = QLineEdit("4095"); grid.addWidget(QLabel("ADC分辨率 (Max):"), 1, 2); grid.addWidget(self.tbl_adc_res, 1, 3)
        grid.addWidget(QLabel("(例如 12bit 填 4095, 10bit 填 1023)"), 1, 4)
        
        grp_set.setLayout(grid)
        layout.addWidget(grp_set)
        
        # Note
        note = QLabel("提示：此工具将使用 'Tab 1' 中配置的 NTC 参数和电路参数生成代码。")
        note.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(note)
        
        # Buttons Row
        btn_layout = QHBoxLayout()
        
        btn_gen = QPushButton("生成 C 语言查表代码")
        btn_gen.setFixedHeight(45)
        btn_gen.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_gen.clicked.connect(self.generate_table)
        
        btn_plot = QPushButton("查看 ADC-温度 曲线")
        btn_plot.setFixedHeight(45)
        btn_plot.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold;")
        btn_plot.clicked.connect(self.plot_curve)
        
        btn_layout.addWidget(btn_gen, 2)
        btn_layout.addWidget(btn_plot, 1)
        layout.addLayout(btn_layout)
        
        # Output Area
        self.txt_output = QTextEdit()
        self.txt_output.setPlaceholderText("生成的代码将显示在这里...")
        self.txt_output.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self.txt_output)
        
        tab.setLayout(layout)

    def generate_table(self):
        try:
            # Get Params from Tab 1
            r25 = float(self.ntc_r25.text())
            beta = float(self.ntc_beta.text())
            r_div = float(self.circuit_r.text())
            is_pullup = self.rb_pullup.isChecked()
            
            # Get Table Settings
            start_t = int(self.tbl_start_t.text())
            end_t = int(self.tbl_end_t.text())
            step = int(self.tbl_step.text())
            adc_max = int(self.tbl_adc_res.text())
            
            if start_t >= end_t or step <= 0: raise ValueError("温度范围或步长无效")
            
            # Generate
            code = []
            code.append(f"// NTC Table Generated by Hardware Toolbox")
            code.append(f"// R25={r25}k, B={beta}, R_div={r_div}k, Pull-up={is_pullup}")
            code.append(f"// Range: {start_t}C to {end_t}C, Step: {step}C")
            code.append(f"// ADC Max: {adc_max}")
            code.append("")
            code.append(f"#define NTC_TABLE_START_TEMP ({start_t})")
            code.append(f"#define NTC_TABLE_STEP ({step})")
            code.append(f"const uint16_t ntc_adc_table[] = {{")
            
            line_vals = []
            for t in range(start_t, end_t + 1, step):
                r_ntc = self.get_ntc_r_from_t(float(t), r25, beta)
                
                if is_pullup:
                    ratio = r_ntc / (r_ntc + r_div)
                else:
                    ratio = r_div / (r_ntc + r_div)
                
                adc_val = int(ratio * adc_max + 0.5)
                if adc_val > adc_max: adc_val = adc_max
                if adc_val < 0: adc_val = 0
                
                line_vals.append(f"{adc_val}")
                
                if len(line_vals) >= 10:
                    code.append("    " + ", ".join(line_vals) + ",")
                    line_vals = []
            
            if line_vals:
                code.append("    " + ", ".join(line_vals))
                
            code.append("};")
            
            self.txt_output.setPlainText("\n".join(code))
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"参数错误: {str(e)}")

    def plot_curve(self):
        try:
            # 1. 获取参数
            r25 = float(self.ntc_r25.text())
            beta = float(self.ntc_beta.text())
            r_div = float(self.circuit_r.text())
            is_pullup = self.rb_pullup.isChecked()
            
            start_t = int(self.tbl_start_t.text())
            end_t = int(self.tbl_end_t.text())
            adc_max = int(self.tbl_adc_res.text())
            
            if start_t >= end_t: raise ValueError("温度范围无效")
            
            # 2. 生成数据点
            temp_list = []
            adc_list = []
            
            step = 1 if (end_t - start_t) < 200 else 2 
            for t in range(start_t, end_t + 1, step):
                r_ntc = self.get_ntc_r_from_t(float(t), r25, beta)
                if is_pullup:
                    ratio = r_ntc / (r_ntc + r_div)
                else:
                    ratio = r_div / (r_ntc + r_div)
                
                adc_val = ratio * adc_max
                temp_list.append(t)
                adc_list.append(adc_val)
            
            # 3. 绘图 (matplotlib)
            plt.rcParams.update({'font.size': 10, 'font.family': 'sans-serif'})
            fig = plt.figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            ax.plot(adc_list, temp_list, label='Temp vs ADC', color='#e74c3c', linewidth=2)
            ax.set_xlabel(f"ADC Value (0 ~ {adc_max})")
            ax.set_ylabel("Temperature (°C)")
            ax.set_title("NTC Characteristic Curve: Temp vs ADC")
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend()
            
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            
            # 4. 显示弹窗
            dialog = QDialog(self)
            dialog.setWindowTitle(f"ADC-温度 曲线 ({start_t}°C ~ {end_t}°C)")
            dialog.resize(850, 650)
            
            layout = QVBoxLayout(dialog)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            scroll.setWidget(content)
            
            l_layout = QVBoxLayout(content)
            img_label = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            img_label.setPixmap(pixmap)
            img_label.setAlignment(Qt.AlignCenter)
            l_layout.addWidget(img_label)
            
            layout.addWidget(scroll)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"绘图失败: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"绘图引擎错误: {str(e)}")

    # ==============================================================================
    # Tab 3: Steinhart-Hart Fitting
    # ==============================================================================
    def init_sh_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Inputs
        grp_in = QGroupBox("1. 输入三个校准点 (Data Points)")
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        
        grid.addWidget(QLabel("Temperature [°C]"), 0, 1)
        grid.addWidget(QLabel("Resistance R [kΩ]"), 0, 2)
        
        self.sh_t1 = QLineEdit("-40"); self.sh_r1 = QLineEdit("336.5") # Example values for 10k NTC
        grid.addWidget(QLabel("Point 1 (Low):"), 1, 0)
        grid.addWidget(self.sh_t1, 1, 1); grid.addWidget(self.sh_r1, 1, 2)
        
        self.sh_t2 = QLineEdit("25"); self.sh_r2 = QLineEdit("10.0")
        grid.addWidget(QLabel("Point 2 (Mid):"), 2, 0)
        grid.addWidget(self.sh_t2, 2, 1); grid.addWidget(self.sh_r2, 2, 2)
        
        self.sh_t3 = QLineEdit("125"); self.sh_r3 = QLineEdit("0.34")
        grid.addWidget(QLabel("Point 3 (High):"), 3, 0)
        grid.addWidget(self.sh_t3, 3, 1); grid.addWidget(self.sh_r3, 3, 2)
        
        btn_calc = QPushButton("计算 A, B, C 系数")
        btn_calc.setFixedHeight(40)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_sh_coeffs)
        grid.addWidget(btn_calc, 4, 0, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # 2. Results
        grp_res = QGroupBox("2. 拟合系数 (Steinhart-Hart Coefficients)")
        r_grid = QGridLayout()
        
        self.res_a = QLineEdit(); self.res_a.setReadOnly(True)
        self.res_b = QLineEdit(); self.res_b.setReadOnly(True)
        self.res_c = QLineEdit(); self.res_c.setReadOnly(True)
        
        r_grid.addWidget(QLabel("A ="), 0, 0); r_grid.addWidget(self.res_a, 0, 1)
        r_grid.addWidget(QLabel("B ="), 1, 0); r_grid.addWidget(self.res_b, 1, 1)
        r_grid.addWidget(QLabel("C ="), 2, 0); r_grid.addWidget(self.res_c, 2, 1)
        
        # Formula display
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r"1/T = A + B \ln(R) + C (\ln(R))^3"))
        r_grid.addWidget(l_form, 0, 2, 3, 1)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 3. Validation
        grp_val = QGroupBox("3. 验证 (Validation)")
        v_grid = QGridLayout()
        
        self.val_r = QLineEdit("10.0"); 
        v_grid.addWidget(QLabel("输入 R [kΩ]:"), 0, 0); v_grid.addWidget(self.val_r, 0, 1)
        
        self.val_t = QLineEdit(); self.val_t.setReadOnly(True)
        v_grid.addWidget(QLabel("计算 T [°C]:"), 0, 2); v_grid.addWidget(self.val_t, 0, 3)
        
        btn_val = QPushButton("验证")
        btn_val.clicked.connect(self.verify_sh)
        v_grid.addWidget(btn_val, 0, 4)
        
        grp_val.setLayout(v_grid)
        layout.addWidget(grp_val)
        
        layout.addStretch()
        tab.setLayout(layout)

    def solve_linear_3x3(self, matrix, result):
        # Cramer's rule or simple elimination for 3x3
        m = matrix
        det = m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1]) - \
              m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0]) + \
              m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0])
              
        if abs(det) < 1e-15: return None
        
        def calc_det_k(k):
            tm = [row[:] for row in m]
            for i in range(3):
                tm[i][k] = result[i]
            return tm[0][0]*(tm[1][1]*tm[2][2] - tm[1][2]*tm[2][1]) - \
                   tm[0][1]*(tm[1][0]*tm[2][2] - tm[1][2]*tm[2][0]) + \
                   tm[0][2]*(tm[1][0]*tm[2][1] - tm[1][1]*tm[2][0])

        x = calc_det_k(0) / det
        y = calc_det_k(1) / det
        z = calc_det_k(2) / det
        return (x, y, z)

    def calc_sh_coeffs(self):
        try:
            t_vals = [float(self.sh_t1.text()), float(self.sh_t2.text()), float(self.sh_t3.text())]
            r_vals = [float(self.sh_r1.text()), float(self.sh_r2.text()), float(self.sh_r3.text())]
            
            matrix = []
            results = []
            
            for i in range(3):
                if r_vals[i] <= 0: raise ValueError(f"R cannot be 0 or negative (Row {i+1})")
                tk = t_vals[i] + 273.15
                ln_r = math.log(r_vals[i])
                
                row = [1.0, ln_r, ln_r**3]
                matrix.append(row)
                results.append(1.0 / tk)
                
            solution = self.solve_linear_3x3(matrix, results)
            if solution is None:
                QMessageBox.warning(self, "错误", "无法求解 (行列式为0)，请检查输入点是否重复")
                return
                
            a, b, c = solution
            self.sh_a = a; self.sh_b = b; self.sh_c = c
            
            self.res_a.setText(f"{a:.6e}")
            self.res_b.setText(f"{b:.6e}")
            self.res_c.setText(f"{c:.6e}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入错误: {str(e)}")

    def verify_sh(self):
        try:
            if not hasattr(self, 'sh_a'): return
            r_in = float(self.val_r.text())
            if r_in <= 0: return
            ln_r = math.log(r_in)
            inv_t = self.sh_a + self.sh_b * ln_r + self.sh_c * (ln_r**3)
            if inv_t == 0: return
            tk = 1.0 / inv_t
            tc = tk - 273.15
            self.val_t.setText(f"{tc:.3f} °C")
        except: pass

    # ==============================================================================
    # Tab 4: Resistor Divider Optimization (NEW)
    # ==============================================================================
    def init_opt_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explanation
        info = QLabel("功能说明: 计算使目标温度点附近 ADC 分辨率最高（电压变化率最大）的最佳分压电阻 R_div。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #555; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Input Group
        grp_in = QGroupBox("1. 目标设定")
        grid = QGridLayout()
        
        self.opt_t_center = QLineEdit("90")
        grid.addWidget(QLabel("关注的中心温度 T_center [°C]:"), 0, 0)
        grid.addWidget(self.opt_t_center, 0, 1)
        grid.addWidget(QLabel("(例如: 监控电池过热关注 60°C，水温关注 90°C)"), 0, 2)
        
        # Note about source params
        lbl_hint = QLabel("提示: 此计算使用 Tab 1 中的 NTC 参数 (R25, Beta)。")
        lbl_hint.setStyleSheet("color: #7f8c8d;")
        grid.addWidget(lbl_hint, 1, 0, 1, 3)

        btn_calc = QPushButton("计算最佳分压电阻 (Calculate Optimal R_div)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calculate_opt_r)
        grid.addWidget(btn_calc, 2, 0, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # Result Group
        grp_res = QGroupBox("2. 推荐结果")
        r_grid = QGridLayout()
        
        self.opt_res_r = QLineEdit()
        self.opt_res_r.setReadOnly(True)
        self.opt_res_r.setStyleSheet("font-size: 14px; font-weight: bold; color: #d35400; background: #fdf2e9;")
        
        r_grid.addWidget(QLabel("理论最佳 R_div [kΩ]:"), 0, 0)
        r_grid.addWidget(self.opt_res_r, 0, 1)
        r_grid.addWidget(QLabel("(建议取最接近的 E96/E24 标准电阻)"), 0, 2)
        
        # 2024-Update: Added display area for calculation details (No Popup)
        self.opt_result_msg = QLabel("")
        self.opt_result_msg.setWordWrap(True)
        self.opt_result_msg.setStyleSheet("color: #2980b9; font-size: 13px; margin-top: 8px;")
        r_grid.addWidget(self.opt_result_msg, 1, 0, 1, 3)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Plot Preview
        btn_plot = QPushButton("显示灵敏度曲线 (Sensitivity Plot)")
        btn_plot.clicked.connect(self.plot_opt_sensitivity)
        layout.addWidget(btn_plot)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calculate_opt_r(self):
        try:
            # Get NTC Params from Tab 1
            r25 = float(self.ntc_r25.text())
            beta = float(self.ntc_beta.text())
            t_center = float(self.opt_t_center.text())
            
            # Principle: Max sensitivity (dV/dT) occurs when R_div = R_ntc @ T
            # Reference: Voltage Divider equation derivation d2V/dT2 = 0
            
            r_target = self.get_ntc_r_from_t(t_center, r25, beta)
            
            self.opt_res_r.setText(f"{r_target:.4f}")
            self.opt_r_target_cache = r_target # Save for plotting
            
            # Update the label instead of showing a Popup
            msg = (f"详细说明: 在目标温度 {t_center}°C 时，NTC 的阻值为 {r_target:.4f} kΩ。\n"
                   f"根据阻抗匹配原理，当分压电阻 R_div 等于此时的 NTC 阻值时，"
                   f"电路在该温度附近的电压变化率 (灵敏度) 最大。")
            self.opt_result_msg.setText(msg)
            
        except Exception as e:
             QMessageBox.warning(self, "错误", f"输入数值无效: {str(e)}")

    def plot_opt_sensitivity(self):
        try:
            if not hasattr(self, 'opt_r_target_cache'):
                self.calculate_opt_r()
                
            r25 = float(self.ntc_r25.text())
            beta = float(self.ntc_beta.text())
            t_center = float(self.opt_t_center.text())
            r_div = self.opt_r_target_cache # Use the calculated optimal
            vref = float(self.circuit_vref.text())
            
            # Range: T_center +/- 50 deg
            t_start = int(t_center - 50)
            t_end = int(t_center + 50)
            
            temps = []
            sensitivities = [] # dV/dT (mV/C)
            voltages = []
            
            for t in range(t_start, t_end + 1, 1):
                temps.append(t)
                
                # Simple finite difference for derivative
                r_t = self.get_ntc_r_from_t(t, r25, beta)
                r_t_plus = self.get_ntc_r_from_t(t + 0.1, r25, beta)
                
                # Assume Pull-up resistor (NTC at bottom) V = Vref * R_ntc / (R_ntc + R_div)
                # Or Pull-up NTC (Resistor at bottom) V = Vref * R_div / (R_ntc + R_div)
                # Sensitivity magnitude is same for both structures
                
                v_now = vref * r_t / (r_t + r_div)
                v_next = vref * r_t_plus / (r_t_plus + r_div)
                
                diff = abs(v_next - v_now) / 0.1 # V/degC
                sensitivities.append(diff * 1000) # mV/degC
                voltages.append(v_now)

            # Plot
            plt.rcParams.update({'font.size': 10, 'font.family': 'sans-serif'})
            fig, ax1 = plt.figure(figsize=(9, 6), dpi=100), plt.gca()
            fig = plt.gcf()
            
            color = 'tab:red'
            ax1.set_xlabel('Temperature (°C)')
            ax1.set_ylabel('Sensitivity |dV/dT| (mV/°C)', color=color)
            ax1.plot(temps, sensitivities, color=color, linewidth=2, label='Sensitivity')
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.axvline(x=t_center, color='green', linestyle='--', label=f'Center {t_center}°C')
            ax1.grid(True, linestyle='--', alpha=0.5)
            
            ax2 = ax1.twinx()
            color = 'tab:blue'
            ax2.set_ylabel('ADC Voltage (V)', color=color)
            ax2.plot(temps, voltages, color=color, linestyle=':', label='Voltage')
            ax2.tick_params(axis='y', labelcolor=color)
            
            plt.title(f"Optimization Analysis (R_div = {r_div:.2f} kΩ)")
            fig.tight_layout()
            
            # Show
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("灵敏度分析")
            dialog.resize(900, 650)
            l_layout = QVBoxLayout(dialog)
            img = QLabel()
            pix = QPixmap()
            pix.loadFromData(buf.getvalue())
            img.setPixmap(pix)
            img.setAlignment(Qt.AlignCenter)
            l_layout.addWidget(img)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"参数错误: {str(e)}")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("NTC 深度原理指南")
        dialog.resize(850, 700)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px; font-size: 13px;")
        
        html = """
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 20px;}
            h3 { color: #d35400; margin-top: 15px; }
            .box { background-color: #ecf0f1; padding: 10px; border-left: 5px solid #bdc3c7; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; }
        </style>
        
        <h1>NTC 热敏电阻：从入门到精通</h1>
        
        <h2>1. 简单模型：B 值公式 (Beta Equation)</h2>
        <div class="box">
            <p><code>R = R25 * exp( B * (1/T - 1/T25) )</code></p>
            <p><b>适用场景：</b> 窄温域（如 0°C ~ 70°C），或对精度要求不高的消费类电子。</p>
            <p><b>缺点：</b> B 值本身不是常数，它随温度变化。在宽温域下，单一 B 值会带来较大误差。</p>
        </div>

        <h2>2. 高精度模型：Steinhart-Hart 方程</h2>
        <div class="box">
            <p><code>1/T = A + B*ln(R) + C*(ln(R))^3</code></p>
            <p><b>适用场景：</b> 车规级、工控、医疗等宽温域高精度应用。</p>
            <p><b>优势：</b> 通过三个点（低温、常温、高温）拟合，可以极好地修正 NTC 的非线性特性。</p>
        </div>
        
        <h2>3. 分压电阻线性化 (Linearization)</h2>
        <div class="box">
            <p>在简单的电阻分压电路中，为了获得最大的 ADC 分辨率（即单位温度变化引起的电压变化量最大），应合理选择分压电阻 R_div。</p>
            <p><b>结论：</b> 当 R_div 等于 NTC 在中心温度点的阻值时，该温度点附近的灵敏度 (dV/dT) 最大，线性度最好。</p>
            <p><i>例如：若主要监测 90°C 的水温，查表知 NTC 在 90°C 时为 0.9kΩ，则分压电阻选 1kΩ 比选 10kΩ 效果好得多。</i></p>
        </div>

        <h2>4. 硬件设计坑点</h2>
        <h3>自热效应 (Self-heating)</h3>
        <p>NTC 流过电流会发热。建议控制 NTC 功耗 < 1mW（或者 < NTC 耗散系数的 10%）。</p>
        
        <h3>ADC 阻抗匹配</h3>
        <p>如果 NTC 电路总阻抗太高（如 > 100k），ADC 采样时间不足会导致读数偏小。建议在 ADC 引脚加一个 10nF~100nF 的电容。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()