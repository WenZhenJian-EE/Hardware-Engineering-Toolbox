import math
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QScrollArea, QTabWidget, QFrame, QHBoxLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from gui.base_window import BaseWindow

class PdnAnalysisTab(BaseWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 顶部说明
        top_info = QLabel("PDN (Power Distribution Network) 设计工具箱")
        top_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
        main_layout.addWidget(top_info)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #bdc3c7; background: #fff; border-radius: 4px; }
            QTabBar::tab { background: #ecf0f1; border: 1px solid #bdc3c7; padding: 8px 15px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #2980b9; }
        """)

        self.tab_design = QWidget()
        self.tab_verify = QWidget()

        self.init_design_ui(self.tab_design)
        self.init_verify_ui(self.tab_verify)

        self.tabs.addTab(self.tab_design, "1. 目标阻抗设计 (Target Z)")
        self.tabs.addTab(self.tab_verify, "2. 并联反谐振分析 (Anti-Resonance)")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # ==============================================================================
    # Tab 1: PDN 目标阻抗设计 (Design)
    # ==============================================================================
    def init_design_ui(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("设计目标：确保电源分配网络 (PDN) 的阻抗在感兴趣的频率范围内低于目标阻抗 Z_target，以满足芯片的电压纹波要求。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 15px;")
        layout.addWidget(info)

        # 1. 负载需求输入
        grp_req = QGroupBox("1. 负载瞬态需求 (Load Transient Requirements)")
        g_req = QGridLayout()
        g_req.setVerticalSpacing(12)
        
        self.tgt_di = QLineEdit("2.0"); g_req.addWidget(QLabel("最大阶跃电流 ΔI [A]:"), 0, 0); g_req.addWidget(self.tgt_di, 0, 1)
        self.tgt_v_ripple = QLineEdit("50"); g_req.addWidget(QLabel("允许电压纹波 ΔV [mV]:"), 0, 2); g_req.addWidget(self.tgt_v_ripple, 0, 3)
        
        btn_calc_z = QPushButton("计算目标阻抗 Z_target")
        btn_calc_z.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc_z.setFixedHeight(35)
        btn_calc_z.clicked.connect(self.calc_target_z)
        g_req.addWidget(btn_calc_z, 1, 0, 1, 4)
        
        # Result Z
        self.res_z_target = QLineEdit()
        self.res_z_target.setReadOnly(True)
        self.res_z_target.setStyleSheet("background-color: #e8f8f5; color: #27ae60; font-weight: bold; font-size: 14px;")
        g_req.addWidget(QLabel("目标阻抗 Z_target [mΩ]:"), 2, 0); g_req.addWidget(self.res_z_target, 2, 1)
        
        l_form = QLabel()
        l_form.setPixmap(self.render_formula(r'Z_{target} = \frac{\Delta V_{ripple}}{\Delta I_{transient}}'))
        g_req.addWidget(l_form, 2, 2, 1, 2)
        
        grp_req.setLayout(g_req)
        layout.addWidget(grp_req)

        # 2. 电容选型辅助
        grp_cap = QGroupBox("2. 电容去耦配置估算 (Decoupling Capacitor Estimator)")
        g_cap = QGridLayout()
        g_cap.setVerticalSpacing(12)
        
        self.cap_esr = QLineEdit("10"); g_cap.addWidget(QLabel("单颗电容 ESR [mΩ]:"), 0, 0); g_cap.addWidget(self.cap_esr, 0, 1)
        self.cap_esl = QLineEdit("0.8"); g_cap.addWidget(QLabel("单颗安装 ESL [nH]:"), 0, 2); g_cap.addWidget(self.cap_esl, 0, 3)
        
        btn_calc_n = QPushButton("计算所需并联数量")
        btn_calc_n.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc_n.setFixedHeight(35)
        btn_calc_n.clicked.connect(self.calc_cap_num)
        g_cap.addWidget(btn_calc_n, 1, 0, 1, 4)
        
        # Results
        self.res_n_req = QLineEdit(); g_cap.addWidget(QLabel("至少并联数量 N:"), 2, 0); g_cap.addWidget(self.res_n_req, 2, 1)
        self.res_f_eff = QLineEdit(); g_cap.addWidget(QLabel("有效去耦截止频率 f_eff:"), 2, 2); g_cap.addWidget(self.res_f_eff, 2, 3)
        
        for w in [self.res_n_req, self.res_f_eff]:
            w.setReadOnly(True); w.setStyleSheet("background-color: #f4ecf7; color: #8e44ad; font-weight: bold;")
            
        # Explanations
        l_form_n = QLabel()
        l_form_n.setPixmap(self.render_formula(r'N \geq \frac{ESR_{cap}}{Z_{target}}'))
        g_cap.addWidget(l_form_n, 3, 0, 1, 2)
        
        l_form_f = QLabel()
        l_form_f.setPixmap(self.render_formula(r'f_{eff} = \frac{Z_{target}}{2\pi \cdot (ESL_{cap}/N)}'))
        g_cap.addWidget(l_form_f, 3, 2, 1, 2)
        
        grp_cap.setLayout(g_cap)
        layout.addWidget(grp_cap)
        
        layout.addStretch()

    def calc_target_z(self):
        try:
            di = float(self.tgt_di.text())
            dv_mv = float(self.tgt_v_ripple.text())
            
            if di <= 0: raise ValueError
            
            z_target_ohm = (dv_mv * 1e-3) / di
            z_target_mohm = z_target_ohm * 1e3
            
            self.res_z_target.setText(f"{z_target_mohm:.2f}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

    def calc_cap_num(self):
        try:
            z_tgt_text = self.res_z_target.text()
            if not z_tgt_text:
                self.calc_target_z()
                z_tgt_text = self.res_z_target.text()
                
            z_target_mohm = float(z_tgt_text)
            esr_single = float(self.cap_esr.text())
            esl_single = float(self.cap_esl.text()) # nH
            
            if z_target_mohm <= 0: return
            
            # N = ESR / Z_target
            n_req = math.ceil(esr_single / z_target_mohm)
            if n_req < 1: n_req = 1
            
            # Effective frequency limit due to ESL
            # At high freq, Z = w * L_total = w * (ESL / N)
            # We want w * (ESL / N) <= Z_target
            # f <= Z_target / (2 * pi * ESL/N)
            
            z_target_ohm = z_target_mohm * 1e-3
            esl_total = (esl_single * 1e-9) / n_req
            
            f_eff = z_target_ohm / (2 * math.pi * esl_total)
            
            self.res_n_req.setText(f"{n_req:.0f}")
            self.res_f_eff.setText(f"{f_eff/1e6:.2f} MHz")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "计算参数无效，请检查输入")

    # ==============================================================================
    # Tab 2: 并联反谐振分析 (Original Verification)
    # ==============================================================================
    def init_verify_ui(self, tab):
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("功能说明：分析两个并联电容（考虑ESR/ESL）产生的并联反谐振峰 (Anti-Resonance Peak)。\n"
                      "当大电容呈感性、小电容呈容性时，并联阻抗会急剧升高，导致滤波失效。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. Capacitor 1 (Bulk)
        grp_c1 = QGroupBox("1. 电容 1 参数 (通常为大容量 Bulk)")
        g1 = QGridLayout()
        self.pdn_c1 = QLineEdit("10"); g1.addWidget(QLabel("容值 C1 [uF]:"), 0, 0); g1.addWidget(self.pdn_c1, 0, 1)
        self.pdn_esr1 = QLineEdit("50"); g1.addWidget(QLabel("ESR1 [mΩ]:"), 0, 2); g1.addWidget(self.pdn_esr1, 0, 3)
        self.pdn_esl1 = QLineEdit("3.0"); g1.addWidget(QLabel("ESL1 [nH]:"), 0, 4); g1.addWidget(self.pdn_esl1, 0, 5)
        grp_c1.setLayout(g1)
        layout.addWidget(grp_c1)

        # 2. Capacitor 2 (Decoupling)
        grp_c2 = QGroupBox("2. 电容 2 参数 (通常为去耦 MLCC)")
        g2 = QGridLayout()
        self.pdn_c2 = QLineEdit("0.1"); g2.addWidget(QLabel("容值 C2 [uF]:"), 0, 0); g2.addWidget(self.pdn_c2, 0, 1)
        self.pdn_esr2 = QLineEdit("10"); g2.addWidget(QLabel("ESR2 [mΩ]:"), 0, 2); g2.addWidget(self.pdn_esr2, 0, 3)
        self.pdn_esl2 = QLineEdit("0.8"); g2.addWidget(QLabel("ESL2 [nH]:"), 0, 4); g2.addWidget(self.pdn_esl2, 0, 5)
        grp_c2.setLayout(g2)
        layout.addWidget(grp_c2)

        # 3. Analyze Button
        btn_calc = QPushButton("绘制阻抗曲线并寻找反谐振点")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_pdn_verify)
        layout.addWidget(btn_calc)

        # 4. Results
        grp_res = QGroupBox("3. 关键频率点")
        r_grid = QGridLayout()
        self.pdn_res_f1 = QLineEdit(); r_grid.addWidget(QLabel("C1 自谐振 (SRF1):"), 0, 0); r_grid.addWidget(self.pdn_res_f1, 0, 1)
        self.pdn_res_f2 = QLineEdit(); r_grid.addWidget(QLabel("C2 自谐振 (SRF2):"), 0, 2); r_grid.addWidget(self.pdn_res_f2, 0, 3)
        
        self.pdn_res_peak = QLineEdit()
        self.pdn_res_peak.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold;")
        r_grid.addWidget(QLabel("反谐振频率 (Anti-Res):"), 1, 0); r_grid.addWidget(self.pdn_res_peak, 1, 1)
        
        self.pdn_res_zpeak = QLineEdit()
        self.pdn_res_zpeak.setStyleSheet("background-color: #fdedec; color: #c0392b; font-weight: bold;")
        r_grid.addWidget(QLabel("反谐振峰值阻抗 Z_peak:"), 1, 2); r_grid.addWidget(self.pdn_res_zpeak, 1, 3)

        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()

    def calc_pdn_verify(self):
        try:
            c1 = float(self.pdn_c1.text()) * 1e-6
            esr1 = float(self.pdn_esr1.text()) * 1e-3
            esl1 = float(self.pdn_esl1.text()) * 1e-9
            
            c2 = float(self.pdn_c2.text()) * 1e-6
            esr2 = float(self.pdn_esr2.text()) * 1e-3
            esl2 = float(self.pdn_esl2.text()) * 1e-9
            
            if c1 <= 0 or c2 <= 0: raise ValueError

            # Calculate SRFs
            srf1 = 1.0 / (2 * math.pi * math.sqrt(esl1 * c1))
            srf2 = 1.0 / (2 * math.pi * math.sqrt(esl2 * c2))
            
            self.pdn_res_f1.setText(f"{srf1/1e6:.2f} MHz")
            self.pdn_res_f2.setText(f"{srf2/1e6:.2f} MHz")

            # Frequency Sweep
            f_start = 1e3 # 1kHz
            f_stop = 1e9  # 1GHz
            num_points = 1000
            freqs = np.logspace(3, 9, num_points)
            w = 2 * np.pi * freqs
            
            # Impedance Z = R + j(wL - 1/wC)
            Z1 = esr1 + 1j * (w * esl1 - 1.0 / (w * c1))
            Z2 = esr2 + 1j * (w * esl2 - 1.0 / (w * c2))
            
            # Parallel Impedance Zpar = Z1*Z2 / (Z1+Z2)
            Zpar = (Z1 * Z2) / (Z1 + Z2)
            Zmag = np.abs(Zpar)
            
            # Find Peak
            idx_max = np.argmax(Zmag)
            f_peak = freqs[idx_max]
            z_peak = Zmag[idx_max]
            
            self.pdn_res_peak.setText(f"{f_peak/1e6:.2f} MHz")
            self.pdn_res_zpeak.setText(f"{z_peak:.2f} Ω")
            
            # Plot
            plt.rcParams.update({'font.size': 10})
            fig, ax = plt.subplots(figsize=(8, 5), dpi=100)
            
            ax.loglog(freqs, np.abs(Z1), '--', label='C1 Only', alpha=0.6)
            ax.loglog(freqs, np.abs(Z2), '--', label='C2 Only', alpha=0.6)
            ax.loglog(freqs, Zmag, 'r-', linewidth=2, label='Parallel (Total)')
            
            # Draw Target Z line if available from Tab 1
            try:
                z_tgt_val = float(self.res_z_target.text()) * 1e-3
                if z_tgt_val > 0:
                    ax.axhline(y=z_tgt_val, color='green', linestyle=':', label=f'Target Z ({z_tgt_val*1000:.1f}mΩ)')
            except:
                pass
            
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Impedance (Ohm)')
            ax.set_title(f'PDN Impedance: Anti-Resonance @ {f_peak/1e6:.2f} MHz')
            ax.grid(True, which="both", ls="-", alpha=0.4)
            ax.legend()
            
            # Show Dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("PDN 阻抗曲线")
            dialog.resize(850, 600)
            layout = QVBoxLayout(dialog)
            
            # Embed plot
            scroll = QScrollArea()
            content = QWidget()
            scroll.setWidget(content)
            scroll.setWidgetResizable(True)
            l_layout = QVBoxLayout(content)
            img_label = QLabel()
            
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            img_label.setPixmap(pixmap)
            
            l_layout.addWidget(img_label)
            layout.addWidget(scroll)
            dialog.exec_()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"计算错误: {str(e)}")