from modules.base_module import BaseModule
# safe_creepage_clearance.py

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QComboBox, 
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import math

class SafetySpacingWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "安规爬电与间隙"
    description = "IEC 60950 / 62368 查表"
    window_id = "safe_creepage"

    def init_module_ui(self):
        
        self.setWindowTitle("安规爬电与间隙计算器 (Creepage & Clearance - IEC 60950/62368)")
        self.resize(800, 650)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 样式表
        self.setStyleSheet("""
            QWidget { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; }
            QGroupBox { font-size: 13px; font-weight: bold; border: 1px solid #bdc3c7; margin-top: 15px; border-radius: 5px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #2c3e50; }
            QLabel { font-size: 12px; }
            QLineEdit { border: 1px solid #ccc; border-radius: 4px; padding: 5px; background: #fff; }
            QComboBox { border: 1px solid #ccc; border-radius: 4px; padding: 5px; background: #fff; }
            QPushButton { background-color: #3498db; color: white; border-radius: 5px; padding: 8px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #2980b9; }
        """)

        # --- 第一部分：参数输入 ---
        grp_input = QGroupBox("1. 输入参数 (IEC 标准)")
        grid_in = QGridLayout()
        grid_in.setSpacing(15)
        grid_in.setContentsMargins(15, 20, 15, 15)

        self.in_voltage = QLineEdit("800")
        self.in_voltage.setPlaceholderText("例如: 800")
        grid_in.addWidget(QLabel("工作电压 (RMS 或 DC) [V]:"), 0, 0)
        grid_in.addWidget(self.in_voltage, 0, 1)

        self.in_peak = QLineEdit("1130")
        self.in_peak.setPlaceholderText("例如: 1130 (用于Clearance)")
        self.in_peak.setToolTip("如果不确定，可以填 RMS * 1.414")
        grid_in.addWidget(QLabel("峰值电压 (Peak) [V]:"), 0, 2)
        grid_in.addWidget(self.in_peak, 0, 3)

        self.in_pd = QComboBox()
        self.in_pd.addItems([
            "1: 无污染或干燥非导电污染 (密封空间)", 
            "2: 非导电污染, 偶尔凝露导电 (办公/实验室)", 
            "3: 导电污染, 或干非导电污染遇凝露 (工业)"
        ])
        self.in_pd.setCurrentIndex(1)
        grid_in.addWidget(QLabel("污染等级 (Pollution Degree):"), 1, 0)
        grid_in.addWidget(self.in_pd, 1, 1, 1, 3)

        self.in_cti = QComboBox()
        self.in_cti.addItems([
            "材料组别 I: 600 ≤ CTI", 
            "材料组别 II: 400 ≤ CTI < 600", 
            "材料组别 IIIa: 175 ≤ CTI < 400 (FR4 默认)", 
            "材料组别 IIIb: 100 ≤ CTI < 175"
        ])
        self.in_cti.setCurrentIndex(2)
        grid_in.addWidget(QLabel("PCB 材料组别 (CTI):"), 2, 0)
        grid_in.addWidget(self.in_cti, 2, 1, 1, 3)

        self.in_insulation = QComboBox()
        self.in_insulation.addItems([
            "功能绝缘 / 基本绝缘 (Functional / Basic)", 
            "附加绝缘 (Supplementary)", 
            "加强绝缘 / 双重绝缘 (Reinforced)"
        ])
        grid_in.addWidget(QLabel("绝缘类型要求:"), 3, 0)
        grid_in.addWidget(self.in_insulation, 3, 1)

        self.in_altitude = QLineEdit("2000")
        grid_in.addWidget(QLabel("海拔高度 [m]:"), 3, 2)
        grid_in.addWidget(self.in_altitude, 3, 3)

        grp_input.setLayout(grid_in)
        layout.addWidget(grp_input)

        # --- 计算按钮 ---
        btn_calc = QPushButton("依据 IEC 60950 / IEC 62368 计算")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad;")
        btn_calc.clicked.connect(self.calculate_safety)
        layout.addWidget(btn_calc)

        # --- 第二部分：结果显示 ---
        grp_res = QGroupBox("2. 计算结果 (Min. Requirements)")
        grid_res = QGridLayout()
        grid_res.setSpacing(15)
        grid_res.setContentsMargins(15, 20, 15, 15)

        style_res = "background-color: #f4ecf7; color: #8e44ad; font-weight: bold; font-size: 16px;"

        self.out_creepage = QLineEdit(); self.out_creepage.setReadOnly(True)
        self.out_creepage.setStyleSheet(style_res)
        grid_res.addWidget(QLabel("【最小爬电距离】 Creepage [mm]:"), 0, 0)
        grid_res.addWidget(self.out_creepage, 0, 1)

        self.out_clearance = QLineEdit(); self.out_clearance.setReadOnly(True)
        self.out_clearance.setStyleSheet(style_res)
        grid_res.addWidget(QLabel("【最小电气间隙】 Clearance [mm]:"), 1, 0)
        grid_res.addWidget(self.out_clearance, 1, 1)

        self.out_alt_factor = QLineEdit(); self.out_alt_factor.setReadOnly(True)
        self.out_alt_factor.setStyleSheet("background-color: #f0f0f0; color: #7f8c8d; font-weight: bold;")
        grid_res.addWidget(QLabel("其中海拔乘子 (Kp):"), 2, 0)
        grid_res.addWidget(self.out_alt_factor, 2, 1)

        self.out_slotting = QLabel()
        self.out_slotting.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px;")
        grid_res.addWidget(self.out_slotting, 3, 0, 1, 2)

        grp_res.setLayout(grid_res)
        layout.addWidget(grp_res)

        # 说明文字
        info = QLabel(
            "说明:\n"
            "1. 爬电距离 (Creepage) 依赖于工作电压的 RMS/DC 值、污染等级和材料的 CTI。\n"
            "2. 电气间隙 (Clearance) 依赖于工作电压的 峰值 (Peak)、海拔高度。高海拔空气稀薄，易击穿。\n"
            "3. 如果计算出 爬电距离 < 电气间隙，标准要求 爬电距离 = 电气间隙。\n"
            "4. 加强绝缘要求通常是基本绝缘距离的 2 倍。"
        )
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; line-height: 1.5;")
        layout.addWidget(info)
        layout.addStretch()

    def interpolate_table(self, v, table_v, table_d):
        if v <= table_v[0]: return table_d[0]
        if v >= table_v[-1]: return table_d[-1]
        for i in range(len(table_v) - 1):
            if table_v[i] <= v <= table_v[i+1]:
                # 线性插值
                ratio = (v - table_v[i]) / (table_v[i+1] - table_v[i])
                return table_d[i] + ratio * (table_d[i+1] - table_d[i])
        return table_d[-1]

    def calculate_safety(self):
        try:
            v_rms = float(self.in_voltage.text())
            v_peak = float(self.in_peak.text())
            alt = float(self.in_altitude.text())
            
            pd_idx = self.in_pd.currentIndex() + 1 # 1, 2, 3
            cti_idx = self.in_cti.currentIndex() # 0:I, 1:II, 2:IIIa, 3:IIIb
            ins_type = self.in_insulation.currentIndex() # 0:Basic, 1:Supp, 2:Reinforced
            
            is_reinforced = (ins_type == 2)
            
            # ------------------------------------------------------------------
            # 1. 计算爬电距离 Creepage (基于 IEC 标准简化数据点插值)
            # ------------------------------------------------------------------
            # 电压档位
            v_crp = [50, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000]
            
            # 各电压档位对应的爬电距离 (PD1 独立, PD2/3 区分 CTI)
            if pd_idx == 1:
                # 污染等级 1
                crp_data = [0.18, 0.25, 0.28, 0.32, 0.42, 0.56, 0.75, 1.0, 1.3, 1.8, 2.4, 3.2]
                creepage = self.interpolate_table(v_rms, v_crp, crp_data)
            elif pd_idx == 2:
                # 污染等级 2 区别材料组别 [I, II, IIIa, IIIb=IIIa] (这里将 IIIb 基本等同于 IIIa, 某些标准中可能只查到 IIIa)
                if cti_idx == 0:   d_data = [0.6, 0.7, 0.8, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0]
                elif cti_idx == 1: d_data = [0.9, 1.0, 1.1, 1.1, 1.4, 1.8, 2.2, 2.8, 3.6, 4.5, 5.6, 7.1]
                else:              d_data = [1.2, 1.4, 1.5, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0]
                creepage = self.interpolate_table(v_rms, v_crp, d_data)
            else:
                # 污染等级 3
                if cti_idx == 0:   d_data = [1.5, 1.8, 1.9, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0, 12.5]
                elif cti_idx == 1: d_data = [1.7, 2.0, 2.1, 2.2, 2.8, 3.6, 4.5, 5.6, 7.1, 9.0, 11.0, 14.0]
                else:              d_data = [1.9, 2.2, 2.4, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0, 12.5, 16.0]
                creepage = self.interpolate_table(v_rms, v_crp, d_data)

            # ------------------------------------------------------------------
            # 2. 计算电气间隙 Clearance
            # ------------------------------------------------------------------
            v_clr = [50, 100, 150, 300, 600, 1000]
            if pd_idx == 1:
                # Basic clearance (PD1)
                clr_data = [0.18, 0.2, 0.5, 1.5, 3.0, 4.0]
            elif pd_idx == 2:
                clr_data = [0.2,  0.2, 0.5, 1.5, 3.0, 4.0]
            else:
                clr_data = [0.8,  0.8, 0.8, 1.5, 3.0, 4.0]
                
            base_clearance = self.interpolate_table(v_peak, v_clr, clr_data)

            # ------------------------------------------------------------------
            # 3. 修正系数与保护类型加倍
            # ------------------------------------------------------------------
            # 海拔修正 (Altitude Multiplier Kb) - IEC 60664-1 Table A.2 Piecewise Interpolation
            alt_table = [2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 15000, 20000]
            factor_table = [1.00, 1.14, 1.29, 1.48, 1.70, 1.95, 2.25, 2.62, 3.02, 6.53, 17.0]
            
            if alt <= 2000:
                alt_factor = 1.0
            elif alt >= 20000:
                alt_factor = 17.0
            else:
                alt_factor = 1.0
                for i in range(len(alt_table) - 1):
                    if alt_table[i] <= alt <= alt_table[i+1]:
                        ratio = (alt - alt_table[i]) / (alt_table[i+1] - alt_table[i])
                        alt_factor = factor_table[i] + ratio * (factor_table[i+1] - factor_table[i])
                        break
            
            final_clearance = base_clearance * alt_factor

            # 加强绝缘: Clearance 倍增 1.6 左右 (IEC中有些查次高一档的脉冲电压), 此处采用通常估算 x2
            # Creepage 必须是 Basic 的 2 倍。
            if is_reinforced:
                # 对于加强绝缘，电气间隙一般也要加倍或者按照高一等级的瞬态过电压计算
                final_clearance *= 2.0
                creepage *= 2.0

            # 标准规定：爬电距离永远不应小于电气间隙。如果计算出爬电小于间隙，强制拉平。
            if creepage < final_clearance:
                creepage = final_clearance

            # ------------------------------------------------------------------
            # 4. 显示与提示
            # ------------------------------------------------------------------
            self.out_creepage.setText(f"{creepage:.2f}  [ 或 {creepage/0.0254:.0f} mil ]")
            self.out_clearance.setText(f"{final_clearance:.2f}  [ 或 {final_clearance/0.0254:.0f} mil ]")
            self.out_alt_factor.setText(f"{alt_factor:.3f} (海拔 > 2000m 倍增系数)")

            if creepage > final_clearance + 0.5:
                slot_txt = f"提示: 爬电距离 ({creepage:.1f}mm) 远大于电气间隙 ({final_clearance:.1f}mm)!!!\n\n空间不够时，可以【在 PCB 开槽 (Slotting)】将爬电路径阻断转化为空间间隙从而符合安规要求。"
                self.out_slotting.setText(slot_txt)
            else:
                self.out_slotting.setText("")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入值错误: {e}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = SafetySpacingWindow()
    win.show()
    sys.exit(app.exec_())
