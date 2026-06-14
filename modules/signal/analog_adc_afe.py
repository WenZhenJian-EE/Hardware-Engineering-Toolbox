from modules.base_module import BaseModule
# adc_calibration_window.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox,
                             QDialog, QTextBrowser, QTabWidget, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
import matplotlib.pyplot as plt
from io import BytesIO
import math
from utils import render_formula

class AdcCalibrationWindow(BaseModule):
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "ADC 信号调理"
    description = "原理图 / AFE推导 / 两点校准"
    window_id = "analog_adc"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('传感器 ADC 标定助手 (分段还原逻辑版)')
        self.setGeometry(350, 350, 1100, 900)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("分段还原手册 / 逻辑解析")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(220)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_scale = QWidget()
        self.tab_budget = QWidget()
        self.tab_calc = QWidget()
        self.tab_2point = QWidget()
        
        self.init_rc_filter_ui(self.tab_scale)
        self.init_sampling_budget_ui(self.tab_budget)
        self.init_calc_ui(self.tab_calc)
        self.init_2point_ui(self.tab_2point)
        
        self.tabs.addTab(self.tab_scale, "ADC 采样 RC 滤波设计 (RC Filter)")
        self.tabs.addTab(self.tab_budget, "采样链预算 (Noise/Delay)")
        self.tabs.addTab(self.tab_calc, "硬件设计推导 (AFE -> ADC)")
        self.tabs.addTab(self.tab_2point, "实测两点校准 (测量值反推 K, B)")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def init_rc_filter_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("<b>设计场景：</b> 运放前端驱动 ADC 时，在运放输出与 ADC 输入引脚之间构建 RC 低通/采样保持滤波器。<br>"
                      "<b>主要目标：</b> 满足抗混叠、信号建立时间 (5RC) 以及充当采样电荷桶的作用。")
        info.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info)
        
        grp_in = QGroupBox("1. 滤波器与 ADC 参数 (Input Parameters)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.rc_res = QLineEdit("100"); grid.addWidget(QLabel("滤波电阻 R [Ω]:"), 0, 0); grid.addWidget(self.rc_res, 0, 1)
        self.rc_cap = QLineEdit("10"); grid.addWidget(QLabel("外部滤波电容 C [nF]:"), 0, 2); grid.addWidget(self.rc_cap, 0, 3)
        self.rc_csh = QLineEdit("10"); grid.addWidget(QLabel("MCU 内部采样电容 C_sh [pF]:"), 1, 0); grid.addWidget(self.rc_csh, 1, 1)
        self.rc_bits = QLineEdit("12"); grid.addWidget(QLabel("ADC 分辨率 (Bits):"), 1, 2); grid.addWidget(self.rc_bits, 1, 3)
        self.rc_vref = QLineEdit("3.3"); grid.addWidget(QLabel("ADC 参考电压 V_adc [V]:"), 2, 0); grid.addWidget(self.rc_vref, 2, 1)
        
        btn = QPushButton("计算滤波器与电荷桶特性")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_rc_filter)
        grid.addWidget(btn, 3, 0, 1, 4)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)

        grp_out = QGroupBox("2. 分析结果与建议 (Analysis Results)")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.out_fc = QLineEdit()
        self.out_delay = QLineEdit()
        self.out_vdrop = QLineEdit()
        self.out_drop_lsb = QLineEdit()
        self.out_bucket_status = QLineEdit()
        
        for w in [self.out_fc, self.out_delay, self.out_vdrop, self.out_drop_lsb]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
        self.out_bucket_status.setReadOnly(True)
        
        r_grid.addWidget(QLabel("截止频率 Fc [kHz]:"), 0, 0); r_grid.addWidget(self.out_fc, 0, 1)
        r_grid.addWidget(QLabel("信号稳定延迟 (5RC) [μs]:"), 0, 2); r_grid.addWidget(self.out_delay, 0, 3)
        r_grid.addWidget(QLabel("采样开关闭合瞬间跌落电压 [mV]:"), 1, 0); r_grid.addWidget(self.out_vdrop, 1, 1)
        r_grid.addWidget(QLabel("误差转化 LSB 个数:"), 1, 2); r_grid.addWidget(self.out_drop_lsb, 1, 3)
        r_grid.addWidget(QLabel("电荷桶容量评估结论:"), 2, 0); r_grid.addWidget(self.out_bucket_status, 2, 1, 1, 3)
        
        tip = QLabel("判定标准：\n1. R 值建议在数十欧到数百欧，以隔离运放容性负载，但不宜过大影响压降。\n"
                     "2. 电荷桶跌落 LSB 必须 < 0.5 或者 < 1 (即外部电容 C >= 2^N * C_sh)。")
        tip.setStyleSheet("color: #555; font-style: italic; background-color: #f0f0f0; padding: 5px;")
        r_grid.addWidget(tip, 3, 0, 1, 4)
        
        grp_out.setLayout(r_grid)
        layout.addWidget(grp_out)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_rc_filter(self):
        try:
            r_val = float(self.rc_res.text()) # Ohm
            c_val = float(self.rc_cap.text()) * 1e-9 # F
            csh = float(self.rc_csh.text()) * 1e-12 # F
            bits = int(self.rc_bits.text())
            vref = float(self.rc_vref.text())
            
            if c_val <= 0 or r_val <= 0:
                raise ValueError("R 和 C 必须大于 0")
            
            # 1. 截止频率
            fc = 1.0 / (2 * math.pi * r_val * c_val)
            self.out_fc.setText(f"{fc/1000:.2f}")
            
            # 2. 5RC 时延
            tau = r_val * c_val
            delay_5tau = 5 * tau * 1e6 # in us
            self.out_delay.setText(f"{delay_5tau:.3f}")
            
            # 3. 电荷桶瞬态电压跌落 (假设极限情况 Csh 为 0V 瞬间并联 C)
            # 根据电荷守恒 Q = Q_final -> C * Vref = (C + Csh) * V_final
            # delta V = Vref - V_final = Vref * Csh / (C + Csh)
            v_drop = vref * csh / (c_val + csh) 
            self.out_vdrop.setText(f"{v_drop * 1000:.4f}")
            
            # LSB 分析
            lsb_val = vref / (2**bits - 1)
            drop_lsb = v_drop / lsb_val
            self.out_drop_lsb.setText(f"{drop_lsb:.2f} LSB")
            
            # 评估结论
            req_c = (2**bits) * csh 
            if c_val >= req_c:
                self.out_bucket_status.setText(f"优秀 (Pass) - 外部电容满足理论最小 {req_c * 1e9:.2f} nF")
                self.out_bucket_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
            else:
                self.out_bucket_status.setText(f"失败/薄弱 - 电容不够！建议 C 提升至 {req_c * 1e9:.2f} nF 以上")
                self.out_bucket_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "输入错误", str(e))

    def init_sampling_budget_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            "Budget settling, anti-aliasing, noise and loop delay for voltage/current sampling chains."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #566573; font-style: italic;")
        layout.addWidget(info)

        grp = QGroupBox("1. Sampling chain parameters")
        g = QGridLayout()
        self.sb_rsrc = QLineEdit("200")
        self.sb_rflt = QLineEdit("100")
        self.sb_cflt = QLineEdit("4.7")
        self.sb_csh = QLineEdit("12")
        self.sb_tsample = QLineEdit("500")
        self.sb_fs = QLineEdit("20")
        self.sb_fsignal = QLineEdit("1000")
        self.sb_bits = QLineEdit("12")
        self.sb_vref = QLineEdit("3.3")
        self.sb_gain = QLineEdit("0.01")
        self.sb_op_noise = QLineEdit("20")
        self.sb_bw = QLineEdit("10")
        self.sb_loop_fc = QLineEdit("2")

        fields = [
            ("Sensor/source R [ohm]:", self.sb_rsrc),
            ("ADC series/filter R [ohm]:", self.sb_rflt),
            ("Filter cap C [nF]:", self.sb_cflt),
            ("ADC sample cap Csh [pF]:", self.sb_csh),
            ("ADC sample time [ns]:", self.sb_tsample),
            ("ADC sample rate [kS/s]:", self.sb_fs),
            ("Highest signal/noise of interest [Hz]:", self.sb_fsignal),
            ("ADC bits:", self.sb_bits),
            ("Vref [V]:", self.sb_vref),
            ("AFE gain to ADC pin [V/unit]:", self.sb_gain),
            ("AFE input noise [nV/sqrtHz]:", self.sb_op_noise),
            ("Noise bandwidth [kHz]:", self.sb_bw),
            ("Control loop crossover [kHz]:", self.sb_loop_fc),
        ]
        for i, (label, widget) in enumerate(fields):
            r, c = i // 2, (i % 2) * 2
            g.addWidget(QLabel(label), r, c)
            g.addWidget(widget, r, c + 1)
        grp.setLayout(g)
        layout.addWidget(grp)

        btn = QPushButton("Calculate sampling budget")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_sampling_budget)
        layout.addWidget(btn)

        grp_res = QGroupBox("2. Results")
        r = QGridLayout()
        self.sb_res = {}
        labels = [
            ("RC cutoff:", "fc"),
            ("Anti-alias attenuation:", "alias"),
            ("5RC delay:", "delay"),
            ("Loop phase lag:", "phase"),
            ("Sampling settling error:", "settle"),
            ("Error in LSB:", "lsb"),
            ("ADC pin RMS noise:", "noise_pin"),
            ("Input-referred RMS noise:", "noise_in"),
            ("Quantization RMS:", "qnoise"),
            ("Recommended sample time:", "ts_rec"),
        ]
        for i, (label, key) in enumerate(labels):
            w = QLineEdit()
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #1e8449;")
            self.sb_res[key] = w
            rr, cc = i // 2, (i % 2) * 2
            r.addWidget(QLabel(label), rr, cc)
            r.addWidget(w, rr, cc + 1)
        grp_res.setLayout(r)
        layout.addWidget(grp_res)

        self.sb_note = QTextBrowser()
        self.sb_note.setMinimumHeight(120)
        self.sb_note.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d5d8dc;")
        layout.addWidget(self.sb_note)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_sampling_budget(self):
        try:
            rsrc = float(self.sb_rsrc.text())
            rflt = float(self.sb_rflt.text())
            cflt = float(self.sb_cflt.text()) * 1e-9
            csh = float(self.sb_csh.text()) * 1e-12
            tsample = float(self.sb_tsample.text()) * 1e-9
            fs = float(self.sb_fs.text()) * 1e3
            fsignal = float(self.sb_fsignal.text())
            bits = int(self.sb_bits.text())
            vref = float(self.sb_vref.text())
            gain = float(self.sb_gain.text())
            op_noise = float(self.sb_op_noise.text()) * 1e-9
            bw = float(self.sb_bw.text()) * 1e3
            loop_fc = float(self.sb_loop_fc.text()) * 1e3

            rtotal = rsrc + rflt
            if min(rtotal, cflt, csh, tsample, fs, bits, vref, abs(gain), bw) <= 0:
                raise ValueError

            fc = 1.0 / (2.0 * math.pi * rtotal * cflt)
            alias_att = -20.0 * math.log10(math.sqrt(1.0 + (fsignal / fc) ** 2))
            delay = rtotal * cflt
            phase = -math.degrees(math.atan(2.0 * math.pi * loop_fc * delay))
            settle_err = math.exp(-tsample / (rtotal * csh))
            lsb = vref / ((2 ** bits) - 1)
            err_lsb = (settle_err * vref) / lsb
            k = 1.380649e-23
            temp_k = 300.0
            r_noise = math.sqrt(4.0 * k * temp_k * rtotal * bw)
            op_rms = op_noise * math.sqrt(bw)
            q_noise = lsb / math.sqrt(12.0)
            pin_noise = math.sqrt(r_noise ** 2 + op_rms ** 2 + q_noise ** 2)
            input_noise = pin_noise / abs(gain)
            ts_rec = -math.log(0.5 * lsb / vref) * rtotal * csh

            self.sb_res["fc"].setText(f"{fc / 1000:.2f} kHz")
            self.sb_res["alias"].setText(f"{alias_att:.1f} dB @ {fsignal:.0f} Hz")
            self.sb_res["delay"].setText(f"{delay * 1e6:.2f} us")
            self.sb_res["phase"].setText(f"{phase:.1f} deg @ fc")
            self.sb_res["settle"].setText(f"{settle_err * 100:.4f} %FS")
            self.sb_res["lsb"].setText(f"{err_lsb:.2f} LSB")
            self.sb_res["noise_pin"].setText(f"{pin_noise * 1e6:.2f} uVrms")
            self.sb_res["noise_in"].setText(f"{input_noise:.6g} unit rms")
            self.sb_res["qnoise"].setText(f"{q_noise * 1e6:.2f} uVrms")
            self.sb_res["ts_rec"].setText(f"> {ts_rec * 1e9:.0f} ns")

            warnings = []
            if err_lsb > 0.5:
                warnings.append("Sampling time is short versus source impedance and Csh; increase sample time or lower source resistance.")
            if abs(phase) > 5:
                warnings.append("RC delay costs more than 5 degrees at loop crossover; check current-loop/voltage-loop phase margin.")
            if fc > fs / 2:
                warnings.append("RC cutoff is above Nyquist; this is not an anti-alias filter.")
            if not warnings:
                warnings.append("Budget looks reasonable for a first pass.")
            self.sb_note.setHtml("<br>".join(warnings))
        except Exception:
            QMessageBox.warning(self, "Input error", "Please check sampling budget inputs.")

    def init_calc_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. ADC 硬件参数
        grp_hw = QGroupBox(" 1. ADC 基础参数设置")
        grid_hw = QGridLayout()
        self.inp_vref = QLineEdit("3.3"); grid_hw.addWidget(QLabel("参考电压 (Vref) [V]:"), 0, 0); grid_hw.addWidget(self.inp_vref, 0, 1)
        self.inp_bits = QLineEdit("12"); grid_hw.addWidget(QLabel("ADC 位数 (Bits):"), 0, 2); grid_hw.addWidget(self.inp_bits, 0, 3)
        self.out_max_code = QLineEdit("4095"); self.out_max_code.setReadOnly(True); self.out_max_code.setStyleSheet("background-color: #f0f0f0; color: #7f8c8d;")
        grid_hw.addWidget(QLabel("最大读取值 (Max Code):"), 1, 0); grid_hw.addWidget(self.out_max_code, 1, 1)
        self.inp_bits.textChanged.connect(self.update_max_code)
        grp_hw.setLayout(grid_hw)
        layout.addWidget(grp_hw)

        # 2. 模拟前端设计 (AFE)
        grp_afe = QGroupBox(" 2. 硬件模拟前端设计 (AFE)")
        grid_afe = QGridLayout()
        self.afe_mode = QComboBox(); self.afe_mode.addItems(["电压分压 (Divider)", "运算放大器 (Op-Amp Gain)", "电阻采样 (Current Shunt)"])
        self.afe_mode.currentIndexChanged.connect(self.update_afe_labels)
        grid_afe.addWidget(QLabel("电路拓扑模型:"), 0, 0); grid_afe.addWidget(self.afe_mode, 0, 1)
        
        self.lbl_p1 = QLabel("上电阻 R1 [kΩ]:"); self.inp_p1 = QLineEdit("100")
        self.lbl_p2 = QLabel("下电阻 R2 [kΩ]:"); self.inp_p2 = QLineEdit("3.3")
        self.lbl_bias = QLabel("直流偏置 (Bias) [V]:"); self.inp_bias = QLineEdit("0.0")
        
        grid_afe.addWidget(self.lbl_p1, 1, 0); grid_afe.addWidget(self.inp_p1, 1, 1)
        grid_afe.addWidget(self.lbl_p2, 1, 2); grid_afe.addWidget(self.inp_p2, 1, 3)
        grid_afe.addWidget(self.lbl_bias, 2, 0); grid_afe.addWidget(self.inp_bias, 2, 1)
        grp_afe.setLayout(grid_afe)
        layout.addWidget(grp_afe)

        # 3. 验证与正向模拟
        grp_sim = QGroupBox(" 3. 验证与正向模拟 (Simulation)")
        grid_sim = QGridLayout()
        self.inp_phys = QLineEdit("220"); grid_sim.addWidget(QLabel("输入物理量 (如 220V):"), 0, 0); grid_sim.addWidget(self.inp_phys, 0, 1)
        
        self.out_v_pin = QLineEdit(); self.out_v_pin.setReadOnly(True); self.out_v_pin.setStyleSheet("background-color: #fcf3cf; font-weight: bold; color: #b7950b;")
        grid_sim.addWidget(QLabel("ADC 引脚电压 [V]:"), 1, 0); grid_sim.addWidget(self.out_v_pin, 1, 1)
        
        self.out_adc_res = QLineEdit(); self.out_adc_res.setReadOnly(True); self.out_adc_res.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
        grid_sim.addWidget(QLabel("ADC 最终读数 (Code):"), 1, 2); grid_sim.addWidget(self.out_adc_res, 1, 3)
        
        self.sim_status_label = QLabel("计算状态提示：等待输入...")
        self.sim_status_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        grid_sim.addWidget(self.sim_status_label, 2, 0, 1, 4)
        
        grp_sim.setLayout(grid_sim)
        layout.addWidget(grp_sim)

        btn = QPushButton("开始计算并生成软件还原公式")
        btn.setFixedHeight(45); btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; font-size: 14px;")
        btn.clicked.connect(self.do_calc_afe)
        layout.addWidget(btn)

        # 4. 软件还原链条显示
        grp_res = QGroupBox(" 4. 软件还原链条 (Software Reconstruction Chain)")
        res_vbox = QVBoxLayout()
        self.lbl_step1 = QLabel("步骤 1：通过计数值还原引脚电压 (LSB还原)"); self.img_step1 = QLabel()
        self.lbl_step2 = QLabel("步骤 2：通过引脚电压还原前级物理量 (AFE逆推)"); self.img_step2 = QLabel()
        res_vbox.addWidget(self.lbl_step1); res_vbox.addWidget(self.img_step1)
        res_vbox.addWidget(self.lbl_step2); res_vbox.addWidget(self.img_step2)
        
        self.final_res_box = QGroupBox(" 最终软件一阶公式: Value = ADC_Code * K + B")
        f_grid = QGridLayout()
        self.out_k = QLineEdit(); self.out_b = QLineEdit()
        for w in [self.out_k, self.out_b]: w.setReadOnly(True); w.setStyleSheet("font-weight: bold; color: #d35400; font-size: 14px;")
        f_grid.addWidget(QLabel("比例系数 (K):"), 0, 0); f_grid.addWidget(self.out_k, 0, 1)
        f_grid.addWidget(QLabel("偏移常数 (B):"), 0, 2); f_grid.addWidget(self.out_b, 0, 3)
        self.final_res_box.setLayout(f_grid)
        res_vbox.addWidget(self.final_res_box)
        
        grp_res.setLayout(res_vbox)
        layout.addWidget(grp_res)
        layout.addStretch()
        tab.setLayout(layout)
        self.update_afe_labels()

    def update_max_code(self):
        try:
            bits = int(self.inp_bits.text())
            self.out_max_code.setText(str((2**bits) - 1))
        except: pass

    def update_afe_labels(self):
        m = self.afe_mode.currentIndex()
        if m == 0: # Divider
            self.lbl_p1.setText("上电阻 R1 [kΩ]:"); self.lbl_p2.setText("下电阻 R2 [kΩ]:"); self.inp_p2.setEnabled(True)
        elif m == 1: # OpAmp
            self.lbl_p1.setText("电路总增益 (Gain):"); self.lbl_p2.setText("---"); self.inp_p2.setEnabled(False); self.inp_p2.setText("1.0")
        else: # Shunt
            self.lbl_p1.setText("采样电阻 [mΩ]:"); self.lbl_p2.setText("放大倍数 (Gain):"); self.inp_p2.setEnabled(True)

    def do_calc_afe(self):
        try:
            vref = float(self.inp_vref.text()); bits = int(self.inp_bits.text()); max_c = (2**bits)-1
            bias = float(self.inp_bias.text()); phys_in = float(self.inp_phys.text()); lsb = vref / max_c
            
            m = self.afe_mode.currentIndex()
            if m == 0: # Divider
                gain = float(self.inp_p2.text()) / (float(self.inp_p1.text()) + float(self.inp_p2.text()))
            elif m == 1: # Op-Amp
                gain = float(self.inp_p1.text())
            else: # Shunt
                gain = (float(self.inp_p1.text())/1000.0) * float(self.inp_p2.text())
            
            # --- 正向计算 ---
            v_pin = (phys_in * gain) + bias
            adc_code = v_pin / lsb
            self.out_v_pin.setText(f"{v_pin:.4f} V")
            self.out_adc_res.setText(f"{int(adc_code)}")
            
            # --- 状态检查 ---
            if v_pin > vref:
                self.sim_status_label.setText("警告：引脚电压超过 Vref，ADC 已饱和！")
                self.sim_status_label.setStyleSheet("color: #c0392b; font-weight: bold;")
                self.out_v_pin.setStyleSheet("background-color: #f2d7d5; color: #c0392b; font-weight: bold;")
            elif v_pin < 0:
                self.sim_status_label.setText("警告：引脚电压为负值，ADC 无法读取！")
                self.sim_status_label.setStyleSheet("color: #c0392b; font-weight: bold;")
                self.out_v_pin.setStyleSheet("background-color: #f2d7d5; color: #c0392b; font-weight: bold;")
            else:
                self.sim_status_label.setText("提示：电压量程正常，软件公式有效。")
                self.sim_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.out_v_pin.setStyleSheet("background-color: #fcf3cf; font-weight: bold; color: #b7950b;")

            # --- 反向公式渲染 ---
            # 步骤 1: ADC Code -> Pin Voltage
            s1_str = r'V_{adc\_pin} = \text{ADC\_Code} \cdot \left( \frac{' + f"{vref}" + r'}{' + f"{max_c}" + r'} \right) = \text{ADC\_Code} \cdot ' + f"{lsb:.10f}"
            self.img_step1.setPixmap(self.render_formula(s1_str))
            
            # 步骤 2: Pin Voltage -> Physical Value
            s2_str = r'\text{Value} = \frac{V_{adc\_pin} - (' + f"{bias}" + r')}{' + f"{gain:.6f}" + r'}'
            self.img_step2.setPixmap(self.render_formula(s2_str))
            
            # 最终系数
            k = lsb / gain
            b = -bias / gain
            self.out_k.setText(f"{k:.12f}")
            self.out_b.setText(f"{b:.12f}")
            
        except Exception as e: QMessageBox.warning(self, "计算错误", str(e))

    def init_2point_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        info = QLabel("说明：通过实测两个点（已知物理量和对应的 ADC 计数值）来计算系统最真实的 K 和 B。")
        layout.addWidget(info)
        grp_data = QGroupBox(" 实测标定数据录入 (y = kx + b)")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        grid.addWidget(QLabel("测试点 1 (Low):"), 0, 0)
        self.p1_x = QLineEdit("100"); grid.addWidget(QLabel("ADC 读数:"), 0, 1); grid.addWidget(self.p1_x, 0, 2)
        self.p1_y = QLineEdit("0.5"); grid.addWidget(QLabel("真实物理值:"), 0, 3); grid.addWidget(self.p1_y, 0, 4)
        grid.addWidget(QLabel("测试点 2 (High):"), 1, 0)
        self.p2_x = QLineEdit("3800"); grid.addWidget(QLabel("ADC 读数:"), 1, 1); grid.addWidget(self.p2_x, 1, 2)
        self.p2_y = QLineEdit("10.0"); grid.addWidget(QLabel("真实物理值:"), 1, 3); grid.addWidget(self.p2_y, 1, 4)
        grp_data.setLayout(grid); layout.addWidget(grp_data)
        
        btn = QPushButton("反推校准系数 (K, B)")
        btn.setFixedHeight(45); btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_2point_fit)
        layout.addWidget(btn)
        
        res_grp = QGroupBox(" 最终校准结果")
        r_grid = QGridLayout()
        self.cal_k = QLineEdit(); self.cal_b = QLineEdit()
        for w in [self.cal_k, self.cal_b]: w.setReadOnly(True); w.setStyleSheet("background-color: #f4ecf7; font-weight: bold; color: #8e44ad;")
        r_grid.addWidget(QLabel("斜率系数 K:"), 0, 0); r_grid.addWidget(self.cal_k, 0, 1)
        r_grid.addWidget(QLabel("偏移常数 B:"), 0, 2); r_grid.addWidget(self.cal_b, 0, 3)
        res_grp.setLayout(r_grid); layout.addWidget(res_grp)
        layout.addStretch(); tab.setLayout(layout)

    def calc_2point_fit(self):
        try:
            x1, y1, x2, y2 = float(self.p1_x.text()), float(self.p1_y.text()), float(self.p2_x.text()), float(self.p2_y.text())
            if x1 == x2: return
            k = (y2 - y1) / (x2 - x1); b = y1 - k * x1
            self.cal_k.setText(f"{k:.12f}"); self.cal_b.setText(f"{b:.12f}")
        except: pass

    def show_tutorial(self):
        dialog = QDialog(self); dialog.setWindowTitle("ADC 标定助手 - 详细用户手册"); dialog.resize(800, 600)
        l = QVBoxLayout(dialog); t = QTextBrowser(); l.addWidget(t)
        t.setHtml("""
        <style>
            h2 { color: #2980b9; border-bottom: 1px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; }
            .code { background-color: #f4f4f4; padding: 8px; border-left: 4px solid #7f8c8d; font-family: 'Courier New'; }
            .important { color: #c0392b; font-weight: bold; }
        </style>
        <h2>1. 核心计算逻辑</h2>
        <p>本工具解决的是如何将单片机读取的<b>计数值 (0-4095)</b> 准确还原为<b>原始物理量 (如 0-1000V)</b> 的问题。</p>
        
        <h3>A. 正向建模 (硬件设计)</h3>
        <p>物理信号通过模拟电路 (AFE) 和 ADC 转换为数字。过程如下：</p>
        <div class='code'>ADC_Code = [(Physical * Gain) + Bias] / (Vref / Max_Code)</div>
        <ul>
            <li><b>Gain:</b> 电路的缩放比例（分压比或放大倍数）。</li>
            <li><b>Bias:</b> 电路的直流偏置（如 1.65V 中点抬升）。</li>
        </ul>

        <h3>B. 反向还原 (软件实现)</h3>
        <p>软件需要一步步撤销硬件的影响：</p>
        <ol>
            <li><b>计数值还原为电压：</b> <code>V_pin = ADC_Code * (Vref / Max_Code)</code></li>
            <li><b>电压还原为物理量：</b> <code>Physical = (V_pin - Bias) / Gain</code></li>
        </ol>

        <h2>2. 参数说明</h2>
        <ul>
            <li><b>Vref:</b> ADC 的参考电压。如果引脚电压超过 Vref，读数将一直保持最大值 (4095)。</li>
            <li><b>K (系数):</b> 软件还原公式中的乘数。它等于 <code>LSB / Gain</code>。</li>
            <li><b>B (偏移):</b> 软件还原公式中的加数。它等于 <code>-Bias / Gain</code>。</li>
        </ul>

        <h2>3. 关于实测校准</h2>
        <p class='important'>理论计算永远不考虑电阻误差和基准偏差。最精准的做法是：</p>
        <p>使用万用表测出两个点的实际物理量，并记录单片机对应的 ADC 读数，在“两点校准”页签中输入，得到的 K 和 B 才是你这一套硬件系统的最真实参数。</p>
        """)
        dialog.exec_()
