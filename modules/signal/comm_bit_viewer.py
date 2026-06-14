import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGridLayout, QGroupBox, 
                             QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class BitViewerPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.is_32bit_mode = True # 默认为32位
        
        main_layout = QVBoxLayout(self)
        
        # --- 顶部输入区 ---
        input_group = QGroupBox("🔢 寄存器数值 (Register Value)")
        input_layout = QHBoxLayout()
        
        # Hex 输入
        input_layout.addWidget(QLabel("Hex (0x):"))
        self.hex_input = QLineEdit("00000000")
        self.hex_input.setFont(QFont("Consolas", 12))
        self.hex_input.setMaxLength(10) # 0xFFFFFFFF
        self.hex_input.returnPressed.connect(self.on_hex_changed)
        input_layout.addWidget(self.hex_input)
        
        # Decimal 输入
        input_layout.addWidget(QLabel("Dec:"))
        self.dec_input = QLineEdit("0")
        self.dec_input.setFont(QFont("Consolas", 12))
        self.dec_input.returnPressed.connect(self.on_dec_changed)
        input_layout.addWidget(self.dec_input)
        
        # 刷新按钮
        btn_update = QPushButton("🔄 刷新")
        btn_update.clicked.connect(self.on_hex_changed)
        input_layout.addWidget(btn_update)

        # --- 模式切换按钮 ---
        self.btn_mode_switch = QPushButton("切换到 16-bit 模式")
        self.btn_mode_switch.setStyleSheet("background-color: #17a2b8; color: white; font-weight: bold;")
        self.btn_mode_switch.clicked.connect(self.toggle_bit_mode)
        input_layout.addWidget(self.btn_mode_switch)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # --- 核心位域显示区 ---
        self.bit_group = QGroupBox("🎛️ 位域状态 (Bit Field Visualization)")
        self.bit_layout = QGridLayout()
        self.bit_layout.setSpacing(4)
        
        # 强制 8 列均匀拉伸
        for col in range(8):
            self.bit_layout.setColumnStretch(col, 1)
        
        self.bit_buttons = []
        
        # 样式定义
        self.btn_style_on = """
            QPushButton { 
                background-color: #28a745; color: white; font-weight: bold; 
                border: 2px solid #1e7e34; border-radius: 4px; 
                min-width: 40px; min-height: 35px; font-size: 11px;
            }
        """
        self.btn_style_off = """
            QPushButton { 
                background-color: #e9ecef; color: #495057; font-weight: normal;
                border: 2px solid #ced4da; border-radius: 4px; 
                min-width: 40px; min-height: 35px; font-size: 11px;
            }
            QPushButton:hover { background-color: #dbe2ef; }
        """

        # 初始化 32 个按钮
        # Row 0: 0-7, Row 1: 8-15, Row 2: 16-23, Row 3: 24-31
        for i in range(32):
            row_idx = i // 8
            col_idx = i % 8
            
            # 容器 (用于同时隐藏按钮和标签)
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0,0,0,0)
            v_layout.setSpacing(1)
            
            btn = QPushButton("0")
            btn.setCheckable(True)
            btn.setStyleSheet(self.btn_style_off)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.clicked.connect(self.update_inputs_from_bits)
            
            lbl = QLabel(str(i))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #666; font-size: 9px; font-weight: bold;")
            
            v_layout.addWidget(btn)
            v_layout.addWidget(lbl)
            
            self.bit_layout.addWidget(container, row_idx, col_idx)
            
            # 将 container 存起来，方便后面隐藏
            btn.setProperty("container_widget", container)
            btn.setProperty("bit_index", i)
            self.bit_buttons.append(btn)

        self.bit_group.setLayout(self.bit_layout)
        main_layout.addWidget(self.bit_group)
        
        # --- 辅助操作区 ---
        tool_layout = QHBoxLayout()
        
        btn_clear = QPushButton("🗑️ 全清")
        btn_clear.clicked.connect(lambda: self.set_value(0))
        
        btn_set = QPushButton("💡 全置")
        btn_set.clicked.connect(self.set_all_bits)
        
        btn_invert = QPushButton("🌗 反转")
        btn_invert.clicked.connect(self.invert_bits)
        
        btn_shift_l = QPushButton("⬅️ 左移")
        btn_shift_l.clicked.connect(lambda: self.shift_val(left=True))
        
        btn_shift_r = QPushButton("➡️ 右移")
        btn_shift_r.clicked.connect(lambda: self.shift_val(left=False))

        tool_layout.addWidget(btn_clear)
        tool_layout.addWidget(btn_set)
        tool_layout.addWidget(btn_invert)
        tool_layout.addWidget(btn_shift_l)
        tool_layout.addWidget(btn_shift_r)
        
        main_layout.addLayout(tool_layout)
        main_layout.addStretch()

    def toggle_bit_mode(self):
        self.is_32bit_mode = not self.is_32bit_mode
        
        if self.is_32bit_mode:
            # 切换到 32位
            self.btn_mode_switch.setText("切换到 16-bit 模式")
            self.hex_input.setMaxLength(10) # 0xFFFFFFFF
            # 显示高16位 (Bit 16-31)
            for i in range(16, 32):
                container = self.bit_buttons[i].property("container_widget")
                if container: container.show()
        else:
            # 切换到 16位
            self.btn_mode_switch.setText("切换到 32-bit 模式")
            # 截断当前值
            try:
                current_val = int(self.hex_input.text(), 16) if self.hex_input.text() else 0
                self.set_value(current_val & 0xFFFF)
            except: pass
            
            self.hex_input.setMaxLength(6) # 0xFFFF
            # 隐藏高16位
            for i in range(16, 32):
                container = self.bit_buttons[i].property("container_widget")
                if container: container.hide()

    def set_value(self, val):
        mask = 0xFFFFFFFF if self.is_32bit_mode else 0xFFFF
        val = int(val) & mask
        
        width = 8 if self.is_32bit_mode else 4
        self.hex_input.setText(f"{val:0{width}X}")
        self.dec_input.setText(f"{val}")
        
        for i, btn in enumerate(self.bit_buttons):
            is_set = (val >> i) & 0x01
            btn.setChecked(bool(is_set))
            btn.setText("1" if is_set else "0")
            btn.setStyleSheet(self.btn_style_on if is_set else self.btn_style_off)

    def set_all_bits(self):
        val = 0xFFFFFFFF if self.is_32bit_mode else 0xFFFF
        self.set_value(val)

    def on_hex_changed(self):
        text = self.hex_input.text().strip()
        if not text: return
        try:
            val = int(text, 16) if not text.lower().startswith("0x") else int(text, 16)
            self.set_value(val)
        except ValueError: pass

    def on_dec_changed(self):
        text = self.dec_input.text().strip()
        if not text: return
        try:
            self.set_value(int(text))
        except ValueError: pass

    def update_inputs_from_bits(self):
        new_val = 0
        limit = 32 if self.is_32bit_mode else 16
        for i in range(limit):
            if self.bit_buttons[i].isChecked():
                new_val |= (1 << i)
        
        width = 8 if self.is_32bit_mode else 4
        self.hex_input.setText(f"{new_val:0{width}X}")
        self.dec_input.setText(f"{new_val}")
        
        sender = self.sender()
        if sender:
            is_on = sender.isChecked()
            sender.setText("1" if is_on else "0")
            sender.setStyleSheet(self.btn_style_on if is_on else self.btn_style_off)

    def invert_bits(self):
        try:
            val = int(self.hex_input.text(), 16)
            mask = 0xFFFFFFFF if self.is_32bit_mode else 0xFFFF
            self.set_value(~val & mask)
        except: pass

    def shift_val(self, left=True):
        try:
            val = int(self.hex_input.text(), 16)
            val = (val << 1) if left else (val >> 1)
            self.set_value(val)
        except: pass