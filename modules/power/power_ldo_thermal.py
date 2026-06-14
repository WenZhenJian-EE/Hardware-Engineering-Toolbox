from modules.base_module import BaseModule
# power_ldo_thermal.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt
from utils import render_formula

class LdoThermalWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "LDO 热计算"
    description = "LDO功耗 / 结温"
    window_id = "power_ldo_th"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('LDO 线性稳压器热与功耗分析 (LDO Thermal & Power)')
        self.setGeometry(350, 350, 650, 500)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        info_lbl = QLabel("<b>核心逻辑：</b> LDO 的功耗 $P_D = (V_{in} - V_{out}) \\times I_{out} + V_{in} \\times I_q$<br>"
                          "<b>结温计算：</b> $T_J = T_A + P_D \\times \\theta_{JA}$")
        info_lbl.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        main_layout.addWidget(info_lbl)

        # 参数输入
        grp_in = QGroupBox("输入参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.inp_vin = QLineEdit("12.0"); grid.addWidget(QLabel("输入电压 Vin [V]:"), 0, 0); grid.addWidget(self.inp_vin, 0, 1)
        self.inp_vout = QLineEdit("3.3"); grid.addWidget(QLabel("输出电压 Vout [V]:"), 0, 2); grid.addWidget(self.inp_vout, 0, 3)
        self.inp_iout = QLineEdit("0.3"); grid.addWidget(QLabel("负载电流 Iout [A]:"), 1, 0); grid.addWidget(self.inp_iout, 1, 1)
        self.inp_iq = QLineEdit("0.005"); grid.addWidget(QLabel("静态电流 Iq [A]:"), 1, 2); grid.addWidget(self.inp_iq, 1, 3)
        
        self.inp_rja = QLineEdit("65.0"); grid.addWidget(QLabel("热阻 θ_JA [°C/W]:"), 2, 0); grid.addWidget(self.inp_rja, 2, 1)
        self.inp_ta = QLineEdit("60.0"); grid.addWidget(QLabel("最高环境温度 Ta [°C]:"), 2, 2); grid.addWidget(self.inp_ta, 2, 3)
        
        btn = QPushButton("计算功耗与结温 (T_J)")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; margin-top: 10px;")
        btn.clicked.connect(self.calc_thermal)
        grid.addWidget(btn, 3, 0, 1, 4)
        
        grp_in.setLayout(grid)
        main_layout.addWidget(grp_in)

        # 结果输出
        grp_res = QGroupBox("计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(12)
        
        self.out_pd = QLineEdit()
        self.out_tj = QLineEdit()
        self.status_lbl = QLabel("等待计算...")
        
        for w in [self.out_pd, self.out_tj]: 
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60; font-size: 14px;")
            
        r_grid.addWidget(QLabel("总功耗 Pd [W]:"), 0, 0); r_grid.addWidget(self.out_pd, 0, 1)
        r_grid.addWidget(QLabel("最高结温 T_J [°C]:"), 1, 0); r_grid.addWidget(self.out_tj, 1, 1)
        r_grid.addWidget(self.status_lbl, 2, 0, 1, 2)
        
        grp_res.setLayout(r_grid)
        main_layout.addWidget(grp_res)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def calc_thermal(self):
        try:
            vin = float(self.inp_vin.text())
            vout = float(self.inp_vout.text())
            iout = float(self.inp_iout.text())
            iq = float(self.inp_iq.text())
            rja = float(self.inp_rja.text())
            ta = float(self.inp_ta.text())
            
            if vin <= vout:
                raise ValueError("Vin 必须大于 Vout")

            pd = (vin - vout) * iout + (vin * iq)
            tj = ta + (pd * rja)
            
            self.out_pd.setText(f"{pd:.4f}")
            self.out_tj.setText(f"{tj:.2f}")
            
            # T_J 范围判定
            if tj >= 150:
                self.status_lbl.setText("【极危】结温已超过绝对最大额定值 (Abs Max, 通常150°C)，芯片可能瞬间烧毁或触发热保护停机！")
                self.status_lbl.setStyleSheet("color: #c0392b; font-weight: bold;")
                self.out_tj.setStyleSheet("background-color: #f2d7d5; color: #c0392b; font-weight: bold; font-size: 14px;")
            elif tj >= 125:
                self.status_lbl.setText("【警告】结温超过 125°C 工业级上限，长期运行寿命将严重衰减，建议增加散热敷铜或改用 DCDC！")
                self.status_lbl.setStyleSheet("color: #d35400; font-weight: bold;")
                self.out_tj.setStyleSheet("background-color: #fdebd0; color: #d35400; font-weight: bold; font-size: 14px;")
            elif tj >= 100:
                self.status_lbl.setText("【注意】结温较高，符合允许范围，但烫手。")
                self.status_lbl.setStyleSheet("color: #b7950b; font-weight: bold;")
                self.out_tj.setStyleSheet("background-color: #fcf3cf; color: #b7950b; font-weight: bold; font-size: 14px;")
            else:
                self.status_lbl.setText("【安全】热裕量充足，芯片运行在安全温度区间内。")
                self.status_lbl.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.out_tj.setStyleSheet("background-color: #e8f8f5; color: #27ae60; font-weight: bold; font-size: 14px;")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数据无效: {e}")
