from modules.base_module import BaseModule
# mag_transformer_loss.py
# (Re-factored Entry Point & Main Container)

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QDialog, QTextBrowser, QTabWidget)
from PyQt5.QtCore import Qt

# 导入拆分后的子模块
from mag_trans_topo import TopologyDesignPanel
from mag_trans_phys import PhysicsAnalysisPanel

class TransformerDesignWindow(BaseModule):
    category = "1. 磁性元件与电源拓扑 (Magnetics & Topology)"
    display_name = "变压器设计"
    description = "AP法 / 磁损 / 漏感 / 拓扑"
    window_id = "mag_transformer"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('变压器设计与磁性元件综合工具 (Transformer Design Studio)')
        self.setGeometry(350, 350, 1150, 850)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部教程按钮
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("设计教程 / 磁损拟合指南")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(280)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # 主 Tab：分为“拓扑设计”和“物理特性”两大类
        self.main_tabs = QTabWidget()
        
        # 【修改】移除了 min-width，让宽度自适应文字
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
                min-width: 250px;
            }
            QTabBar::tab:selected { 
                background: #ffffff; 
                border-bottom: 1px solid #ffffff; 
                font-weight: bold; 
                color: #3498db; 
            }
        """)

        # 加载子模块
        self.tab_topo = TopologyDesignPanel()
        self.tab_phys = PhysicsAnalysisPanel()

        self.main_tabs.addTab(self.tab_topo, "变压器拓扑设计 (Topology Design)")
        self.main_tabs.addTab(self.tab_phys, "物理特性与估算 (Physics Estimation)")

        main_layout.addWidget(self.main_tabs)
        self.setLayout(main_layout)

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("变压器设计指南 & 帮助 (Transformer Design Guide)")
        dialog.resize(900, 750)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setOpenExternalLinks(True)
        
        html = r"""
        <style>
            h3 { color: #2980b9; margin-top: 20px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }
            h4 { color: #c0392b; margin-top: 15px; }
            p { font-size: 14px; line-height: 1.6; color: #333; }
            li { font-size: 14px; margin-bottom: 5px; }
            .code-box { background-color: #f8f9fa; padding: 5px; border-left: 4px solid #3498db; border-radius: 4px; font-family: monospace; color: #2c3e50; font-weight: bold; }
            .note { background-color: #fff3cd; padding: 10px; border-radius: 4px; border-left: 5px solid #ffc107; margin: 10px 0; }
        </style>
        
        <h2>变压器设计与磁性元件指南</h2>
        
        <h3>1. AP法磁芯选型 (Area Product Method)</h3>
        <p><b>痛点：</b> 拿到功率需求，不知道该选多大的磁芯。</p>
        <p><b>原理：</b> 磁芯的功率承载能力与“窗口面积 Aw”和“截面积 Ae”的乘积成正比。</p>
        <div class="code-box">AP = Ae · Aw = Pout / (K · ΔB · f · J)</div>
        <ul>
            <li><b>K (拓扑系数)</b>: 反映不同拓扑对磁芯利用率的差异。反激利用率低(K小)，正激利用率高(K大)。</li>
        </ul>

        <h3>2. 绕组填充率校核 (Winding Fill Factor)</h3>
        <p><b>价值：</b> 计算得再好，绕不进骨架也是白搭。必须在设计阶段校核。</p>
        <ul>
            <li><b>填充率 (Fill Factor)：</b> 铜线总截面积 / 窗口面积。手工绕制通常很难超过 0.4 (40%)。</li>
            <li><b>堆叠高度 (Build)：</b> 必须小于窗口深度，建议留 10%~20% 余量。</li>
        </ul>

        <h3>3. 正激/反激设计 (Topology Design)</h3>
        <p><b>正激/全桥：</b> 能量由变压器直接传递。关键在于匝比设计和伏秒积平衡（避免饱和）。</p>
        <p><b>反激：</b> 变压器实质上是耦合电感。需设计气隙来存储能量。气隙越大，抗饱和能力越强，但漏感可能增加。</p>

        <h3>4. 磁芯损耗 (Core Loss)</h3>
        <p><b>B_ac 的定义：</b> 在磁芯损耗计算 (Steinmetz公式) 中，<b>B</b> 通常指<b>交流磁通密度的峰值 (Peak AC Flux Density)</b>。</p>
        <ul>
            <li><b>磁通摆幅 (ΔB)</b>: 磁芯在开关周期内磁通密度的总变化量。</li>
            <li><b>关系</b>: <span class="code-box">B_ac = ΔB / 2</span></li>
        </ul>
        <div class="note">
            <b>设计建议：</b> 
            通常建议将磁芯损耗密度 Pv 控制在 <b>100 ~ 300 mW/cm³</b> 之间。
        </div>

        <h3>5. 漏感估算 (Leakage Inductance)</h3>
        <p>漏感是变压器非理想耦合的体现，会引起电压尖峰。</p>
        <ul>
            <li><b>工程公式</b>: <span class="code-box">L_lk ≈ μ0 · N² · (MLT/bw) · (Σh/3 + Σδ)</span></li>
            <li><b>三明治绕法 (Sandwich)</b>（初级分两半夹次级）可将漏感降低至普通绕法的 1/4 左右。</li>
        </ul>

        <h3>6. 绕组 AC 损耗与邻近效应 (Proximity Effect)</h3>
        <p>在高频下，绕组损耗不仅仅是直流电阻 ($I^2 R_{dc}$)，更多来自于交流效应 ($I^2 R_{ac}$)。</p>
        <p><b>排线系数 ($\eta$)</b>: 绕组宽度方向的铜填充程度。$\eta = N \cdot d / W_{window}$。</p>
        <p><b>优化方法：</b> 减小单根线径 (利兹线) 或使用三明治绕法以减少有效层数。</p>

        <h3>7. Steinmetz 磁损系数拟合 (Curve Fitting)</h3>
        <p><b>应用场景：</b> 使用国产或新材料磁芯时，Datasheet 往往没有直接给出 Steinmetz 系数 ($k, \alpha, \beta$)，只有 $P_v - B$ 曲线图。</p>
        <p><b>使用方法：</b></p>
        <ol>
            <li>打开 Datasheet 的 Core Loss 曲线图。</li>
            <li>选取 3 个或更多的数据点。例如：
                <ul>
                    <li>点1: f=100kHz, B=100mT, Pv=...</li>
                    <li>点2: f=100kHz, B=200mT, Pv=... (同频率，不同磁密)</li>
                    <li>点3: f=200kHz, B=100mT, Pv=... (同磁密，不同频率)</li>
                </ul>
            </li>
            <li>将数据填入 <b>"Steinmetz 拟合"</b> Tab 的表格中。</li>
            <li>点击计算，工具会自动进行对数线性回归，解算出 $k, \alpha, \beta$。</li>
        </ol>
        <div class="note">
            <b>原理：</b> 公式 $P_v = k \cdot f^\alpha \cdot B^\beta$ 两边取对数变为 $\ln(P_v) = \ln(k) + \alpha \ln(f) + \beta \ln(B)$，这是一个标准的线性方程组，可用最小二乘法求解。
        </div>
        """
        text.setHtml(html)
        layout.addWidget(text)
        
        close_btn = QPushButton("关闭指南")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec_()

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = TransformerDesignWindow()
    window.show()
    sys.exit(app.exec_())