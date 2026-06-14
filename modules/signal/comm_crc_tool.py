import struct
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QGroupBox, QComboBox, 
                             QLineEdit, QRadioButton, QButtonGroup, QGridLayout)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class CRCToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        
        # --- 1. 输入区 ---
        input_group = QGroupBox("📝 数据输入 (Hex Input)")
        input_layout = QVBoxLayout()
        
        self.data_input = QTextEdit()
        self.data_input.setPlaceholderText("请输入 Hex 数据，例如: 01 03 00 00 00 02 (Modbus 读保持寄存器)")
        self.data_input.setFont(QFont("Consolas", 12))
        self.data_input.setMaximumHeight(100)
        
        input_layout.addWidget(self.data_input)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # --- 2. 算法选择与操作 ---
        algo_layout = QHBoxLayout()
        
        algo_layout.addWidget(QLabel("算法:"))
        self.combo_algo = QComboBox()
        self.combo_algo.addItems(["CRC-16 / MODBUS (工业通用)", "CRC-16 / CCITT-FALSE", "Checksum (Sum & 0xFF)"])
        algo_layout.addWidget(self.combo_algo)
        
        self.btn_calc = QPushButton("⚙️ 计算 CRC (Calculate)")
        self.btn_calc.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 6px;")
        self.btn_calc.clicked.connect(self.calculate_crc)
        algo_layout.addWidget(self.btn_calc)
        
        main_layout.addLayout(algo_layout)
        
        # --- 3. 结果显示 ---
        result_group = QGroupBox("✅ 计算结果 (Result)")
        result_layout = QGridLayout()
        
        # CRC High Byte / Low Byte
        self.res_hex = QLineEdit()
        self.res_hex.setReadOnly(True)
        self.res_hex.setStyleSheet("font-family: Consolas; font-size: 14pt; color: #dc3545; font-weight: bold;")
        
        self.res_info = QLabel("等待计算...")
        self.res_info.setStyleSheet("color: #666;")
        
        # 完整指令预览
        self.full_frame = QTextEdit()
        self.full_frame.setReadOnly(True)
        self.full_frame.setMaximumHeight(60)
        self.full_frame.setStyleSheet("background-color: #f8f9fa; font-family: Consolas;")
        
        result_layout.addWidget(QLabel("校验码 (CRC):"), 0, 0)
        result_layout.addWidget(self.res_hex, 0, 1)
        result_layout.addWidget(self.res_info, 0, 2)
        
        result_layout.addWidget(QLabel("带校验完整帧:"), 1, 0)
        result_layout.addWidget(self.full_frame, 1, 1, 1, 2)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        # --- 知识库 ---
        note_label = QLabel(
            "📌 Modbus 提示: 所有的 Modbus RTU 设备都使用 'CRC-16 / MODBUS'。\n"
            "   多项式=0x8005, 初始值=0xFFFF, 结果低字节在前 (Little Endian)。\n"
            "   例如: 01 03 ... 校验码为 C4 0B，发送时发 C4 0B。"
        )
        note_label.setStyleSheet("color: #0056b3; font-size: 9pt;")
        main_layout.addWidget(note_label)
        
        main_layout.addStretch()

    def calculate_crc(self):
        # 1. 获取并清洗数据
        raw_text = self.data_input.toPlainText()
        hex_str = ''.join(raw_text.split()).replace('0x', '')
        
        try:
            data_bytes = bytes.fromhex(hex_str)
        except:
            self.res_info.setText("❌ 输入包含非法字符")
            return

        algo_idx = self.combo_algo.currentIndex()
        
        # 2. 计算
        if algo_idx == 0: # CRC-16 / MODBUS
            crc = self.crc16_modbus(data_bytes)
            # Modbus 发送时通常是低字节在前
            crc_bytes = struct.pack('<H', crc) 
            desc = f"0x{crc:04X} (Low Byte First)"
            
        elif algo_idx == 1: # CRC-16 / CCITT-FALSE
            crc = self.crc16_ccitt_false(data_bytes)
            crc_bytes = struct.pack('>H', crc) # 通常 Big Endian
            desc = f"0x{crc:04X} (Big Endian)"
            
        else: # Checksum
            checksum = sum(data_bytes) & 0xFF
            crc_bytes = struct.pack('B', checksum)
            desc = f"0x{checksum:02X} (Sum & 0xFF)"

        # 3. 显示
        self.res_hex.setText(' '.join([f"{b:02X}" for b in crc_bytes]))
        self.res_info.setText(desc)
        
        full_data = data_bytes + crc_bytes
        self.full_frame.setText(' '.join([f"{b:02X}" for b in full_data]))

    # --- 算法实现 ---
    def crc16_modbus(self, data: bytes) -> int:
        """ 标准 Modbus CRC16 实现 """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def crc16_ccitt_false(self, data: bytes) -> int:
        """ 常见于一些自定义协议 (Poly 0x1021, Init 0xFFFF) """
        crc = 0xFFFF
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
            crc &= 0xFFFF
        return crc