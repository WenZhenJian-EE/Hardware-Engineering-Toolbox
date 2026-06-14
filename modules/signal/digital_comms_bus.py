from modules.base_module import BaseModule
# digital_comms_bus.py

import math
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QGridLayout, QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt

class DigitalBusWindow(BaseModule):
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "总线电缆与接口"
    description = "I2C 匹配 / RS-485与CAN 终端"
    window_id = "digital_bus"

    def init_module_ui(self):
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('数字通信与总线计算器 (Digital Bus & Comms)')
        self.setGeometry(350, 350, 850, 600)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e4e8; background: #fff; border-radius: 6px; }
            QTabBar::tab { background: #f4f6f9; border: 1px solid #e1e4e8; padding: 10px 20px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #ffffff; border-bottom-color: #ffffff; font-weight: bold; color: #3498db; }
        """)

        self.tab_i2c = QWidget()
        self.tab_485 = QWidget()
        
        self.init_i2c_ui(self.tab_i2c)
        self.init_485_ui(self.tab_485)
        
        self.tabs.addTab(self.tab_i2c, "I2C 上拉电阻匹配 (I2C Pull-up)")
        self.tabs.addTab(self.tab_485, "RS-485 / CAN 终端匹配 (Bus Termination & Failsafe)")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    # =========================================================================
    # Tab 1: I2C Pull-up Calculator
    # =========================================================================
    def init_i2c_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("<b>设计场景：</b> I2C 是开漏 (Open-Drain) 总线，须接上拉电阻。<br>"
                      "• <b>阻值太小：</b> 灌入 MCU 引脚的电流过大（超 3mA），导致输出低电平 $V_{OL}$ 抬高，无法被识别为逻辑零。<br>"
                      "• <b>阻值太大：</b> 寄生电容 $C_b$ 导致上升时间 $t_r$ 过长，波形变梯形，无法满足时序要求。")
        info.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(info)
        
        grp_in = QGroupBox("输入参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.i2c_vcc = QLineEdit("3.3"); grid.addWidget(QLabel("总线电压 Vcc [V]:"), 0, 0); grid.addWidget(self.i2c_vcc, 0, 1)
        self.i2c_vol = QLineEdit("0.4"); grid.addWidget(QLabel("最大低电平输出 Vol [V]:"), 0, 2); grid.addWidget(self.i2c_vol, 0, 3)
        self.i2c_iol = QLineEdit("3.0"); grid.addWidget(QLabel("最大灌电流 Iol [mA]:"), 1, 0); grid.addWidget(self.i2c_iol, 1, 1)
        self.i2c_cb = QLineEdit("100"); grid.addWidget(QLabel("总线等效寄生电容 Cb [pF]:"), 1, 2); grid.addWidget(self.i2c_cb, 1, 3)
        self.i2c_tr = QLineEdit("1000"); grid.addWidget(QLabel("允许的最大上升时间 tr [ns]:"), 2, 0); grid.addWidget(self.i2c_tr, 2, 1)
        
        btn = QPushButton("计算上拉电阻合理区间")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_i2c)
        grid.addWidget(btn, 3, 0, 1, 4)
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)

        grp_out = QGroupBox("推荐结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.i2c_rmin = QLineEdit()
        self.i2c_rmax = QLineEdit()
        self.i2c_status = QLabel("等待计算...")
        
        for w in [self.i2c_rmin, self.i2c_rmax]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #27ae60;")
            
        r_grid.addWidget(QLabel("最小安全电阻 R_min [kΩ]:"), 0, 0); r_grid.addWidget(self.i2c_rmin, 0, 1)
        r_grid.addWidget(QLabel("最大允许电阻 R_max [kΩ]:"), 1, 0); r_grid.addWidget(self.i2c_rmax, 1, 1)
        r_grid.addWidget(self.i2c_status, 2, 0, 1, 2)
        
        warn_lbl = QLabel("注：标准模式(100kHz) tr<1000ns；快速模式(400kHz) tr<300ns。<br>R_min = (Vcc-Vol)/Iol, R_max = tr / (0.8473 * Cb)")
        warn_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        r_grid.addWidget(warn_lbl, 3, 0, 1, 2)
        
        grp_out.setLayout(r_grid)
        layout.addWidget(grp_out)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_i2c(self):
        try:
            vcc = float(self.i2c_vcc.text())
            vol = float(self.i2c_vol.text())
            iol = float(self.i2c_iol.text()) * 1e-3 # A
            cb = float(self.i2c_cb.text()) * 1e-12 # F
            tr = float(self.i2c_tr.text()) * 1e-9 # s
            
            rmin = (vcc - vol) / iol
            # Time constant calculation for standard CMOS limits (0.3Vcc to 0.7Vcc)
            rmax = tr / (0.8473 * cb)
            
            self.i2c_rmin.setText(f"{rmin/1000:.3f}")
            self.i2c_rmax.setText(f"{rmax/1000:.3f}")
            
            if rmin > rmax:
                self.i2c_status.setText("警告：寄生电容过大，无法在不超过灌电流限制下满足上升时间！请降低总线速度或使用I2C缓冲器(Buffer)。")
                self.i2c_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                self.i2c_status.setText("评估：可行。请在 R_min 和 R_max 之间选取常用标准电阻 (如 4.7kΩ 或 10kΩ)")
                self.i2c_status.setStyleSheet("color: #27ae60; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.warning(self, "输入错误", "请检查输入数值")

    # =========================================================================
    # Tab 2: RS-485 / CAN Termination
    # =========================================================================
    def init_485_ui(self, tab):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        info = QLabel("<b>设计场景：</b> 长线通信 (RS-485/CAN) 需要在总线两端(首尾节点)并联终端电阻($R_T$)以消除信号反射。<br>"
                      "<b>失效保护 (Fail-safe)：</b> 当所有节点不发送数据(空闲)或断线时，由于终端电阻下拉，A、B端电压差变为0。某些接收器会误判或产生干扰噪声。<br>"
                      "方案：在总线<b>某一端</b>加入上/下拉偏置电阻(Bias/Failsafe Resistor)，强制产生 >200mV (RS485) 的空闲电压。")
        info.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        grp_in = QGroupBox("输入参数")
        grid = QGridLayout()
        grid.setVerticalSpacing(12)
        
        self.bus_vcc = QLineEdit("5.0"); grid.addWidget(QLabel("总线供电 Vcc [V]:"), 0, 0); grid.addWidget(self.bus_vcc, 0, 1)
        self.bus_z0 = QLineEdit("120"); grid.addWidget(QLabel("线缆特征阻抗 Z0 [Ω]:"), 0, 2); grid.addWidget(self.bus_z0, 0, 3)
        self.bus_vab = QLineEdit("0.25"); grid.addWidget(QLabel("期望空闲电压 V_AB [V]:"), 1, 0); grid.addWidget(self.bus_vab, 1, 1)
        self.bus_nodes = QLineEdit("32"); grid.addWidget(QLabel("节点数量 N [个]:"), 1, 2); grid.addWidget(self.bus_nodes, 1, 3)
        
        btn = QPushButton("计算终端与失效保护偏置")
        btn.setFixedHeight(45)
        btn.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold;")
        btn.clicked.connect(self.calc_485)
        grid.addWidget(btn, 2, 0, 1, 4)
        grp_in.setLayout(grid)
        layout.addWidget(grp_in)

        grp_out = QGroupBox("推荐参数结果")
        r_grid = QGridLayout()
        r_grid.setVerticalSpacing(15)
        
        self.out_rt = QLineEdit()
        self.out_rs_failsafe = QLineEdit()
        
        for w in [self.out_rt, self.out_rs_failsafe]:
            w.setReadOnly(True)
            w.setStyleSheet("background-color: #f4ecf7; font-weight: bold; color: #8e44ad;")
            
        r_grid.addWidget(QLabel("标准并联终端电阻 R_T (首尾各一个) [Ω]:"), 0, 0); r_grid.addWidget(self.out_rt, 0, 1)
        r_grid.addWidget(QLabel("上下拉偏置电阻 R_bias (A拉Vcc, B拉GND) [Ω]:"), 1, 0); r_grid.addWidget(self.out_rs_failsafe, 1, 1)
        
        warn_lbl = QLabel("注：RS-485接收阈值通常为 ±200mV，因此空闲时 V_A - V_B 至少应为 200mV (如输入250mV)。<br>"
                          "该计算基于 1/8 单位负载 (12kΩ) 的常见收发器。偏置电阻全总线加一处即可。")
        warn_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        r_grid.addWidget(warn_lbl, 2, 0, 1, 2)
        
        grp_out.setLayout(r_grid)
        layout.addWidget(grp_out)
        layout.addStretch()
        tab.setLayout(layout)

    def calc_485(self):
        try:
            vcc = float(self.bus_vcc.text())
            z0 = float(self.bus_z0.text())
            vab_target = float(self.bus_vab.text())
            nodes = float(self.bus_nodes.text())
            
            # 标准匹配
            self.out_rt.setText(f"{z0:.1f} (或根据实际线型选择 100~120Ω)")
            
            # 等效负载计算
            # 两个终端并联 (120 || 120 = 60)
            rt_eq = z0 / 2.0 
            # 接收器输入阻抗推算，假设普遍 1/8 UI (12k Ohm)
            rin_node = 12000.0
            r_nodes_eq = rin_node / nodes
            
            # 整个总线的总并联阻抗 (RT首 || RT尾 || 所有接收节点)
            r_bus_eq = (rt_eq * r_nodes_eq) / (rt_eq + r_nodes_eq)
            
            # 需要两个对称的 R_bias 将 A 拉到 VCC，B 拉到 GND。
            # 分压公式：V_AB = VCC * R_bus_eq / (2 * R_bias + R_bus_eq)
            # 换算 Rbias:
            if vcc <= vab_target:
                raise ValueError("目标偏置电压不能大于 Vcc")
                
            r_bias = (r_bus_eq * (vcc - vab_target)) / (2 * vab_target)
            
            self.out_rs_failsafe.setText(f"{r_bias:.1f} (请在一处主机节点将A加上拉，B加下拉)")
            
        except Exception as e:
            QMessageBox.warning(self, "输入错误", str(e))
