# filter_tabs_active.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QComboBox)
from PyQt5.QtCore import Qt

class ActiveFilterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 拓扑选择与目标
        grp_top = QGroupBox("1. 滤波器拓扑与指标 (2nd Order LPF)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.combo_topo = QComboBox()
        self.combo_topo.addItems(["Sallen-Key (Unity Gain)", "MFB (Multiple Feedback) - 反相"])
        self.combo_topo.currentIndexChanged.connect(self.update_topo_desc)
        grid.addWidget(QLabel("拓扑结构:"), 0, 0); grid.addWidget(self.combo_topo, 0, 1)
        
        self.inp_fc = QLineEdit("1000"); grid.addWidget(QLabel("截止频率 fc [Hz]:"), 1, 0); grid.addWidget(self.inp_fc, 1, 1)
        self.inp_q = QLineEdit("0.707"); self.inp_q.setToolTip("0.707=Butterworth, 0.58=Bessel, 1.0=Chebyshev")
        grid.addWidget(QLabel("品质因数 Q:"), 1, 2); grid.addWidget(self.inp_q, 1, 3)
        
        grp_top.setLayout(grid)
        layout.addWidget(grp_top)
        
        # 2. 电容选型 (种子值)
        grp_cap = QGroupBox("2. 电容预选 (Capacitor Selection)")
        grid_c = QGridLayout()
        
        self.inp_c1 = QLineEdit("10"); self.inp_c1.setToolTip("Sallen-Key: 接地的电容; MFB: 反馈电容")
        grid_c.addWidget(QLabel("基准电容 C [nF]:"), 0, 0); grid_c.addWidget(self.inp_c1, 0, 1)
        
        self.inp_c2 = QLineEdit("None"); self.inp_c2.setPlaceholderText("自动计算")
        self.inp_c2.setToolTip("若不填，软件将根据 Q 值推荐最佳匹配电容")
        grid_c.addWidget(QLabel("匹配电容 [nF] (可选):"), 0, 2); grid_c.addWidget(self.inp_c2, 0, 3)
        
        grp_cap.setLayout(grid_c)
        layout.addWidget(grp_cap)
        
        # 计算按钮
        btn_calc = QPushButton("计算电阻 R & 推荐电容")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_active_filter)
        layout.addWidget(btn_calc)
        
        # 3. 结果
        grp_res = QGroupBox("3. 元件参数 (Component Values)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.res_c1 = QLineEdit(); self.res_c2 = QLineEdit()
        self.res_r1 = QLineEdit(); self.res_r2 = QLineEdit(); self.res_r3 = QLineEdit()
        
        # C1/C2 Label need to be dynamic based on topo
        self.lbl_c1 = QLabel("电容 C1:"); self.lbl_c2 = QLabel("电容 C2:")
        
        r_grid.addWidget(self.lbl_c1, 0, 0); r_grid.addWidget(self.res_c1, 0, 1)
        r_grid.addWidget(self.lbl_c2, 0, 2); r_grid.addWidget(self.res_c2, 0, 3)
        
        r_grid.addWidget(QLabel("电阻 R1:"), 1, 0); r_grid.addWidget(self.res_r1, 1, 1)
        r_grid.addWidget(QLabel("电阻 R2:"), 1, 2); r_grid.addWidget(self.res_r2, 1, 3)
        
        self.lbl_r3 = QLabel("电阻 R3 (MFB):")
        r_grid.addWidget(self.lbl_r3, 2, 0); r_grid.addWidget(self.res_r3, 2, 1)
        
        style = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_c1, self.res_c2, self.res_r1, self.res_r2, self.res_r3]:
            w.setReadOnly(True); w.setStyleSheet(style)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # 描述与公式
        self.lbl_desc = QLabel()
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet("color: #555; background-color: #f9f9f9; padding: 10px; border: 1px dashed #ccc;")
        layout.addWidget(self.lbl_desc)
        
        layout.addStretch()
        self.setLayout(layout)
        self.update_topo_desc()

    def update_topo_desc(self):
        if self.combo_topo.currentIndex() == 0: # Sallen-Key
            self.lbl_r3.setVisible(False); self.res_r3.setVisible(False)
            self.lbl_c1.setText("电容 C1 (反馈):"); self.lbl_c2.setText("电容 C2 (对地):")
            self.lbl_desc.setText("<b>Sallen-Key (Unity Gain):</b>\n"
                                  "优点：对运放带宽要求较低，输入阻抗高。\n"
                                  "缺点：高频阻带衰减受运放输出阻抗影响，不如 MFB。\n"
                                  "拓扑：Vin -> R1 -> R2 -> Vp; Vn -> Vout; C1 接 R1/R2中点到 Vout; C2 接 Vp 到 GND。")
        else: # MFB
            self.lbl_r3.setVisible(True); self.res_r3.setVisible(True)
            self.lbl_c1.setText("电容 C1 (反馈):"); self.lbl_c2.setText("电容 C2 (中间):")
            self.lbl_desc.setText("<b>MFB (Multiple Feedback):</b>\n"
                                  "优点：对元件灵敏度低，高频特性好 (反相结构)。\n"
                                  "缺点：输入阻抗由 R1 决定，增益固定为 -1 (本工具设定)。\n"
                                  "拓扑：Vin -> R1 -> Node; Node -> R2 -> Vn; Node -> C2 -> GND; Node -> C1 -> Vout; Vn -> R3 -> Vout.")

    def calc_active_filter(self):
        try:
            fc = float(self.inp_fc.text())
            q = float(self.inp_q.text())
            c_base_nf = float(self.inp_c1.text())
            c_base = c_base_nf * 1e-9
            
            # User optional C2
            c_opt = 0
            if self.inp_c2.text() and self.inp_c2.text().lower() != "none":
                try: c_opt = float(self.inp_c2.text()) * 1e-9
                except: pass
            
            topo = self.combo_topo.currentIndex()
            w = 2 * math.pi * fc
            
            if topo == 0: # Sallen-Key
                # C1 (Feedback), C2 (Ground).
                # Condition for Real R: C1 >= 4 * Q^2 * C2
                # Let's verify or pick C2.
                
                c1 = c_base # User inputs the larger one usually
                
                if c_opt > 0:
                    c2 = c_opt
                else:
                    # Auto Pick C2. Let m = C1/C2. m >= 4Q^2.
                    # Pick m slightly larger for real roots.
                    m_min = 4 * q**2
                    m_pick = m_min * 1.5 # Margin
                    c2 = c1 / m_pick
                
                # Check realizability
                if c1 < 4 * q**2 * c2 * 0.99:
                     QMessageBox.warning(self, "参数错误", "Sallen-Key Unity Gain 要求 C1 >= 4*Q^2*C2，否则电阻为虚数。\n请减小 C2 或增大 C1。")
                     return

                # Calc R
                # R1,2 = [1 +/- sqrt(1 - 4Q^2 C2/C1)] / (2 w C2 Q)  <-- Simplified, careful derivation
                # Standard TI: 
                # m = C1/C2
                # R1 = 2 / (w * C2 * (1/Q + sqrt(1/Q^2 - 4*m))) ? No.
                # Use:
                # k = 1 (Gain)
                # a = 1, b = 1/Q
                # R1 = (a*C2 - sqrt(a^2 C2^2 - 4 b k C1 C2)) / ... No, this is messy.
                
                # Let's use the explicit R1, R2 for m=C1/C2
                term = math.sqrt(1 - 4 * (q**2) * (c2/c1))
                r1 = (1 + term) / (2 * w * c2 * q)
                r2 = (1 - term) / (2 * w * c2 * q)
                
                self.res_c1.setText(f"{c1*1e9:.3f} nF")
                self.res_c2.setText(f"{c2*1e9:.3f} nF")
                self.res_r1.setText(f"{r1/1000:.3f} kΩ")
                self.res_r2.setText(f"{r2/1000:.3f} kΩ")
                self.res_r3.setText("---")

            else: # MFB (Gain = -1)
                # C1 (Feedback), C2 (Gnd/Node). 
                # Note: Definitions vary. Here we use TI's notation C1=C_fb, C2=C_gnd? 
                # Actually TI often uses C5 and C2.
                # Let's use simplified design for Gain = -1.
                # C1 (Feedback) = c_base.
                # C2 (Ground).
                # Condition: C2 > C1?? 
                # For MFB Gain=-1:
                # Q = 0.5 * sqrt(C2/C1) => C2 = 4 * Q^2 * C1.
                # This assumes R1=R2=R3.
                
                c1 = c_base
                
                # Design for R1 = R2 = R3 = R (Special case Gain=-1)
                # Then Q = 0.5 * sqrt(C2/C1).
                # So C2 must be 4*Q^2 * C1.
                
                if c_opt > 0:
                    c2 = c_opt
                    # If user forces C2, we might not get R1=R2=R3, need general formula.
                    # General MFB (Gain=-1):
                    # Let R1=R3=R (Input=Feedback).
                    # w = 1/sqrt(R*R2 * C1*C2)
                    # Q = w / (2/(R*C1) + 1/(R2*C1)) = ...
                else:
                    c2 = c1 * 4 * (q**2) # Matched for R1=R2=R3
                
                # Calculate R's
                # From "Op Amps for Everyone":
                # k = 1
                # w0 = 2*pi*fc
                # C1 chosen. C2 chosen.
                # R2 = (1 / (2*w0*C1*Q)) * (1 +/- sqrt(1 - 4*Q^2*(1+k)*C1/C2)) ?? No
                
                # Let's stick to the robust iterative method or specific ratio
                # If we picked C2 = 4*Q^2*C1:
                # R2 = 1 / (2 * w * Q * c1)  (Derived from Q formula when R1=R2=R3)
                # R1 = R2
                # R3 = R2
                
                # General case calculation:
                # let's assume R1=R3=R_in_fb. R2=R_gnd.
                # 1/Q = sqrt(R2/R) * (2*sqrt(C2/C1) + sqrt(C1/C2) * R/R2) ... complex
                
                # Use simplified logic:
                # 1. Pick C1 (Feedback)
                # 2. Calc C2 = C1 * (4*Q^2 * (1 + Gain)) -> For Gain=1, C2 = C1 * 8 Q^2?
                # No, standard MFB Gain=-1 design:
                # C_ground (C2) usually ~ 10 * C_feedback (C1).
                
                # Let's use the exact synthesis:
                k = 1 # Magnitude of gain
                c2 = c1 * 10 # Heuristic if not specified
                if c_opt > 0: c2 = c_opt

                # Coefficients
                # R2 = 1 / (2 * w * c1 * Q) ?? No.
                
                # Correct Algorithm (ADI):
                # 1. Pick C1 (Feedback)
                # 2. Pick C2 (Ground) such that C2 > C1 * 4 * Q^2 * (1+k) / k ?? No.
                
                # Let's go with R1=R3=R.
                # w^2 = 1 / (R * R2 * C1 * C2)  =>  R * R2 = 1 / (w^2 C1 C2)  (Eq 1)
                # 1/Q = sqrt(1/(w^2 C1 C2)) * (2/R + 1/R2) * C1 ? No.
                # 1/Q = (2/R + 1/R2) / (w * C2) ??
                # Q = w * C2 / (2/R + 1/R2).
                
                # Let x = 1/R, y = 1/R2.
                # x * y = w^2 * C1 * C2  (from Eq 1, inverted R)
                # 2x + y = w * C2 / Q
                
                # We have system:
                # y = S - 2x  (where S = w*C2/Q)
                # x(S - 2x) = P (where P = w^2 C1 C2)
                # 2x^2 - Sx + P = 0
                
                S = w * c2 / q
                P = w**2 * c1 * c2
                
                discriminant = S**2 - 8*P
                if discriminant < 0:
                    QMessageBox.warning(self, "参数冲突", "MFB: 选定的电容无法实现目标 Q 值。\n请增大 C2 (对地电容) 或减小 C1 (反馈电容)。")
                    return
                
                sqrt_d = math.sqrt(discriminant)
                # Solutions for x (Conductance 1/R)
                x1 = (S + sqrt_d) / 4.0
                x2 = (S - sqrt_d) / 4.0
                
                # Pick valid real R
                # Usually pick the one that gives reasonable R values
                G_R = x1 
                G_R2 = S - 2*G_R
                
                r = 1.0 / G_R
                r2 = 1.0 / G_R2
                r1 = r
                r3 = r # Since we assumed R1=R3 for Gain=-1
                
                self.res_c1.setText(f"{c1*1e9:.3f} nF")
                self.res_c2.setText(f"{c2*1e9:.3f} nF")
                self.res_r1.setText(f"{r1/1000:.3f} kΩ")
                self.res_r2.setText(f"{r2/1000:.3f} kΩ")
                self.res_r3.setText(f"{r3/1000:.3f} kΩ")

        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")