import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QGridLayout, 
                             QGroupBox, QTextEdit)
from PyQt5.QtGui import QFont

class CANToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # --- CAN ID 静态分析器 ---
        can_group = QGroupBox("📡 CAN ID 静态分析器 (Static Analyzer)")
        can_layout = QGridLayout()
        
        can_layout.addWidget(QLabel("Hex ID:"), 0, 0)
        self.can_id_input = QLineEdit("18FF50E5")
        self.can_id_input.setFont(QFont("Consolas", 11))
        self.can_id_input.setPlaceholderText("例如: 18FF50E5")
        self.can_id_input.textChanged.connect(self.analyze_can_id)
        can_layout.addWidget(self.can_id_input, 0, 1)
        
        self.can_result = QTextEdit()
        self.can_result.setReadOnly(True)
        self.can_result.setMaximumHeight(150) # 稍微加大一点
        self.can_result.setStyleSheet("background-color: #f0f4f7; font-family: Consolas;")
        can_layout.addWidget(self.can_result, 1, 0, 1, 2)
        
        can_group.setLayout(can_layout)
        layout.addWidget(can_group)
        
        layout.addStretch()
        
        # 初始调用
        self.analyze_can_id()

    def analyze_can_id(self):
        try:
            text = self.can_id_input.text().replace("0x", "").strip()
            if not text:
                self.can_result.setText("")
                return
                
            can_id = int(text, 16)
            res = []
            
            # 判断标准/扩展
            if can_id > 0x7FF:
                res.append(f"🆔 ID: 0x{can_id:08X} (Extended Frame, 29-bit)")
                
                # J1939 解析逻辑
                priority = (can_id >> 26) & 0x7
                pgn = (can_id >> 8) & 0x3FFFF
                sa = can_id & 0xFF
                
                res.append(f"\n🚛 J1939 Protocol:")
                res.append(f"   • Priority : {priority}")
                res.append(f"   • PGN      : {pgn} (0x{pgn:04X})")
                res.append(f"   • Source   : {sa} (0x{sa:02X})")
            else:
                res.append(f"🆔 ID: 0x{can_id:03X} (Standard Frame, 11-bit)")
                res.append("\n   • 标准帧通常作为功能 ID 或指令 ID。")
            
            self.can_result.setText("\n".join(res))
        except ValueError:
            self.can_result.setText("等待有效 Hex 输入...")