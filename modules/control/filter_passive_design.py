from modules.base_module import BaseModule
# filter_passive_design.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QDialog, QTextBrowser, QTabWidget)
from PyQt5.QtCore import Qt

# 导入所有子模块
try:
    from filter_tabs_basic import RcFilterTab, LcFilterTab, RlFilterTab
    from filter_tabs_active import ActiveFilterTab
    # 更新：引入了 InputFilterStabilityTab
    from filter_tabs_power import EmiFilterTab, CmcSaturationTab, SpwmFilterTab, FerriteBeadTab, InputFilterStabilityTab
    from filter_tabs_pdn import PdnAnalysisTab
except ImportError:
    pass

class FilterDesignWindow(BaseModule):
    category = "3. 环路控制与滤波 (Control & Filter)"
    display_name = "滤波器设计"
    description = "有源/无源/输入阻尼/PDN/EMI"
    window_id = "filter_passive"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('通用滤波器计算工具 (Filter Design)')
        self.setGeometry(350, 350, 1050, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- 顶部按钮 ---
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("滤波器设计基础 / 指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(240)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # --- 主 Tab 容器 (一级分类) ---
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

        # 实例化页面
        self.tab_signal_group = QWidget()
        self.tab_active_group = ActiveFilterTab()
        self.tab_power_group = QWidget()

        self.init_signal_group_ui()
        self.init_power_group_ui()

        # 添加到主 Tab
        self.main_tabs.addTab(self.tab_signal_group, "1. 基础无源滤波器 (RC/LC)")
        self.main_tabs.addTab(self.tab_active_group, "2. 有源滤波器设计 (Active Filter)")
        self.main_tabs.addTab(self.tab_power_group, "3. 电源与 EMI 滤波器 (Power & EMI)")

        main_layout.addWidget(self.main_tabs)
        self.setLayout(main_layout)

    def init_signal_group_ui(self):
        """初始化信号滤波器组"""
        layout = QVBoxLayout(self.tab_signal_group)
        layout.setContentsMargins(0, 10, 0, 0)
        
        sub_tabs = QTabWidget()
        if 'RcFilterTab' in globals(): sub_tabs.addTab(RcFilterTab(), "RC 滤波器 (一阶)")
        if 'LcFilterTab' in globals(): sub_tabs.addTab(LcFilterTab(), "LC 滤波器 (二阶)")
        if 'RlFilterTab' in globals(): sub_tabs.addTab(RlFilterTab(), "RL 滤波器 (一阶)")
        
        layout.addWidget(sub_tabs)

    def init_power_group_ui(self):
        """初始化电源滤波器组 (包含 PDN, EMI, CMC, Input Damping 等)"""
        layout = QVBoxLayout(self.tab_power_group)
        layout.setContentsMargins(0, 10, 0, 0)
        
        sub_tabs = QTabWidget()
        # 原有功能
        if 'EmiFilterTab' in globals(): sub_tabs.addTab(EmiFilterTab(), "EMI 滤波器 (共模/差模)")
        if 'CmcSaturationTab' in globals(): sub_tabs.addTab(CmcSaturationTab(), "共模电感饱和 (CMC Sat)")
        if 'SpwmFilterTab' in globals(): sub_tabs.addTab(SpwmFilterTab(), "SPWM 逆变滤波 (LCL/LC)")
        if 'FerriteBeadTab' in globals(): sub_tabs.addTab(FerriteBeadTab(), "磁珠选型 & 阻尼")
        
        # 新增功能在这里注册！
        if 'InputFilterStabilityTab' in globals(): sub_tabs.addTab(InputFilterStabilityTab(), "DC-DC 输入阻尼 (Input Stability)")
        
        if 'PdnAnalysisTab' in globals(): sub_tabs.addTab(PdnAnalysisTab(), "PDN 反谐振分析")
        
        layout.addWidget(sub_tabs)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("滤波器设计基础")
        dialog.resize(900, 750)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setStyleSheet("border: none; background-color: #f9f9f9; padding: 15px;")
        
        # 修复：使用 raw string (r"") 避免 LaTeX 中的反斜杠被转义警告
        html = r"""
        <style>
            h2 { color: #2980b9; border-bottom: 2px solid #2980b9; padding-bottom: 5px; }
            h3 { color: #d35400; margin-top: 15px; }
            li { margin-bottom: 5px; }
            .warn { color: #c0392b; font-weight: bold; }
            .box { background-color: #ecf0f1; padding: 10px; border-left: 5px solid #bdc3c7; }
        </style>
        
        <h1>滤波器设计速查</h1>
        
        <h2>1. DC-DC 输入滤波器阻尼 (Input Stability) [New]</h2>
        <div class="box">
            <b>Middlebrook 稳定性判据：</b> 开关电源对于输入侧来说是一个<b>恒功率负载 (负电阻特性)</b>。<br>
            如果前级 LC 滤波器的输出阻抗峰值 $Z_{out}$ 大于电源的输入阻抗绝对值 $|Z_{in}| = V_{in}^2 / P$，系统就会发生震荡。
        </div>
        <ul>
            <li><b>现象：</b> 电源输入电压出现持续的正弦波振荡，甚至导致电源保护或损坏。</li>
            <li><b>对策：</b> 在 LC 滤波器的电容上并联一个由 $R_d$ 和 $C_d$ 组成的阻尼网络。</li>
            <li><b>参数：</b> $R_d \approx Z_o = \sqrt{L/C}$，且 $C_d \ge 4 \times C$。</li>
        </ul>

        <hr>

        <h2>2. 有源滤波器 (Active Filter)</h2>
        <div class="box">
            <b>Sallen-Key:</b> 简单，高输入阻抗，适合通用设计。<br>
            <b>MFB (多重反馈):</b> 对元件不敏感，高频特性好，适合高 Q 值或高精度应用。
        </div>

        <h2>3. 共模电感饱和 (CMC Saturation)</h2>
        <p><b>痛点：</b> CMC 漏感虽然小 (1~2%)，但它承受全部的差模电流 (Idm)。<br>
        如果 Idm 很大，漏感产生的 B_leak 可能导致磁芯饱和，使 Lcm 瞬间归零，EMI 飙升。</p>

        <h2>4. PDN 反谐振</h2>
        <div class="warn">警告：电容并联可能导致阻抗升高！</div>
        <p>大电容(L)与小电容(C)在特定频率会发生并联谐振，阻抗极大。尽量利用 ESR 或错开频率来抑制。</p>
        """
        text.setHtml(html)
        layout.addWidget(text)
        dialog.exec_()