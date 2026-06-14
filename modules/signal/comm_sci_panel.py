import struct
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QGroupBox, 
                             QGridLayout, QSpinBox, QDoubleSpinBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QApplication, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QTextCharFormat

class SCIPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        # 主布局 (改为直接基于 self)
        main_layout = QHBoxLayout(self)

        # --- 左侧：协议构建与计算区 ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 1. 协议构建流 (Grid布局：标签 | 输入 | 实时转换值 | 格式说明)
        builder_group = QGroupBox("📦 C2000 SCI 协议帧构建 (Protocol Builder)")
        builder_layout = QGridLayout()
        # 列宽调整：输入框适中，实时值拉伸
        builder_layout.setColumnStretch(1, 0) 
        builder_layout.setColumnStretch(2, 1) 
        
        # 样式定义
        self.info_style = "color: #007bff; font-weight: bold; font-family: Consolas;" # 蓝色实时信息

        # --- Row 1: Header ---
        self.header_input = QLineEdit("S")
        self.header_input.setFixedWidth(100)
        self.header_input.setPlaceholderText("Char/Hex")
        self.header_input.textChanged.connect(self.trigger_update)
        
        self.lbl_header_info = QLabel()
        self.lbl_header_info.setStyleSheet(self.info_style)
        
        builder_layout.addWidget(QLabel("1. 包头 (Header):"), 0, 0)
        builder_layout.addWidget(self.header_input, 0, 1)
        builder_layout.addWidget(self.lbl_header_info, 0, 2) # 实时显示 ASCII/Hex
        builder_layout.addWidget(QLabel("uint8 (1 Byte)"), 0, 3)

        # --- Row 2: Address (恢复十进制输入) ---
        self.idx_input = QSpinBox()
        self.idx_input.setRange(0, 65535)
        self.idx_input.setValue(1) # 默认值为1
        self.idx_input.setFixedWidth(100)
        # 不设置 setDisplayIntegerBase(16)，保持十进制显示
        self.idx_input.valueChanged.connect(self.trigger_update)

        self.lbl_addr_info = QLabel()
        self.lbl_addr_info.setStyleSheet(self.info_style)

        builder_layout.addWidget(QLabel("2. 地址 (Address):"), 1, 0)
        builder_layout.addWidget(self.idx_input, 1, 1)
        builder_layout.addWidget(self.lbl_addr_info, 1, 2) # 实时显示 Hex 0xXXXX
        builder_layout.addWidget(QLabel("uint16 (Little Endian)"), 1, 3)

        # --- Row 3: Data ---
        self.val_input = QDoubleSpinBox()
        self.val_input.setRange(-3.4e38, 3.4e38) 
        self.val_input.setDecimals(4)
        self.val_input.setValue(500.1)
        self.val_input.setFixedWidth(100)
        self.val_input.valueChanged.connect(self.trigger_update)

        self.lbl_data_info = QLabel()
        self.lbl_data_info.setStyleSheet(self.info_style)

        builder_layout.addWidget(QLabel("3. 数据 (Data):"), 2, 0)
        builder_layout.addWidget(self.val_input, 2, 1)
        builder_layout.addWidget(self.lbl_data_info, 2, 2) # 实时显示 IEEE754 Hex
        builder_layout.addWidget(QLabel("float (4 Bytes)"), 2, 3)

        # --- Row 4: Checksum (Auto) ---
        self.checksum_display = QLineEdit()
        self.checksum_display.setReadOnly(True)
        self.checksum_display.setStyleSheet("background-color: #f0f0f0; color: #dc3545; font-weight: bold;")
        self.checksum_display.setFixedWidth(100)

        self.lbl_check_info = QLabel("Auto Calculated")
        self.lbl_check_info.setStyleSheet("color: #28a745; font-style: italic;")

        builder_layout.addWidget(QLabel("4. 校验和 (Check):"), 3, 0)
        builder_layout.addWidget(self.checksum_display, 3, 1)
        builder_layout.addWidget(self.lbl_check_info, 3, 2)
        builder_layout.addWidget(QLabel("uint8 (Sum & 0xFF)"), 3, 3)

        # --- Row 5: Tail ---
        self.tail_input = QLineEdit("E")
        self.tail_input.setFixedWidth(100)
        self.tail_input.textChanged.connect(self.trigger_update)
        
        self.lbl_tail_info = QLabel()
        self.lbl_tail_info.setStyleSheet(self.info_style)

        builder_layout.addWidget(QLabel("5. 包尾 (Tail):"), 4, 0)
        builder_layout.addWidget(self.tail_input, 4, 1)
        builder_layout.addWidget(self.lbl_tail_info, 4, 2)
        builder_layout.addWidget(QLabel("uint8 (1 Byte)"), 4, 3)

        builder_group.setLayout(builder_layout)
        left_layout.addWidget(builder_group)

        # 2. 结果显示区 (Hex)
        result_group = QGroupBox("🚀 最终指令 (Final Hex String)")
        result_layout = QVBoxLayout()
        self.hex_display = QTextEdit()
        self.hex_display.setReadOnly(True)
        self.hex_display.setFont(QFont("Consolas", 16, QFont.Bold)) 
        self.hex_display.setMaximumHeight(70)
        self.hex_display.setStyleSheet("background-color: #2b2b2b; color: #fff; border-radius: 5px;")
        
        copy_btn = QPushButton("📋 复制 HEX 指令")
        copy_btn.setStyleSheet("""
            QPushButton { background-color: #007bff; color: white; padding: 6px; border-radius: 4px; font-weight: bold;}
            QPushButton:hover { background-color: #0056b3; }
        """)
        copy_btn.clicked.connect(self.copy_to_clipboard)

        result_layout.addWidget(self.hex_display)
        result_layout.addWidget(copy_btn)
        result_group.setLayout(result_layout)
        left_layout.addWidget(result_group)

        # --- [新增] Modbus RTU 快速组包区 ---
        modbus_group = QGroupBox("🔌 Modbus RTU 快速组包 (Fast Send)")
        modbus_layout = QGridLayout()
        
        self.mb_addr_input = QSpinBox()
        self.mb_addr_input.setRange(1, 247)
        self.mb_addr_input.setValue(1)
        
        self.mb_func_cb = QComboBox()
        self.mb_func_cb.addItems(["03 (读寄存器)", "06 (写单寄存器)", "10 (写多寄存器)"])
        
        self.mb_reg_addr = QLineEdit("00 00")
        self.mb_reg_addr.setPlaceholderText("Hex: 00 00")
        
        self.mb_reg_data = QLineEdit("00 01")
        self.mb_reg_data.setPlaceholderText("Hex: 00 00...")
        
        btn_build_mb = QPushButton("⚡ 生成 Modbus RTU 指令")
        btn_build_mb.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        btn_build_mb.clicked.connect(self.build_modbus_rtu)
        
        modbus_layout.addWidget(QLabel("从站地址(Dec):"), 0, 0)
        modbus_layout.addWidget(self.mb_addr_input, 0, 1)
        modbus_layout.addWidget(QLabel("功能码:"), 0, 2)
        modbus_layout.addWidget(self.mb_func_cb, 0, 3)
        
        modbus_layout.addWidget(QLabel("寄存器地址(Hex):"), 1, 0)
        modbus_layout.addWidget(self.mb_reg_addr, 1, 1)
        modbus_layout.addWidget(QLabel("数据(长度/内容 Hex):"), 1, 2)
        modbus_layout.addWidget(self.mb_reg_data, 1, 3)
        
        modbus_layout.addWidget(btn_build_mb, 2, 0, 1, 4)
        modbus_group.setLayout(modbus_layout)
        left_layout.addWidget(modbus_group)

        # 3. 教学解析窗口
        teach_group = QGroupBox("🎓 详细过程解析 (Analysis)")
        teach_layout = QVBoxLayout()
        self.process_display = QTextEdit()
        self.process_display.setReadOnly(True)
        self.process_display.setFont(QFont("Consolas", 10))
        self.process_display.setStyleSheet("background-color: #f8f9fa; color: #333; border: 1px solid #ddd;")
        teach_layout.addWidget(self.process_display)
        teach_group.setLayout(teach_layout)
        left_layout.addWidget(teach_group, stretch=1)

        # --- 右侧：数据类型速查表 ---
        right_panel = self.create_reference_panel()

        # 添加到主窗口
        main_layout.addWidget(left_panel, stretch=2)
        main_layout.addWidget(right_panel, stretch=1)

        # 初始化一次
        self.trigger_update()

    # --- 辅助功能 ---
    def create_reference_panel(self):
        group = QGroupBox("📚 常用类型速查")
        layout = QVBoxLayout()
        table = QTableWidget(8, 3)
        table.setHorizontalHeaderLabels(["类型", "字节", "范围"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        data = [
            ("uint8", "1", "0 ~ 255"), ("int8", "1", "-128 ~ 127"),
            ("uint16", "2", "0 ~ 65535"), ("int16", "2", "-32768 ~ 32767"),
            ("uint32", "4", "0 ~ 42.9亿"), ("int32", "4", "-21.4亿 ~ 21.4亿"),
            ("float", "4", "±3.4e38"), ("double", "8", "±1.7e308")
        ]
        for i, (name, size, desc) in enumerate(data):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(size))
            table.setItem(i, 2, QTableWidgetItem(desc))
        layout.addWidget(table)
        group.setLayout(layout)
        return group

    # 智能解析函数：处理 S, 0x53, 83 等多种输入
    def get_config_byte(self, text, default_char):
        text = text.strip()
        if not text: 
            return ord(default_char), f"Default '{default_char}'"
        
        # 1. 尝试十六进制 (0x...)
        if text.lower().startswith("0x"):
            try: return int(text, 16), text
            except: return 0, "Invalid Hex"
            
        # 1.5 尝试纯两位十六进制 (例如 5A)
        if len(text) == 2 and all(c in '0123456789abcdefABCDEF' for c in text):
             try: return int(text, 16), f"0x{text}"
             except: pass
        
        # 2. 尝试纯数字 (0-255)
        if text.isdigit():
            val = int(text)
            if val <= 255:
                 return val, f"Dec {val}"
        
        # 3. 默认为字符
        return ord(text[0]), f"Char '{text[0]}'"

    def trigger_update(self):
        self.calculate_and_display(self.idx_input.value(), self.val_input.value())

    def calculate_and_display(self, idx_val, float_val):
        try:
            # --- 1. Header 处理 ---
            header_val, header_desc = self.get_config_byte(self.header_input.text(), 'S')
            b_header = struct.pack('B', header_val)
            # 实时更新 Header 信息标签
            self.lbl_header_info.setText(f"→ Hex: 0x{header_val:02X} (Dec:{header_val})")

            # --- 2. Address 处理 ---
            # 您输入的是十进制 (idx_val)，这里转为 uint16 Hex
            b_idx = struct.pack('<H', int(idx_val))
            # 实时更新 Address 信息标签
            self.lbl_addr_info.setText(f"→ Hex: 0x{int(idx_val):04X}")

            # --- 3. Data 处理 ---
            b_data = struct.pack('<f', float(float_val))
            float_hex_int = struct.unpack('<I', b_data)[0]
            # 实时更新 Data 信息标签
            self.lbl_data_info.setText(f"→ Hex: 0x{float_hex_int:08X}")

            # --- 4. Checksum 处理 ---
            payload = b_idx + b_data
            payload_sum = sum(payload)
            checksum_int = payload_sum & 0xFF 
            b_check = struct.pack('B', checksum_int)
            self.checksum_display.setText(f"0x{checksum_int:02X}")

            # --- 5. Tail 处理 ---
            tail_val, tail_desc = self.get_config_byte(self.tail_input.text(), 'E')
            b_tail = struct.pack('B', tail_val)
            # 实时更新 Tail 信息标签
            self.lbl_tail_info.setText(f"→ Hex: 0x{tail_val:02X} (Dec:{tail_val})")

            # --- 最终 Hex 显示 ---
            self.hex_display.clear()
            cursor = self.hex_display.textCursor()
            def append_colored(bytes_obj, color):
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(color))
                text = ' '.join([f'{b:02X}' for b in bytes_obj]) + ' '
                cursor.insertText(text, fmt)

            append_colored(b_header, "#888888")   # 灰
            append_colored(b_idx,    "#007bff")   # 蓝
            append_colored(b_data,   "#28a745")   # 绿
            append_colored(b_check,  "#dc3545")   # 红
            append_colored(b_tail,   "#888888")   # 灰
            
            self.current_hex = ' '.join([f'{b:02X}' for b in (b_header + payload + b_check + b_tail)])

            # --- 生成教学文本 (Process) ---
            process_text = []
            process_text.append(f"🔍 协议解析过程:")
            process_text.append(f"--------------------------------------------------")
            
            process_text.append(f"1. 包头 (Header):")
            process_text.append(f"   - 输入: {self.header_input.text()} ({header_desc})")
            process_text.append(f"   - 结果: 0x{header_val:02X}")

            process_text.append(f"\n2. 地址 (Address):")
            process_text.append(f"   - 输入(Dec): {int(idx_val)}")
            process_text.append(f"   - 转换(Hex): 0x{int(idx_val):04X}")
            process_text.append(f"   - 物理字节 : {b_idx[0]:02X} {b_idx[1]:02X} (Little Endian)")

            process_text.append(f"\n3. 数据 (Data):")
            process_text.append(f"   - 输入(Float): {float_val:.4f}")
            process_text.append(f"   - IEEE754 Hex: 0x{float_hex_int:08X}")
            process_text.append(f"   - 物理字节   : {b_data[0]:02X} {b_data[1]:02X} {b_data[2]:02X} {b_data[3]:02X}")

            process_text.append(f"\n4. 校验和 (Checksum):")
            calc_str = " + ".join([f"{b:02X}" for b in payload])
            process_text.append(f"   - 累加范围: Address + Data")
            process_text.append(f"   - 计算式  : ({calc_str}) = 0x{payload_sum:X}")
            process_text.append(f"   - 取低8位 : 0x{checksum_int:02X}")

            process_text.append(f"\n5. 包尾 (Tail):")
            process_text.append(f"   - 输入: {self.tail_input.text()} ({tail_desc})")
            process_text.append(f"   - 结果: 0x{tail_val:02X}")

            self.process_display.setText("\n".join(process_text))

        except Exception as e:
            self.hex_display.setPlainText(f"Error: {str(e)}")

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.current_hex)

    # --- Modbus RTU 快速生成业务 --- 
    def build_modbus_rtu(self):
        try:
            addr = self.mb_addr_input.value()
            func_idx = self.mb_func_cb.currentIndex()
            # 0: Func 03, 1: Func 06, 2: Func 10 (十六进制为 10, 十进制为 16)
            func = [0x03, 0x06, 0x10][func_idx]
            
            # 清洗 Hex
            def clean_hex(txt):
                return bytes.fromhex(txt.replace('0x', '').replace(' ', ''))
                
            b_reg = clean_hex(self.mb_reg_addr.text())
            b_data = clean_hex(self.mb_reg_data.text())
            
            payload = struct.pack('B', addr) + struct.pack('B', func) + b_reg + b_data
            
            # 计算 Modbus CRC16
            crc = 0xFFFF
            for b in payload:
                crc ^= b
                for _ in range(8):
                    if (crc & 0x0001):
                        crc >>= 1
                        crc ^= 0xA001
                    else:
                        crc >>= 1
            
            # 注意 Modbus 是 Little Endian 放置 CRC
            b_crc = struct.pack('<H', crc)
            
            final_bytes = payload + b_crc
            self.current_hex = ' '.join([f'{b:02X}' for b in final_bytes])
            
            # 显示结果到原有窗口
            self.hex_display.clear()
            cursor = self.hex_display.textCursor()
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#28a745")) # 全绿
            cursor.insertText(self.current_hex, fmt)
            
            # 更新解析过程
            process_text = []
            process_text.append(f"🔌 Modbus RTU 组包:")
            process_text.append(f"--------------------------------------------------")
            process_text.append(f"1. 地址   : 0x{addr:02X} (Dec:{addr})")
            process_text.append(f"2. 功能码 : 0x{func:02X}")
            process_text.append(f"3. 寄存器 : " + ' '.join([f'{b:02X}' for b in b_reg]))
            process_text.append(f"4. 数据   : " + ' '.join([f'{b:02X}' for b in b_data]))
            process_text.append(f"5. CRC16  : {b_crc[0]:02X} {b_crc[1]:02X} (Little Endian)")
            self.process_display.setText("\n".join(process_text))
            
        except Exception as e:
            self.hex_display.setPlainText(f"Modbus Error: 请检查输入 Hex 格式是否正确。错误信息: {str(e)}")