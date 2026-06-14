# mag_trans_topo.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QGridLayout, QGroupBox, QComboBox, QTabWidget)
from mag_trans_data import create_core_selector

# -----------------------------------------------------------------------------
# 自定义 Tab Widget 类 (用于统一控制子页面 Tab 的宽度)
# -----------------------------------------------------------------------------
class QTabWidget_Custom(QTabWidget):
    def __init__(self):
        super().__init__()
        # 【修改】移除了 min-width，调整 padding 为适当值，使标签紧凑且自适应
        self.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; border-radius: 4px; }
            QTabBar::tab { 
                background: #f4f6f9; 
                border: 1px solid #c0c0c0; 
                padding: 8px 12px; /* 减小左右内边距，去除空白 */
                margin-right: 1px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                /* min-width: 260px;  <-- 已彻底移除，允许自适应 */
            }
            QTabBar::tab:selected { background: #ffffff; border-bottom: 1px solid #ffffff; font-weight: bold; color: #2980b9; }
        """)

class TopologyDesignPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 使用自定义的 Tab 容器
        self.tabs = QTabWidget_Custom()
        
        self.tab_forward = QWidget()
        self.tab_flyback = QWidget()
        
        self.init_forward_ui(self.tab_forward)
        self.init_flyback_ui(self.tab_flyback)
        
        self.tabs.addTab(self.tab_forward, "正激/全桥设计 (Forward/Bridge)")
        self.tabs.addTab(self.tab_flyback, "反激变压器设计 (Flyback)")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # ==============================================================================
    # Tab: 正激/桥式/推挽
    # ==============================================================================
    def init_forward_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入
        input_group = QGroupBox("1. 电路参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.fwd_topology = QComboBox()
        self.fwd_topology.addItems(["全桥 (Full Bridge)", "半桥 (Half Bridge)", "推挽 (Push-Pull)", "单管正激 (Forward)"])
        grid.addWidget(QLabel("拓扑结构:"), 0, 0); grid.addWidget(self.fwd_topology, 0, 1)
        
        self.fwd_vin_min = QLineEdit("300"); grid.addWidget(QLabel("Min Vin [V]:"), 1, 0); grid.addWidget(self.fwd_vin_min, 1, 1)
        self.fwd_vout = QLineEdit("24"); grid.addWidget(QLabel("Vout [V]:"), 2, 0); grid.addWidget(self.fwd_vout, 2, 1)
        self.fwd_iout = QLineEdit("10"); grid.addWidget(QLabel("Iout [A]:"), 2, 2); grid.addWidget(self.fwd_iout, 2, 3)
        self.fwd_fsw = QLineEdit("100"); grid.addWidget(QLabel("fsw [kHz]:"), 3, 0); grid.addWidget(self.fwd_fsw, 3, 1)
        self.fwd_dmax = QLineEdit("0.45"); grid.addWidget(QLabel("Max Duty [0~1]:"), 3, 2); grid.addWidget(self.fwd_dmax, 3, 3)
        self.fwd_b_peak = QLineEdit("0.15"); grid.addWidget(QLabel("B_peak [T]:"), 4, 0); grid.addWidget(self.fwd_b_peak, 4, 1)
        self.fwd_j = QLineEdit("4.0"); grid.addWidget(QLabel("J [A/mm²]:"), 4, 2); grid.addWidget(self.fwd_j, 4, 3)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        # 磁芯
        core_group = QGroupBox("2. 磁芯选择")
        core_layout = QGridLayout()
        self.fwd_ae = QLineEdit("119"); self.fwd_aw = QLineEdit("43")
        core_select = create_core_selector(self.fwd_ae, self.fwd_aw)
        core_layout.addWidget(QLabel("预选磁芯:"), 0, 0); core_layout.addWidget(core_select, 0, 1)
        core_layout.addWidget(QLabel("Ae [mm²]:"), 0, 2); core_layout.addWidget(self.fwd_ae, 0, 3)
        core_group.setLayout(core_layout)
        layout.addWidget(core_group)
        
        btn = QPushButton("设计变压器")
        btn.setFixedHeight(45); btn.clicked.connect(self.calc_forward)
        layout.addWidget(btn)
        
        # 结果
        res_group = QGroupBox("3. 结果")
        res_grid = QGridLayout()
        self.fwd_np = QLineEdit(); self.fwd_ns = QLineEdit(); self.fwd_ap = QLineEdit()
        res_grid.addWidget(QLabel("Np (匝):"), 0, 0); res_grid.addWidget(self.fwd_np, 0, 1)
        res_grid.addWidget(QLabel("Ns (匝):"), 1, 0); res_grid.addWidget(self.fwd_ns, 1, 1)
        res_grid.addWidget(QLabel("AP值 (cm^4):"), 2, 0); res_grid.addWidget(self.fwd_ap, 2, 1)
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_forward(self):
        try:
            vin = float(self.fwd_vin_min.text())
            vout = float(self.fwd_vout.text())
            fsw = float(self.fwd_fsw.text())
            dmax = float(self.fwd_dmax.text())
            bpk = float(self.fwd_b_peak.text())
            ae = float(self.fwd_ae.text())
            topo = self.fwd_topology.currentText()
            
            v_pri = vin / 2.0 if "Half" in topo else vin
            db = bpk if "Forward" in topo else 2 * bpk
            
            np = math.ceil((v_pri * dmax * 1000) / (fsw * ae * db))
            ns = math.ceil(np * (vout + 0.5) / (v_pri * dmax))
            
            self.fwd_np.setText(str(np))
            self.fwd_ns.setText(str(ns))
            self.fwd_ap.setText(f"{(ae * float(self.fwd_aw.text())) / 10000:.2f}")
        except: pass

    # ==============================================================================
    # Tab: 反激
    # ==============================================================================
    def init_flyback_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        input_group = QGroupBox("1. 反激参数")
        grid = QGridLayout()
        self.fly_vin = QLineEdit("85"); grid.addWidget(QLabel("Vin_min [V]:"), 0, 0); grid.addWidget(self.fly_vin, 0, 1)
        self.fly_vor = QLineEdit("80"); grid.addWidget(QLabel("Vor [V]:"), 0, 2); grid.addWidget(self.fly_vor, 0, 3)
        self.fly_vout = QLineEdit("12"); grid.addWidget(QLabel("Vout [V]:"), 1, 0); grid.addWidget(self.fly_vout, 1, 1)
        self.fly_iout = QLineEdit("2"); grid.addWidget(QLabel("Iout [A]:"), 1, 2); grid.addWidget(self.fly_iout, 1, 3)
        self.fly_fsw = QLineEdit("65"); grid.addWidget(QLabel("fsw [kHz]:"), 2, 0); grid.addWidget(self.fly_fsw, 2, 1)
        self.fly_krf = QLineEdit("0.4"); grid.addWidget(QLabel("Krf (0.3~0.5):"), 2, 2); grid.addWidget(self.fly_krf, 2, 3)
        self.fly_bmax = QLineEdit("0.25"); grid.addWidget(QLabel("Bmax [T]:"), 3, 0); grid.addWidget(self.fly_bmax, 3, 1)
        self.fly_ae = QLineEdit("23"); grid.addWidget(QLabel("Ae [mm2]:"), 3, 2); grid.addWidget(self.fly_ae, 3, 3)
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        core_group = QGroupBox("2. 磁芯")
        c_grid = QGridLayout()
        self.fly_ae = QLineEdit("23")
        core_sel = create_core_selector(self.fly_ae, None)
        c_grid.addWidget(QLabel("磁芯:"), 0, 0); c_grid.addWidget(core_sel, 0, 1)
        c_grid.addWidget(QLabel("Ae [mm²]:"), 0, 2); c_grid.addWidget(self.fly_ae, 0, 3)
        core_group.setLayout(c_grid)
        layout.addWidget(core_group)
        
        btn = QPushButton("设计反激参数")
        btn.setFixedHeight(45); btn.clicked.connect(self.calc_flyback)
        layout.addWidget(btn)
        
        res_group = QGroupBox("3. 结果")
        r_grid = QGridLayout()
        self.fly_lp = QLineEdit(); self.fly_np = QLineEdit(); self.fly_gap = QLineEdit()
        r_grid.addWidget(QLabel("Lp [uH]:"), 0, 0); r_grid.addWidget(self.fly_lp, 0, 1)
        r_grid.addWidget(QLabel("Np [T]:"), 1, 0); r_grid.addWidget(self.fly_np, 1, 1)
        r_grid.addWidget(QLabel("气隙 lg [mm]:"), 2, 0); r_grid.addWidget(self.fly_gap, 2, 1)
        res_group.setLayout(r_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_flyback(self):
        try:
            vin = float(self.fly_vin.text())
            vor = float(self.fly_vor.text())
            vout = float(self.fly_vout.text())
            iout = float(self.fly_iout.text())
            fsw = float(self.fly_fsw.text())
            krf = float(self.fly_krf.text())
            bmax = float(self.fly_bmax.text())
            ae = float(self.fly_ae.text())
            
            dmax = vor / (vin + vor)
            pin = (vout * iout) / 0.85
            iin_avg = pin / vin
            iedc = iin_avg / dmax
            ipk = iedc * (1 + krf/2)
            
            lph = (vin * dmax) / (krf * iedc * fsw * 1000)
            np = math.ceil((lph * ipk * 1e6) / (bmax * ae))
            lg = (4 * math.pi * 1e-7 * np**2 * ae * 1e-6) / lph
            
            self.fly_lp.setText(f"{lph*1e6:.1f}")
            self.fly_np.setText(str(np))
            self.fly_gap.setText(f"{lg*1000:.3f}")
        except: pass