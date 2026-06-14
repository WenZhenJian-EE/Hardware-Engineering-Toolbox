import struct
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGroupBox, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

class DecoderPanel(QWidget):
    def __init__(self):
        super().__init__()
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 顶部：说明与输入
        input_group = QGroupBox("📥 接收数据输入 (Hex Input)")
        input_layout = QVBoxLayout()
        
        hint_label = QLabel("请粘贴接收到的十六进制数据 (支持带空格/不带空格/带0x前缀)")
        hint_label.setStyleSheet("color: #666; font-style: italic;")
        
        self.hex_input = QTextEdit()
        self.hex_input.setPlaceholderText("例如完整协议: 53 01 00 CD 0C FA 43 17 45\n或者纯数据: CD 0C FA 43")
        self.hex_input.setMaximumHeight(80)
        self.hex_input.setFont(QFont("Consolas", 12))
        
        self.btn_decode = QPushButton("🔍 智能解析 (Smart Decode)")
        self.btn_decode.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_decode.clicked.connect(self.parse_data)
        
        input_layout.addWidget(hint_label)
        input_layout.addWidget(self.hex_input)
        input_layout.addWidget(self.btn_decode)
        input_group.setLayout(input_layout)
        
        # 底部：结果显示
        result_group = QGroupBox("📊 解析结果 (Analysis Result)")
        result_layout = QVBoxLayout()
        
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(QFont("Consolas", 11))
        self.result_display.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ccc;")
        
        result_layout.addWidget(self.result_display)
        result_group.setLayout(result_layout)
        
        main_layout.addWidget(input_group)
        main_layout.addWidget(result_group)

    def parse_data(self):
        # 1. 清洗数据：移除空格、换行、0x、逗号
        raw_text = self.hex_input.toPlainText()
        clean_text = re.sub(r'[^0-9a-fA-F]', '', raw_text)
        
        log = []
        log.append(f"🔎 原始数据: {raw_text.strip()}")
        log.append("-" * 50)
        
        if not clean_text:
            self.result_display.setText("❌ 输入为空或无有效十六进制字符")
            return

        # 尝试转换为字节流
        try:
            # 补齐偶数位，防止 'abc' 这种奇数长度报错
            if len(clean_text) % 2 != 0:
                clean_text = '0' + clean_text
                log.append("⚠️ 警告: 输入长度为奇数，已自动高位补0")
                
            data_bytes = bytes.fromhex(clean_text)
            length = len(data_bytes)
            
            # 显示整理后的 Hex
            formatted_hex = ' '.join([f"{b:02X}" for b in data_bytes])
            log.append(f"📦 字节流 (Len={length}): {formatted_hex}")
            log.append("-" * 50)
            
            # === 场景 A: 尝试按标准协议解析 (Header+Addr+Data+Check+Tail) ===
            # 假设协议固定长度为 9 字节 (1+2+4+1+1)
            if length == 9:
                log.append("✅ [检测到标准协议帧 (9 Bytes)]")
                self.decode_protocol_frame(data_bytes, log)
            elif length > 9:
                 log.append("ℹ️ [提示] 数据长度大于9，如果包含协议帧，请确保只复制一帧数据。")
                 self.decode_general_values(data_bytes, log)
            else:
                log.append("ℹ️ [非标准协议长度] 执行通用数值解析...")
                self.decode_general_values(data_bytes, log)

        except Exception as e:
            log.append(f"❌ 解析发生严重错误: {str(e)}")

        self.result_display.setText("\n".join(log))

    def decode_protocol_frame(self, data, log):
        """解析 S + Addr(2) + Data(4) + Check + E 结构"""
        header = data[0]
        addr_bytes = data[1:3]
        payload_bytes = data[3:7]
        checksum = data[7]
        tail = data[8]
        
        # 1. Header
        log.append(f"1. 包头 (Header): 0x{header:02X} ({chr(header) if 32<=header<=126 else '?'})")
        
        # 2. Address (Little Endian)
        addr_val = struct.unpack('<H', addr_bytes)[0]
        log.append(f"2. 地址 (Addr)  : 0x{addr_val:04X} (Dec: {addr_val})")
        
        # 3. Data (核心：不知道是Float还是Int，都显示)
        log.append(f"3. 数据 (Data)  : [Hex: {payload_bytes.hex().upper()}]")
        
        f_val = struct.unpack('<f', payload_bytes)[0]
        i_val = struct.unpack('<I', payload_bytes)[0] # Unsigned Int
        si_val = struct.unpack('<i', payload_bytes)[0] # Signed Int
        
        log.append(f"   👉 若为 Float  : {f_val:.6f}")
        log.append(f"   👉 若为 Uint32 : {i_val}")
        if si_val < 0:
            log.append(f"   👉 若为 Int32  : {si_val}")
            
        # 4. Checksum
        # 计算方式：Address + Data 的累加和低8位 (根据你的协议规则)
        calc_payload = addr_bytes + payload_bytes
        calc_sum = sum(calc_payload) & 0xFF
        status = "✅ PASS" if calc_sum == checksum else f"❌ FAIL (Exp: 0x{calc_sum:02X})"
        log.append(f"4. 校验 (Check) : 0x{checksum:02X} -> {status}")
        
        # 5. Tail (修改：增加字符显示)
        log.append(f"5. 包尾 (Tail)  : 0x{tail:02X} ({chr(tail) if 32<=tail<=126 else '?'})")

    def decode_general_values(self, data, log):
        """解析任意长度数据的通用数值"""
        # 如果长度是4字节，极大概率是一个参数
        if len(data) == 4:
            log.append("💡 [4字节通用解析 - Little Endian (DSP/Intel常用)]")
            try:
                f_val = struct.unpack('<f', data)[0]
                log.append(f"   • Float  : {f_val:.6f}")
            except Exception:
                log.append(f"   • Float  : [Invalid NaN/Inf]")
                
            i_val = struct.unpack('<I', data)[0]
            log.append(f"   • Uint32 : {i_val}")
            log.append(f"   • Int32  : {struct.unpack('<i', data)[0]}")
            
            log.append("\n💡 [4字节通用解析 - Big Endian (网络/Motorola常用)]")
            try:
                f_val_be = struct.unpack('>f', data)[0]
                log.append(f"   • Float  : {f_val_be:.6f}")
            except Exception:
                log.append(f"   • Float  : [Invalid NaN/Inf]")
        
        elif len(data) == 2:
            log.append("💡 [2字节通用解析]")
            val_u16 = struct.unpack('<H', data)[0]
            val_16 = struct.unpack('<h', data)[0]
            log.append(f"   • Uint16 : {val_u16}")
            log.append(f"   • Int16  : {val_16}")
            
        else:
            log.append("ℹ️ 数据长度不是标准的 2 或 4 字节，仅显示 ASCII 和 十进制流。")
            
        # 显示十进制流
        dec_stream = ' '.join([str(b) for b in data])
        log.append(f"\n🔢 十进制流: {dec_stream}")
        
        # [优化] 显示 ASCII 预览 (电力电子开发调试常用：查看 Printf 字符串)
        ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
        log.append(f"🔤 ASCII预览: {ascii_str}")