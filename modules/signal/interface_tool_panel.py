import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGridLayout, QGroupBox, 
                             QComboBox, QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class InterfaceToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # --- 1. CAN ID 静态分析器 ---
        can_group = QGroupBox("📡 CAN ID 静态分析器 (J1939 & Custom)")
        can_layout = QGridLayout()
        
        can_layout.addWidget(QLabel("Hex ID:"), 0, 0)
        self.can_id_input = QLineEdit("18FF50E5")
        self.can_id_input.setFont(QFont("Consolas", 11))
        self.can_id_input.textChanged.connect(self.analyze_can_id)
        can_layout.addWidget(self.can_id_input, 0, 1)
        
        self.can_result = QTextEdit()
        self.can_result.setReadOnly(True)
        self.can_result.setMaximumHeight(100)
        self.can_result.setStyleSheet("background-color: #f0f4f7;")
        can_layout.addWidget(self.can_result, 1, 0, 1, 2)
        
        can_group.setLayout(can_layout)
        layout.addWidget(can_group)

        # --- 2. SPI 模式 & 地址拆分 ---
        spi_row = QHBoxLayout()
        
        # SPI 模式助手
        spi_mode_group = QGroupBox("⏱️ SPI Mode 助手")
        spi_mode_layout = QVBoxLayout()
        self.spi_combo = QComboBox()
        self.spi_combo.addItems(["Mode 0 (CPOL=0, CPHA=0)", "Mode 1 (CPOL=0, CPHA=1)", 
                                 "Mode 2 (CPOL=1, CPHA=0)", "Mode 3 (CPOL=1, CPHA=1)"])
        self.spi_combo.currentIndexChanged.connect(self.update_spi_info)
        self.spi_info_lbl = QLabel("空闲低电平, 上升沿采样")
        self.spi_info_lbl.setStyleSheet("color: #007bff; font-weight: bold;")
        spi_mode_layout.addWidget(self.spi_combo)
        spi_mode_layout.addWidget(self.spi_info_lbl)
        spi_mode_group.setLayout(spi_mode_layout)
        spi_row.addWidget(spi_mode_group)

        # 地址拆分器
        addr_group = QGroupBox("📂 地址拆分 (Flash/EEPROM)")
        addr_layout = QGridLayout()
        addr_layout.addWidget(QLabel("Addr:"), 0, 0)
        self.addr_input = QLineEdit("0x123456")
        self.addr_input.textChanged.connect(self.split_address)
        addr_layout.addWidget(self.addr_input, 0, 1)
        self.addr_res = QLabel("Bytes: [0x12, 0x34, 0x56]")
        addr_layout.addWidget(self.addr_res, 1, 0, 1, 2)
        addr_group.setLayout(addr_layout)
        spi_row.addWidget(addr_group)
        
        layout.addLayout(spi_row)

        # --- 3. IIC 助手 ---
        iic_group = QGroupBox("🔗 IIC 地址转换 & EEPROM 智算")
        iic_layout = QGridLayout()
        
        iic_layout.addWidget(QLabel("7-bit Addr:"), 0, 0)
        self.iic_7bit = QLineEdit("0x50")
        self.iic_7bit.textChanged.connect(self.convert_iic_7to8)
        iic_layout.addWidget(self.iic_7bit, 0, 1)
        
        iic_layout.addWidget(QLabel("8-bit (W/R):"), 0, 2)
        self.iic_8bit_res = QLabel("0xA0 / 0xA1")
        self.iic_8bit_res.setStyleSheet("font-weight: bold; color: #dc3545;")
        iic_layout.addWidget(self.iic_8bit_res, 0, 3)

        # EEPROM 智算
        iic_layout.addWidget(QLabel("EEPROM 型号:"), 1, 0)
        self.eeprom_type = QComboBox()
        self.eeprom_type.addItems(["AT24C02 (2k)", "AT24C04 (4k)", "AT24C08 (8k)", "AT24C16 (16k)"])
        self.eeprom_type.currentIndexChanged.connect(self.calc_eeprom)
        iic_layout.addWidget(self.eeprom_type, 1, 1)
        
        iic_layout.addWidget(QLabel("目标地址:"), 1, 2)
        self.eeprom_addr = QLineEdit("0x1FF")
        self.eeprom_addr.textChanged.connect(self.calc_eeprom)
        iic_layout.addWidget(self.eeprom_addr, 1, 3)
        
        self.eeprom_res = QLabel("Result: Device=0xA2, Word=0xFF")
        self.eeprom_res.setStyleSheet("color: #28a745; font-family: Consolas;")
        iic_layout.addWidget(self.eeprom_res, 2, 0, 1, 4)
        
        iic_group.setLayout(iic_layout)
        layout.addWidget(iic_group)
        
        layout.addStretch()
        self.analyze_can_id() # 初始执行

    def analyze_can_id(self):
        try:
            hex_str = self.can_id_input.text().replace("0x", "")
            can_id = int(hex_str, 16)
            res = []
            if can_id > 0x7FF:
                res.append("✨ 类型: 扩展帧 (29-bit Extended)")
                # J1939 解析
                priority = (can_id >> 26) & 0x7
                pgn = (can_id >> 8) & 0x3FFFF
                sa = can_id & 0xFF
                res.append(f"🚛 J1939: Priority={priority}, PGN={pgn} (0x{pgn:04X}), SA={sa} (0x{sa:02X})")
            else:
                res.append("✨ 类型: 标准帧 (11-bit Standard)")
            
            self.can_result.setText("\n".join(res))
        except: self.can_result.setText("等待有效输入...")

    def update_spi_info(self, index):
        infos = [
            "空闲低(CPOL=0), 上升沿采样(CPHA=0)",
            "空闲低(CPOL=0), 下降沿采样(CPHA=1)",
            "空闲高(CPOL=1), 下降沿采样(CPHA=0)",
            "空闲高(CPOL=1), 上升沿采样(CPHA=1)"
        ]
        self.spi_info_lbl.setText(infos[index])

    def split_address(self):
        try:
            addr = int(self.addr_input.text(), 16) if 'x' in self.addr_input.text() else int(self.addr_input.text())
            b1 = (addr >> 16) & 0xFF
            b2 = (addr >> 8) & 0xFF
            b3 = addr & 0xFF
            self.addr_res.setText(f"Bytes: [0x{b1:02X}, 0x{b2:02X}, 0x{b3:02X}]")
        except: pass

    def convert_iic_7to8(self):
        try:
            addr7 = int(self.iic_7bit.text(), 16) if 'x' in self.iic_7bit.text() else int(self.iic_7bit.text())
            self.iic_8bit_res.setText(f"0x{(addr7<<1):02X} / 0x{(addr7<<1)|1:02X}")
        except: pass

    def calc_eeprom(self):
        try:
            addr = int(self.eeprom_addr.text(), 16) if 'x' in self.eeprom_addr.text() else int(self.eeprom_addr.text())
            chip_idx = self.eeprom_type.currentIndex() # 0:2k, 1:4k, 2:8k, 3:16k
            
            base_dev = 0xA0
            if chip_idx == 0: # 2k
                dev, word = base_dev, addr & 0xFF
            else:
                # 4k以上页地址占用设备地址位
                page_bits = (addr >> 8) & 0x07
                dev, word = base_dev | (page_bits << 1), addr & 0xFF
            
            self.eeprom_res.setText(f"Result: Device=0x{dev:02X}, Word=0x{word:02X}")
        except: pass