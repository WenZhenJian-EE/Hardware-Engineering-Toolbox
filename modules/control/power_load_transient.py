from modules.base_module import BaseModule
# power_load_transient.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt
from utils import render_formula

class LoadTransientWindow(BaseModule):
    category = "3. 环路控制与滤波 (Control & Filter)"
    display_name = "动态响应 (Load Transient)"
    description = "估算电压跌落与恢复"
    window_id = "power_transient"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('动态响应与评估 (Load Transient)')
        self.setGeometry(300, 300, 750, 500)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        info_label = QLabel("估算负载阶跃跳变时，输出电压的跌落/过冲幅度，用于评估输出电容是否充足。\n"
                            "假设环路带宽 fc 已知 (通常为 fsw/10)。\n"
                            "此工具可用于评估所有 DC-DC 降压/升压转换器以及 LDO 的瞬态性能。")
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 15px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)

        # 1. 输入参数
        grp_in = QGroupBox("1. 动态条件 (Transient Conditions)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.tr_i_step = QLineEdit("2.0"); self.tr_i_step.setToolTip("负载电流跳变量 ΔI")
        grid.addWidget(QLabel("负载跳变 ΔI [A]:"), 0, 0); grid.addWidget(self.tr_i_step, 0, 1)
        
        self.tr_fc = QLineEdit("50"); self.tr_fc.setToolTip("环路穿越频率 (Bandwidth)")
        grid.addWidget(QLabel("环路带宽 fc [kHz]:"), 0, 2); grid.addWidget(self.tr_fc, 0, 3)
        
        self.tr_cout = QLineEdit("47"); self.tr_cout.setToolTip("输出总电容 (考虑偏置降容后)")
        grid.addWidget(QLabel("输出电容 Cout [μF]:"), 1, 0); grid.addWidget(self.tr_cout, 1, 1)
        
        self.tr_esr = QLineEdit("5"); self.tr_esr.setToolTip("电容总 ESR (并联后)")
        grid.addWidget(QLabel("电容总 ESR [mΩ]:"), 1, 2); grid.addWidget(self.tr_esr, 1, 3)
        
        grp_in.setLayout(grid)
        main_layout.addWidget(grp_in)
        
        btn = QPushButton("估算电压跌落 (Calculate V_drop)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px; margin-top: 10px; margin-bottom: 10px;")
        btn.clicked.connect(self.calc_transient)
        main_layout.addWidget(btn)
        
        # 2. 估算结果
        grp_res = QGroupBox("2. 估算结果 (Estimation Results)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(20)
        r_grid.setColumnStretch(1, 1)
        
        self.res_v_cap = QLineEdit()
        self.res_v_esr = QLineEdit()
        self.res_v_total = QLineEdit()
        
        # Capacitive Drop
        r_grid.addWidget(QLabel("电容放电跌落 (ΔVc):"), 0, 0)
        r_grid.addWidget(self.res_v_cap, 0, 1)
        l_c = QLabel(); l_c.setPixmap(self.render_formula(r'\Delta V_C \approx \frac{\Delta I}{2\pi f_c C_{out}}'))
        r_grid.addWidget(l_c, 0, 2)
        
        # ESR Drop
        r_grid.addWidget(QLabel("ESR 瞬态跌落 (ΔVesr):"), 1, 0)
        r_grid.addWidget(self.res_v_esr, 1, 1)
        l_r = QLabel(); l_r.setPixmap(self.render_formula(r'\Delta V_{ESR} = \Delta I \cdot ESR'))
        r_grid.addWidget(l_r, 1, 2)
        
        # Total Drop
        r_grid.addWidget(QLabel("总电压跌落 (V_drop):"), 2, 0)
        r_grid.addWidget(self.res_v_total, 2, 1)
        l_tot = QLabel(); l_tot.setPixmap(self.render_formula(r'\Delta V_{total} \approx \Delta V_C + \Delta V_{ESR}'))
        r_grid.addWidget(l_tot, 2, 2)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 15px;"
        style_warn = "background-color: #fff8e1; font-weight: bold; color: #d35400; font-size: 15px;"
        
        self.res_v_cap.setReadOnly(True); self.res_v_cap.setStyleSheet(style)
        self.res_v_esr.setReadOnly(True); self.res_v_esr.setStyleSheet(style)
        self.res_v_total.setReadOnly(True); self.res_v_total.setStyleSheet(style_warn)
        
        grp_res.setLayout(r_grid)
        main_layout.addWidget(grp_res)
        
        main_layout.addStretch()
        self.setLayout(main_layout)

    def calc_transient(self):
        try:
            di = float(self.tr_i_step.text())
            fc = float(self.tr_fc.text()) * 1000
            cout = float(self.tr_cout.text()) * 1e-6
            esr = float(self.tr_esr.text()) * 1e-3
            
            if fc <= 0 or cout <= 0: raise ValueError("频率或电容不能为 0")
            
            dv_cap = di / (2 * math.pi * fc * cout)
            dv_esr = di * esr
            
            dv_total = dv_cap + dv_esr
            
            self.res_v_cap.setText(f"{dv_cap*1000:.1f} mV")
            self.res_v_esr.setText(f"{dv_esr*1000:.1f} mV")
            self.res_v_total.setText(f"{dv_total*1000:.1f} mV")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算错误或输入无效: {e}")
