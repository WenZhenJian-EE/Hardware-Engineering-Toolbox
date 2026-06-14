# power_device_physics.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QTabWidget, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QDialog, QTextBrowser, QRadioButton, QButtonGroup, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

class DevicePhysicsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; border-radius: 4px; }
            QTabBar::tab { 
                background: #f4f6f9; 
                border: 1px solid #c0c0c0; 
                padding: 8px 15px; 
                margin-right: 2px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px;
                font-size: 12px;
            }
            QTabBar::tab:selected { 
                background: #ffffff; 
                border-bottom: 1px solid #ffffff; 
                font-weight: bold; 
                color: #2980b9; 
            }
        """)
        
        # 添加子标签页
        self.tabs.addTab(LossCalculationTab(), "MOSFET/IGBT 损耗")
        self.tabs.addTab(DeadtimeLossTab(), "同步整流死区损耗")
        self.tabs.addTab(MillerEffectTab(), "米勒效应误导通评估")
        self.tabs.addTab(ZthCalculationTab(), "瞬态热阻抗 (Zth)")
        self.tabs.addTab(DiodeLossTab(), "二极管损耗")
        self.tabs.addTab(SoaCheckTab(), "SOA 与 短路安全") 
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("开关器件设计指南 (损耗/驱动/瞬态热/SOA)")
        dialog.resize(900, 750)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; margin-top: 20px;}
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 8px; }
            .key-param { color: #c0392b; font-weight: bold; background-color: #e0e0e0; padding: 0 4px; border-radius: 3px; }
            .box { background-color: #fff9c4; padding: 10px; border-left: 5px solid #f1c40f; margin: 10px 0; }
            table { border-collapse: collapse; width: 100%; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            code { background-color: #e0e0e0; color: #c0392b; padding: 2px 4px; border-radius: 3px; font-family: monospace;}
        </style>
        
        <h1>开关器件设计指南</h1>
        
        <h2>一、瞬态热阻抗 (Transient Zth)</h2>
        <div class="box">
            <b>核心概念：</b> 芯片的热容导致温度无法突变。Zth 描述了在特定时间的温度响应。
        </div>

        <h3>1. 单次脉冲 vs 重复脉冲</h3>
        <ul>
            <li><b>单次脉冲 (Single Pulse):</b> 对应浪涌、短路保护等一次性事件。结温由 $Z_{th}(t_{pulse})$ 决定。</li>
            <li><b>重复脉冲 (Repetitive Pulse):</b> 对应 PWM 稳态工作或电机启动。热量会逐个周期累积。
                <br>若频率很高（如 >10kHz），结温趋向于平均值 $T_j \approx P_{avg} \cdot R_{th(J-C)}$。
                <br>若频率较低（如 <100Hz），结温会跟随脉冲大幅波动。本工具使用 Foster 模型叠加法精确计算峰值结温。
            </li>
        </ul>

        <h3>2. Foster 模型参数填表</h3>
        <p>请查阅 Datasheet 的 "Transient Thermal Impedance" 章节，找到 RC 网络参数表格 (Ri, Tau_i) 并填入软件。</p>
        <p><b>公式逻辑：</b></p>
        <ul>
            <li>单次：$Z_{th}(t) = \sum R_i \cdot (1 - e^{-t/\tau_i})$</li>
            <li>重复：$Z_{th\_peak} = \sum R_i \cdot \frac{1 - e^{-t_{on}/\tau_i}}{1 - e^{-T/\tau_i}}$ (考虑了占空比和周期的无穷级数求和)</li>
        </ul>

        <hr>

        <h2>二、损耗计算 (Loss)</h2>
        <ul>
            <li><b>开关损耗：</b> $P_{sw} = (E_{on} + E_{off}) \cdot f_{sw}$。注意 Eon/Eoff 是基于特定测试电压电流测得的，本软件会根据实际工况进行线性折算。</li>
            <li><b>导通损耗：</b> MOSFET 是 $I^2 R$，IGBT 是 $V \cdot I$。注意 Rds(on) 随温度显著增加 (100°C时约增加50%~80%)，填表时建议填高温下的值。</li>
        </ul>

        <h2>三、同步整流死区损耗 (Deadtime Loss)</h2>
        <ul>
            <li><b>痛点：</b> GaN HEMT 没有体二极管，其反向导通机制（类似二极管）的压降 $V_{sd}$ 很大（通常 2V~4V）。</li>
            <li><b>计算：</b> $P_{dt} = V_{sd} \cdot I_{load} \cdot (T_{dead\_on} + T_{dead\_off}) \cdot f_{sw}$</li>
            <li><b>优化：</b> 必须在保证不直通的前提下，尽可能压缩死区时间（例如 < 20ns）。</li>
        </ul>

        <h2>四、米勒效应误导通 (Miller Induced Turn-on)</h2>
        <div class="box">
            <b>危险场景：</b> 桥臂中，当一个开关管快速开通时，高 $dV/dt$ 通过 $C_{gd}$ 产生电流 $I = C_{gd} \cdot dV/dt$，流经 $R_g$ 产生压降，可能误导通对管。
        </div>

        <h2>五、MOSFET SOA 与 Spirito 效应</h2>
        <ul>
            <li><b>线性模式 (Linear Mode)：</b> 指 MOSFET 同时承受高电压和电流（如电子负载）。此时功率全部转化为热。</li>
            <li><b>Spirito 效应：</b> 在高压 ($V_{ds} > 20V$) 且长脉冲下，芯片内部电流分配不均形成热点，实际 SOA 能力远低于理论热限制。</li>
        </ul>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        btn_close = QPushButton("关闭指南")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec_()

# ==============================================================================
# 1. MOSFET / IGBT Loss Calculation
# ==============================================================================
class LossCalculationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. 器件类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("器件类型:"))
        self.sw_type = QComboBox()
        self.sw_type.addItems(["MOSFET (基于 Rds_on)", "IGBT (基于 Vce_sat)"])
        self.sw_type.currentIndexChanged.connect(self.on_sw_type_changed)
        type_layout.addWidget(self.sw_type)
        
        tips = QLabel("鼠标悬停在输入框上可查看详细说明")
        tips.setStyleSheet("color: #7f8c8d; font-style: italic; margin-left: 10px;")
        type_layout.addWidget(tips)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # 2. 参数输入
        input_layout = QGridLayout()
        input_layout.setVerticalSpacing(15)
        
        # Group: 实际工况
        grp_op = QGroupBox("1. 实际电路工况 (Actual Operating Conditions)")
        grid_op = QGridLayout()
        
        self.sw_v_bus = QLineEdit("400")
        self.sw_v_bus.setToolTip("【V_actual】\nMOS/IGBT 关断时承受的电压。\n通常等于母线电压 (Bus Voltage) 或 Vin。")
        self.sw_i_load = QLineEdit("10")
        self.sw_i_load.setToolTip("【I_actual】\nMOS/IGBT 导通时流过的电流。\n通常取电感电流的峰值或平均值。")
        self.sw_fsw = QLineEdit("50")
        self.sw_fsw.setToolTip("PWM 开关频率。")
        self.sw_duty = QLineEdit("0.5")
        self.sw_duty.setToolTip("导通占空比。\n用于计算导通损耗的时间占比。")
        
        grid_op.addWidget(QLabel("实际关断电压 (V_act) [V]:"), 0, 0); grid_op.addWidget(self.sw_v_bus, 0, 1)
        grid_op.addWidget(QLabel("实际导通电流 (I_act) [A]:"), 0, 2); grid_op.addWidget(self.sw_i_load, 0, 3)
        grid_op.addWidget(QLabel("开关频率 (f_sw) [kHz]:"), 1, 0); grid_op.addWidget(self.sw_fsw, 1, 1)
        grid_op.addWidget(QLabel("占空比 (D) [0~1]:"), 1, 2); grid_op.addWidget(self.sw_duty, 1, 3)
        grp_op.setLayout(grid_op)
        input_layout.addWidget(grp_op, 0, 0, 1, 2)

        # Group: Datasheet 参数
        grp_ds = QGroupBox("2. 规格书参数 (Datasheet Specs)")
        grid_ds = QGridLayout()
        
        # 导通参数 (动态变化)
        self.lbl_cond = QLabel("导通电阻 Rds(on) [mΩ]:")
        self.sw_cond_val = QLineEdit("100")
        self.sw_cond_val.setToolTip("MOSFET: 查 Rds(on) @ Tj=100°C (建议取高温值)\nIGBT: 查 Vce(sat) @ Rated Current")
        grid_ds.addWidget(self.lbl_cond, 0, 0); grid_ds.addWidget(self.sw_cond_val, 0, 1)
        
        grid_ds.addWidget(QLabel("测试参考电压 (V_test) [V]:"), 1, 0); 
        self.sw_v_test = QLineEdit("300")
        self.sw_v_test.setToolTip("【V_test】\nDatasheet 中测量 Eon/Eoff 时的电压条件。")
        grid_ds.addWidget(self.sw_v_test, 1, 1)
        
        grid_ds.addWidget(QLabel("测试参考电流 (I_test) [A]:"), 1, 2); 
        self.sw_i_test = QLineEdit("10")
        self.sw_i_test.setToolTip("【I_test】\nDatasheet 中测量 Eon/Eoff 时的电流条件。")
        grid_ds.addWidget(self.sw_i_test, 1, 3)
        
        grid_ds.addWidget(QLabel("开通损耗 (E_on) [uJ]:"), 2, 0); 
        self.sw_eon = QLineEdit("500")
        self.sw_eon.setToolTip("查表得 Eon。\n注意单位是 uJ (微焦耳)。")
        grid_ds.addWidget(self.sw_eon, 2, 1)
        
        grid_ds.addWidget(QLabel("关断损耗 (E_off) [uJ]:"), 2, 2); 
        self.sw_eoff = QLineEdit("300")
        self.sw_eoff.setToolTip("查表得 Eoff。")
        grid_ds.addWidget(self.sw_eoff, 2, 3)
        
        grp_ds.setLayout(grid_ds)
        input_layout.addWidget(grp_ds, 1, 0, 1, 2)
        layout.addLayout(input_layout)

        # 计算按钮
        btn = QPushButton("计算总损耗")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_switch_loss)
        layout.addWidget(btn)

        # 结果显示
        res_group = QGroupBox("3. 估算结果")
        res_grid = QGridLayout()
        res_grid.setColumnStretch(1, 1)
        
        self.sw_p_cond = QLineEdit(); self.sw_p_sw = QLineEdit(); self.sw_p_tot = QLineEdit()
        
        res_grid.addWidget(QLabel("导通损耗 (P_cond):"), 0, 0); res_grid.addWidget(self.sw_p_cond, 0, 1)
        self.l_form_cond = QLabel(); self.l_form_cond.setPixmap(render_formula(r'P_{cond} = I_{act}^2 \cdot R_{ds(on)} \cdot D'))
        res_grid.addWidget(self.l_form_cond, 0, 2)
        
        res_grid.addWidget(QLabel("开关损耗 (P_sw):"), 1, 0); res_grid.addWidget(self.sw_p_sw, 1, 1)
        l_form_sw = QLabel(); l_form_sw.setPixmap(render_formula(r'P_{sw} = (E_{on}+E_{off}) \cdot \frac{V_{act}}{V_{test}} \cdot \frac{I_{act}}{I_{test}} \cdot f_{sw}'))
        res_grid.addWidget(l_form_sw, 1, 2)
        
        res_grid.addWidget(QLabel("总损耗 (P_total):"), 2, 0); res_grid.addWidget(self.sw_p_tot, 2, 1)
        res_grid.addWidget(QLabel("Tips: 损耗 = 热量，请据此设计散热器"), 2, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_tot = "background-color: #fff5f5; font-weight: bold; color: #c0392b; font-size: 14px;"
        self.sw_p_cond.setReadOnly(True); self.sw_p_cond.setStyleSheet(style_res)
        self.sw_p_sw.setReadOnly(True); self.sw_p_sw.setStyleSheet(style_res)
        self.sw_p_tot.setReadOnly(True); self.sw_p_tot.setStyleSheet(style_tot)
        
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        self.setLayout(layout)

    def on_sw_type_changed(self):
        if self.sw_type.currentIndex() == 0: # MOSFET
            self.lbl_cond.setText("导通电阻 Rds(on) [mΩ]:")
            self.sw_cond_val.setText("100")
            self.l_form_cond.setPixmap(render_formula(r'P_{cond} = I_{act}^2 \cdot R_{ds(on)} \cdot D'))
        else: # IGBT
            self.lbl_cond.setText("饱和压降 Vce(sat) [V]:")
            self.sw_cond_val.setText("1.8")
            self.l_form_cond.setPixmap(render_formula(r'P_{cond} = V_{ce(sat)} \cdot I_{act} \cdot D'))

    def calc_switch_loss(self):
        try:
            v_act = float(self.sw_v_bus.text())
            i_act = float(self.sw_i_load.text())
            f_sw = float(self.sw_fsw.text()) * 1000
            duty = float(self.sw_duty.text())
            cond_param = float(self.sw_cond_val.text())
            v_test = float(self.sw_v_test.text())
            i_test = float(self.sw_i_test.text())
            e_on = float(self.sw_eon.text()) * 1e-6
            e_off = float(self.sw_eoff.text()) * 1e-6
            
            if v_test == 0 or i_test == 0: raise ValueError
            
            scaling = (v_act / v_test) * (i_act / i_test)
            e_total_act = (e_on + e_off) * scaling
            p_sw = e_total_act * f_sw
            
            if self.sw_type.currentIndex() == 0: # MOSFET
                r_on = cond_param * 1e-3
                p_cond = (i_act ** 2) * duty * r_on
            else: # IGBT
                v_ce = cond_param
                p_cond = v_ce * i_act * duty
            
            p_tot = p_cond + p_sw
            self.sw_p_cond.setText(f"{p_cond:.2f} W")
            self.sw_p_sw.setText(f"{p_sw:.2f} W")
            self.sw_p_tot.setText(f"{p_tot:.2f} W")
        except Exception as e:
            QMessageBox.warning(self, "错误", "请输入有效的数值")

# ==============================================================================
# 2. Deadtime Loss
# ==============================================================================
class DeadtimeLossTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        intro_lbl = QLabel("针对同步整流 (SR) 或 GaN/SiC 应用，死区时间内的反向导通压降 (Vsd) 会产生显著损耗。")
        intro_lbl.setStyleSheet("color: #2980b9; font-style: italic; margin-bottom: 10px;")
        intro_lbl.setWordWrap(True)
        layout.addWidget(intro_lbl)

        grp_in = QGroupBox("1. 死区与工况参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)

        self.dt_vsd = QLineEdit("2.5")
        self.dt_vsd.setToolTip("源漏反向电压降 Vsd。GaN HEMT 通常较高 (2~4V)。")
        grid.addWidget(QLabel("反向导通压降 Vsd [V]:"), 0, 0); grid.addWidget(self.dt_vsd, 0, 1)

        self.dt_iload = QLineEdit("10")
        grid.addWidget(QLabel("负载电流 I_load [A]:"), 0, 2); grid.addWidget(self.dt_iload, 0, 3)

        self.dt_fsw = QLineEdit("100")
        grid.addWidget(QLabel("开关频率 f_sw [kHz]:"), 1, 0); grid.addWidget(self.dt_fsw, 1, 1)

        self.dt_ton = QLineEdit("50"); self.dt_ton.setToolTip("开通前的死区时间")
        grid.addWidget(QLabel("开通死区 T_dt_on [ns]:"), 2, 0); grid.addWidget(self.dt_ton, 2, 1)

        self.dt_toff = QLineEdit("50"); self.dt_toff.setToolTip("关断后的死区时间")
        grid.addWidget(QLabel("关断死区 T_dt_off [ns]:"), 2, 2); grid.addWidget(self.dt_toff, 2, 3)

        grp_in.setLayout(grid)
        layout.addWidget(grp_in)

        btn = QPushButton("计算死区损耗")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_deadtime_loss)
        layout.addWidget(btn)

        grp_res = QGroupBox("2. 损耗结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)

        self.dt_res_loss = QLineEdit()
        self.dt_res_ratio = QLineEdit()

        r_grid.addWidget(QLabel("死区总损耗 P_deadtime:"), 0, 0); r_grid.addWidget(self.dt_res_loss, 0, 1)
        l_form = QLabel(); l_form.setPixmap(render_formula(r'P_{dt} = V_{sd} \cdot I_{load} \cdot (T_{on} + T_{off}) \cdot f_{sw}'))
        r_grid.addWidget(l_form, 0, 2)

        r_grid.addWidget(QLabel("占总功率比例 (估算):"), 1, 0); r_grid.addWidget(self.dt_res_ratio, 1, 1)
        r_grid.addWidget(QLabel("假设输出电压 Vo=12V (仅供参考)"), 1, 2)

        style_res = "background-color: #fdedec; font-weight: bold; color: #c0392b; font-size: 15px;"
        self.dt_res_loss.setReadOnly(True); self.dt_res_loss.setStyleSheet(style_res)
        self.dt_res_ratio.setReadOnly(True); self.dt_res_ratio.setStyleSheet("background-color: #f0f0f0;")

        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)

    def calc_deadtime_loss(self):
        try:
            vsd = float(self.dt_vsd.text())
            i = float(self.dt_iload.text())
            f = float(self.dt_fsw.text()) * 1e3
            ton = float(self.dt_ton.text()) * 1e-9
            toff = float(self.dt_toff.text()) * 1e-9

            p_loss = vsd * i * (ton + toff) * f
            
            self.dt_res_loss.setText(f"{p_loss:.3f} W")
            p_out_ref = 12 * i 
            if p_out_ref > 0:
                ratio = (p_loss / p_out_ref) * 100
                self.dt_res_ratio.setText(f"{ratio:.2f} % (of 12V Pout)")
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# 3. Miller Effect
# ==============================================================================
class MillerEffectTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("评估在桥臂高速开关 (dv/dt) 下，关断管是否会被米勒电容 (Crss) 感应导通。")
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        grp_param = QGroupBox("1. 器件参数与工况")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.mil_crss = QLineEdit("100"); self.mil_crss.setToolTip("反向传输电容 Crss (Cgd)。")
        grid.addWidget(QLabel("米勒电容 C_rss [pF]:"), 0, 0); grid.addWidget(self.mil_crss, 0, 1)
        
        self.mil_ciss = QLineEdit("1000"); self.mil_ciss.setToolTip("输入电容 Ciss。")
        grid.addWidget(QLabel("输入电容 C_iss [pF]:"), 0, 2); grid.addWidget(self.mil_ciss, 0, 3)
        
        self.mil_vth = QLineEdit("3.0"); self.mil_vth.setToolTip("最小开启阈值 Vth_min。")
        grid.addWidget(QLabel("最小阈值 Vth_min [V]:"), 1, 0); grid.addWidget(self.mil_vth, 1, 1)
        
        self.mil_rgoff = QLineEdit("2.0"); self.mil_rgoff.setToolTip("关断回路总电阻。")
        grid.addWidget(QLabel("关断总电阻 Rg_off [Ω]:"), 1, 2); grid.addWidget(self.mil_rgoff, 1, 3)
        
        self.mil_dvdt = QLineEdit("50"); self.mil_dvdt.setToolTip("开关节点电压变化率。")
        grid.addWidget(QLabel("开关速度 dV/dt [V/ns]:"), 2, 0); grid.addWidget(self.mil_dvdt, 2, 1)
        
        grp_param.setLayout(grid)
        layout.addWidget(grp_param)
        
        btn = QPushButton("评估误导通风险")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_miller)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("2. 评估结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.mil_imiller = QLineEdit()
        self.mil_vgs_ind = QLineEdit()
        self.mil_status = QLineEdit()
        self.mil_c_ratio = QLineEdit()
        
        r_grid.addWidget(QLabel("米勒感应电流 I_miller:"), 0, 0); r_grid.addWidget(self.mil_imiller, 0, 1)
        l_im = QLabel(); l_im.setPixmap(render_formula(r'I_{miller} = C_{rss} \cdot \frac{dV}{dt}'))
        r_grid.addWidget(l_im, 0, 2)
        
        r_grid.addWidget(QLabel("感应栅极电压 Vgs_induced:"), 1, 0); r_grid.addWidget(self.mil_vgs_ind, 1, 1)
        l_vm = QLabel(); l_vm.setPixmap(render_formula(r'V_{gs} \approx I_{miller} \cdot R_{g\_off}'))
        r_grid.addWidget(l_vm, 1, 2)
        
        r_grid.addWidget(QLabel("电容比 C_rss / C_iss:"), 2, 0); r_grid.addWidget(self.mil_c_ratio, 2, 1)
        
        r_grid.addWidget(QLabel("安全状态评估:"), 3, 0); r_grid.addWidget(self.mil_status, 3, 1)
        self.mil_advice_label = QLabel("")
        self.mil_advice_label.setWordWrap(True)
        r_grid.addWidget(self.mil_advice_label, 4, 0, 1, 3) 

        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.mil_imiller, self.mil_c_ratio]: w.setReadOnly(True); w.setStyleSheet(style_res)
        self.mil_vgs_ind.setReadOnly(True); self.mil_vgs_ind.setStyleSheet("background-color: #fff8e1; font-weight: bold; color: #d35400;")
        self.mil_status.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)

    def calc_miller(self):
        try:
            crss = float(self.mil_crss.text()) * 1e-12 # pF -> F
            ciss = float(self.mil_ciss.text()) * 1e-12 # pF -> F
            vth = float(self.mil_vth.text())
            dvdt = float(self.mil_dvdt.text()) * 1e9 # V/ns -> V/s
            rg = float(self.mil_rgoff.text())
            
            if crss <= 0 or ciss <= 0 or vth <= 0: raise ValueError
            
            i_miller = crss * dvdt
            v_induced = i_miller * rg
            c_ratio = crss / ciss
            
            self.mil_imiller.setText(f"{i_miller:.2f} A")
            self.mil_vgs_ind.setText(f"{v_induced:.2f} V")
            self.mil_c_ratio.setText(f"1 : {1/c_ratio:.1f}")
            
            if v_induced < vth * 0.7:
                self.mil_status.setText("安全 (Safe)")
                self.mil_status.setStyleSheet("background-color: #d4edda; color: #155724; font-weight: bold;")
                self.mil_advice_label.setText("状态良好。")
                self.mil_advice_label.setStyleSheet("color: #27ae60; margin-top: 5px;")
            elif v_induced < vth:
                self.mil_status.setText("警告：边缘 (Marginal)")
                self.mil_status.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold;")
                self.mil_advice_label.setText("注意：感应电压接近阈值，建议优化。")
                self.mil_advice_label.setStyleSheet("color: #d35400; font-weight: bold; margin-top: 5px;")
            else:
                self.mil_status.setText("危险！极易误导通 (Risk!)")
                self.mil_status.setStyleSheet("background-color: #f8d7da; color: #721c24; font-weight: bold;")
                msg = (f"警告：感应电压 {v_induced:.2f}V 超过了阈值 {vth}V！建议减小关断电阻或使用米勒钳位。")
                self.mil_advice_label.setText(msg)
                self.mil_advice_label.setStyleSheet("color: #c0392b; font-weight: bold; margin-top: 5px; background-color: #fdedec; padding: 5px; border-radius: 4px;")
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# 4. Zth Calculation
# ==============================================================================
class ZthCalculationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        top_layout = QHBoxLayout()
        
        # 1. 脉冲工况
        grp_cond = QGroupBox("1. 脉冲工况 (Pulse Condition)")
        grid_cond = QGridLayout()
        grid_cond.setVerticalSpacing(12)
        
        self.zth_power = QLineEdit("1000")
        grid_cond.addWidget(QLabel("脉冲功率 P_pulse [W]:"), 0, 0); grid_cond.addWidget(self.zth_power, 0, 1)
        
        self.zth_time = QLineEdit("10")
        self.zth_time.setToolTip("脉冲导通时间 ton。")
        grid_cond.addWidget(QLabel("导通时间 t_on [ms]:"), 1, 0); grid_cond.addWidget(self.zth_time, 1, 1)
        
        self.zth_t_init = QLineEdit("25")
        grid_cond.addWidget(QLabel("初始温度 T_init [°C]:"), 2, 0); grid_cond.addWidget(self.zth_t_init, 2, 1)

        # Repetitive Pulse Settings
        self.chk_repetitive = QCheckBox("启用重复脉冲模式 (Repetitive Mode)")
        self.chk_repetitive.setStyleSheet("font-weight: bold; color: #8e44ad;")
        self.chk_repetitive.stateChanged.connect(self.on_mode_changed)
        grid_cond.addWidget(self.chk_repetitive, 3, 0, 1, 2)

        self.lbl_freq = QLabel("频率 f [Hz]:")
        self.zth_freq = QLineEdit("50")
        self.lbl_duty = QLabel("占空比 D (0~1):")
        self.zth_duty = QLineEdit("0.5")
        
        grid_cond.addWidget(self.lbl_freq, 4, 0); grid_cond.addWidget(self.zth_freq, 4, 1)
        grid_cond.addWidget(self.lbl_duty, 5, 0); grid_cond.addWidget(self.zth_duty, 5, 1)
        
        # Default hidden
        self.lbl_freq.setVisible(False); self.zth_freq.setVisible(False)
        self.lbl_duty.setVisible(False); self.zth_duty.setVisible(False)

        grp_cond.setLayout(grid_cond)
        top_layout.addWidget(grp_cond, 1)
        
        # 2. Foster 热模型
        grp_model = QGroupBox("2. Foster 热网络参数 (R-C Model)")
        v_model = QVBoxLayout()
        self.zth_table = QTableWidget(4, 2)
        self.zth_table.setHorizontalHeaderLabels(["R_i [°C/W] (热阻)", "Tau_i [s] (时间常数)"])
        self.zth_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        defaults = [("0.05", "0.0001"), ("0.15", "0.005"), ("0.40", "0.05"), ("0.20", "0.5")]
        for r, (rv, tv) in enumerate(defaults):
            self.zth_table.setItem(r, 0, QTableWidgetItem(rv))
            self.zth_table.setItem(r, 1, QTableWidgetItem(tv))
        v_model.addWidget(self.zth_table)
        grp_model.setLayout(v_model)
        top_layout.addWidget(grp_model, 2)
        
        layout.addLayout(top_layout)
        
        btn_calc = QPushButton("计算结温 (Peak Tj)")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn_calc.clicked.connect(self.calc_transient)
        layout.addWidget(btn_calc)
        
        grp_res = QGroupBox("3. 计算结果")
        r_grid = QGridLayout()
        self.zth_res_val = QLineEdit()
        self.zth_res_dt = QLineEdit()
        self.zth_res_tj = QLineEdit()
        
        r_grid.addWidget(QLabel("有效热阻抗 Zth_eff:"), 0, 0); r_grid.addWidget(self.zth_res_val, 0, 1)
        
        # Dynamic Formula Label
        self.l_form_z = QLabel()
        self.update_formula_label(False)
        r_grid.addWidget(self.l_form_z, 0, 2)
        
        r_grid.addWidget(QLabel("结温温升 ΔTj:"), 1, 0); r_grid.addWidget(self.zth_res_dt, 1, 1)
        r_grid.addWidget(QLabel("峰值结温 Tj_peak:"), 2, 0); r_grid.addWidget(self.zth_res_tj, 2, 1)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_tj = "background-color: #fdedec; font-weight: bold; color: #c0392b; font-size: 14px;"
        self.zth_res_val.setReadOnly(True); self.zth_res_val.setStyleSheet(style_res)
        self.zth_res_dt.setReadOnly(True); self.zth_res_dt.setStyleSheet(style_res)
        self.zth_res_tj.setReadOnly(True); self.zth_res_tj.setStyleSheet(style_tj)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Extra Tool
        grp_extra = QGroupBox("小工具：热容估算")
        e_layout = QHBoxLayout()
        self.cth_mass = QLineEdit("1.0"); self.cth_mass.setPlaceholderText("质量 (g)")
        self.cth_mat = QComboBox(); self.cth_mat.addItems(["铜 (Cu)", "铝 (Al)", "硅 (Si)"])
        btn_est_cth = QPushButton("估算 C_th ->")
        btn_est_cth.clicked.connect(self.calc_cth_estimate)
        self.cth_res = QLabel("C_th = ? J/K")
        e_layout.addWidget(QLabel("物体质量 [g]:")); e_layout.addWidget(self.cth_mass)
        e_layout.addWidget(QLabel("材质:")); e_layout.addWidget(self.cth_mat)
        e_layout.addWidget(btn_est_cth); e_layout.addWidget(self.cth_res); e_layout.addStretch()
        grp_extra.setLayout(e_layout)
        layout.addWidget(grp_extra)
        
        layout.addStretch()
        self.setLayout(layout)

    def on_mode_changed(self):
        is_rep = self.chk_repetitive.isChecked()
        self.lbl_freq.setVisible(is_rep); self.zth_freq.setVisible(is_rep)
        self.lbl_duty.setVisible(is_rep); self.zth_duty.setVisible(is_rep)
        self.update_formula_label(is_rep)
        
        if is_rep:
            # Auto-fill suggested duty from time if valid
            try:
                t = float(self.zth_time.text()) * 1e-3
                f = float(self.zth_freq.text())
                d = t * f
                if 0 < d < 1: self.zth_duty.setText(f"{d:.2f}")
            except: pass

    def update_formula_label(self, is_repetitive):
        if is_repetitive:
            self.l_form_z.setPixmap(render_formula(r'Z_{peak} = \sum R_i \frac{1 - e^{-t_{on}/\tau_i}}{1 - e^{-T/\tau_i}}'))
            self.l_form_z.setToolTip("重复脉冲模式：基于 Foster 模型的无穷级数叠加")
        else:
            self.l_form_z.setPixmap(render_formula(r'Z_{th}(t) = \sum R_i (1 - e^{-t/\tau_i})'))
            self.l_form_z.setToolTip("单次脉冲模式")

    def calc_transient(self):
        try:
            p_pulse = float(self.zth_power.text())
            t_init = float(self.zth_t_init.text())
            zth_total = 0.0
            
            is_rep = self.chk_repetitive.isChecked()
            
            if is_rep:
                # Repetitive Mode
                f = float(self.zth_freq.text())
                d = float(self.zth_duty.text())
                if f <= 0 or d <= 0 or d >= 1: raise ValueError("频率或占空比无效")
                
                period = 1.0 / f
                t_on = period * d
                
                # Update t_on display for clarity
                self.zth_time.setText(f"{t_on*1000:.3f}")
                
                rows = self.zth_table.rowCount()
                for r in range(rows):
                    item_r = self.zth_table.item(r, 0)
                    item_tau = self.zth_table.item(r, 1)
                    if item_r and item_tau:
                        ri = float(item_r.text())
                        tau_i = float(item_tau.text())
                        # Foster Repetitive Summation Formula
                        term = ri * (1.0 - math.exp(-t_on / tau_i)) / (1.0 - math.exp(-period / tau_i))
                        zth_total += term
            else:
                # Single Pulse Mode
                t_pulse = float(self.zth_time.text()) * 1e-3
                rows = self.zth_table.rowCount()
                for r in range(rows):
                    item_r = self.zth_table.item(r, 0)
                    item_tau = self.zth_table.item(r, 1)
                    if item_r and item_tau:
                        ri = float(item_r.text())
                        tau_i = float(item_tau.text())
                        val = ri * (1.0 - math.exp(-t_pulse / tau_i))
                        zth_total += val
            
            dt = p_pulse * zth_total
            tj_peak = t_init + dt
            
            self.zth_res_val.setText(f"{zth_total:.4f} °C/W")
            self.zth_res_dt.setText(f"{dt:.2f} °C")
            self.zth_res_tj.setText(f"{tj_peak:.2f} °C")
            
            if tj_peak > 150: QMessageBox.warning(self, "过热警告", f"结温 ({tj_peak:.1f}°C) 超过 150°C！")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"输入数值无效: {str(e)}")

    def calc_cth_estimate(self):
        try:
            mass = float(self.cth_mass.text())
            c_spec = [0.385, 0.897, 0.71][self.cth_mat.currentIndex()]
            c_th = mass * c_spec
            self.cth_res.setText(f"C_th ≈ {c_th:.3f} J/K")
        except: pass

# ==============================================================================
# 5. Diode Loss
# ==============================================================================
class DiodeLossTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        input_group = QGroupBox("参数设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(15)
        
        self.d_vr = QLineEdit("400")
        self.d_if = QLineEdit("10")
        self.d_fsw = QLineEdit("50")
        self.d_duty = QLineEdit("0.5")
        
        grid.addWidget(QLabel("<b>工况参数:</b>"), 0, 0, 1, 4)
        grid.addWidget(QLabel("反向电压 Vr [V]:"), 1, 0); grid.addWidget(self.d_vr, 1, 1)
        grid.addWidget(QLabel("正向电流 If [A]:"), 1, 2); grid.addWidget(self.d_if, 1, 3)
        grid.addWidget(QLabel("开关频率 fsw [kHz]:"), 2, 0); grid.addWidget(self.d_fsw, 2, 1)
        grid.addWidget(QLabel("导通占空比 D [0~1]:"), 2, 2); grid.addWidget(self.d_duty, 2, 3)
        
        grid.addWidget(QLabel("------------------------------------------------"), 3, 0, 1, 4)
        grid.addWidget(QLabel("<b>器件参数 (Datasheet):</b>"), 4, 0, 1, 4)
        self.d_vf = QLineEdit("1.2")
        self.d_qrr = QLineEdit("500")
        grid.addWidget(QLabel("正向压降 Vf [V]:"), 5, 0); grid.addWidget(self.d_vf, 5, 1)
        grid.addWidget(QLabel("反向恢复电荷 Qrr [nC]:"), 5, 2); grid.addWidget(self.d_qrr, 5, 3)
        
        input_group.setLayout(grid)
        layout.addWidget(input_group)
        
        btn = QPushButton("计算二极管损耗")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_diode)
        layout.addWidget(btn)
        
        res_group = QGroupBox("估算结果")
        res_grid = QGridLayout()
        self.d_p_cond = QLineEdit()
        self.d_p_rr = QLineEdit()
        self.d_p_tot = QLineEdit()
        
        res_grid.addWidget(QLabel("导通损耗 (P_cond):"), 0, 0); res_grid.addWidget(self.d_p_cond, 0, 1)
        l_dc = QLabel(); l_dc.setPixmap(render_formula(r'P_{cond} = V_f \cdot I_f \cdot D'))
        res_grid.addWidget(l_dc, 0, 2)
        
        res_grid.addWidget(QLabel("反向恢复损耗 (P_rr):"), 1, 0); res_grid.addWidget(self.d_p_rr, 1, 1)
        l_dr = QLabel(); l_dr.setPixmap(render_formula(r'P_{rr} \approx \frac{1}{4} Q_{rr} V_r f_{sw}'))
        res_grid.addWidget(l_dr, 1, 2)
        
        res_grid.addWidget(QLabel("总损耗 (P_total):"), 2, 0); res_grid.addWidget(self.d_p_tot, 2, 1)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        style_tot = "background-color: #fff5f5; font-weight: bold; color: #c0392b; font-size: 14px;"
        self.d_p_cond.setReadOnly(True); self.d_p_cond.setStyleSheet(style_res)
        self.d_p_rr.setReadOnly(True); self.d_p_rr.setStyleSheet(style_res)
        self.d_p_tot.setReadOnly(True); self.d_p_tot.setStyleSheet(style_tot)
        
        res_group.setLayout(res_grid)
        layout.addWidget(res_group)
        layout.addStretch()
        self.setLayout(layout)

    def calc_diode(self):
        try:
            vr = float(self.d_vr.text())
            if_val = float(self.d_if.text())
            fsw = float(self.d_fsw.text()) * 1000
            duty = float(self.d_duty.text())
            vf = float(self.d_vf.text())
            qrr = float(self.d_qrr.text()) * 1e-9
            
            p_cond = vf * if_val * duty
            e_rr = 0.25 * qrr * vr
            p_rr = e_rr * fsw
            p_tot = p_cond + p_rr
            
            self.d_p_cond.setText(f"{p_cond:.2f} W")
            self.d_p_rr.setText(f"{p_rr:.2f} W")
            self.d_p_tot.setText(f"{p_tot:.2f} W")
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

# ==============================================================================
# 6. SOA & Short Circuit
# ==============================================================================
class SoaCheckTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Explanation
        info = QLabel("功能说明：评估 MOSFET 在线性模式 (Linear Mode) 或 短路冲击 下的热安全性。\n"
                      "注意：对于高压长脉冲 (如 >20V, >1ms)，MOSFET 容易发生 Spirito 效应 (热失稳)，其实际耐受能力可能远低于 Zth 曲线预测值。")
        info.setWordWrap(True)
        info.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info)

        # 1. 冲击工况
        grp_cond = QGroupBox("1. 冲击工况 (Stress Condition)")
        g_cond = QGridLayout()
        g_cond.setVerticalSpacing(12)
        
        self.soa_vds = QLineEdit("24"); g_cond.addWidget(QLabel("漏源电压 Vds [V]:"), 0, 0); g_cond.addWidget(self.soa_vds, 0, 1)
        self.soa_id = QLineEdit("10"); g_cond.addWidget(QLabel("漏极电流 Id [A]:"), 0, 2); g_cond.addWidget(self.soa_id, 0, 3)
        self.soa_time = QLineEdit("1.0"); g_cond.addWidget(QLabel("脉冲持续时间 t [ms]:"), 1, 0); g_cond.addWidget(self.soa_time, 1, 1)
        
        self.soa_tc = QLineEdit("25"); g_cond.addWidget(QLabel("初始壳温 Tc [°C]:"), 2, 0); g_cond.addWidget(self.soa_tc, 2, 1)
        self.soa_tjmax = QLineEdit("175"); g_cond.addWidget(QLabel("最大结温 Tj_max [°C]:"), 2, 2); g_cond.addWidget(self.soa_tjmax, 2, 3)
        
        grp_cond.setLayout(g_cond)
        layout.addWidget(grp_cond)
        
        # 2. 热参数 (Datasheet Zth)
        grp_zth = QGroupBox("2. 瞬态热阻 (Datasheet Zth)")
        g_zth = QGridLayout()
        
        self.soa_zth_val = QLineEdit("0.5")
        self.soa_zth_val.setToolTip("请查阅 Datasheet 中的 'Transient Thermal Impedance' 曲线，\n找到对应脉冲时间 (t) 下的 Zth 值。")
        g_zth.addWidget(QLabel("Zth(t) [°C/W]:"), 0, 0)
        g_zth.addWidget(self.soa_zth_val, 0, 1)
        
        btn_help_zth = QPushButton("不会查表？使用 RC 模型估算")
        btn_help_zth.setStyleSheet("color: #2980b9; border: none; font-weight: bold; text-align: left;")
        btn_help_zth.clicked.connect(lambda: QMessageBox.information(self, "提示", "请切换到 '瞬态热阻抗 (Zth)' 标签页，利用 Foster 模型计算任意时刻的 Zth 值。"))
        g_zth.addWidget(btn_help_zth, 0, 2)
        
        grp_zth.setLayout(g_zth)
        layout.addWidget(grp_zth)
        
        btn_calc = QPushButton("执行 SOA 安全性校验")
        btn_calc.setFixedHeight(45)
        btn_calc.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; font-size: 14px;")
        btn_calc.clicked.connect(self.calc_soa)
        layout.addWidget(btn_calc)
        
        # 3. 结果
        grp_res = QGroupBox("3. 评估报告")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.soa_power = QLineEdit()
        self.soa_dt = QLineEdit()
        self.soa_tj_peak = QLineEdit()
        self.soa_status = QLineEdit()
        self.soa_spirito = QLineEdit() # Spirito Warning
        
        r_grid.addWidget(QLabel("冲击功率 P_pulse:"), 0, 0); r_grid.addWidget(self.soa_power, 0, 1)
        l_p = QLabel(); l_p.setPixmap(render_formula(r'P = V_{ds} \cdot I_d'))
        r_grid.addWidget(l_p, 0, 2)
        
        r_grid.addWidget(QLabel("结温温升 ΔTj:"), 1, 0); r_grid.addWidget(self.soa_dt, 1, 1)
        l_t = QLabel(); l_t.setPixmap(render_formula(r'\Delta T_j = P \cdot Z_{th}(t)'))
        r_grid.addWidget(l_t, 1, 2)
        
        r_grid.addWidget(QLabel("峰值结温 Tj_peak:"), 2, 0); r_grid.addWidget(self.soa_tj_peak, 2, 1)
        r_grid.addWidget(QLabel("Pass / Fail ?"), 2, 2)
        
        r_grid.addWidget(QLabel("热安全性判定:"), 3, 0); r_grid.addWidget(self.soa_status, 3, 1, 1, 2)
        
        r_grid.addWidget(QLabel("Spirito 效应风险:"), 4, 0); r_grid.addWidget(self.soa_spirito, 4, 1, 1, 2)
        
        style_gray = "background-color: #f0f0f0;"
        for w in [self.soa_power, self.soa_dt, self.soa_tj_peak, self.soa_status, self.soa_spirito]:
            w.setReadOnly(True)
            w.setStyleSheet(style_gray)
            
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        layout.addStretch()
        self.setLayout(layout)

    def calc_soa(self):
        try:
            vds = float(self.soa_vds.text())
            id_curr = float(self.soa_id.text())
            t_ms = float(self.soa_time.text())
            tc = float(self.soa_tc.text())
            tj_max = float(self.soa_tjmax.text())
            zth = float(self.soa_zth_val.text())
            
            p_pulse = vds * id_curr
            dt = p_pulse * zth
            tj_peak = tc + dt
            
            self.soa_power.setText(f"{p_pulse:.2f} W")
            self.soa_dt.setText(f"+ {dt:.2f} °C")
            self.soa_tj_peak.setText(f"{tj_peak:.2f} °C")
            
            # 1. Thermal Limit Check
            if tj_peak > tj_max:
                self.soa_status.setText(f"失败 (FAIL) ! 超温 {tj_peak-tj_max:.1f}°C")
                self.soa_status.setStyleSheet("background-color: #fdedec; color: red; font-weight: bold;")
            elif tj_peak > tj_max * 0.9:
                self.soa_status.setText("警告 (Warning) - 裕量不足 10%")
                self.soa_status.setStyleSheet("background-color: #fff3cd; color: #856404; font-weight: bold;")
            else:
                self.soa_status.setText("通过 (PASS)")
                self.soa_status.setStyleSheet("background-color: #d4edda; color: green; font-weight: bold;")
                
            # 2. Spirito Effect Check (Simplified Engineering Rule)
            # High Vds + Long time -> Hot spots -> Early failure
            is_spirito_risk = False
            if vds > 20 and t_ms > 1.0: 
                is_spirito_risk = True
            
            if is_spirito_risk:
                self.soa_spirito.setText("高风险！高压长脉冲可能导致 Spirito 失效。请参考 Datasheet SOA 曲线的斜率变化。")
                self.soa_spirito.setStyleSheet("background-color: #fff3cd; color: #d35400; font-weight: bold;")
            else:
                self.soa_spirito.setText("低风险 (主要是功率限制)")
                self.soa_spirito.setStyleSheet("background-color: #f0f0f0; color: #555;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")