# pcb_fusing_tool.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from utils import render_formula

# ==============================================================================
# 铜箔瞬态熔断计算 (Trace Fusing)
# ==============================================================================
class FusingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        info = QLabel("基于 Onderdonk 公式计算铜箔在短路或浪涌电流下的温升与熔断风险。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(info)

        # 1. 铜箔几何参数
        grp_geo = QGroupBox("1. 铜箔参数 (Trace Geometry)")
        grid_geo = QGridLayout()
        grid_geo.setVerticalSpacing(12)
        
        self.fus_width = QLineEdit("0.5")
        self.fus_width_unit = QComboBox(); self.fus_width_unit.addItems(["mm", "mil"])
        h_w = QHBoxLayout(); h_w.addWidget(self.fus_width); h_w.addWidget(self.fus_width_unit); h_w.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(QLabel("线宽 (Width):"), 0, 0); grid_geo.addLayout(h_w, 0, 1)
        
        self.fus_thick = QLineEdit("1.0")
        self.fus_thick_unit = QComboBox(); self.fus_thick_unit.addItems(["oz", "mm", "mil"])
        h_t = QHBoxLayout(); h_t.addWidget(self.fus_thick); h_t.addWidget(self.fus_thick_unit); h_t.setContentsMargins(0,0,0,0)
        grid_geo.addWidget(QLabel("厚度 (Thickness):"), 0, 2); grid_geo.addLayout(h_t, 0, 3)
        
        grp_geo.setLayout(grid_geo)
        layout.addWidget(grp_geo)
        
        # 2. 冲击条件
        grp_cond = QGroupBox("2. 冲击条件 (Impact Condition)")
        grid_cond = QGridLayout()
        
        self.fus_curr = QLineEdit("10"); grid_cond.addWidget(QLabel("冲击电流 I [A]:"), 0, 0); grid_cond.addWidget(self.fus_curr, 0, 1)
        self.fus_time = QLineEdit("100"); self.fus_time_unit = QComboBox(); self.fus_time_unit.addItems(["ms", "s", "us"])
        h_tm = QHBoxLayout(); h_tm.addWidget(self.fus_time); h_tm.addWidget(self.fus_time_unit); h_tm.setContentsMargins(0,0,0,0)
        grid_cond.addWidget(QLabel("持续时间 t:"), 0, 2); grid_cond.addLayout(h_tm, 0, 3)
        
        self.fus_tamb = QLineEdit("25"); grid_cond.addWidget(QLabel("环境温度 Tamb [°C]:"), 1, 0); grid_cond.addWidget(self.fus_tamb, 1, 1)
        
        grp_cond.setLayout(grid_cond)
        layout.addWidget(grp_cond)
        
        # 按钮
        btn = QPushButton("计算瞬态温升与熔断风险")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_fusing)
        layout.addWidget(btn)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估结果")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        
        self.fus_area = QLineEdit()
        self.fus_trise = QLineEdit()
        self.fus_tfinal = QLineEdit()
        self.fus_status = QLineEdit()
        
        res_grid.addWidget(QLabel("截面积 (Area):"), 0, 0); res_grid.addWidget(self.fus_area, 0, 1)
        res_grid.addWidget(QLabel("瞬态温升 (ΔT):"), 1, 0); res_grid.addWidget(self.fus_trise, 1, 1)
        res_grid.addWidget(QLabel("最终温度 (T_final):"), 2, 0); res_grid.addWidget(self.fus_tfinal, 2, 1)
        res_grid.addWidget(QLabel("状态评估:"), 3, 0); res_grid.addWidget(self.fus_status, 3, 1)
        
        l_form = QLabel()
        l_form.setPixmap(render_formula(r'I = A \cdot \sqrt{\frac{\log(1 + \Delta T / (234 + T_a))}{33 t}}'))
        res_grid.addWidget(l_form, 0, 2, 4, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #2c3e50;"
        for w in [self.fus_area, self.fus_trise, self.fus_tfinal]:
            w.setReadOnly(True); w.setStyleSheet(style)
        self.fus_status.setReadOnly(True)
        
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        # 修复点：原代码为 tab.setLayout(layout)，改为 self.setLayout(layout)
        self.setLayout(layout)

    def calc_fusing(self):
        try:
            w_val = float(self.fus_width.text())
            w_mil = w_val / 0.0254 if self.fus_width_unit.currentText() == "mm" else w_val
            t_val = float(self.fus_thick.text())
            t_u = self.fus_thick_unit.currentText()
            t_mil = t_val / 0.0254 if t_u == "mm" else (t_val * 1.378 if t_u == "oz" else t_val)
            
            if w_mil <= 0 or t_mil <= 0: raise ValueError
            area_cmil = w_mil * t_mil * 1.2732
            
            curr = float(self.fus_curr.text())
            t_val = float(self.fus_time.text())
            t_u = self.fus_time_unit.currentText()
            time_sec = t_val / 1000.0 if t_u == "ms" else (t_val / 1e6 if t_u == "us" else t_val)
            tamb = float(self.fus_tamb.text())
            
            if curr <= 0 or time_sec <= 0: raise ValueError
            
            term = 33.0 * time_sec * ((curr / area_cmil) ** 2)
            if term > 5.0: dt = 9999
            else: dt = (234.0 + tamb) * (math.pow(10, term) - 1)
            t_final = tamb + dt
            
            self.fus_area.setText(f"{area_cmil:.1f} cmils")
            self.fus_trise.setText(f"+{dt:.1f} °C" if dt <= 2000 else "> 2000 °C")
            self.fus_tfinal.setText(f"{t_final:.1f} °C" if dt <= 2000 else "> 2000 °C")
            
            if t_final >= 1083:
                self.fus_status.setText("熔断 (FUSED)! > 1083°C")
                self.fus_status.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
            elif t_final >= 250:
                self.fus_status.setText("基材损坏 (Damage Risk) > 250°C")
                self.fus_status.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
            else:
                self.fus_status.setText("安全 (Safe)")
                self.fus_status.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        except Exception as e: QMessageBox.warning(self, "错误", "输入数值无效")