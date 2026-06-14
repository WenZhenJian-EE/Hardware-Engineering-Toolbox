from modules.base_module import BaseModule
# power_device_driver.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QFrame,
                             QDialog, QTextBrowser, QTabWidget, QComboBox,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from utils import render_formula

# 引入物理计算面板
from modules.power.power_device_physics import DevicePhysicsPanel

class SwitchDeviceWindow(BaseModule):
    category = '2. 功率器件与能源 (Devices, Battery & Thermal)'
    display_name = '开关器件综合'
    description = '驱动 / 保护 / 损耗 / Zth / SOA'
    window_id = 'power_device'

    def init_module_ui(self):
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('开关器件综合工具 (Driver Design & Device Physics)')
        self.setGeometry(350, 350, 1050, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计指南 / Foster 模型 / SOA")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(300)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # 主 Tab：分为“驱动设计”和“器件物理特性”两大类
        self.main_tabs = QTabWidget()
        
        self.main_tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #c0c0c0; background: #ffffff; border-radius: 4px; margin-top: 5px; }
            QTabBar::tab { 
                background: #f0f0f0; 
                border: 1px solid #c0c0c0; 
                padding: 10px 15px; 
                margin-right: 4px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                font-size: 14px; 
                min-width: 150px;
            }
            QTabBar::tab:selected { 
                background: #ffffff; 
                border-bottom: 1px solid #ffffff; 
                font-weight: bold; 
                color: #3498db; 
            }
        """)

        # Tab 1: 驱动设计 (Driver Design) - 本地定义
        self.tab_driver_design = DriverDesignPanel()
        
        # Tab 2: 器件物理计算 (Device Physics) - 从外部文件导入
        self.tab_device_physics = DevicePhysicsPanel()

        self.main_tabs.addTab(self.tab_driver_design, "驱动电路设计 (Driver Design)")
        self.main_tabs.addTab(self.tab_device_physics, "开关管特性分析 (Device Physics)")

        main_layout.addWidget(self.main_tabs)
        self.setLayout(main_layout)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("开关器件设计指南 (损耗/驱动/Desat保护/SOA)")
        dialog.resize(950, 800)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 使用完整的 HTML 内容
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
        
        <h2>一、Desat 短路保护 (Desaturation Protection)</h2>
        <div class="box">
            <b>设计痛点：</b> Desat 电容 ($C_{blk}$) 选小了，开关噪声会导致误触发；选大了，短路保护太慢，IGBT/SiC 炸机。<br>
            <b>核心原理：</b> 利用 IGBT/SiC 退出饱和区时 $V_{ce}$ 电压升高的特性。当 $V_{ce} > V_{th}$ 时，驱动芯片判定为短路。
        </div>
        <ul>
            <li><b>Blanking Time (消隐时间)：</b> 开通瞬间 $V_{ce}$ 从高电平下降，需要一段时间。此时 Desat 必须“闭眼”不看，否则会误触发。</li>
            <li><b>计算公式：</b> $C_{blk} = \frac{I_{chg} \cdot T_{blank}}{V_{th} - V_F - V_{ce\_sat}}$。
                <br>注意：这里的 $V_{ce\_sat}$ 指的是你希望“容忍”的电压水平（或判定起始位），实际上主要是利用电容充电延时来覆盖开通过程。</li>
            <li><b>二极管选择：</b> Desat 二极管必须选用 <b>高压快恢复二极管</b>，反向耐压需高于 Bus 电压，且结电容要小。</li>
        </ul>

        <h2>二、瞬态热阻抗 (Transient Zth) & Foster 模型</h2>
        <div class="box">
            <b>为什么要填这个表？</b><br>
            实际的 MOSFET/IGBT 并不是一瞬间就热起来的，而是有一个“热容”效应。Foster 模型用几组 RC 网络来模拟这个过程，从而计算脉冲功率下的瞬态结温。<br>
            <b>不填表能不能算？</b> 不能。如果不填，软件默认是稳态计算，会极大高估短路或浪涌时的结温。
        </div>

        <h3>1. 去哪里找参数？</h3>
        <p>打开器件的 Datasheet，搜索关键字：</p>
        <ul>
            <li><b>Transient Thermal Impedance</b> (瞬态热阻抗)</li>
            <li><b>ZthJC</b> (结到壳热阻)</li>
            <li><b>Foster Model</b> 或 <b>RC Model</b></li>
        </ul>
        <p>优质的厂商（如 Infineon, ST, Vishay, Wolfspeed）通常会在 Zth 曲线图旁边直接给出一个表格，列出 <code>Ri</code> 和 <code>Tau_i</code> (或 Ci)。</p>

        <h3>2. 如何填表？</h3>
        <p>找到表格后，直接将数值对应填入软件：</p>
        <table style="width:80%">
            <tr><th>层级 (i)</th><th>R_i (K/W)</th><th>Tau_i (s)</th><th>说明</th></tr>
            <tr><td>1</td><td>0.05</td><td>0.0001</td><td>第一层：芯片本身（热容极小，响应极快）</td></tr>
            <tr><td>2</td><td>0.15</td><td>0.005</td><td>第二层：焊料/DBC</td></tr>
            <tr><td>3</td><td>...</td><td>...</td><td>...</td></tr>
        </table>

        <h2>三、损耗与驱动计算</h2>
        <ul>
            <li><b>开关损耗：</b> $P_{sw} = (E_{on} + E_{off}) \cdot f_{sw}$。注意 Eon/Eoff 是基于特定测试电压电流测得的。</li>
            <li><b>自举电容 (Bootstrap)：</b> $C_{boot} > Q_{total} / \Delta V_{boot}$。通常取计算值的 10 倍以上。</li>
            <li><b>驱动变压器 (GDT)：</b> 核心是防止饱和。$B_{peak} = \frac{V \cdot T_{on}}{N \cdot A_e} < B_{sat}$。</li>
        </ul>

        <h2>四、MOSFET SOA 与 Spirito 效应</h2>
        <div class="box">
            <b>核心风险：</b> 在<b>线性模式</b>（如软启动、LDO）下，随着 $V_{ds}$ 升高，MOSFET 内部容易出现电流集中（热点），导致实际 SOA 远低于功率限制线。
        </div>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        btn_close = QPushButton("关闭指南")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec_()

# ==============================================================================
# Driver Design Panel (Container for Driver Tabs)
# ==============================================================================
class DriverDesignPanel(QWidget):
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
                margin-right: 1px; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px;
                font-size: 13px;
            }
            QTabBar::tab:selected { 
                background: #ffffff; 
                border-bottom: 1px solid #ffffff; 
                font-weight: bold; 
                color: #2980b9; 
            }
        """)
        
        self.tabs.addTab(GateDriverTab(), "栅极驱动电路 ")
        self.tabs.addTab(DesatProtectionTab(), "Desat短路保护 ")
        self.tabs.addTab(BootstrapTab(), "自举电路 ")
        self.tabs.addTab(GdtDesignTab(), "驱动变压器 (GDT)") 
        self.tabs.addTab(DeviceCompareTab(), "MOS/SiC/GaN 对比")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

# ==============================================================================
# 1. Gate Driver Design
# ==============================================================================
class GateDriverTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_in = QGroupBox("1. 驱动参数设置")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.dr_vcc = QLineEdit("15")
        self.dr_vee = QLineEdit("0")
        grid.addWidget(QLabel("正驱动电压 (Vcc) [V]:"), 0, 0); grid.addWidget(self.dr_vcc, 0, 1)
        grid.addWidget(QLabel("负驱动电压 (Vee) [V]:"), 0, 2); grid.addWidget(self.dr_vee, 0, 3)
        
        self.dr_rg_ext = QLineEdit("10")
        self.dr_rg_int = QLineEdit("2")
        grid.addWidget(QLabel("外部栅极电阻 (Rg_ext) [Ω]:"), 1, 0); grid.addWidget(self.dr_rg_ext, 1, 1)
        grid.addWidget(QLabel("内部栅极电阻 (Rg_int) [Ω]:"), 1, 2); grid.addWidget(self.dr_rg_int, 1, 3)
        
        self.dr_qg = QLineEdit("100")
        self.dr_fsw = QLineEdit("50")
        grid.addWidget(QLabel("总栅极电荷 (Qg) [nC]:"), 2, 0); grid.addWidget(self.dr_qg, 2, 1)
        grid.addWidget(QLabel("开关频率 (fsw) [kHz]:"), 2, 2); grid.addWidget(self.dr_fsw, 2, 3)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        btn = QPushButton("计算驱动参数 (电流/功率/死区)")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.clicked.connect(self.calc_driver)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("2. 设计结果与选型建议")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        
        self.res_i_peak = QLineEdit()
        self.res_p_drv = QLineEdit()
        self.res_p_rg = QLineEdit()
        self.res_deadtime = QLineEdit()
        
        res_grid.addWidget(QLabel("峰值驱动电流 (I_peak):"), 0, 0); res_grid.addWidget(self.res_i_peak, 0, 1)
        l_ipeak = QLabel(); l_ipeak.setPixmap(render_formula(r'I_{peak} = \frac{V_{cc}-V_{ee}}{R_{g\_ext} + R_{g\_int}}')); 
        res_grid.addWidget(l_ipeak, 0, 2)
        
        res_grid.addWidget(QLabel("驱动芯片功率需求 (P_drv):"), 1, 0); res_grid.addWidget(self.res_p_drv, 1, 1)
        l_pdrv = QLabel(); l_pdrv.setPixmap(render_formula(r'P_{drv} = Q_g \cdot (V_{cc}-V_{ee}) \cdot f_{sw}')); 
        res_grid.addWidget(l_pdrv, 1, 2)
        
        res_grid.addWidget(QLabel("栅极电阻功率 (P_Rg):"), 2, 0); res_grid.addWidget(self.res_p_rg, 2, 1)
        l_prg = QLabel(); l_prg.setPixmap(render_formula(r'P_{R_g} = P_{drv} \cdot \frac{R_{g\_ext}}{R_{total}}')); 
        res_grid.addWidget(l_prg, 2, 2)
        
        res_grid.addWidget(QLabel("参考死区时间 (Deadtime):"), 3, 0); res_grid.addWidget(self.res_deadtime, 3, 1)
        res_grid.addWidget(QLabel("基于 5*R*Ciss 估算"), 3, 2)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_i_peak, self.res_p_drv, self.res_p_rg, self.res_deadtime]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
            
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)

    def calc_driver(self):
        try:
            vcc = float(self.dr_vcc.text())
            vee = float(self.dr_vee.text())
            v_swing = vcc + abs(vee)
            rg_ext = float(self.dr_rg_ext.text())
            rg_int = float(self.dr_rg_int.text())
            qg = float(self.dr_qg.text()) * 1e-9
            fsw = float(self.dr_fsw.text()) * 1000
            
            r_total = rg_ext + rg_int
            if r_total <= 0: raise ValueError
            
            i_peak = v_swing / r_total
            p_total = qg * v_swing * fsw
            p_rg_ext = p_total * (rg_ext / r_total)
            
            c_iss_est = qg / v_swing 
            tau = r_total * c_iss_est
            deadtime = 5 * tau * 1e9
            
            self.res_i_peak.setText(f"{i_peak:.2f} A")
            self.res_p_drv.setText(f"{p_total*1000:.1f} mW")
            self.res_p_rg.setText(f"{p_rg_ext*1000:.1f} mW")
            self.res_deadtime.setText(f"> {deadtime:.0f} ns")
            
            if p_rg_ext > 0.1:
                self.res_p_rg.setStyleSheet("background-color: #fff5f5; font-weight: bold; color: #c0392b;")
            else:
                self.res_p_rg.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# 2. Desat Protection (New Feature)
# ==============================================================================
class DesatProtectionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Input Group
        grp_in = QGroupBox("1. 保护参数设置 (Protection Parameters)")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.ds_vth = QLineEdit("6.5")
        self.ds_vth.setToolTip("驱动芯片内部的 Desat 比较器阈值 (如 Avago/Broadcom 常为 6.5V, TI/Infineon 可能为 9V)")
        grid.addWidget(QLabel("检测阈值 Vth_desat [V]:"), 0, 0); grid.addWidget(self.ds_vth, 0, 1)
        
        self.ds_ichg = QLineEdit("250")
        self.ds_ichg.setToolTip("驱动芯片内部给 Desat 电容充电的恒流源电流 (通常 250uA ~ 500uA)")
        grid.addWidget(QLabel("充电电流 Ichg [uA]:"), 0, 2); grid.addWidget(self.ds_ichg, 0, 3)
        
        self.ds_tblank = QLineEdit("2.0")
        self.ds_tblank.setToolTip("期望的消隐时间 (Blanking Time)，即忽略开通瞬间误触发的时间窗。通常 IGBT 取 2-3us，SiC 取 1-1.5us。")
        grid.addWidget(QLabel("目标消隐时间 T_blank [us]:"), 1, 0); grid.addWidget(self.ds_tblank, 1, 1)
        
        self.ds_vf = QLineEdit("0.7")
        grid.addWidget(QLabel("二极管压降 Vf_diode [V]:"), 1, 2); grid.addWidget(self.ds_vf, 1, 3)
        
        self.ds_vce_trip = QLineEdit("2.5")
        self.ds_vce_trip.setToolTip("希望保护触发时的 Vce 电压起点。通常取饱和压降 Vce_sat (如 2V) 或稍高值。")
        grid.addWidget(QLabel("保护起始 Vce_sat [V]:"), 2, 0); grid.addWidget(self.ds_vce_trip, 2, 1)
        
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)
        
        # Calculate Button
        btn = QPushButton("计算 Desat 电容 (C_blk) 与 建议电阻")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.setStyleSheet("background-color: #e67e22; color: white;")
        btn.clicked.connect(self.calc_desat)
        layout.addWidget(btn)
        
        # Result Group
        grp_res = QGroupBox("2. 计算结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.res_c_blk = QLineEdit()
        self.res_c_std = QLineEdit()
        self.res_r_desat = QLineEdit()
        self.res_warn = QLineEdit()
        
        r_grid.addWidget(QLabel("计算电容值 C_blk_calc:"), 0, 0); r_grid.addWidget(self.res_c_blk, 0, 1)
        l_form = QLabel(); l_form.setPixmap(render_formula(r'C_{blk} = \frac{I_{chg} \cdot T_{blank}}{V_{th} - V_F - V_{ce\_sat}}'))
        r_grid.addWidget(l_form, 0, 2)
        
        r_grid.addWidget(QLabel("推荐标准值 (E12/E24):"), 1, 0); r_grid.addWidget(self.res_c_std, 1, 1)
        r_grid.addWidget(QLabel("建议选用 NPO/C0G 材质"), 1, 2)
        
        r_grid.addWidget(QLabel("限流电阻 R_desat:"), 2, 0); r_grid.addWidget(self.res_r_desat, 2, 1)
        r_grid.addWidget(QLabel("推荐 100Ω ~ 1kΩ (保护二极管)"), 2, 2)
        
        style_res = "background-color: #fdf2e9; font-weight: bold; color: #d35400;"
        for w in [self.res_c_blk, self.res_c_std, self.res_r_desat, self.res_warn]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
        
        # 警告栏
        self.res_warn.setStyleSheet("background-color: #fff; color: red; border: none;")
        layout.addWidget(self.res_warn)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        tip = QLabel("提示：SiC MOSFET 短路耐受时间 (SCWT) 通常仅 2~3us，请务必确保 T_blank < SCWT。\n如果计算出电容过小 (<47pF)，建议增加 PCB 屏蔽或使用更抗噪的驱动芯片。")
        tip.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(tip)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def calc_desat(self):
        try:
            vth = float(self.ds_vth.text())
            ichg = float(self.ds_ichg.text()) * 1e-6
            tblank = float(self.ds_tblank.text()) * 1e-6
            vf = float(self.ds_vf.text())
            vce = float(self.ds_vce_trip.text())
            
            # 校验电压余量
            delta_v = vth - vf - vce
            if delta_v <= 0.5:
                self.res_warn.setText(f"警告: 电压余量太小 ({delta_v:.2f}V)！可能导致误触发或无法充电。")
                self.res_c_blk.setText("Error")
                return
            else:
                self.res_warn.setText("")
            
            # C = I * t / V
            c_val = ichg * tblank / delta_v
            
            # 寻找最近标准电容 (pF)
            c_pf = c_val * 1e12
            std_vals = [47, 56, 68, 82, 100, 120, 150, 180, 220, 270, 330, 390, 470, 560]
            nearest = min(std_vals, key=lambda x: abs(x - c_pf))
            
            self.res_c_blk.setText(f"{c_pf:.1f} pF")
            self.res_c_std.setText(f"{nearest} pF")
            self.res_r_desat.setText("100Ω ~ 1kΩ") # 经验值
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# Device comparison for MOSFET / SiC / GaN candidates
# ==============================================================================
class DeviceCompareTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        info = QLabel(
            "Quick loss comparison for MOSFET / SiC / GaN candidates. "
            "Enter datasheet values at or near the working point; Eon/Eoff are treated as operating-point energies."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #566573; font-style: italic;")
        layout.addWidget(info)

        grp_op = QGroupBox("1. Operating point")
        g = QGridLayout()
        self.cmp_vbus = QLineEdit("400")
        self.cmp_irms = QLineEdit("10")
        self.cmp_isw = QLineEdit("10")
        self.cmp_duty = QLineEdit("50")
        self.cmp_fsw = QLineEdit("100")
        self.cmp_vgate = QLineEdit("15")
        self.cmp_tcase = QLineEdit("80")

        fields = [
            ("Bus voltage Vbus [V]:", self.cmp_vbus),
            ("Device RMS current [A]:", self.cmp_irms),
            ("Switching current [A]:", self.cmp_isw),
            ("Conduction duty [%]:", self.cmp_duty),
            ("Switching frequency [kHz]:", self.cmp_fsw),
            ("Gate drive swing [V]:", self.cmp_vgate),
            ("Case temperature [C]:", self.cmp_tcase),
        ]
        for i, (label, widget) in enumerate(fields):
            r, c = i // 2, (i % 2) * 2
            g.addWidget(QLabel(label), r, c)
            g.addWidget(widget, r, c + 1)
        grp_op.setLayout(g)
        layout.addWidget(grp_op)

        self.cmp_table = QTableWidget()
        headers = [
            "Name", "Tech", "Vds[V]", "Id[A]", "Rds[mOhm]", "Qg[nC]",
            "Eon[uJ]", "Eoff[uJ]", "Eoss[uJ]", "Qrr[nC]",
            "RthJC[C/W]", "Tcase[C]", "Result"
        ]
        self.cmp_table.setColumnCount(len(headers))
        self.cmp_table.setHorizontalHeaderLabels(headers)
        self.cmp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cmp_table.setMinimumHeight(260)
        layout.addWidget(self.cmp_table)

        btn_row = QHBoxLayout()
        b_add = QPushButton("Add candidate")
        b_add.clicked.connect(lambda: self.add_device_row())
        btn_row.addWidget(b_add)
        b_del = QPushButton("Delete selected")
        b_del.clicked.connect(self.del_device_row)
        btn_row.addWidget(b_del)
        b_calc = QPushButton("Compare losses")
        b_calc.setFixedHeight(42)
        b_calc.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold;")
        b_calc.clicked.connect(self.calc_compare)
        btn_row.addWidget(b_calc)
        layout.addLayout(btn_row)

        self.cmp_summary = QTextBrowser()
        self.cmp_summary.setMinimumHeight(130)
        self.cmp_summary.setStyleSheet("background-color: #f8f9fa; border: 1px solid #d5d8dc;")
        layout.addWidget(self.cmp_summary)

        self.setLayout(layout)
        self.add_device_row(["SiC_A", "SiC", "650", "30", "45", "85", "120", "80", "12", "0", "0.7", "", ""])
        self.add_device_row(["MOS_A", "MOS", "650", "25", "95", "60", "180", "120", "8", "80", "1.0", "", ""])
        self.add_device_row(["GaN_A", "GaN", "650", "20", "70", "18", "45", "35", "5", "0", "1.5", "", ""])

    def add_device_row(self, data=None):
        row = self.cmp_table.rowCount()
        self.cmp_table.insertRow(row)
        data = data or ["", "MOS", "", "", "", "", "", "", "", "", "", "", ""]
        for c, val in enumerate(data):
            self.cmp_table.setItem(row, c, QTableWidgetItem(str(val)))

    def del_device_row(self):
        row = self.cmp_table.currentRow()
        if row >= 0:
            self.cmp_table.removeRow(row)

    def _cell_float(self, row, col, default=None):
        item = self.cmp_table.item(row, col)
        text = item.text().strip() if item else ""
        if text == "" and default is not None:
            return default
        return float(text)

    def calc_compare(self):
        try:
            vbus = float(self.cmp_vbus.text())
            irms = float(self.cmp_irms.text())
            isw = float(self.cmp_isw.text())
            duty = float(self.cmp_duty.text()) / 100.0
            fsw = float(self.cmp_fsw.text()) * 1e3
            vgate = float(self.cmp_vgate.text())
            default_tcase = float(self.cmp_tcase.text())
            if vbus <= 0 or fsw <= 0 or vgate <= 0:
                raise ValueError

            rows = []
            for r in range(self.cmp_table.rowCount()):
                name_item = self.cmp_table.item(r, 0)
                name = name_item.text().strip() if name_item else f"Device {r + 1}"
                rds = self._cell_float(r, 4) * 1e-3
                qg = self._cell_float(r, 5) * 1e-9
                eon = self._cell_float(r, 6, 0.0) * 1e-6
                eoff = self._cell_float(r, 7, 0.0) * 1e-6
                eoss = self._cell_float(r, 8, 0.0) * 1e-6
                qrr = self._cell_float(r, 9, 0.0) * 1e-9
                rth = self._cell_float(r, 10)
                tcase = self._cell_float(r, 11, default_tcase)

                p_cond = (irms ** 2) * rds * duty
                p_sw = (eon + eoff + eoss) * fsw
                p_qrr = qrr * vbus * fsw
                p_gate = qg * vgate * fsw
                p_total = p_cond + p_sw + p_qrr + p_gate
                tj = tcase + p_total * rth

                rg_fast = vgate * 30e-9 / qg if qg > 0 else 0.0
                rg_slow = vgate * 100e-9 / qg if qg > 0 else 0.0
                result = f"P={p_total:.2f}W, Tj={tj:.1f}C, Rg~{rg_fast:.1f}-{rg_slow:.1f}Ω"
                self.cmp_table.setItem(r, 12, QTableWidgetItem(result))
                rows.append((p_total, tj, name, p_cond, p_sw, p_qrr, p_gate))

            rows.sort(key=lambda x: x[0])
            html = "<b>Rank by total estimated loss:</b><br>"
            for p_total, tj, name, p_cond, p_sw, p_qrr, p_gate in rows:
                color = "#c0392b" if tj >= 125 else "#d35400" if tj >= 100 else "#1e8449"
                html += (
                    f"<span style='color:{color}'><b>{name}</b>: {p_total:.2f} W, Tj={tj:.1f} C</span>"
                    f" &nbsp; Cond={p_cond:.2f}W, Sw={p_sw:.2f}W, Qrr={p_qrr:.2f}W, Gate={p_gate:.2f}W<br>"
                )
            html += "<br><i>Note: this is a fast screening model. Re-scale Eon/Eoff if datasheet test voltage/current differ from your operating point.</i>"
            self.cmp_summary.setHtml(html)
        except Exception:
            QMessageBox.warning(self, "Input error", "Please check numeric fields in the operating point and candidate table.")

# ==============================================================================
# 3. Bootstrap Design
# ==============================================================================
class BootstrapTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        grp_hs = QGroupBox("1. 高边驱动参数 (High-Side Driver Params)")
        grid_hs = QGridLayout()
        grid_hs.setVerticalSpacing(12)
        
        self.bt_qg = QLineEdit("50"); grid_hs.addWidget(QLabel("MOSFET Total Qg [nC]:"), 0, 0); grid_hs.addWidget(self.bt_qg, 0, 1)
        self.bt_fsw = QLineEdit("100"); grid_hs.addWidget(QLabel("开关频率 fsw [kHz]:"), 0, 2); grid_hs.addWidget(self.bt_fsw, 0, 3)
        self.bt_iq = QLineEdit("50"); grid_hs.addWidget(QLabel("总漏电流/静态电流 I_leak [uA]:"), 1, 0); grid_hs.addWidget(self.bt_iq, 1, 1)
        self.bt_duty = QLineEdit("95"); grid_hs.addWidget(QLabel("最大占空比 D_max [%]:"), 1, 2); grid_hs.addWidget(self.bt_duty, 1, 3)
        self.bt_vdrop = QLineEdit("0.5"); grid_hs.addWidget(QLabel("允许压降 ΔV_boot [V]:"), 2, 0); grid_hs.addWidget(self.bt_vdrop, 2, 1)
        self.bt_qrr = QLineEdit("20"); grid_hs.addWidget(QLabel("二极管 Qrr [nC]:"), 2, 2); grid_hs.addWidget(self.bt_qrr, 2, 3)
        
        grp_hs.setLayout(grid_hs)
        layout.addWidget(grp_hs)
        
        grp_pwr = QGroupBox("2. 电源与时序 (Supply & Timing)")
        grid_pwr = QGridLayout()
        self.bt_vcc = QLineEdit("15"); grid_pwr.addWidget(QLabel("驱动电源 Vcc [V]:"), 0, 0); grid_pwr.addWidget(self.bt_vcc, 0, 1)
        self.bt_vf = QLineEdit("1.0"); grid_pwr.addWidget(QLabel("二极管压降 Vf [V]:"), 0, 2); grid_pwr.addWidget(self.bt_vf, 0, 3)
        grp_pwr.setLayout(grid_pwr)
        layout.addWidget(grp_pwr)
        
        btn = QPushButton("计算自举元件 (C_boot & R_boot)")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.setStyleSheet("background-color: #3498db; color: white;")
        btn.clicked.connect(self.calc_bootstrap)
        layout.addWidget(btn)
        
        grp_res = QGroupBox("3. 选型结果")
        res_grid = QGridLayout()
        res_grid.setVerticalSpacing(15)
        res_grid.setColumnStretch(1, 1)
        
        self.bt_c_min = QLineEdit()
        self.bt_c_rec = QLineEdit()
        self.bt_r_max = QLineEdit()
        self.bt_i_inrush = QLineEdit()
        
        res_grid.addWidget(QLabel("最小自举电容 (C_boot_min):"), 0, 0); res_grid.addWidget(self.bt_c_min, 0, 1)
        l_cboot = QLabel(); l_cboot.setPixmap(render_formula(r'C_{boot} \geq \frac{Q_g + I_{leak} T_{on} + Q_{rr}}{\Delta V_{boot}}'))
        res_grid.addWidget(l_cboot, 0, 2)
        
        res_grid.addWidget(QLabel("推荐选型值 (C_boot):"), 1, 0); res_grid.addWidget(self.bt_c_rec, 1, 1)
        res_grid.addWidget(QLabel("通常取计算值的 10~20 倍"), 1, 2)
        
        res_grid.addWidget(QLabel("最大自举电阻 (R_boot_max):"), 2, 0); res_grid.addWidget(self.bt_r_max, 2, 1)
        l_rboot = QLabel(); l_rboot.setPixmap(render_formula(r'R_{boot} < \frac{T_{off\_min}}{3 \cdot C_{boot}}'))
        res_grid.addWidget(l_rboot, 2, 2)
        
        res_grid.addWidget(QLabel("充电冲击电流 (I_inrush):"), 3, 0); res_grid.addWidget(self.bt_i_inrush, 3, 1)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        self.bt_c_min.setReadOnly(True); self.bt_c_min.setStyleSheet(style_res)
        self.bt_c_rec.setReadOnly(True); self.bt_c_rec.setStyleSheet(style_res)
        self.bt_r_max.setReadOnly(True); self.bt_r_max.setStyleSheet(style_res)
        self.bt_i_inrush.setReadOnly(True); self.bt_i_inrush.setStyleSheet(style_res)
        
        grp_res.setLayout(res_grid)
        layout.addWidget(grp_res)
        layout.addStretch()
        self.setLayout(layout)

    def calc_bootstrap(self):
        try:
            qg = float(self.bt_qg.text()) * 1e-9
            fsw = float(self.bt_fsw.text()) * 1e3
            duty = float(self.bt_duty.text()) / 100.0
            iq = float(self.bt_iq.text()) * 1e-6
            qrr = float(self.bt_qrr.text()) * 1e-9
            vdrop = float(self.bt_vdrop.text())
            vcc = float(self.bt_vcc.text())
            vf = float(self.bt_vf.text())
            
            if vdrop <= 0 or fsw <= 0: raise ValueError
            
            t_on_max = duty / fsw
            q_leak = iq * t_on_max
            q_total = qg + q_leak + qrr
            
            c_min = q_total / vdrop
            c_rec = c_min * 10
            
            t_off_min = (1 - duty) / fsw
            if t_off_min <= 0: t_off_min = 1e-9
            r_max = t_off_min / (3 * c_rec)
            
            r_typ = 2.2
            i_peak = (vcc - vf) / r_typ
            
            self.bt_c_min.setText(f"{c_min*1e6:.3f} uF")
            self.bt_c_rec.setText(f"{c_rec*1e6:.3f} uF")
            self.bt_r_max.setText(f"< {r_max:.2f} Ω")
            self.bt_i_inrush.setText(f"Peak ~ {i_peak:.1f} A")
            
            if r_max < 1.0:
                self.bt_r_max.setStyleSheet("background-color: #ffcdd2; font-weight: bold; color: #c62828;")
            else:
                self.bt_r_max.setStyleSheet("background-color: #fff8e1; font-weight: bold; color: #d35400;")
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入无效")

# ==============================================================================
# 4. GDT Design (Gate Drive Transformer)
# ==============================================================================
class GdtDesignTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Drive Signal
        grp_drive = QGroupBox("1. 驱动信号参数 (Drive Signal)")
        g_drive = QGridLayout()
        g_drive.setVerticalSpacing(12)
        
        self.gdt_vcc = QLineEdit("15"); g_drive.addWidget(QLabel("驱动电压 V_drive [V]:"), 0, 0); g_drive.addWidget(self.gdt_vcc, 0, 1)
        self.gdt_fsw = QLineEdit("100"); g_drive.addWidget(QLabel("开关频率 f_sw [kHz]:"), 0, 2); g_drive.addWidget(self.gdt_fsw, 0, 3)
        self.gdt_duty = QLineEdit("0.45"); 
        self.gdt_duty.setToolTip("最大占空比。对于半桥/全桥通常 < 0.5。")
        g_drive.addWidget(QLabel("最大占空比 D_max:"), 1, 0); g_drive.addWidget(self.gdt_duty, 1, 1)
        
        grp_drive.setLayout(g_drive)
        layout.addWidget(grp_drive)
        
        # 2. Transformer Specs
        grp_core = QGroupBox("2. 变压器/磁芯参数 (GDT Specs)")
        g_core = QGridLayout()
        g_core.setVerticalSpacing(12)
        
        self.gdt_ae = QLineEdit("10"); self.gdt_ae.setToolTip("磁芯有效截面积。例如 EE13 约 17mm2，T10x6x5 环形约 10mm2。")
        g_core.addWidget(QLabel("磁芯截面积 Ae [mm²]:"), 0, 0); g_core.addWidget(self.gdt_ae, 0, 1)
        
        self.gdt_bsat = QLineEdit("0.3"); self.gdt_bsat.setToolTip("饱和磁通密度。铁氧体通常 0.3T ~ 0.4T。")
        g_core.addWidget(QLabel("饱和磁密 B_sat [T]:"), 0, 2); g_core.addWidget(self.gdt_bsat, 0, 3)
        
        self.gdt_np = QLineEdit("20"); g_core.addWidget(QLabel("原边匝数 Np [Ts]:"), 1, 0); g_core.addWidget(self.gdt_np, 1, 1)
        
        self.gdt_al = QLineEdit("2000"); self.gdt_al.setToolTip("电感系数 AL 值，单位 nH/N^2。高导磁率环形磁芯通常很高 (2000+)。")
        g_core.addWidget(QLabel("AL 值 [nH/N²]:"), 1, 2); g_core.addWidget(self.gdt_al, 1, 3)
        
        grp_core.setLayout(g_core)
        layout.addWidget(grp_core)
        
        btn = QPushButton("计算伏秒积与饱和裕量")
        btn.setFixedHeight(45)
        btn.setFont(QFont('Arial', 11, QFont.Bold))
        btn.setStyleSheet("background-color: #3498db; color: white;")
        btn.clicked.connect(self.calc_gdt)
        layout.addWidget(btn)
        
        # 3. Results
        grp_res = QGroupBox("3. 评估结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        r_grid.setColumnStretch(1, 1)
        
        self.res_et = QLineEdit()
        self.res_b_peak = QLineEdit()
        self.res_imag = QLineEdit()
        self.res_status = QLineEdit()
        
        # ET Product
        r_grid.addWidget(QLabel("所需伏秒积 (ET Product):"), 0, 0); r_grid.addWidget(self.res_et, 0, 1)
        l_et = QLabel(); l_et.setPixmap(render_formula(r'ET = V_{drv} \cdot T_{on} \quad [V \cdot \mu s]'))
        r_grid.addWidget(l_et, 0, 2)
        
        # Flux Density
        r_grid.addWidget(QLabel("工作磁密 B_peak:"), 1, 0); r_grid.addWidget(self.res_b_peak, 1, 1)
        l_b = QLabel(); l_b.setPixmap(render_formula(r'B_{peak} = \frac{ET}{N_p \cdot A_e} \quad [T]'))
        r_grid.addWidget(l_b, 1, 2)
        
        # Magnetizing Current
        r_grid.addWidget(QLabel("励磁电流峰值 I_mag_pk:"), 2, 0); r_grid.addWidget(self.res_imag, 2, 1)
        l_imag = QLabel(); l_imag.setPixmap(render_formula(r'I_{mag} = \frac{ET}{L_m} = \frac{V \cdot T_{on}}{A_L \cdot N^2}'))
        r_grid.addWidget(l_imag, 2, 2)
        
        # Status
        r_grid.addWidget(QLabel("饱和风险评估:"), 3, 0); r_grid.addWidget(self.res_status, 3, 1)
        
        style_res = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
        for w in [self.res_et, self.res_b_peak, self.res_imag]:
            w.setReadOnly(True); w.setStyleSheet(style_res)
        self.res_status.setReadOnly(True)
        
        grp_res.setLayout(r_grid)
        layout.addWidget(grp_res)
        
        # Tips
        tip = QLabel("设计提示：\n1. 必须保证 B_peak < B_sat (建议留 30% 裕量，即 < 0.2T~0.25T)。\n2. 励磁电流 I_mag 不宜过大，否则会增加驱动芯片负担并导致发热。通常控制在 50mA~100mA 以内。")
        tip.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(tip)
        
        layout.addStretch()
        self.setLayout(layout)

    def calc_gdt(self):
        try:
            v_drv = float(self.gdt_vcc.text())
            f_khz = float(self.gdt_fsw.text())
            d_max = float(self.gdt_duty.text())
            
            ae = float(self.gdt_ae.text())
            bsat = float(self.gdt_bsat.text())
            np = float(self.gdt_np.text())
            al_val = float(self.gdt_al.text()) # nH/N2
            
            if f_khz <= 0 or ae <= 0 or np <= 0 or al_val <= 0: raise ValueError
            
            # 1. Ton & ET
            t_on_us = (d_max / (f_khz * 1000)) * 1e6
            et_product = v_drv * t_on_us # V*us
            
            # 2. B_peak
            # B = ET / (N * Ae). If ET in V*us, Ae in mm2, result in Tesla.
            b_peak = et_product / (np * ae)
            
            # 3. Imag
            # Lm = AL * N^2 (nH)
            lm_nh = al_val * (np ** 2)
            lm_uh = lm_nh / 1000.0
            # Imag = V * Ton / Lm = ET(V*us) / Lm(uH)  -> Amps
            i_mag = et_product / lm_uh
            
            self.res_et.setText(f"{et_product:.2f} V·µs")
            self.res_b_peak.setText(f"{b_peak:.3f} T")
            self.res_imag.setText(f"{i_mag*1000:.1f} mA")
            
            # Check
            limit = bsat * 0.8
            if b_peak > bsat:
                self.res_status.setText(f"严重饱和！(> {bsat}T)")
                self.res_status.setStyleSheet("background-color: #ffcdd2; color: #c62828; font-weight: bold;")
            elif b_peak > limit:
                self.res_status.setText(f"风险 (裕量不足 < 20%)")
                self.res_status.setStyleSheet("background-color: #fff9c4; color: #fbc02d; font-weight: bold;")
            else:
                self.res_status.setText(f"安全 (裕量充足)")
                self.res_status.setStyleSheet("background-color: #c8e6c9; color: #2e7d32; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")
