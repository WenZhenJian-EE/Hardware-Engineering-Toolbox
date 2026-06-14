import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, 
                             QLineEdit, QGroupBox, QComboBox)
from PyQt5.QtGui import QFont

class IICToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # --- IIC 地址转换 ---
        iic_group = QGroupBox("🔗 IIC 地址助手 (Address Helper)")
        iic_layout = QGridLayout()
        
        iic_layout.addWidget(QLabel("7-bit Addr (Hex):"), 0, 0)
        self.iic_7bit = QLineEdit("50")
        self.iic_7bit.setFont(QFont("Consolas", 10))
        self.iic_7bit.textChanged.connect(self.convert_iic_7to8)
        iic_layout.addWidget(self.iic_7bit, 0, 1)
        
        iic_layout.addWidget(QLabel("8-bit (Write/Read):"), 1, 0)
        self.iic_8bit_res = QLabel("0xA0 / 0xA1")
        self.iic_8bit_res.setStyleSheet("font-weight: bold; color: #dc3545; font-family: Consolas; font-size: 11pt;")
        iic_layout.addWidget(self.iic_8bit_res, 1, 1)
        
        iic_group.setLayout(iic_layout)
        layout.addWidget(iic_group)

        # --- EEPROM 智算 ---
        eeprom_group = QGroupBox("💾 EEPROM (AT24Cxx) 计算器")
        eeprom_layout = QGridLayout()

        eeprom_layout.addWidget(QLabel("EEPROM 型号:"), 0, 0)
        self.eeprom_type = QComboBox()
        self.eeprom_type.addItems(["AT24C02 (2k)", "AT24C04 (4k)", "AT24C08 (8k)", "AT24C16 (16k)"])
        self.eeprom_type.currentIndexChanged.connect(self.calc_eeprom)
        eeprom_layout.addWidget(self.eeprom_type, 0, 1)
        
        eeprom_layout.addWidget(QLabel("目标绝对地址(Hex):"), 1, 0)
        self.eeprom_addr = QLineEdit("1FF")
        self.eeprom_addr.setFont(QFont("Consolas", 10))
        self.eeprom_addr.textChanged.connect(self.calc_eeprom)
        eeprom_layout.addWidget(self.eeprom_addr, 1, 1)
        
        self.eeprom_res = QLabel("Dev=0xA2, Word=0xFF")
        self.eeprom_res.setStyleSheet("color: #28a745; font-family: Consolas; font-weight: bold; font-size: 11pt;")
        eeprom_layout.addWidget(self.eeprom_res, 2, 0, 1, 2)
        
        eeprom_group.setLayout(eeprom_layout)
        layout.addWidget(eeprom_group)
        
        layout.addStretch()
        self.convert_iic_7to8()
        self.calc_eeprom()

    def convert_iic_7to8(self):
        try:
            text = self.iic_7bit.text().replace("0x", "").strip()
            if not text: return
            addr7 = int(text, 16)
            
            write_addr = (addr7 << 1) & 0xFE
            read_addr = write_addr | 0x01
            
            self.iic_8bit_res.setText(f"Wr:0x{write_addr:02X} / Rd:0x{read_addr:02X}")
        except:
            self.iic_8bit_res.setText("Error")

    def calc_eeprom(self):
        try:
            text = self.eeprom_addr.text().replace("0x", "").strip()
            if not text: return
            addr = int(text, 16)
            
            chip_idx = self.eeprom_type.currentIndex() 
            base_dev = 0xA0
            
            if chip_idx == 0: # 2k
                page_mask = 0
            elif chip_idx == 1: # 4k
                page_mask = 0x1
            elif chip_idx == 2: # 8k
                page_mask = 0x3
            else: # 16k
                page_mask = 0x7
            
            page_val = (addr >> 8) & page_mask
            dev_addr = base_dev | (page_val << 1)
            word_addr = addr & 0xFF
            
            self.eeprom_res.setText(f"Dev=0x{dev_addr:02X}, Word=0x{word_addr:02X}")
        except:
            self.eeprom_res.setText("Error")