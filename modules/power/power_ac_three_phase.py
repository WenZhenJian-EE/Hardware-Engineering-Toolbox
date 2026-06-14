from modules.base_module import BaseModule
import sys
import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QGroupBox, 
                             QTabWidget, QGridLayout, QMessageBox, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ThreePhaseCalculatorWindow(BaseModule):
    category = "1. 磁性元件与电源拓扑 (Magnetics & Topology)"
    display_name = "三相与锁相环(PLL)"
    description = "Y-Δ / PFC / 坐标变换"
    window_id = "power_ac_3ph"

    def init_module_ui(self):
        
        self.setWindowTitle("三相电与锁相环(PLL)工具箱 (3-Phase & PLL Tool)")
        self.resize(700, 550)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 样式表
        self.setStyleSheet("""
            QGroupBox { font-weight: bold; border: 1px solid #bdc3c7; margin-top: 10px; border-radius: 5px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QLabel { font-size: 12px; }
            QLineEdit { border: 1px solid #ccc; border-radius: 3px; padding: 4px; background: #fff; }
            QPushButton { background-color: #3498db; color: white; border-radius: 4px; padding: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #2980b9; }
            QComboBox { border: 1px solid #ccc; border-radius: 3px; padding: 4px; }
        """)

        # 选项卡
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # --- Tab 1: 三相参数换算 ---
        self.tab_params = QWidget()
        tabs.addTab(self.tab_params, "参数换算 (V/I/P/Z)")
        self.init_params_tab()

        # --- Tab 2: PFC与无功补偿 ---
        self.tab_pfc = QWidget()
        tabs.addTab(self.tab_pfc, "PFC无功补偿")
        self.init_pfc_tab()

        # --- Tab 3: Y-Δ 变换 ---
        self.tab_yd = QWidget()
        tabs.addTab(self.tab_yd, "Y-Δ 阻抗变换")
        self.init_yd_tab()

        # --- Tab 4: PLL与坐标变换 ---
        self.tab_pll = QWidget()
        tabs.addTab(self.tab_pll, "PLL与坐标变换")
        self.init_pll_tab()

    # ==================== Tab 1: 参数换算 ====================
    def init_params_tab(self):
        layout = QVBoxLayout(self.tab_params)
        
        # 输入区
        input_group = QGroupBox("系统输入 (System Input)")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)

        input_layout.addWidget(QLabel("线电压 V_LL (V):"), 0, 0)
        self.input_vll = QLineEdit("380")
        input_layout.addWidget(self.input_vll, 0, 1)

        input_layout.addWidget(QLabel("线电流 I_Line (A):"), 0, 2)
        self.input_iline = QLineEdit("10")
        input_layout.addWidget(self.input_iline, 0, 3)

        input_layout.addWidget(QLabel("功率因数 PF (0-1):"), 1, 0)
        self.input_pf = QLineEdit("0.8")
        input_layout.addWidget(self.input_pf, 1, 1)

        input_layout.addWidget(QLabel("频率 Freq (Hz):"), 1, 2)
        self.input_freq = QLineEdit("50")
        input_layout.addWidget(self.input_freq, 1, 3)

        input_layout.addWidget(QLabel("负载接法:"), 2, 0)
        self.combo_conn = QComboBox()
        self.combo_conn.addItems(["星型接法 (Star/Y)", "角型接法 (Delta/Δ)"])
        input_layout.addWidget(self.combo_conn, 2, 1)

        btn_calc = QPushButton("计算 (Calculate)")
        btn_calc.clicked.connect(self.calculate_params)
        input_layout.addWidget(btn_calc, 2, 3)

        layout.addWidget(input_group)

        # 结果区
        res_group = QGroupBox("计算结果 (Results)")
        res_layout = QGridLayout()
        res_group.setLayout(res_layout)

        self.res_labels = {}
        fields = [
            ("相电压 V_ph (V):", "v_ph", 0, 0), ("相电流 I_ph (A):", "i_ph", 0, 2),
            ("视在功率 S (kVA):", "s_val", 1, 0), ("有功功率 P (kW):", "p_val", 1, 2),
            ("无功功率 Q (kVar):", "q_val", 2, 0), ("单相阻抗 Z (Ω):", "z_ph", 2, 2),
            ("等效电阻 R (Ω):", "r_ph", 3, 0), ("等效电抗 X (Ω):", "x_ph", 3, 2),
            ("等效电感/容:", "lc_val", 4, 0)
        ]

        for text, key, r, c in fields:
            res_layout.addWidget(QLabel(text), r, c)
            lbl = QLabel("-")
            lbl.setStyleSheet("color: blue; font-weight: bold;")
            res_layout.addWidget(lbl, r, c+1)
            self.res_labels[key] = lbl

        layout.addWidget(res_group)
        layout.addStretch()

    def calculate_params(self):
        try:
            v_ll = float(self.input_vll.text())
            i_line = float(self.input_iline.text())
            pf = float(self.input_pf.text())
            freq = float(self.input_freq.text())
            is_star = "Star" in self.combo_conn.currentText()

            if not (0 <= pf <= 1):
                raise ValueError("PF must be 0-1")

            # 计算逻辑
            if is_star:
                v_ph = v_ll / math.sqrt(3)
                i_ph = i_line
            else:
                v_ph = v_ll
                i_ph = i_line / math.sqrt(3)

            s_total = math.sqrt(3) * v_ll * i_line
            p_total = s_total * pf
            q_total = math.sqrt(max(0, s_total**2 - p_total**2))

            z_ph = v_ph / i_ph if i_ph > 0 else 0
            r_ph = z_ph * pf
            x_ph = math.sqrt(max(0, z_ph**2 - r_ph**2))

            lc_str = "-"
            if x_ph > 0 and freq > 0:
                l_val = x_ph / (2 * math.pi * freq) * 1000 # mH
                lc_str = f"L: {l_val:.2f} mH (若感性)"

            # 更新UI
            self.res_labels['v_ph'].setText(f"{v_ph:.2f}")
            self.res_labels['i_ph'].setText(f"{i_ph:.2f}")
            self.res_labels['s_val'].setText(f"{s_total/1000:.3f}")
            self.res_labels['p_val'].setText(f"{p_total/1000:.3f}")
            self.res_labels['q_val'].setText(f"{q_total/1000:.3f}")
            self.res_labels['z_ph'].setText(f"{z_ph:.2f}")
            self.res_labels['r_ph'].setText(f"{r_ph:.2f}")
            self.res_labels['x_ph'].setText(f"{x_ph:.2f}")
            self.res_labels['lc_val'].setText(lc_str)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入无效: {str(e)}")

    # ==================== Tab 2: PFC 计算 ====================
    def init_pfc_tab(self):
        layout = QVBoxLayout(self.tab_pfc)
        
        input_group = QGroupBox("PFC 参数")
        input_layout = QGridLayout()
        input_group.setLayout(input_layout)

        input_layout.addWidget(QLabel("有功功率 P (kW):"), 0, 0)
        self.pfc_p = QLineEdit("10")
        input_layout.addWidget(self.pfc_p, 0, 1)

        input_layout.addWidget(QLabel("线电压 V_LL (V):"), 0, 2)
        self.pfc_v = QLineEdit("380")
        input_layout.addWidget(self.pfc_v, 0, 3)

        input_layout.addWidget(QLabel("当前 PF (Old):"), 1, 0)
        self.pfc_old = QLineEdit("0.8")
        input_layout.addWidget(self.pfc_old, 1, 1)

        input_layout.addWidget(QLabel("目标 PF (Target):"), 1, 2)
        self.pfc_target = QLineEdit("0.95")
        input_layout.addWidget(self.pfc_target, 1, 3)

        input_layout.addWidget(QLabel("频率 (Hz):"), 2, 0)
        self.pfc_freq = QLineEdit("50")
        input_layout.addWidget(self.pfc_freq, 2, 1)

        input_layout.addWidget(QLabel("电容柜接法:"), 2, 2)
        self.pfc_conn = QComboBox()
        self.pfc_conn.addItems(["角型 (Delta/Δ) - 推荐", "星型 (Star/Y)"])
        input_layout.addWidget(self.pfc_conn, 2, 3)

        btn_pfc = QPushButton("计算补偿量 (Calculate)")
        btn_pfc.clicked.connect(self.calculate_pfc)
        input_layout.addWidget(btn_pfc, 3, 3)

        layout.addWidget(input_group)

        res_group = QGroupBox("补偿结果")
        res_layout = QVBoxLayout()
        res_group.setLayout(res_layout)
        
        self.lbl_pfc_q = QLabel("需补偿无功 Q_c: - kVar")
        self.lbl_pfc_q.setStyleSheet("font-size: 14px; font-weight: bold;")
        res_layout.addWidget(self.lbl_pfc_q)
        
        self.lbl_pfc_c = QLabel("单相电容 C_phase: - uF")
        self.lbl_pfc_c.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
        res_layout.addWidget(self.lbl_pfc_c)
        
        self.lbl_pfc_note = QLabel("注：电容耐压需 > 线电压(Δ接法) 或 相电压(Y接法)")
        self.lbl_pfc_note.setStyleSheet("color: gray; font-size: 10px;")
        res_layout.addWidget(self.lbl_pfc_note)

        layout.addWidget(res_group)
        layout.addStretch()

    def calculate_pfc(self):
        try:
            p_kw = float(self.pfc_p.text())
            v_ll = float(self.pfc_v.text())
            pf_old = float(self.pfc_old.text())
            pf_new = float(self.pfc_target.text())
            freq = float(self.pfc_freq.text())
            is_delta = "Delta" in self.pfc_conn.currentText()

            if pf_old >= pf_new:
                QMessageBox.warning(self, "提示", "目标PF应大于当前PF")
                return

            tan1 = math.tan(math.acos(pf_old))
            tan2 = math.tan(math.acos(pf_new))
            
            q_kvar = p_kw * (tan1 - tan2)
            q_var = q_kvar * 1000

            # C = Q / (3 * w * V^2)  (这里的V是加在电容两端的电压)
            if is_delta:
                v_cap = v_ll
            else:
                v_cap = v_ll / math.sqrt(3)

            omega = 2 * math.pi * freq
            c_f = (q_var / 3) / (omega * v_cap**2)
            c_uf = c_f * 1e6

            self.lbl_pfc_q.setText(f"需补偿无功 Q_c: {q_kvar:.3f} kVar")
            self.lbl_pfc_c.setText(f"单相电容 C_phase: {c_uf:.2f} uF (每相)")

        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))

    # ==================== Tab 3: Y-Delta 变换 ====================
    def init_yd_tab(self):
        layout = QVBoxLayout(self.tab_yd)
        
        group = QGroupBox("Y <-> Δ 阻抗变换 (平衡负载)")
        grid = QGridLayout()
        group.setLayout(grid)

        grid.addWidget(QLabel("已知单相阻抗 Z (Ω):"), 0, 0)
        self.yd_z = QLineEdit("10")
        grid.addWidget(self.yd_z, 0, 1)

        grid.addWidget(QLabel("变换方向:"), 1, 0)
        self.yd_dir = QComboBox()
        self.yd_dir.addItems(["Y 转 Δ (Y -> Δ)", "Δ 转 Y (Δ -> Y)"])
        grid.addWidget(self.yd_dir, 1, 1)

        btn_yd = QPushButton("转换")
        btn_yd.clicked.connect(self.calculate_yd)
        grid.addWidget(btn_yd, 2, 1)

        layout.addWidget(group)

        self.yd_res = QLabel("结果: - Ω")
        self.yd_res.setStyleSheet("font-size: 16px; font-weight: bold; color: #d35400; margin-top: 20px;")
        self.yd_res.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.yd_res)

        layout.addWidget(QLabel("原理:\nZ_Δ = 3 * Z_Y\nZ_Y = Z_Δ / 3"))
        layout.addStretch()

    def calculate_yd(self):
        try:
            z = float(self.yd_z.text())
            if "Y -> Δ" in self.yd_dir.currentText():
                res = z * 3
                sym = "Δ"
            else:
                res = z / 3
                sym = "Y"
            self.yd_res.setText(f"等效 {sym} 阻抗: {res:.4f} Ω")
        except:
            pass

    # ==================== Tab 4: PLL与坐标变换 ====================
    def init_pll_tab(self):
        layout = QVBoxLayout(self.tab_pll)
        
        # --- Section 1: Coordinate Transform ---
        grp_transform = QGroupBox("1. 坐标变换 (abc <-> αβ <-> dq)")
        grid_tf = QGridLayout()
        grid_tf.setSpacing(10)
        grp_transform.setLayout(grid_tf)
        
        grid_tf.addWidget(QLabel("三相输入 (a,b,c):"), 0, 0)
        self.tf_a = QLineEdit("220"); self.tf_a.setPlaceholderText("a")
        self.tf_b = QLineEdit("-110"); self.tf_b.setPlaceholderText("b")
        self.tf_c = QLineEdit("-110"); self.tf_c.setPlaceholderText("c")
        h_abc = QHBoxLayout(); h_abc.addWidget(self.tf_a); h_abc.addWidget(self.tf_b); h_abc.addWidget(self.tf_c)
        grid_tf.addLayout(h_abc, 0, 1, 1, 3)
        
        grid_tf.addWidget(QLabel("网侧电角度 θ [度]:"), 1, 0)
        self.tf_theta = QLineEdit("0")
        grid_tf.addWidget(self.tf_theta, 1, 1)
        
        btn_tf_clarke = QPushButton("Clarke (abc -> αβ)")
        btn_tf_clarke.clicked.connect(self.calc_clarke)
        btn_tf_park = QPushButton("Park (αβ -> dq)")
        btn_tf_park.clicked.connect(self.calc_park)
        
        grid_tf.addWidget(btn_tf_clarke, 2, 0, 1, 2)
        grid_tf.addWidget(btn_tf_park, 2, 2, 1, 2)
        
        self.lbl_tf_alpha_beta = QLineEdit(); self.lbl_tf_alpha_beta.setReadOnly(True)
        self.lbl_tf_dq = QLineEdit(); self.lbl_tf_dq.setReadOnly(True)
        self.lbl_tf_alpha_beta.setStyleSheet("background-color: #f0f0f0; color: #2980b9; font-weight: bold;")
        self.lbl_tf_dq.setStyleSheet("background-color: #f0f0f0; color: #27ae60; font-weight: bold;")
        
        grid_tf.addWidget(QLabel("α, β 结果:"), 3, 0); grid_tf.addWidget(self.lbl_tf_alpha_beta, 3, 1, 1, 3)
        grid_tf.addWidget(QLabel("d, q 结果:"), 4, 0); grid_tf.addWidget(self.lbl_tf_dq, 4, 1, 1, 3)
        
        # Note
        note = QLabel("注: Clarke 变换采用恒幅值变换 (Amplitude Invariant)")
        note.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        grid_tf.addWidget(note, 5, 0, 1, 4)
        
        layout.addWidget(grp_transform)

        # --- Section 2: PLL PI Tuning ---
        grp_pll = QGroupBox("2. SRF-PLL PI 参数整定 (基于带宽与阻尼)")
        grid_pll = QGridLayout()
        grid_pll.setSpacing(10)
        grp_pll.setLayout(grid_pll)
        
        grid_pll.addWidget(QLabel("电网电压峰值 V_m [V]:"), 0, 0)
        self.pll_vm = QLineEdit("311.12") # 220*sqrt(2)
        grid_pll.addWidget(self.pll_vm, 0, 1)
        
        grid_pll.addWidget(QLabel("目标带宽 f_bw [Hz]:"), 0, 2)
        self.pll_fbw = QLineEdit("20") # 通常10~50Hz
        grid_pll.addWidget(self.pll_fbw, 0, 3)
        
        grid_pll.addWidget(QLabel("阻尼系数 ζ (Zeta):"), 1, 0)
        self.pll_zeta = QLineEdit("0.707") 
        grid_pll.addWidget(self.pll_zeta, 1, 1)
        
        btn_pll = QPushButton("计算 PI 参数 (Kp, Ki)")
        btn_pll.clicked.connect(self.calc_pll_pi)
        btn_pll.setStyleSheet("background-color: #8e44ad;")
        grid_pll.addWidget(btn_pll, 1, 2, 1, 2)
        
        self.lbl_pll_kp = QLineEdit(); self.lbl_pll_kp.setReadOnly(True)
        self.lbl_pll_ki = QLineEdit(); self.lbl_pll_ki.setReadOnly(True)
        self.lbl_pll_kp.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; font-weight: bold;")
        self.lbl_pll_ki.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; font-weight: bold;")
        
        grid_pll.addWidget(QLabel("比例系数 Kp:"), 2, 0); grid_pll.addWidget(self.lbl_pll_kp, 2, 1)
        grid_pll.addWidget(QLabel("积分系数 Ki:"), 2, 2); grid_pll.addWidget(self.lbl_pll_ki, 2, 3)
        
        layout.addWidget(grp_pll)
        layout.addStretch()

    def calc_clarke(self):
        try:
            a = float(self.tf_a.text())
            b = float(self.tf_b.text())
            c = float(self.tf_c.text())
            
            # Amplitude invariant Clarke transform
            alpha = (2/3) * (a - 0.5*b - 0.5*c)
            beta = (2/3) * (math.sqrt(3)/2 * b - math.sqrt(3)/2 * c)
            
            self.lbl_tf_alpha_beta.setText(f"α = {alpha:.3f}, β = {beta:.3f}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入错误: {e}")

    def calc_park(self):
        try:
            # First ensure alpha/beta are up to date
            self.calc_clarke()
            
            alpha_str = self.lbl_tf_alpha_beta.text()
            if not alpha_str: return
            
            parts = alpha_str.split(',')
            alpha = float(parts[0].split('=')[1].strip())
            beta = float(parts[1].split('=')[1].strip())
            
            theta_deg = float(self.tf_theta.text())
            theta_rad = math.radians(theta_deg)
            
            d_val = alpha * math.cos(theta_rad) + beta * math.sin(theta_rad)
            q_val = -alpha * math.sin(theta_rad) + beta * math.cos(theta_rad)
            
            self.lbl_tf_dq.setText(f"d = {d_val:.3f}, q = {q_val:.3f}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入错误: {e}")

    def calc_pll_pi(self):
        try:
            vm = float(self.pll_vm.text())
            fbw = float(self.pll_fbw.text())
            zeta = float(self.pll_zeta.text())
            
            if vm <= 0 or fbw <= 0 or zeta <= 0:
                raise ValueError("参数必须大于 0")
                
            wn = 2 * math.pi * fbw
            kp = (2 * zeta * wn) / vm
            ki = (wn * wn) / vm
            
            self.lbl_pll_kp.setText(f"{kp:.5f}")
            self.lbl_pll_ki.setText(f"{ki:.5f}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算失败: {e}")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = ThreePhaseCalculatorWindow()
    win.show()
    sys.exit(app.exec_())