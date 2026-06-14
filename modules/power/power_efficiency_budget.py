from modules.base_module import BaseModule
# power_efficiency_budget.py

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from io import BytesIO

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QGridLayout, QGroupBox, QDialog, QTextBrowser,
                             QScrollArea, QFrame, QMessageBox) # 修复：添加 QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

class EfficiencyBudgetWindow(BaseModule):
    category = "2. 功率器件与能源 (Devices, Battery & Thermal)"
    display_name = "效率损耗预算"
    description = "MOS/磁芯/电容损耗汇总"
    window_id = "power_budget"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('电源效率损耗预算工具 (Efficiency Budgeting)')
        self.setGeometry(350, 350, 1000, 800)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 顶部栏
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.help_btn = QPushButton("使用说明")
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setFixedWidth(150)
        self.help_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 4px; padding: 6px;")
        self.help_btn.clicked.connect(self.show_tutorial)
        top_bar.addWidget(self.help_btn)
        main_layout.addLayout(top_bar)

        # 滚动区域 (防止屏幕小显示不全)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # 1. 系统规格
        grp_sys = QGroupBox("1. 系统规格 (System Specifications)")
        grid_sys = QGridLayout()
        grid_sys.setVerticalSpacing(12)
        
        self.eff_vin = QLineEdit("48"); grid_sys.addWidget(QLabel("输入电压 Vin [V]:"), 0, 0); grid_sys.addWidget(self.eff_vin, 0, 1)
        self.eff_vout = QLineEdit("12"); grid_sys.addWidget(QLabel("输出电压 Vout [V]:"), 0, 2); grid_sys.addWidget(self.eff_vout, 0, 3)
        self.eff_iout = QLineEdit("10"); grid_sys.addWidget(QLabel("输出电流 Iout [A]:"), 1, 0); grid_sys.addWidget(self.eff_iout, 1, 1)
        
        # 自动计算 Pout
        self.lbl_pout = QLabel("输出功率 Pout: 0.0 W")
        self.lbl_pout.setStyleSheet("color: #2980b9; font-weight: bold;")
        grid_sys.addWidget(self.lbl_pout, 1, 2, 1, 2)
        
        grp_sys.setLayout(grid_sys)
        layout.addWidget(grp_sys)

        # 2. 损耗明细 (手动输入)
        grp_loss = QGroupBox("2. 损耗明细 (Loss Breakdown - Manual Input)")
        grid_loss = QGridLayout()
        grid_loss.setVerticalSpacing(10)
        
        self.loss_sw = QLineEdit("2.5"); self.loss_sw.setPlaceholderText("MOS/IGBT 导通+开关")
        grid_loss.addWidget(QLabel("开关器件损耗 (Switching Device) [W]:"), 0, 0); grid_loss.addWidget(self.loss_sw, 0, 1)
        
        self.loss_mag = QLineEdit("1.2"); self.loss_mag.setPlaceholderText("电感/变压器 铜损+铁损")
        grid_loss.addWidget(QLabel("磁性元件损耗 (Magnetics) [W]:"), 0, 2); grid_loss.addWidget(self.loss_mag, 0, 3)
        
        self.loss_rect = QLineEdit("0.8"); self.loss_rect.setPlaceholderText("二极管/SR")
        grid_loss.addWidget(QLabel("整流损耗 (Rectifier/Diode) [W]:"), 1, 0); grid_loss.addWidget(self.loss_rect, 1, 1)
        
        self.loss_cap = QLineEdit("0.3"); self.loss_cap.setPlaceholderText("输入+输出电容 ESR")
        grid_loss.addWidget(QLabel("电容损耗 (Capacitor ESR) [W]:"), 1, 2); grid_loss.addWidget(self.loss_cap, 1, 3)
        
        self.loss_ctrl = QLineEdit("0.5"); self.loss_ctrl.setPlaceholderText("IC, LDO, Fan, Gate Drive")
        grid_loss.addWidget(QLabel("控制与驱动损耗 (Control/Drive) [W]:"), 2, 0); grid_loss.addWidget(self.loss_ctrl, 2, 1)
        
        self.loss_misc = QLineEdit("0.2"); self.loss_misc.setPlaceholderText("PCB走线, 采样电阻, 连接器")
        grid_loss.addWidget(QLabel("其他杂散损耗 (Misc/PCB) [W]:"), 2, 2); grid_loss.addWidget(self.loss_misc, 2, 3)
        
        grp_loss.setLayout(grid_loss)
        layout.addWidget(grp_loss)
        
        # 计算按钮
        btn_calc = QPushButton("计算总效率与损耗分布")
        btn_calc.setFixedHeight(50)
        btn_calc.setFont(QFont('Arial', 12, QFont.Bold))
        btn_calc.setStyleSheet("background-color: #3498db; color: white; border-radius: 6px;")
        btn_calc.clicked.connect(self.calc_efficiency)
        layout.addWidget(btn_calc)
        
        # 3. 结果显示
        grp_res = QGroupBox("3. 效率报告 (Report)")
        hbox_res = QHBoxLayout()
        
        # 左侧：数值结果
        grid_res = QGridLayout()
        self.res_ptot = QLineEdit(); self.res_ptot.setReadOnly(True)
        self.res_pin = QLineEdit(); self.res_pin.setReadOnly(True)
        self.res_eff = QLineEdit(); self.res_eff.setReadOnly(True)
        
        style_key = "font-size: 18px; font-weight: bold; color: #27ae60; background-color: #e8f8f5;"
        self.res_eff.setStyleSheet(style_key)
        
        grid_res.addWidget(QLabel("总损耗 P_loss [W]:"), 0, 0); grid_res.addWidget(self.res_ptot, 0, 1)
        grid_res.addWidget(QLabel("输入功率 P_in [W]:"), 1, 0); grid_res.addWidget(self.res_pin, 1, 1)
        grid_res.addWidget(QLabel("整机效率 Efficiency [%]:"), 2, 0); grid_res.addWidget(self.res_eff, 2, 1)
        
        hbox_res.addLayout(grid_res, 1)
        
        # 右侧：图表占位
        self.chart_label = QLabel("Chart Area")
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setStyleSheet("border: 1px dashed #ccc; background: white;")
        self.chart_label.setMinimumSize(400, 300)
        hbox_res.addWidget(self.chart_label, 2)
        
        grp_res.setLayout(hbox_res)
        layout.addWidget(grp_res)
        
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
        
        # 初始运行一次
        self.calc_efficiency()

    def calc_efficiency(self):
        try:
            # System
            vout = float(self.eff_vout.text())
            iout = float(self.eff_iout.text())
            pout = vout * iout
            self.lbl_pout.setText(f"输出功率 Pout: {pout:.2f} W")
            
            # Losses
            def get_val(w):
                txt = w.text()
                return float(txt) if txt else 0.0
            
            l_sw = get_val(self.loss_sw)
            l_mag = get_val(self.loss_mag)
            l_rect = get_val(self.loss_rect)
            l_cap = get_val(self.loss_cap)
            l_ctrl = get_val(self.loss_ctrl)
            l_misc = get_val(self.loss_misc)
            
            p_loss_total = l_sw + l_mag + l_rect + l_cap + l_ctrl + l_misc
            p_in = pout + p_loss_total
            
            if p_in <= 0:
                eff = 0
            else:
                eff = (pout / p_in) * 100.0
            
            self.res_ptot.setText(f"{p_loss_total:.3f} W")
            self.res_pin.setText(f"{p_in:.3f} W")
            self.res_eff.setText(f"{eff:.2f} %")
            
            # Update Chart
            self.plot_pie_chart([l_sw, l_mag, l_rect, l_cap, l_ctrl, l_misc])
            
        except Exception as e:
            QMessageBox.warning(self, "错误", "输入数值无效")

    def plot_pie_chart(self, losses):
        labels = ['Switching', 'Magnetics', 'Rectifier', 'Capacitor', 'Control', 'Misc']
        # Filter out zero losses
        data = []
        lbls = []
        for v, l in zip(losses, labels):
            if v > 0:
                data.append(v)
                lbls.append(l)
        
        if not data:
            self.chart_label.setText("无损耗数据")
            return

        try:
            plt.rcParams.update({'font.size': 9})
            fig = plt.figure(figsize=(5, 3.5), dpi=100)
            ax = fig.add_subplot(111)
            
            wedges, texts, autotexts = ax.pie(data, labels=lbls, autopct='%1.1f%%', 
                                              startangle=90, pctdistance=0.85,
                                              colors=['#3498db', '#e74c3c', '#f1c40f', '#9b59b6', '#34495e', '#95a5a6'])
            
            # Draw circle for Donut chart style
            centre_circle = plt.Circle((0,0),0.70,fc='white')
            fig.gca().add_artist(centre_circle)
            
            ax.axis('equal')  
            plt.tight_layout()
            
            # Render to QPixmap
            buf = BytesIO()
            fig.savefig(buf, format='png', transparent=True)
            plt.close(fig)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.chart_label.setPixmap(pixmap)
            
        except Exception as e:
            self.chart_label.setText(f"绘图错误: {str(e)}")

    def show_tutorial(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("效率预算使用说明")
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        text = QTextBrowser()
        text.setHtml("""
        <h2>效率预算 (Efficiency Budgeting)</h2>
        <p><b>用途：</b>在设计初期或评估阶段，汇总各部分估算的损耗，预测整机效率。</p>
        <p><b>数据来源：</b></p>
        <ul>
            <li><b>Switching Device:</b> 使用 <i>开关器件综合工具</i> 计算 MOS/IGBT 损耗。</li>
            <li><b>Magnetics:</b> 使用 <i>变压器/电感设计工具</i> 计算铜损和铁损。</li>
            <li><b>Rectifier:</b> 二极管导通压降 x 电流 + 反向恢复损耗。</li>
            <li><b>Capacitor:</b> 使用 <i>电容工具箱</i> 计算纹波电流引起的 I²R 损耗。</li>
        </ul>
        <p><b>提示：</b>不要忽略 "Control & Drive" 损耗，高频设计中 Gate 驱动功率 (Qg * Vg * f) 可能高达数瓦。</p>
        """)
        layout.addWidget(text)
        dialog.exec_()