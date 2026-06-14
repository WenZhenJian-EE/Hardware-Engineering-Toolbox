import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QGroupBox, QComboBox, QGridLayout)
from PyQt5.QtGui import QFont

class SPIToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # --- 1. SPI 模式助手 ---
        spi_mode_group = QGroupBox("⏱️ SPI Mode 助手 (CPOL/CPHA)")
        spi_mode_layout = QVBoxLayout()
        
        self.spi_combo = QComboBox()
        self.spi_combo.addItems([
            "Mode 0 (CPOL=0, CPHA=0)", 
            "Mode 1 (CPOL=0, CPHA=1)", 
            "Mode 2 (CPOL=1, CPHA=0)", 
            "Mode 3 (CPOL=1, CPHA=1)"
        ])
        self.spi_combo.currentIndexChanged.connect(self.update_spi_info)
        
        self.spi_info_lbl = QLabel("空闲低电平, 上升沿采样")
        self.spi_info_lbl.setWordWrap(True)
        self.spi_info_lbl.setStyleSheet("color: #007bff; font-weight: bold; margin-top: 10px; font-size: 11pt;")
        
        spi_mode_layout.addWidget(self.spi_combo)
        spi_mode_layout.addWidget(self.spi_info_lbl)
        spi_mode_group.setLayout(spi_mode_layout)
        layout.addWidget(spi_mode_group)

        # --- 2. 地址拆分器 ---
        addr_group = QGroupBox("📂 地址拆分 (SPI-Flash Addr Splitter)")
        addr_layout = QGridLayout()
        addr_layout.addWidget(QLabel("Addr (Hex):"), 0, 0)
        self.addr_input = QLineEdit("123456")
        self.addr_input.setFont(QFont("Consolas", 10))
        self.addr_input.textChanged.connect(self.split_address)
        addr_layout.addWidget(self.addr_input, 0, 1)
        
        self.addr_res = QLabel("Bytes: [0x12, 0x34, 0x56]")
        self.addr_res.setStyleSheet("font-family: Consolas; color: #666; font-weight: bold;")
        addr_layout.addWidget(self.addr_res, 1, 0, 1, 2)
        
        addr_group.setLayout(addr_layout)
        layout.addWidget(addr_group)
        
        layout.addStretch()
        self.update_spi_info(0)

    def update_spi_info(self, index):
        infos = [
            "CLK空闲为低电平 (Low)\n在 第1个跳变沿 (上升沿) 采样数据",
            "CLK空闲为低电平 (Low)\n在 第2个跳变沿 (下降沿) 采样数据",
            "CLK空闲为高电平 (High)\n在 第1个跳变沿 (下降沿) 采样数据",
            "CLK空闲为高电平 (High)\n在 第2个跳变沿 (上升沿) 采样数据"
        ]
        self.spi_info_lbl.setText(infos[index])

    def split_address(self):
        try:
            text = self.addr_input.text().replace("0x", "").strip()
            if not text: return
            
            # 处理奇数长度
            if len(text) % 2 != 0:
                text = "0" + text
                
            byte_list = []
            for i in range(0, len(text), 2):
                byte_val = int(text[i:i+2], 16)
                byte_list.append(f"0x{byte_val:02X}")
                
            self.addr_res.setText(f"Bytes: [{', '.join(byte_list)}]")
        except:
            self.addr_res.setText("Bytes: [Error]")