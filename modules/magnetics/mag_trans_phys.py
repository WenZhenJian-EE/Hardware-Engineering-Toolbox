# mag_trans_phys.py

import math
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QGridLayout, QGroupBox, QComboBox, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from utils import render_formula
from mag_trans_data import MATERIALS_DB, CORE_DB, create_core_selector

# 引入自定义的宽 Tab 样式
from mag_trans_topo import QTabWidget_Custom

class PhysicsAnalysisPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用自定义的宽 Tab 容器
        self.tabs = QTabWidget_Custom()
        
        self.tab_ap = QWidget() # AP法估算
        self.tab_fill = QWidget() # 填充率校核
        self.tab_loss = QWidget() # 磁损分析 Tab
        self.tab_leakage = QWidget() # 漏感估算 Tab
        self.tab_ac_loss = QWidget() # 绕组AC损耗
        self.tab_fit = QWidget() # New: Steinmetz 拟合

        self.init_ap_ui(self.tab_ap)
        self.init_fill_ui(self.tab_fill)
        self.init_loss_ui(self.tab_loss)
        self.init_ac_loss_ui(self.tab_ac_loss) 
        self.init_leakage_ui(self.tab_leakage)
        self.init_fit_ui(self.tab_fit) # Init New Tab

        self.tabs.addTab(self.tab_ap, "1. 磁芯选型估算 (AP法)")
        self.tabs.addTab(self.tab_fill, "2. 绕组填充率校核 (Fill)")
        self.tabs.addTab(self.tab_loss, "3. 磁芯损耗分析 (Core Loss)")
        self.tabs.addTab(self.tab_ac_loss, "4. 绕组 AC 损耗 (Proximity)") 
        self.tabs.addTab(self.tab_leakage, "5. 漏感工程估算 (Leakage)")
        self.tabs.addTab(self.tab_fit, "6. Steinmetz 拟合 (Curve Fitting)") # Add New Tab

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # ==============================================================================
    # Tab 1: AP 法磁芯估算
    # ==============================================================================
    def init_ap_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. 痛点描述与公式
        intro_box = QGroupBox("痛点解决：快速锁定磁芯尺寸")
        intro_layout = QVBoxLayout()
        lbl_formula = QLabel()
        lbl_formula.setPixmap(render_formula(r'AP = A_e \cdot A_w = \frac{P_{out}}{K \cdot \Delta B \cdot f \cdot J} \quad (cm^4)'))
        intro_layout.addWidget(lbl_formula)
        intro_box.setLayout(intro_layout)
        layout.addWidget(intro_box)

        # 2. 参数输入
        input_group = QGroupBox("1. 输入设计需求")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)

        self.ap_pout = QLineEdit("100"); grid.addWidget(QLabel("输出功率 Pout [W]:"), 0, 0); grid.addWidget(self.ap_pout, 0, 1)
        self.ap_fsw = QLineEdit("100"); grid.addWidget(QLabel("开关频率 f [kHz]:"), 0, 2); grid.addWidget(self.ap_fsw, 0, 3)
        
        self.ap_db = QLineEdit("0.2"); grid.addWidget(QLabel("磁通摆幅 ΔB [T] (推荐0.2):"), 1, 0); grid.addWidget(self.ap_db, 1, 1)
        self.ap_j = QLineEdit("4.5"); grid.addWidget(QLabel("电流密度 J [A/mm²] (推荐4-6):"), 1, 2); grid.addWidget(self.ap_j, 1, 3)

        self.ap_topo = QComboBox()
        # K值经验系数：影响分母。K越大，计算出的AP越小（说明该拓扑利用率高）
        self.ap_topo.addItem("反激 (Flyback) - Core利用率低", 1.8) 
        self.ap_topo.addItem("单管正激 (Forward)", 2.8)
        self.ap_topo.addItem("全桥/半桥/推挽 (Bridge/Push-Pull)", 4.0)
        grid.addWidget(QLabel("电路拓扑 (Topology):"), 2, 0); grid.addWidget(self.ap_topo, 2, 1, 1, 3)

        input_group.setLayout(grid)
        layout.addWidget(input_group)

        # 按钮
        btn_calc = QPushButton("计算 AP 值并推荐磁芯")
        btn_calc.setFixedHeight(50)
        btn_calc.setStyleSheet("background-color: #d35400; color: white; font-weight: bold; font-size: 14px;")
        btn_calc.clicked.connect(self.calc_ap_estimation)
        layout.addWidget(btn_calc)

        # 3. 结果显示
        res_group = QGroupBox("2. 估算结果与推荐")
        res_grid = QGridLayout()
        
        self.res_ap_val = QLineEdit()
        self.res_ap_val.setReadOnly(True)
        self.res_ap_val.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #fcece4;")
        res_grid.addWidget(QLabel("计算需求 AP 值 [cm^4]:"), 0, 0); res_grid.addWidget(self.res_ap_val, 0, 1)

        self.res_core_rec = QLabel("等待计算...")
        self.res_core_rec.setStyleSheet("font-size: 16px; font-weight: bold; color: #2e86c1; border: 2px dashed #bdc3c7; padding: 10px; border-radius: 6px;")
        self.res_core_rec.setAlignment(Qt.AlignCenter)
        res_grid.addWidget(QLabel("智能推荐磁芯:"), 1, 0); res_grid.addWidget(self.res_core_rec, 1, 1)

        res_group.setLayout(res_grid)
        layout.addWidget(res_group)

        layout.addStretch()
        tab.setLayout(layout)

    def calc_ap_estimation(self):
        try:
            pout = float(self.ap_pout.text())
            f_khz = float(self.ap_fsw.text())
            db_t = float(self.ap_db.text())
            j_amm2 = float(self.ap_j.text())
            k_topo = self.ap_topo.currentData()
            
            # AP_calc = Pout / (K_topo * dB * f_khz * J)
            # 系数已经过工程单位归一化
            ap_calc = pout / (k_topo * db_t * f_khz * j_amm2)
            
            self.res_ap_val.setText(f"{ap_calc:.4f} cm^4")

            # 寻找合适的磁芯
            candidates = []
            for name, ae, aw, ve in CORE_DB:
                # Core AP in cm^4 = (Ae_mm2 * Aw_mm2) / 10000
                core_ap = (ae * aw) / 10000.0
                if core_ap >= ap_calc * 0.95: # 允许 5% 的误差裕量
                    candidates.append((name, core_ap))

            if candidates:
                # 排序，找最小的满足条件的
                candidates.sort(key=lambda x: x[1])
                rec_name, rec_ap = candidates[0]
                rec_str = f"推荐: {rec_name} (AP={rec_ap:.3f})"
                if len(candidates) > 1:
                     rec_str += f"\n备选: {candidates[1][0]} (AP={candidates[1][1]:.3f})"
                self.res_core_rec.setText(rec_str)
                self.res_core_rec.setStyleSheet("font-size: 16px; font-weight: bold; color: #27ae60; border: 2px solid #27ae60; padding: 10px; border-radius: 6px;")
            else:
                self.res_core_rec.setText("需求过大，请考虑更大的磁芯 (如 EE55/PQ50)")
                self.res_core_rec.setStyleSheet("font-size: 16px; font-weight: bold; color: #c0392b; border: 2px solid #c0392b; padding: 10px; border-radius: 6px;")

        except Exception as e:
            QMessageBox.warning(self, "输入错误", "请输入有效的数字参数")

    # ==============================================================================
    # Tab 2: 绕组填充率校核 (Winding Fill Factor)
    # ==============================================================================
    def init_fill_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 说明
        info = QLabel("本工具用于计算绕组能否在给定的骨架窗口内绕下 (物理装配校核)。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 骨架窗口尺寸
        grp_bobbin = QGroupBox("1. 骨架窗口尺寸 (Bobbin Window)")
        grid_b = QGridLayout()
        
        self.fill_win_w = QLineEdit("8.0"); self.fill_win_w.setToolTip("骨架绕线槽的宽度 (Width)，即每一层能排线的长度")
        grid_b.addWidget(QLabel("窗口宽度 W [mm]:"), 0, 0); grid_b.addWidget(self.fill_win_w, 0, 1)
        
        self.fill_win_d = QLineEdit("3.0"); self.fill_win_d.setToolTip("骨架绕线槽的深度 (Depth)，即允许堆叠的最大厚度")
        grid_b.addWidget(QLabel("窗口深度/高度 H [mm]:"), 0, 2); grid_b.addWidget(self.fill_win_d, 0, 3)
        
        grp_bobbin.setLayout(grid_b)
        layout.addWidget(grp_bobbin)
        
        # 2. 绕组参数
        grp_wind = QGroupBox("2. 绕组参数 (Winding Spec)")
        grid_w = QGridLayout()
        
        self.fill_turns = QLineEdit("40"); grid_w.addWidget(QLabel("总匝数 N [Ts]:"), 0, 0); grid_w.addWidget(self.fill_turns, 0, 1)
        
        self.fill_dia = QLineEdit("0.35"); self.fill_dia.setToolTip("单根导线的外径 (包含绝缘层/漆皮)。如果是利兹线，请输入整束线的等效外径。")
        grid_w.addWidget(QLabel("线径 OD [mm] (含绝缘):"), 0, 2); grid_w.addWidget(self.fill_dia, 0, 3)
        
        self.fill_strands = QLineEdit("1"); self.fill_strands.setToolTip("多股并绕的股数。注意：此处假设多股线是“平铺”并绕的，会占用层宽。如果是绞合线(Litz)，股数填1，线径填绞合后的直径。")
        grid_w.addWidget(QLabel("并绕股数 (Strands):"), 1, 0); grid_w.addWidget(self.fill_strands, 1, 1)
        
        self.fill_tape = QLineEdit("0.05"); self.fill_tape.setToolTip("层间胶带厚度。每绕完一层通常会包胶带。")
        grid_w.addWidget(QLabel("层间胶带厚度 [mm]:"), 1, 2); grid_w.addWidget(self.fill_tape, 1, 3)
        
        grp_wind.setLayout(grid_w)
        layout.addWidget(grp_wind)
        
        # 按钮
        btn_calc = QPushButton("计算堆叠高度与填充率")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; font-size: 14px;")
        btn_calc.clicked.connect(self.calc_fill_factor)
        layout.addWidget(btn_calc)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_layers = QLineEdit()
        self.res_build = QLineEdit()
        self.res_ku = QLineEdit() # 铜填充率
        self.res_status = QLineEdit()
        
        r_grid.addWidget(QLabel("所需层数 (Layers):"), 0, 0); r_grid.addWidget(self.res_layers, 0, 1)
        r_grid.addWidget(QLabel("堆叠高度 (Build) [mm]:"), 0, 2); r_grid.addWidget(self.res_build, 0, 3)
        
        r_grid.addWidget(QLabel("铜填充系数 (Ku):"), 1, 0); r_grid.addWidget(self.res_ku, 1, 1)
        r_grid.addWidget(QLabel("装配校核结果:"), 1, 2); r_grid.addWidget(self.res_status, 1, 3)
        
        for w in [self.res_layers, self.res_build, self.res_ku, self.res_status]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #f0f0f0; font-weight: bold;")
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_fill_factor(self):
        try:
            # Inputs
            win_w = float(self.fill_win_w.text())
            win_h = float(self.fill_win_d.text())
            turns = float(self.fill_turns.text())
            dia = float(self.fill_dia.text())
            strands = int(float(self.fill_strands.text()))
            t_tape = float(self.fill_tape.text())
            
            if win_w <= 0 or win_h <= 0 or dia <= 0: raise ValueError
            
            # 1. Turns per layer
            # 假设并绕是平铺的，占用宽度 = dia * strands
            width_per_turn = dia * strands
            if width_per_turn > win_w:
                self.res_status.setText("单匝宽度 > 窗口宽度！")
                self.res_status.setStyleSheet("background-color: #ffcccc; color: red;")
                return
            
            # 考虑排线间隙，通常取 int
            turns_per_layer = math.floor(win_w / width_per_turn)
            if turns_per_layer == 0: turns_per_layer = 1 # 防除0，虽前面已判断
            
            # 2. Total Layers
            num_layers = math.ceil(turns / turns_per_layer)
            
            # 3. Build Height
            # Build = Layers * Dia + (Layers) * Tape (Top layer also usually taped)
            # 或者 (Layers-1)*Tape. 保守起见按 Layers*Tape 算 (外包胶带)
            build_h = num_layers * dia + (num_layers) * t_tape
            
            # 4. Copper Fill Factor (Ku)
            # Ku = Total Copper Area / Window Area
            # Copper Area = Turns * Strands * (pi * (d_cond/2)^2)
            # Note: dia is OD, conductor dia is smaller. Assuming dia is approx cond for Ku estimation
            # or better: Ku is defined by total wire cross section area.
            total_wire_area = turns * strands * (math.pi * (dia/2)**2)
            window_area = win_w * win_h
            ku = total_wire_area / window_area
            
            # Display
            self.res_layers.setText(f"{num_layers}")
            self.res_build.setText(f"{build_h:.2f} / {win_h:.2f}")
            self.res_ku.setText(f"{ku*100:.1f}%")
            
            # Check (Allow 10% margin)
            limit = win_h * 0.9
            if build_h <= limit:
                self.res_status.setText("OK (可绕下)")
                self.res_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
                self.res_build.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.res_status.setText("Warning (可能绕不下)")
                self.res_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                self.res_build.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    # ==============================================================================
    # Tab 3: 损耗分析 (Loss Analysis)
    # ==============================================================================
    def init_loss_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Part A: Bac 自动计算助手 ---
        grp_bac = QGroupBox("1. 磁通密度交流分量计算助手 (B_ac Calculator)")
        grp_bac.setStyleSheet("QGroupBox { font-weight: bold; color: #2980b9; border: 1px solid #bdc3c7; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 10px; }")
        grid_bac = QGridLayout()
        grid_bac.setVerticalSpacing(12)
        
        # 输入
        self.calc_v = QLineEdit("300"); self.calc_v.setToolTip("施加在绕组上的电压 (Volt-Seconds 的电压部分)\n正激/全桥填 Vin，反激建议填 Vor")
        self.calc_f = QLineEdit("100"); self.calc_f.setToolTip("开关频率 kHz")
        self.calc_d = QLineEdit("0.45"); self.calc_d.setToolTip("对应电压施加的占空比 (Duty Cycle)")
        self.calc_n = QLineEdit("40"); self.calc_n.setToolTip("绕组匝数 (Np)")
        self.calc_ae = QLineEdit("119"); self.calc_ae.setToolTip("磁芯截面积 Ae (mm^2)")
        
        grid_bac.addWidget(QLabel("绕组电压 V [V]:"), 0, 0); grid_bac.addWidget(self.calc_v, 0, 1)
        grid_bac.addWidget(QLabel("频率 f [kHz]:"), 0, 2); grid_bac.addWidget(self.calc_f, 0, 3)
        grid_bac.addWidget(QLabel("占空比 D [0-1]:"), 1, 0); grid_bac.addWidget(self.calc_d, 1, 1)
        grid_bac.addWidget(QLabel("匝数 N [Ts]:"), 1, 2); grid_bac.addWidget(self.calc_n, 1, 3)
        grid_bac.addWidget(QLabel("Ae [mm²]:"), 2, 0); grid_bac.addWidget(self.calc_ae, 2, 1)
        
        # 按钮
        btn_calc_bac = QPushButton("计算 B_ac 并填入下方 ↓")
        btn_calc_bac.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc_bac.clicked.connect(self.calc_bac_val)
        grid_bac.addWidget(btn_calc_bac, 2, 2, 1, 2)
        
        # 说明
        lbl_bac_formula = QLabel()
        lbl_bac_formula.setPixmap(render_formula(r'\Delta B = \frac{V \cdot D \cdot 10^6}{N \cdot A_e \cdot f_{kHz}} \quad \Rightarrow \quad B_{ac} = \Delta B / 2'))
        grid_bac.addWidget(lbl_bac_formula, 3, 0, 1, 4)
        
        grp_bac.setLayout(grid_bac)
        layout.addWidget(grp_bac)
        
        # --- Part B: 磁芯损耗 (Steinmetz) ---
        grp_core = QGroupBox("2. 磁芯损耗 (Steinmetz: Pv = k·f^α·B^β)")
        grid_core = QGridLayout()
        
        # Material
        self.loss_mat_combo = QComboBox()
        for name in MATERIALS_DB.keys():
            self.loss_mat_combo.addItem(name)
        self.loss_mat_combo.currentTextChanged.connect(self.update_material_params)
        grid_core.addWidget(QLabel("磁材:"), 0, 0); grid_core.addWidget(self.loss_mat_combo, 0, 1)
        
        # K, a, b
        self.loss_k = QLineEdit(); self.loss_a = QLineEdit(); self.loss_b = QLineEdit()
        hb_coeff = QHBoxLayout()
        hb_coeff.addWidget(QLabel("k:")); hb_coeff.addWidget(self.loss_k)
        hb_coeff.addWidget(QLabel("α:")); hb_coeff.addWidget(self.loss_a)
        hb_coeff.addWidget(QLabel("β:")); hb_coeff.addWidget(self.loss_b)
        grid_core.addLayout(hb_coeff, 1, 0, 1, 2)
        
        # Inputs for Steinmetz
        self.loss_f_in = QLineEdit("100"); grid_core.addWidget(QLabel("频率 f [kHz]:"), 2, 0); grid_core.addWidget(self.loss_f_in, 2, 1)
        self.loss_bac_in = QLineEdit("80"); grid_core.addWidget(QLabel("交流磁密 B_ac [mT]:"), 3, 0); grid_core.addWidget(self.loss_bac_in, 3, 1)
        
        # Ve
        self.loss_ve = QLineEdit("5350"); 
        
        # --- FIX: Core Selector Syncs Ae and Ve ---
        # Pass self.calc_ae to update the Ae in Group 1
        mini_core_sel = create_core_selector(self.calc_ae, None, self.loss_ve)
        
        hb_ve = QHBoxLayout()
        hb_ve.addWidget(self.loss_ve); hb_ve.addWidget(mini_core_sel)
        grid_core.addWidget(QLabel("磁芯体积 Ve [mm³]:"), 4, 0); grid_core.addLayout(hb_ve, 4, 1)
        
        btn_core = QPushButton("计算 P_core (及单位体积损耗)")
        btn_core.clicked.connect(self.calc_core_loss)
        grid_core.addWidget(btn_core, 5, 0, 1, 2)
        
        # Result
        self.res_pv = QLineEdit()
        self.res_pv.setReadOnly(True)
        self.res_pv.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; font-weight: bold;")
        grid_core.addWidget(QLabel("单位体积损耗 Pv [mW/cm³]:"), 6, 0); grid_core.addWidget(self.res_pv, 6, 1)

        self.res_p_core = QLineEdit()
        self.res_p_core.setReadOnly(True)
        self.res_p_core.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold; font-size: 14px;")
        grid_core.addWidget(QLabel("磁芯总损耗 P_total [W]:"), 7, 0); grid_core.addWidget(self.res_p_core, 7, 1)
        
        grp_core.setLayout(grid_core)
        layout.addWidget(grp_core)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.update_material_params()

    def calc_bac_val(self):
        try:
            v = float(self.calc_v.text())
            d = float(self.calc_d.text())
            f_khz = float(self.calc_f.text())
            n = float(self.calc_n.text())
            ae = float(self.calc_ae.text())
            
            if f_khz*n*ae == 0: return
            
            delta_b_mt = (v * d * 1e6) / (f_khz * n * ae)
            
            # Bac is usually peak AC flux, which is half of the swing for unipolar or bipolar
            # For Steinmetz, we use B_peak_ac
            bac_mt = delta_b_mt / 2.0
            
            self.loss_bac_in.setText(f"{bac_mt:.1f}")
            self.loss_f_in.setText(f"{f_khz}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

    def update_material_params(self):
        name = self.loss_mat_combo.currentText()
        p = MATERIALS_DB.get(name, {'k':0, 'a':0, 'b':0})
        self.loss_k.setText(str(p['k']))
        self.loss_a.setText(str(p['a']))
        self.loss_b.setText(str(p['b']))

    def calc_core_loss(self):
        try:
            k = float(self.loss_k.text())
            a = float(self.loss_a.text())
            b = float(self.loss_b.text())
            f = float(self.loss_f_in.text())
            bac = float(self.loss_bac_in.text())
            ve = float(self.loss_ve.text())
            
            # Pv = k * f^a * B^b (mW/cm3)
            # f in kHz, B in mT
            pv = k * (f ** a) * (bac ** b) # mW/cm3
            
            # Total Power: Pv * (Ve in cm3)
            # Ve mm3 -> cm3 : / 1000
            ptot_mw = pv * (ve / 1000.0) 
            ptot_w = ptot_mw / 1000.0
            
            self.res_pv.setText(f"{pv:.2f}")
            self.res_p_core.setText(f"{ptot_w:.3f}")
        except: pass

    # ==============================================================================
    # Tab 4: 漏感估算 (Leakage Estimator)
    # ==============================================================================
    def init_leakage_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 公式展示
        formula_grp = QGroupBox("漏感计算公式 (Engineering Estimation)")
        f_layout = QVBoxLayout()
        # L_lk = mu0 * N^2 * (MLT/bw) * ( (hp+hs)/3 + tins )
        lbl_formula = QLabel()
        lbl_formula.setPixmap(render_formula(r'L_{lk} \approx \mu_0 N^2 \frac{MLT}{b_w} \left( \frac{\Sigma h}{3} + \Sigma \delta \right) \times K_{config}'))
        f_layout.addWidget(lbl_formula)
        formula_grp.setLayout(f_layout)
        layout.addWidget(formula_grp)

        # 输入区域
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        input_grp = QGroupBox("1. 变压器绕组几何参数")
        
        self.lk_n = QLineEdit("40"); grid.addWidget(QLabel("原边匝数 Np [T]:"), 0, 0); grid.addWidget(self.lk_n, 0, 1)
        self.lk_mlt = QLineEdit("45"); grid.addWidget(QLabel("平均匝长 MLT [mm]:"), 0, 2); grid.addWidget(self.lk_mlt, 0, 3)
        self.lk_bw = QLineEdit("14"); grid.addWidget(QLabel("绕组宽度 bw [mm]:"), 1, 0); grid.addWidget(self.lk_bw, 1, 1)
        self.lk_config = QComboBox(); self.lk_config.addItems(["普通绕法 (Pri-Sec)", "三明治绕法 (Pri/2-Sec-Pri/2)"])
        grid.addWidget(QLabel("绕组结构:"), 1, 2); grid.addWidget(self.lk_config, 1, 3)

        input_grp.setLayout(grid)
        layout.addWidget(input_grp)
        
        # 绝缘/厚度
        thick_grp = QGroupBox("2. 绕组厚度与绝缘")
        t_grid = QGridLayout()
        self.lk_hp = QLineEdit("1.0"); t_grid.addWidget(QLabel("原边绕组总厚度 hp [mm]:"), 0, 0); t_grid.addWidget(self.lk_hp, 0, 1)
        self.lk_hs = QLineEdit("1.0"); t_grid.addWidget(QLabel("副边绕组总厚度 hs [mm]:"), 0, 2); t_grid.addWidget(self.lk_hs, 0, 3)
        self.lk_tins = QLineEdit("0.1"); t_grid.addWidget(QLabel("层间绝缘总厚度 Σδ [mm]:"), 1, 0); t_grid.addWidget(self.lk_tins, 1, 1)
        
        thick_grp.setLayout(t_grid)
        layout.addWidget(thick_grp)
        
        btn_calc = QPushButton("计算漏感 (Estimate Leakage)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_leakage)
        layout.addWidget(btn_calc)
        
        # 结果
        res_grp = QGroupBox("3. 估算结果")
        r_layout = QHBoxLayout()
        self.res_lk = QLineEdit()
        self.res_lk.setReadOnly(True)
        self.res_lk.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        r_layout.addWidget(QLabel("估算漏感 L_lk [uH]:"))
        r_layout.addWidget(self.res_lk)
        res_grp.setLayout(r_layout)
        layout.addWidget(res_grp)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_leakage(self):
        try:
            mu0 = 4 * math.pi * 1e-7
            n = float(self.lk_n.text())
            mlt = float(self.lk_mlt.text()) / 1000.0 # mm -> m
            bw = float(self.lk_bw.text()) / 1000.0 # mm -> m
            hp = float(self.lk_hp.text()) / 1000.0
            hs = float(self.lk_hs.text()) / 1000.0
            tins = float(self.lk_tins.text()) / 1000.0
            
            # Config Factor
            # Ordinary: 1.0
            # Sandwich (P/2-S-P/2): Leakage is roughly 1/4 of ordinary
            k_config = 0.25 if "三明治" in self.lk_config.currentText() else 1.0
            
            # Formula: L = mu0 * N^2 * (MLT / bw) * ( (hp + hs)/3 + tins ) * K
            term_thick = (hp + hs) / 3.0 + tins
            l_val = mu0 * (n**2) * (mlt / bw) * term_thick * k_config
            
            l_uh = l_val * 1e6
            self.res_lk.setText(f"{l_uh:.3f}")
            
        except Exception as e:
            self.res_lk.setText("Error")

    # ==============================================================================
    # Tab 5: 绕组 AC 损耗 (Proximity Effect / Dowell's Eq)
    # ==============================================================================
    def init_ac_loss_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能：估算高频下绕组的邻近效应损耗 (Proximity Effect)。\n"
                      "基于 Dowell 模型计算交流电阻系数 Fr = Rac/Rdc。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 输入
        grp_in = QGroupBox("1. 绕组参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.ac_layers = QLineEdit("3"); self.ac_layers.setToolTip("该绕组的层数 (Number of Layers)")
        grid.addWidget(QLabel("绕组层数 (m):"), 0, 0); grid.addWidget(self.ac_layers, 0, 1)
        
        self.ac_freq = QLineEdit("100"); grid.addWidget(QLabel("开关频率 [kHz]:"), 0, 2); grid.addWidget(self.ac_freq, 0, 3)
        
        self.ac_dia = QLineEdit("0.35"); self.ac_dia.setToolTip("单根导线直径 (如果是铜箔则为厚度)")
        grid.addWidget(QLabel("导线直径/厚度 [mm]:"), 1, 0); grid.addWidget(self.ac_dia, 1, 1)
        
        self.ac_porosity = QLineEdit("0.9"); self.ac_porosity.setToolTip("排线系数 η = N * d / WindowWidth。")
        grid.addWidget(QLabel("排线系数 (η):"), 1, 2); grid.addWidget(self.ac_porosity, 1, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算 AC 电阻系数 Fr")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_ac_loss)
        layout.addWidget(btn)
        
        # 结果
        grp_res = QGroupBox("2. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.res_skin_depth = QLineEdit()
        self.res_x_factor = QLineEdit()
        self.res_fr = QLineEdit()
        
        # Skin Depth
        r_grid.addWidget(QLabel("趋肤深度 (δ):"), 0, 0)
        r_grid.addWidget(self.res_skin_depth, 0, 1)
        l_sd = QLabel(); l_sd.setPixmap(render_formula(r'\delta = \frac{66}{\sqrt{f}} \text{ mm}'))
        r_grid.addWidget(l_sd, 0, 2)
        
        # X Factor
        r_grid.addWidget(QLabel("归一化厚度 (Δ):"), 1, 0)
        r_grid.addWidget(self.res_x_factor, 1, 1)
        l_x = QLabel(); l_x.setPixmap(render_formula(r'\Delta = \frac{d}{\delta} \sqrt{\eta}'))
        r_grid.addWidget(l_x, 1, 2)
        
        # Fr
        r_grid.addWidget(QLabel("交流电阻系数 (Fr):"), 2, 0)
        r_grid.addWidget(self.res_fr, 2, 1)
        l_fr = QLabel(); l_fr.setPixmap(render_formula(r'F_r = R_{ac}/R_{dc}'))
        r_grid.addWidget(l_fr, 2, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;"
        self.res_skin_depth.setReadOnly(True); self.res_skin_depth.setStyleSheet(style)
        self.res_x_factor.setReadOnly(True)
        self.res_fr.setReadOnly(True); self.res_fr.setStyleSheet("background-color: #fdf2e9; font-weight: bold; color: #d35400; font-size: 16px;")
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 警告/提示信息区域
        self.ac_loss_warning_label = QLabel("注：Fr 值随层数 (m) 呈指数级上升。")
        self.ac_loss_warning_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 10px; border-radius: 5px; background-color: #f9f9f9;")
        self.ac_loss_warning_label.setWordWrap(True)
        layout.addWidget(self.ac_loss_warning_label)
        
        layout.addStretch()
        tab.setLayout(layout)

    def calc_ac_loss(self):
        try:
            m = float(self.ac_layers.text())
            f_khz = float(self.ac_freq.text())
            d_mm = float(self.ac_dia.text())
            eta = float(self.ac_porosity.text())
            
            if f_khz <= 0: return
            
            # Skin depth (Copper @ 100C approx)
            # delta = 72 / sqrt(f)
            delta_mm = 72.0 / math.sqrt(f_khz * 1000)
            
            # Dowell's Variable Delta (Phi)
            # Delta = (d / delta) * sqrt(eta)
            phi = (d_mm / delta_mm) * math.sqrt(eta)
            
            # Dowell's Equation (Approximation for m layers)
            if phi > 10: 
                # Large Phi -> Skin effect dominates, Fr ~ Phi
                term1 = 1.0
                term2 = 1.0
            else:
                denom1 = math.cosh(2*phi) - math.cos(2*phi)
                if denom1 == 0: denom1 = 1e-9
                term1 = (math.sinh(2*phi) + math.sin(2*phi)) / denom1
                
                denom2 = math.cosh(phi) + math.cos(phi)
                if denom2 == 0: denom2 = 1e-9
                term2 = (math.sinh(phi) - math.sin(phi)) / denom2
                
            fr = phi * (term1 + (2.0 * (m**2 - 1) / 3.0) * term2)
            
            self.res_skin_depth.setText(f"{delta_mm:.4f} mm")
            self.res_x_factor.setText(f"{phi:.3f}")
            self.res_fr.setText(f"{fr:.2f}")
            
            # 警告逻辑
            if fr > 3.0:
                self.res_fr.setStyleSheet("background-color: #ffcccc; color: red; font-weight: bold; font-size: 16px;")
                self.ac_loss_warning_label.setText(f"⚠️ <b>高损耗警告：</b> AC 电阻是 DC 电阻的 {fr:.1f} 倍！<br>邻近效应非常严重。建议减少单股线径（使用多股并绕）或减少层数（改为三明治绕法）。")
                self.ac_loss_warning_label.setStyleSheet("background-color: #fdedec; color: #c0392b; font-size: 13px; padding: 10px; border-left: 5px solid #c0392b;")
            elif fr > 1.5:
                self.res_fr.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold; font-size: 16px;")
                self.ac_loss_warning_label.setText(f"⚠️ <b>注意：</b> Fr = {fr:.1f}，交流损耗较为明显。<br>建议优化绕组结构，尽量控制 Fr < 1.5。")
                self.ac_loss_warning_label.setStyleSheet("background-color: #fff3cd; color: #856404; font-size: 13px; padding: 10px; border-left: 5px solid #ffc107;")
            else:
                self.res_fr.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold; font-size: 16px;")
                self.ac_loss_warning_label.setText("✅ <b>设计合理：</b> 邻近效应影响较小。")
                self.ac_loss_warning_label.setStyleSheet("background-color: #d4edda; color: #155724; font-size: 13px; padding: 10px; border-left: 5px solid #28a745;")
                
        except Exception as e:
            self.ac_loss_warning_label.setText("输入无效，请检查数值。")

    # ==============================================================================
    # Tab 6: Steinmetz 拟合 (NEW Feature)
    # ==============================================================================
    def init_fit_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：输入 Datasheet 上的损耗点数据，自动拟合计算 Steinmetz 系数 k, α, β。\n"
                      "拟合公式: Pv = k * f^α * B^β (对数空间线性回归)")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 1. 数据输入表格
        grp_data = QGroupBox("1. 采样点输入 (Sample Points from Datasheet)")
        v_data = QVBoxLayout()
        
        self.fit_table = QTableWidget(4, 3) # Default 4 rows
        self.fit_table.setHorizontalHeaderLabels(["频率 f (kHz)", "磁密 B (mT)", "损耗 Pv (mW/cm³)"])
        self.fit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 预填一些示例数据 (PC40 @ 100C approx)
        # 100kHz, 100mT -> ~65 mW/cm3
        # 100kHz, 200mT -> ~400 mW/cm3
        # 200kHz, 100mT -> ~200 mW/cm3
        example_data = [
            ("100", "100", "65"),
            ("100", "200", "400"),
            ("200", "100", "200"),
            ("", "", "")
        ]
        for r, row_data in enumerate(example_data):
            for c, val in enumerate(row_data):
                self.fit_table.setItem(r, c, QTableWidgetItem(val))
        
        v_data.addWidget(self.fit_table)
        
        h_btns = QHBoxLayout()
        btn_add = QPushButton("添加行")
        btn_add.clicked.connect(lambda: self.fit_table.insertRow(self.fit_table.rowCount()))
        btn_clr = QPushButton("清空")
        btn_clr.clicked.connect(self.clear_fit_table)
        h_btns.addWidget(btn_add); h_btns.addWidget(btn_clr)
        v_data.addLayout(h_btns)
        
        grp_data.setLayout(v_data)
        layout.addWidget(grp_data)
        
        # 2. 拟合按钮
        btn_fit = QPushButton("开始拟合 (Calculate Coefficients)")
        btn_fit.setFixedHeight(45)
        btn_fit.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; font-size: 14px;")
        btn_fit.clicked.connect(self.calc_steinmetz_fit)
        layout.addWidget(btn_fit)
        
        # 3. 结果输出
        grp_res = QGroupBox("2. 拟合结果 (Coefficients)")
        grid_res = QGridLayout()
        
        self.fit_k = QLineEdit()
        self.fit_a = QLineEdit()
        self.fit_b = QLineEdit()
        self.fit_error = QLineEdit()
        
        grid_res.addWidget(QLabel("系数 k:"), 0, 0); grid_res.addWidget(self.fit_k, 0, 1)
        grid_res.addWidget(QLabel("指数 α (Alpha):"), 0, 2); grid_res.addWidget(self.fit_a, 0, 3)
        grid_res.addWidget(QLabel("指数 β (Beta):"), 1, 0); grid_res.addWidget(self.fit_b, 1, 1)
        grid_res.addWidget(QLabel("平均误差 (MAPE):"), 1, 2); grid_res.addWidget(self.fit_error, 1, 3)
        
        # 验证器
        grid_res.addWidget(QLabel("验证: 输入 f, B -> 预测 Pv:"), 2, 0)
        h_verify = QHBoxLayout()
        self.val_f = QLineEdit("100"); self.val_f.setPlaceholderText("f (kHz)")
        self.val_b = QLineEdit("150"); self.val_b.setPlaceholderText("B (mT)")
        self.val_pv = QLineEdit(); self.val_pv.setPlaceholderText("Result Pv")
        self.val_pv.setReadOnly(True)
        btn_val = QPushButton("计算"); btn_val.clicked.connect(self.verify_fit)
        
        h_verify.addWidget(self.val_f); h_verify.addWidget(self.val_b); h_verify.addWidget(btn_val); h_verify.addWidget(self.val_pv)
        grid_res.addLayout(h_verify, 2, 1, 1, 3)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.fit_k, self.fit_a, self.fit_b, self.fit_error]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(grid_res)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        tab.setLayout(layout)

    def clear_fit_table(self):
        self.fit_table.setRowCount(0)
        self.fit_table.setRowCount(4)

    def calc_steinmetz_fit(self):
        """
        Solve linear system: Y = C + a*X1 + b*X2
        ln(Pv) = ln(k) + alpha*ln(f) + beta*ln(B)
        """
        f_list = []
        b_list = []
        pv_list = []
        
        try:
            rows = self.fit_table.rowCount()
            for r in range(rows):
                item_f = self.fit_table.item(r, 0)
                item_b = self.fit_table.item(r, 1)
                item_pv = self.fit_table.item(r, 2)
                
                if item_f and item_b and item_pv and item_f.text() and item_b.text() and item_pv.text():
                    f = float(item_f.text())
                    b = float(item_b.text())
                    pv = float(item_pv.text())
                    
                    if f>0 and b>0 and pv>0:
                        f_list.append(f)
                        b_list.append(b)
                        pv_list.append(pv)
            
            if len(f_list) < 3:
                QMessageBox.warning(self, "数据不足", "至少需要 3 组有效数据点才能进行拟合。")
                return
            
            # Log transform
            # Y = ln(Pv)
            Y = np.log(np.array(pv_list))
            
            # A matrix: column of 1s, ln(f), ln(B)
            col_ones = np.ones(len(f_list))
            col_ln_f = np.log(np.array(f_list))
            col_ln_b = np.log(np.array(b_list))
            
            A = np.vstack([col_ones, col_ln_f, col_ln_b]).T
            
            # Solve A * [ln(k), alpha, beta]^T = Y
            # Using Least Squares
            result, residuals, rank, s = np.linalg.lstsq(A, Y, rcond=None)
            
            ln_k, alpha, beta = result
            k = np.exp(ln_k)
            
            self.fit_k.setText(f"{k:.6g}") # Use general format for potentially small k
            self.fit_a.setText(f"{alpha:.4f}")
            self.fit_b.setText(f"{beta:.4f}")
            self.fit_res_k = k
            self.fit_res_a = alpha
            self.fit_res_b = beta
            
            # Calculate Error (MAPE)
            pv_pred = k * (np.array(f_list)**alpha) * (np.array(b_list)**beta)
            pv_act = np.array(pv_list)
            mape = np.mean(np.abs((pv_act - pv_pred) / pv_act)) * 100
            
            self.fit_error.setText(f"{mape:.2f}%")
            
        except Exception as e:
            QMessageBox.warning(self, "拟合错误", f"计算失败: {str(e)}")

    def verify_fit(self):
        try:
            if not hasattr(self, 'fit_res_k'): return
            f = float(self.val_f.text())
            b = float(self.val_b.text())
            
            pv = self.fit_res_k * (f ** self.fit_res_a) * (b ** self.fit_res_b)
            self.val_pv.setText(f"{pv:.2f}")
        except: pass