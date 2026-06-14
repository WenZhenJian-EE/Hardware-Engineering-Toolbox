import struct
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QRadioButton, QButtonGroup, 
                             QGridLayout, QGroupBox, QApplication, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class FloatHexConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.is_updating = False # 防止信号死循环互锁
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- 1. 数值输入区 (Float/Double) ---
        input_group = QGroupBox("📊 浮点数值 (Decimal Float)")
        input_layout = QVBoxLayout()
        
        self.float_input = QLineEdit("0.0")
        self.float_input.setFont(QFont("Consolas", 14, QFont.Bold))
        self.float_input.setPlaceholderText("输入浮点数, 如 3.14")
        self.float_input.textChanged.connect(self.on_float_changed)
        
        input_layout.addWidget(self.float_input)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # --- 2. 十六进制输入区 (Hex) ---
        hex_group = QGroupBox("💾 内存数据 (Hex)")
        hex_layout = QVBoxLayout()
        
        self.hex_input = QLineEdit("00 00 00 00")
        self.hex_input.setFont(QFont("Consolas", 14, QFont.Bold))
        self.hex_input.setStyleSheet("color: #dc3545;") # 红色突出显示 Hex
        self.hex_input.setPlaceholderText("输入 Hex, 如 40 48 F5 C3")
        self.hex_input.textChanged.connect(self.on_hex_changed)
        
        hex_layout.addWidget(self.hex_input)
        hex_group.setLayout(hex_layout)
        main_layout.addWidget(hex_group)
        
        # --- 3. [新增] 定点数/Q格式 (Fixed-Point / Q-Math) ---
        q_group = QGroupBox("⚙️ Q格式定点数 (Q-Format Fixed-Point)")
        q_layout = QGridLayout()
        
        # 输入区
        self.q_float_input = QLineEdit("0.0")
        self.q_float_input.setPlaceholderText("输入十进制, 如 0.5")
        self.q_float_input.textChanged.connect(self.on_q_float_changed)
        
        self.q_hex_input = QLineEdit("00000000")
        self.q_hex_input.setStyleSheet("color: #dc3545;") 
        self.q_hex_input.setPlaceholderText("输入16进制")
        self.q_hex_input.textChanged.connect(self.on_q_hex_changed)
        
        self.q_dec_input = QLineEdit("0")
        self.q_dec_input.setStyleSheet("color: #007bff;")
        self.q_dec_input.setPlaceholderText("输入10进制整数")
        self.q_dec_input.textChanged.connect(self.on_q_dec_changed)
        
        # Q格式类别选择 (默认 Q24)
        self.q_format_cb = QComboBox()
        for i in range(1, 32):  # 支持 Q1 到 Q31
            self.q_format_cb.addItem(f"Q{i}", (1 << i))
        self.q_format_cb.setCurrentText("Q24")
        self.q_format_cb.currentIndexChanged.connect(self.recalc_q_format)
        
        # 字长选择 (16/32位)
        self.q_bits_cb = QComboBox()
        self.q_bits_cb.addItems(["32-bit (IQmath)", "16-bit"])
        self.q_bits_cb.currentIndexChanged.connect(self.recalc_q_format)

        q_layout.addWidget(QLabel("格式:"), 0, 0)
        q_layout.addWidget(self.q_format_cb, 0, 1)
        q_layout.addWidget(self.q_bits_cb, 0, 2)
        
        q_layout.addWidget(QLabel("十进制小数:"), 1, 0)
        q_layout.addWidget(self.q_float_input, 1, 1, 1, 2)
        
        q_layout.addWidget(QLabel("十六进制 (Hex):"), 2, 0)
        q_layout.addWidget(self.q_hex_input, 2, 1, 1, 2)
        
        q_layout.addWidget(QLabel("整型 (Dec):"), 3, 0)
        q_layout.addWidget(self.q_dec_input, 3, 1, 1, 2)
        
        q_group.setLayout(q_layout)
        main_layout.addWidget(q_group)
        
        # --- 4. 配置区 (Type & Endian) ---
        config_layout = QGridLayout()
        
        # [数据类型选择]
        self.type_group = QButtonGroup(self)
        self.rb_float = QRadioButton("Float (32-bit)")
        self.rb_double = QRadioButton("Double (64-bit)")
        self.rb_float.setChecked(True)
        self.type_group.addButton(self.rb_float, 0)
        self.type_group.addButton(self.rb_double, 1)
        self.type_group.buttonClicked.connect(self.recalc_from_active_source)
        
        config_layout.addWidget(QLabel("精度:"), 0, 0)
        config_layout.addWidget(self.rb_float, 0, 1)
        config_layout.addWidget(self.rb_double, 0, 2)
        
        # [字节序选择 - 关键功能]
        # 电力电子/PLC 常见痛点：字节序混乱
        self.endian_group = QButtonGroup(self)
        
        # ABCD (Big Endian) - 网络序/Motorola
        self.rb_abcd = QRadioButton("Big (ABCD)")
        self.rb_abcd.setToolTip("大端模式: 高字节在前 (标准网络序)")
        
        # DCBA (Little Endian) - x86/C2000 Little
        self.rb_dcba = QRadioButton("Little (DCBA)")
        self.rb_dcba.setToolTip("小端模式: 低字节在前 (Intel/ARM)")
        self.rb_dcba.setChecked(True) # 默认小端
        
        # CDAB (Mid-Little) - 常见于 Modbus 设备
        self.rb_cdab = QRadioButton("Swap (CDAB)") 
        self.rb_cdab.setToolTip("字内交换: 16位字内部交换字节 (Modbus常见)")
        
        # BADC (Mid-Big)
        self.rb_badc = QRadioButton("Swap (BADC)")
        self.rb_badc.setToolTip("字间交换: 16位字顺序交换")

        self.endian_group.addButton(self.rb_abcd, 0)
        self.endian_group.addButton(self.rb_dcba, 1)
        self.endian_group.addButton(self.rb_cdab, 2)
        self.endian_group.addButton(self.rb_badc, 3)
        self.endian_group.buttonClicked.connect(self.recalc_from_active_source)
        
        config_layout.addWidget(QLabel("字节序:"), 1, 0)
        config_layout.addWidget(self.rb_abcd, 1, 1)
        config_layout.addWidget(self.rb_dcba, 1, 2)
        config_layout.addWidget(QLabel(""), 1, 3) # 占位
        
        config_layout.addWidget(QLabel(""), 2, 0) # 占位
        config_layout.addWidget(self.rb_cdab, 2, 1)
        config_layout.addWidget(self.rb_badc, 2, 2)

        main_layout.addLayout(config_layout)
        
        # --- 4. 底部状态与操作 ---
        btn_layout = QHBoxLayout()
        btn_copy_float = QPushButton("复制 Float")
        btn_copy_float.clicked.connect(lambda: QApplication.clipboard().setText(self.float_input.text()))
        
        btn_copy_hex = QPushButton("复制 Hex")
        btn_copy_hex.clicked.connect(lambda: QApplication.clipboard().setText(self.hex_input.text()))

        btn_layout.addWidget(btn_copy_float)
        btn_layout.addWidget(btn_copy_hex)
        main_layout.addLayout(btn_layout)
        
        self.status_label = QLabel("Ready.")
        self.status_label.setStyleSheet("color: #666; font-size: 9pt;")
        main_layout.addWidget(self.status_label)
        
        main_layout.addStretch()

        # 记录最后一次是谁触发的修改，用于切换配置时重新计算
        self.last_source = 'float' 

    # --- 核心逻辑 ---
    
    def recalc_from_active_source(self):
        """ 当切换字节序或精度时，根据最后一次修改的输入框刷新另一个输入框 """
        if self.last_source == 'float':
            self.on_float_changed()
        else:
            self.on_hex_changed()

    def get_format_char(self):
        return 'd' if self.rb_double.isChecked() else 'f'

    def get_byte_len(self):
        return 8 if self.rb_double.isChecked() else 4

    def on_float_changed(self):
        if self.is_updating: return
        self.is_updating = True
        self.last_source = 'float'
        
        txt = self.float_input.text().strip()
        try:
            val = float(txt)
            fmt = self.get_format_char()
            
            # 1. 先转为标准 Big Endian 字节流 (ABCD)
            base_bytes = struct.pack('>' + fmt, val) # > means Big Endian Standard
            
            # 2. 根据字节序重排
            final_bytes = self.permute_bytes(base_bytes, to_target_endian=True)
            
            # 3. 显示
            hex_str = ' '.join([f"{b:02X}" for b in final_bytes])
            self.hex_input.setText(hex_str)
            self.status_label.setText("✅ 转换成功")
            
        except ValueError:
            self.status_label.setText("⚠️ 输入非数字")
        except Exception as e:
            self.status_label.setText(f"❌ 错误: {str(e)}")
        finally:
            self.is_updating = False

    def on_hex_changed(self):
        if self.is_updating: return
        self.is_updating = True
        self.last_source = 'hex'
        
        txt = self.hex_input.text()
        # 清洗: 去掉空格, 0x, 逗号
        clean_hex = ''.join(txt.split()).replace('0x', '').replace(',', '')
        
        try:
            target_len = self.get_byte_len()
            if len(clean_hex) != target_len * 2:
                # 长度不够时不强行转换，避免报错干扰输入
                raise ValueError("Incomplete Hex")
                
            input_bytes = bytes.fromhex(clean_hex)
            
            # 1. 还原字节序为标准 Big Endian (ABCD)
            # 这里传入 False，表示是从 Target 变回 Standard
            std_bytes = self.permute_bytes(input_bytes, to_target_endian=False)
            
            # 2. 解析 Float/Double
            fmt = self.get_format_char()
            val = struct.unpack('>' + fmt, std_bytes)[0]
            
            # 3. 显示 (保留一定精度)
            if self.rb_double.isChecked():
                self.float_input.setText(f"{val:.12g}")
            else:
                self.float_input.setText(f"{val:.8g}")
                
            self.status_label.setText("✅ 转换成功")
            
        except ValueError:
            self.status_label.setText("Waiting for complete hex...")
        except Exception as e:
            self.status_label.setText(f"❌ 解析错误")
        finally:
            self.is_updating = False

    def permute_bytes(self, data: bytes, to_target_endian: bool) -> bytes:
        """
        处理 ABCD, DCBA, CDAB, BADC 之间的转换
        base_data 假定是 Standard Big Endian (ABCD)
        """
        # 统一转为列表处理
        b = list(data)
        length = len(b)
        
        # 字节序模式 ID
        mode = self.endian_group.checkedId() 
        # 0: ABCD (Big) - No change
        # 1: DCBA (Little) - Reverse all
        # 2: CDAB (Swap 16-bit inner) - Mid-Little
        # 3: BADC (Swap 16-bit outer) - Mid-Big
        
        if mode == 0: # ABCD
            return bytes(b)
        
        elif mode == 1: # DCBA
            return bytes(b[::-1])
        
        elif mode == 2: # CDAB (Word Swap - 16-bit words reversed)
            # 原始 Big: [A, B] [C, D]
            # Swap:     [C, D] [A, B]
            new_b = []
            for i in range(0, length, 4):
                if i+3 < length:
                    # Input: 0 1 2 3
                    # Out:   2 3 0 1
                    new_b.extend([b[i+2], b[i+3], b[i], b[i+1]])
                else:
                    new_b.extend(b[i:i+4])
            return bytes(new_b)
            
        elif mode == 3: # BADC (Byte Swap within Words)
            # 原始 Big: [A, B] [C, D]
            # Swap:     [B, A] [D, C]
            new_b = []
            for i in range(0, length, 2):
                if i+1 < length:
                    new_b.extend([b[i+1], b[i]])
                else:
                    new_b.append(b[i])
            return bytes(new_b)
            
        return data

    # --- Q格式 转换逻辑 ---
    def recalc_q_format(self):
        if hasattr(self, 'last_q_source'):
            if self.last_q_source == 'float':
                self.on_q_float_changed()
            elif self.last_q_source == 'hex':
                self.on_q_hex_changed()
            else:
                self.on_q_dec_changed()

    def _get_q_params(self):
        q_val = self.q_format_cb.currentData()
        bits = 32 if "32-bit" in self.q_bits_cb.currentText() else 16
        mask = (1 << bits) - 1
        sign_bit = 1 << (bits - 1)
        return q_val, bits, mask, sign_bit

    def on_q_float_changed(self):
        if self.is_updating: return
        self.is_updating = True
        self.last_q_source = 'float'
        try:
            val = float(self.q_float_input.text())
            q_val, bits, mask, sign_bit = self._get_q_params()
            
            # 乘以 2^Q
            int_val = int(round(val * q_val))
            
            # 处理补码
            if int_val < 0:
                int_val = (abs(int_val) ^ mask) + 1
            int_val = int_val & mask
            
            # 显示
            hex_fmt = f"{int_val:0{bits//4}X}"
            self.q_hex_input.setText(hex_fmt)
            
            # 处理显示用的有符号整数
            signed_dec = int_val if not (int_val & sign_bit) else int_val - (1 << bits)
            self.q_dec_input.setText(str(signed_dec))
            
            self.status_label.setText("✅ Q格式转换成功")
        except:
            pass
        finally:
            self.is_updating = False

    def on_q_hex_changed(self):
        if self.is_updating: return
        self.is_updating = True
        self.last_q_source = 'hex'
        try:
            txt = self.q_hex_input.text().strip().replace('0x', '')
            if not txt: raise ValueError
            
            int_val = int(txt, 16)
            q_val, bits, mask, sign_bit = self._get_q_params()
            int_val = int_val & mask
            
            # 处理有符号
            signed_dec = int_val if not (int_val & sign_bit) else int_val - (1 << bits)
            self.q_dec_input.setText(str(signed_dec))
            
            float_val = signed_dec / q_val
            # 根据 Q 格式保留合理的小数位数，避免显示过长 (如约 8 位)
            self.q_float_input.setText(f"{float_val:.8g}")
            
            self.status_label.setText("✅ Q格式解析成功")
        except:
             pass
        finally:
             self.is_updating = False

    def on_q_dec_changed(self):
        if self.is_updating: return
        self.is_updating = True
        self.last_q_source = 'dec'
        try:
             signed_dec = int(self.q_dec_input.text())
             q_val, bits, mask, sign_bit = self._get_q_params()
             
             int_val = signed_dec & mask
             hex_fmt = f"{int_val:0{bits//4}X}"
             self.q_hex_input.setText(hex_fmt)
             
             float_val = signed_dec / q_val
             self.q_float_input.setText(f"{float_val:.8g}")
             
             self.status_label.setText("✅ Q格式解析成功")
        except:
             pass
        finally:
             self.is_updating = False