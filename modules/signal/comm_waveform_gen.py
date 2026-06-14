import sys
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QTabWidget, 
                             QRadioButton, QButtonGroup, QScrollArea, QFrame,
                             QCheckBox, QComboBox, QTextEdit, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# --- Matplotlib 嵌入相关 ---
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams
import matplotlib.patches as patches

# 样式微调
rcParams['font.family'] = 'sans-serif'
rcParams['font.size'] = 8
rcParams['axes.unicode_minus'] = False 

class MplCanvas(FigureCanvas):
    """ 自定义 Matplotlib 画布，支持多通道数字波形绘制 """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        self.init_canvas()

    def init_canvas(self):
        """ 初始化坐标轴 """
        self.axes.clear()
        self.axes.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
        self.axes.set_xlabel('Time (t)')
        # 隐藏 Y 轴刻度，因为我们是堆叠波形
        self.axes.set_yticks([])
        self.axes.spines['left'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['top'].set_visible(False)
        self.draw()

    def draw_digital_channel(self, time, levels, y_offset=0, label="", color='#1f77b4', height=0.8, is_analog=False):
        """ 
        绘制单路波形 
        is_analog: 如果为 True，则 levels 视为真实电压值，忽略 height 缩放，直接叠加 y_offset
        """
        if is_analog:
            y_levels = np.array(levels) + y_offset
        else:
            y_levels = np.array(levels) * height + y_offset
            
        self.axes.step(time, y_levels, where='post', color=color, linewidth=1.5)
        
        # 标注通道名
        label_y = y_offset + (np.mean(levels) if is_analog else height/2)
        self.axes.text(time[0] - 0.5, label_y, label, 
                       verticalalignment='center', horizontalalignment='right', 
                       fontweight='bold', color=color, fontsize=9)

    def add_sampling_mark(self, x, y_bottom, y_top, color='red', linestyle=':'):
        """ 画竖直采样线 """
        self.axes.vlines(x, y_bottom, y_top, colors=color, linestyles=linestyle, linewidth=1, alpha=0.7)

    def add_bit_label(self, x, y, text, color='black', fontsize=7):
        """ 添加 Bit 文字说明 """
        self.axes.text(x, y, text, ha='center', va='bottom', fontsize=fontsize, color=color)

    def add_region_highlight(self, x_start, x_end, text, color='yellow', alpha=0.2, y_min=0, y_max=5):
        """ 添加区域高亮 (如 Address 段) """
        rect = patches.Rectangle((x_start, y_min), x_end - x_start, y_max - y_min, 
                                 linewidth=0, edgecolor='none', facecolor=color, alpha=alpha)
        self.axes.add_patch(rect)
        if text:
            self.axes.text((x_start+x_end)/2, y_max - 0.2, text, 
                           ha='center', va='top', fontsize=8, color='gray', fontweight='bold')

# =============================================================================
# 1. SCI (UART) 面板
# =============================================================================
class SCIPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # --- 左侧设置 ---
        settings = QGroupBox("SCI (UART) 设置")
        settings.setFixedWidth(280)
        vbox = QVBoxLayout()
        
        vbox.addWidget(QLabel("Tx 发送数据 (Hex) - MCU发出:"))
        self.txt_tx = QLineEdit("55 AA")
        vbox.addWidget(self.txt_tx)

        vbox.addWidget(QLabel("Rx 接收数据 (Hex) - MCU收到:"))
        self.txt_rx = QLineEdit("FF 00")  
        vbox.addWidget(self.txt_rx)
        
        vbox.addWidget(QLabel("参数说明:"))
        vbox.addWidget(QLabel("• 1 起始位 (Start) - 低电平"))
        vbox.addWidget(QLabel("• 8 数据位 (Data) - 低位在先(LSB)"))
        
        self.cmb_parity = QComboBox()
        self.cmb_parity.addItems(["无校验 (None)", "偶校验 (Even)", "奇校验 (Odd)"])
        vbox.addWidget(QLabel("• 校验位 (Parity):"))
        vbox.addWidget(self.cmb_parity)
        
        vbox.addWidget(QLabel("• 1 停止位 (Stop) - 高电平"))
        
        btn_gen = QPushButton("生成波形")
        btn_gen.clicked.connect(self.generate_waveform)
        btn_gen.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; margin-top: 10px;")
        vbox.addWidget(btn_gen)
        vbox.addStretch()
        settings.setLayout(vbox)
        
        # --- 右侧显示 (波形 + 教学) ---
        right_splitter = QSplitter(Qt.Vertical)
        
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("background-color: #f8f9fa; font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
        self.analysis_text.setPlaceholderText("点击生成波形以查看详细解析...")
        
        right_splitter.addWidget(plot_widget)
        right_splitter.addWidget(self.analysis_text)
        right_splitter.setStretchFactor(0, 3) # 波形占大部分
        right_splitter.setStretchFactor(1, 1) # 文字占小部分
        
        layout.addWidget(settings)
        layout.addWidget(right_splitter)

    def get_uart_sequence(self, hex_str, parity_mode="无校验 (None)"):
        """ 将 Hex 字符串转换为 UART 电平序列 (0/1) """
        try:
            data_bytes = bytes.fromhex(hex_str.strip().replace(' ', ''))
        except:
            return None, None, []

        T_BIT = 10
        t_seq = [0]
        lvl_seq = [1] # Idle High
        current_time = 10
        t_seq.append(current_time); lvl_seq.append(1)
        
        bits_info = [] # 记录每一位的逻辑值，用于教学分析
        
        for byte_val in data_bytes:
            # Start Bit (0)
            lvl_seq.append(0); t_seq.append(current_time)
            current_time += T_BIT; t_seq.append(current_time); lvl_seq.append(0)
            bits_info.append(0) 
            
            # Data bits (0-7)
            for i in range(8):
                bit = (byte_val >> i) & 0x01
                lvl_seq.append(bit); t_seq.append(current_time)
                current_time += T_BIT; t_seq.append(current_time); lvl_seq.append(bit)
                bits_info.append(bit)
            
            # Parity Bit
            if parity_mode != "无校验 (None)":
                ones = bin(byte_val).count('1')
                if "偶" in parity_mode: # Even
                    parity_bit = 1 if (ones % 2) != 0 else 0
                else: # Odd
                    parity_bit = 0 if (ones % 2) != 0 else 1
                lvl_seq.append(parity_bit); t_seq.append(current_time)
                current_time += T_BIT; t_seq.append(current_time); lvl_seq.append(parity_bit)
                bits_info.append(parity_bit)
            
            # Stop Bit (1)
            lvl_seq.append(1); t_seq.append(current_time)
            current_time += T_BIT; t_seq.append(current_time); lvl_seq.append(1)
            bits_info.append(1)
            
        current_time += T_BIT; t_seq.append(current_time); lvl_seq.append(1)
        return t_seq, lvl_seq, data_bytes

    def generate_waveform(self):
        self.canvas.init_canvas()
        self.canvas.axes.set_title(f"SCI (UART) 全双工波形演示")
        
        analysis_log = []
        analysis_log.append("🔍 SCI (UART) 波形原理深度解析:")
        analysis_log.append("========================================")
        analysis_log.append("📌 核心逻辑: 空闲(Idle)为高电平(1)，起始位(Start)拉低(0)，停止位(Stop)拉高(1)。低位(LSB)先发。")
        analysis_log.append("📌 交互说明: SCI是全双工通信，TX和RX是两条独立的线。TX的波形完全取决于MCU发什么，RX的波形取决于外部发给了MCU什么。")

        # 1. 生成 TX 波形
        parity_mode = self.cmb_parity.currentText()
        t_tx, l_tx, bytes_tx = self.get_uart_sequence(self.txt_tx.text(), parity_mode)
        if t_tx:
            self.canvas.draw_digital_channel(t_tx, l_tx, y_offset=2.5, label="TX (MCU发出)", color='#2ca02c')
            if len(t_tx) > 2:
                self.canvas.add_bit_label(15, 3.6, "Start", "gray", fontsize=6)
            
            # TX 分析
            analysis_log.append(f"\n👉 [TX 通道分析] MCU 发送数据: {self.txt_tx.text()}")
            for b in bytes_tx:
                analysis_log.append(f"   • 发送 0x{b:02X} (二进制: {b:08b}):")
                if b == 0x55:
                    analysis_log.append("     💡 为什么像方波？因为 0x55 的二进制是 01010101。配合Start(0)和Stop(1)，电平在0和1之间以最高频率跳变。")
                elif b == 0x00:
                    analysis_log.append("     💡 为什么有长低电平？数据全0。加上Start(0)，会形成连续9个位宽的低电平，只有Stop(1)会短暂拉高。")
                elif b == 0xFF:
                    analysis_log.append("     💡 为什么几乎全是高电平？数据全1。Start(0)拉低瞬间后，数据位全1，加上Stop(1)和Idle(1)，整体看起来就是一直高电平，中间偶尔有个窄脉冲(Start)。")
                else:
                    ones = bin(b).count('1')
                    analysis_log.append(f"     - 包含 {ones} 个高电平位，{8-ones} 个低电平位。")
                if parity_mode != "无校验 (None)":
                    ones = bin(b).count('1')
                    p_bit = 1 if (ones % 2) != 0 else 0
                    if "奇" in parity_mode: p_bit = 1 - p_bit
                    analysis_log.append(f"     💡 奇偶校验 ({parity_mode}): 数据中1的个数是{ones}，因此校验位电平为 {p_bit}。")

        # 2. 生成 RX 波形
        t_rx, l_rx, bytes_rx = self.get_uart_sequence(self.txt_rx.text(), parity_mode)
        if t_rx:
            self.canvas.draw_digital_channel(t_rx, l_rx, y_offset=0.5, label="RX (MCU接收)", color='#d62728')
            
            # RX 分析
            analysis_log.append(f"\n👉 [RX 通道分析] MCU 接收数据: {self.txt_rx.text()}")
            analysis_log.append("   (注: 这是外部设备(如上位机)发给MCU的波形，如果MCU的TX接了上位机的RX，那么上位机收到的波形就是上面绿色的TX波形)")
            for b in bytes_rx:
                if b == 0xFF:
                     analysis_log.append(f"   • 收到 0x{b:02X}: ⚠️ 这就是你看到的'高电平居多'现象。")
                     analysis_log.append("     原因: UART空闲是高电平。0xFF (11111111) 数据位全是高，停止位也是高。")
                     analysis_log.append("     👉 整个传输过程中，只有【起始位】那 1/10 的时间是低电平，其余 90% 时间都是高电平！")
                else:
                     analysis_log.append(f"   • 收到 0x{b:02X}: 正常数据帧。")

        self.canvas.axes.set_ylim(-0.5, 4.5)
        self.canvas.draw()
        self.analysis_text.setText("\n".join(analysis_log))

# =============================================================================
# 2. SPI 面板
# =============================================================================
class SPIPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        settings = QGroupBox("SPI 设置")
        settings.setFixedWidth(280)
        vbox = QVBoxLayout()
        
        vbox.addWidget(QLabel("MOSI 发送数据 (Hex):"))
        self.txt_hex = QLineEdit("A5 00")
        vbox.addWidget(self.txt_hex)
        
        vbox.addWidget(QLabel("MISO 接收数据 (Hex):"))
        self.txt_miso = QLineEdit("00 5A")
        vbox.addWidget(self.txt_miso)
        
        grp_cpol = QGroupBox("CPOL (时钟极性)"); vb_cpol = QVBoxLayout()
        self.rb_cpol0 = QRadioButton("0: 空闲低电平 (Low)"); self.rb_cpol1 = QRadioButton("1: 空闲高电平 (High)")
        self.rb_cpol0.setChecked(True); vb_cpol.addWidget(self.rb_cpol0); vb_cpol.addWidget(self.rb_cpol1)
        grp_cpol.setLayout(vb_cpol); vbox.addWidget(grp_cpol)
        
        grp_cpha = QGroupBox("CPHA (时钟相位)"); vb_cpha = QVBoxLayout()
        self.rb_cpha0 = QRadioButton("0: 第1个跳变沿采样"); self.rb_cpha1 = QRadioButton("1: 第2个跳变沿采样")
        self.rb_cpha0.setChecked(True); vb_cpha.addWidget(self.rb_cpha0); vb_cpha.addWidget(self.rb_cpha1)
        grp_cpha.setLayout(vb_cpha); vbox.addWidget(grp_cpha)
        
        btn_gen = QPushButton("生成波形")
        btn_gen.clicked.connect(self.generate_waveform)
        btn_gen.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        vbox.addWidget(btn_gen)
        vbox.addStretch()
        settings.setLayout(vbox)
        
        # --- 右侧显示 ---
        right_splitter = QSplitter(Qt.Vertical)
        
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("background-color: #f8f9fa; font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
        
        right_splitter.addWidget(plot_widget)
        right_splitter.addWidget(self.analysis_text)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)

        layout.addWidget(settings)
        layout.addWidget(right_splitter)

    def generate_waveform(self):
        try: 
            data_bytes = bytes.fromhex(self.txt_hex.text().replace(' ', ''))
            miso_bytes = bytes.fromhex(self.txt_miso.text().replace(' ', ''))
            
            # Pad miso_bytes with 0s or truncate to match length of data_bytes
            if len(miso_bytes) < len(data_bytes):
                miso_bytes += bytes([0] * (len(data_bytes) - len(miso_bytes)))
            elif len(miso_bytes) > len(data_bytes):
                miso_bytes = miso_bytes[:len(data_bytes)]
        except ValueError:
            self.canvas.init_canvas()
            self.analysis_text.setText("❌ 错误: 无效的十六进制输入，请检查输入格式。")
            return
        except Exception: return
        
        cpol = 1 if self.rb_cpol1.isChecked() else 0
        cpha = 1 if self.rb_cpha1.isChecked() else 0
        self.canvas.init_canvas()
        self.canvas.axes.set_title(f"SPI Mode {cpol*2+cpha} (CPOL={cpol}, CPHA={cpha})")
        
        analysis_log = []
        analysis_log.append(f"🔍 SPI 模式解析 (Mode {cpol*2+cpha}):")
        analysis_log.append("========================================")
        
        # CPOL 解析
        if cpol == 0:
            analysis_log.append("1. CPOL=0 (时钟极性):")
            analysis_log.append("   - 空闲状态下，SCLK 保持低电平(Low)。")
            analysis_log.append("   - 只有在传输数据时才会产生正脉冲。")
        else:
            analysis_log.append("1. CPOL=1 (时钟极性):")
            analysis_log.append("   - 空闲状态下，SCLK 保持高电平(High)。")
            analysis_log.append("   - 这是一个常见的坑：如果测量时发现时钟一直是高电平，可能就是CPOL=1而非死机。")
            
        # CPHA 解析
        edge_str = "上升沿" if (cpol==0 and cpha==0) or (cpol==1 and cpha==1) else "下降沿"
        sample_edge = "第1个" if cpha == 0 else "第2个"
        
        analysis_log.append(f"\n2. CPHA={cpha} (时钟相位):")
        analysis_log.append(f"   - 数据采样发生在时钟的【{sample_edge}跳变沿】。")
        analysis_log.append(f"   - 在本例中，MCU会在 SCLK 的【{edge_str}】读取 MOSI/MISO 的电平。")
        if cpha == 0:
            analysis_log.append("   - ⚠️ 注意: 因为是第1个沿采样，数据必须在时钟跳变前就已经准备好(Setup)。")
        else:
            analysis_log.append("   - ⚠️ 注意: 数据在第1个沿变化，在第2个沿稳定被采样。")
            
        analysis_log.append(f"\n3. 全双工通信 (Full-Duplex):")
        analysis_log.append(f"   - 在 SCLK 驱动下，主机发出 {len(data_bytes)} 字节数据，同时从机返回等量字节。")
        analysis_log.append("   - MISO (Master In Slave Out) 受同一个 SCLK 和 CS 同步，体现了 SPI 的全双工特性。")
        
        Y_CS, Y_CLK, Y_MISO, Y_MOSI = 4.5, 3.0, 1.5, 0.0
        T_HALF, T_PERIOD = 10, 20
        
        t_cs=[0]; l_cs=[1]; t_clk=[0]; l_clk=[cpol]; t_mosi=[0]; l_mosi=[0]; t_miso=[0]; l_miso=[0]
        curr_t = 10
        
        # CS Active
        t_cs.extend([curr_t, curr_t]); l_cs.extend([1, 0])
        t_clk.append(curr_t); l_clk.append(cpol)
        t_mosi.append(curr_t); l_mosi.append(0)
        t_miso.append(curr_t); l_miso.append(0)
        curr_t += T_HALF
        
        for idx, byte_val in enumerate(data_bytes):
            miso_val = miso_bytes[idx]
            for i in range(7, -1, -1):
                bit = (byte_val >> i) & 1
                miso_bit = (miso_val >> i) & 1
                e1 = curr_t; e2 = curr_t + T_HALF
                
                # CLK
                t_clk.extend([e1, e1, e2, e2])
                l_clk.extend([cpol, 1-cpol, 1-cpol, cpol])
                
                # MOSI & MISO Sample
                if cpha == 0:
                    t_mosi.extend([e1, e1, e1+T_PERIOD]); l_mosi.extend([l_mosi[-1], bit, bit])
                    t_miso.extend([e1, e1, e1+T_PERIOD]); l_miso.extend([l_miso[-1], miso_bit, miso_bit])
                    self.canvas.add_sampling_mark(e1, Y_MOSI, Y_CLK+0.8)
                else:
                    t_mosi.extend([e1, e1, e1+T_PERIOD]); l_mosi.extend([l_mosi[-1], bit, bit]) 
                    t_miso.extend([e1, e1, e1+T_PERIOD]); l_miso.extend([l_miso[-1], miso_bit, miso_bit])
                    self.canvas.add_sampling_mark(e2, Y_MOSI, Y_CLK+0.8)
                
                self.canvas.add_bit_label(curr_t+T_HALF, Y_MOSI+0.9, f"{bit}", color="green")
                self.canvas.add_bit_label(curr_t+T_HALF, Y_MISO+0.9, f"{miso_bit}", color="orange")
                curr_t += T_PERIOD

        curr_t += T_HALF
        t_cs.extend([curr_t, curr_t, curr_t+10]); l_cs.extend([0, 1, 1])
        t_clk.append(t_cs[-1]); l_clk.append(cpol)
        t_mosi.append(t_cs[-1]); l_mosi.append(l_mosi[-1])
        t_miso.append(t_cs[-1]); l_miso.append(l_miso[-1])
        
        self.canvas.draw_digital_channel(t_cs, l_cs, Y_CS, "CS (片选)", 'purple')
        self.canvas.draw_digital_channel(t_clk, l_clk, Y_CLK, "SCLK (时钟)", 'blue')
        self.canvas.draw_digital_channel(t_miso, l_miso, Y_MISO, "MISO (从机出)", 'orange')
        self.canvas.draw_digital_channel(t_mosi, l_mosi, Y_MOSI, "MOSI (主机出)", 'green')
        self.canvas.axes.set_ylim(-0.5, 6.0)
        self.canvas.draw()
        self.analysis_text.setText("\n".join(analysis_log))

# =============================================================================
# 3. IIC (I2C) 面板
# =============================================================================
class IICToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        settings = QGroupBox("IIC (I2C) 设置")
        settings.setFixedWidth(280)
        vbox = QVBoxLayout()
        
        vbox.addWidget(QLabel("设备地址 (7-bit Hex):"))
        self.txt_addr = QLineEdit("50")
        vbox.addWidget(self.txt_addr)
        
        self.chk_read = QCheckBox("读操作 (Read=1)")
        vbox.addWidget(self.chk_read)
        
        vbox.addWidget(QLabel("内部寄存器地址 (Hex):"))
        self.txt_reg = QLineEdit("00")
        vbox.addWidget(self.txt_reg)
        
        vbox.addWidget(QLabel("数据 (Hex, 空格分隔多字节):"))
        self.txt_data = QLineEdit("FC 11")
        vbox.addWidget(self.txt_data)
        
        btn_gen = QPushButton("生成波形")
        btn_gen.clicked.connect(self.generate_waveform)
        btn_gen.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        vbox.addWidget(btn_gen)
        
        vbox.addWidget(QLabel("\n图例:\n黄色: 地址段\n青色: 数据段\n灰色: 应答(ACK/NACK)"))
        vbox.addStretch()
        settings.setLayout(vbox)
        
        # --- 右侧显示 ---
        right_splitter = QSplitter(Qt.Vertical)
        
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("background-color: #f8f9fa; font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
        
        right_splitter.addWidget(plot_widget)
        right_splitter.addWidget(self.analysis_text)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)

        layout.addWidget(settings)
        layout.addWidget(right_splitter)

    def generate_waveform(self):
        try:
            addr = int(self.txt_addr.text(), 16)
            reg_val = int(self.txt_reg.text().replace(' ', ''), 16)
            data_str = self.txt_data.text().strip()
            if not data_str: data_bytes = b''
            else: data_bytes = bytes.fromhex(data_str.replace(' ', ''))
        except ValueError:
            self.canvas.init_canvas()
            self.analysis_text.setText("❌ 错误: 无效的十六进制输入，请检查输入格式。")
            return
        except Exception: return
        
        is_read = self.chk_read.isChecked()
        
        self.canvas.init_canvas()
        self.canvas.axes.set_title("IIC (I2C) - 完整读/写时序序列图")
        
        analysis_log = []
        analysis_log.append("🔍 IIC (I2C) 协议深度解析:")
        analysis_log.append("========================================")
        analysis_log.append("📌 核心物理特性: Open-Drain (开漏输出)。")
        analysis_log.append("   - ACK 是低电平，因为从机通过拉低总线来回应 '收到'。")
        
        analysis_log.append("\n📌 时序关键点:")
        if is_read:
            analysis_log.append("   - 操作: 复合读 (Random Read/Register Read)")
            analysis_log.append("   - 流程: Start -> DevAddr(W) -> RegAddr -> Repeated Start (Sr) -> DevAddr(R) -> Data -> Stop")
        else:
            analysis_log.append("   - 操作: 连续写 (Page Write)")
            analysis_log.append("   - 流程: Start -> DevAddr(W) -> RegAddr -> Data (多字节) -> Stop")

        Y_SCL = 2.0
        Y_SDA = 0.0
        T_Q = 10 # Quarter period
        
        t_scl = [0]; l_scl = [1]
        t_sda = [0]; l_sda = [1]
        curr_t = 10
        
        def push_start(label="START", color="red"):
            nonlocal curr_t
            t_scl.append(curr_t); l_scl.append(1)
            t_sda.extend([curr_t, curr_t]); l_sda.extend([1, 0])
            self.canvas.add_bit_label(curr_t, Y_SDA-0.5, label, color)
            
            curr_t += T_Q
            t_scl.extend([curr_t, curr_t]); l_scl.extend([1, 0])
            t_sda.append(curr_t); l_sda.append(0)

        def push_stop():
            nonlocal curr_t
            t_sda.extend([curr_t, curr_t]); l_sda.extend([l_sda[-1], 0])
            curr_t += T_Q
            t_scl.extend([curr_t, curr_t]); l_scl.extend([0, 1])
            t_sda.append(curr_t); l_sda.append(0)
            curr_t += T_Q
            t_sda.extend([curr_t, curr_t]); l_sda.extend([0, 1])
            t_scl.append(curr_t); l_scl.append(1)
            self.canvas.add_bit_label(curr_t, Y_SDA-0.5, "STOP", "red")
            curr_t += 10
            t_scl.append(curr_t); l_scl.append(1)
            t_sda.append(curr_t); l_sda.append(1)

        def send_byte(val):
            nonlocal curr_t
            start_x = curr_t
            for i in range(7, -1, -1):
                bit = (val >> i) & 1
                t_sda.extend([curr_t, curr_t])
                l_sda.extend([l_sda[-1], bit])
                t_scl.append(curr_t); l_scl.append(0)
                
                curr_t += T_Q
                t_scl.extend([curr_t, curr_t]); l_scl.extend([0, 1])
                t_sda.append(curr_t); l_sda.append(bit)
                
                self.canvas.add_sampling_mark(curr_t + T_Q/2, Y_SCL, Y_SDA+0.5)
                self.canvas.add_bit_label(curr_t + T_Q/2, Y_SDA + 0.9, str(bit))
                
                curr_t += T_Q
                t_scl.extend([curr_t, curr_t]); l_scl.extend([1, 0])
                t_sda.append(curr_t); l_sda.append(bit)
            return start_x, curr_t

        def push_ack(is_nack=False, label="ACK", is_master=False):
            nonlocal curr_t
            ack_bit = 1 if is_nack else 0
            t_sda.extend([curr_t, curr_t]); l_sda.extend([l_sda[-1], ack_bit])
            curr_t += T_Q
            t_scl.extend([curr_t, curr_t]); l_scl.extend([0, 1])
            t_sda.append(curr_t); l_sda.append(ack_bit)
            self.canvas.add_bit_label(curr_t + T_Q/2, Y_SDA + 0.9, label, "gray" if not is_nack else "red")
            
            curr_t += T_Q
            t_scl.extend([curr_t, curr_t]); l_scl.extend([1, 0])
            t_sda.append(curr_t); l_sda.append(ack_bit)
            
        # ---------- Sequence Execution ----------
        push_start("START", "red")
        
        # 1. Device Addr (Write)
        addr_write = (addr << 1) | 0
        x1, x2 = send_byte(addr_write)
        self.canvas.add_region_highlight(x1, x2, "Dev Addr(W)", "yellow", y_max=3.5)
        push_ack(is_nack=False, label="ACK(S)")
        
        # 2. Reg Addr
        x1, x2 = send_byte(reg_val)
        self.canvas.add_region_highlight(x1, x2, "Reg Addr", "orange", y_max=3.5)
        push_ack(is_nack=False, label="ACK(S)")
        
        if is_read:
            # Repeated Start
            t_sda.extend([curr_t, curr_t]); l_sda.extend([l_sda[-1], 1])
            curr_t += T_Q
            t_scl.extend([curr_t, curr_t]); l_scl.extend([0, 1])
            t_sda.append(curr_t); l_sda.append(1)
            curr_t += T_Q
            push_start("Sr (Repeated Start)", "magenta")
            
            # Dev Addr (Read)
            addr_read = (addr << 1) | 1
            x1, x2 = send_byte(addr_read)
            self.canvas.add_region_highlight(x1, x2, "Dev Addr(R)", "yellow", y_max=3.5)
            push_ack(is_nack=False, label="ACK(S)")
            
            for i, d in enumerate(data_bytes):
                x1, x2 = send_byte(d)
                self.canvas.add_region_highlight(x1, x2, f"Data[{i}]", "cyan", y_max=3.5)
                is_last = (i == len(data_bytes) - 1)
                push_ack(is_nack=is_last, label="NACK(M)" if is_last else "ACK(M)", is_master=True)
                
        else: # Write
            for i, d in enumerate(data_bytes):
                x1, x2 = send_byte(d)
                self.canvas.add_region_highlight(x1, x2, f"Data[{i}]", "cyan", y_max=3.5)
                push_ack(is_nack=False, label="ACK(S)")
                
        push_stop()

        self.canvas.draw_digital_channel(t_scl, l_scl, Y_SCL, "SCL", 'orange')
        self.canvas.draw_digital_channel(t_sda, l_sda, Y_SDA, "SDA", 'blue')
        self.canvas.axes.set_ylim(-1, 3.5)
        self.canvas.draw()
        self.analysis_text.setText("\n".join(analysis_log))

# =============================================================================
# 4. CAN 面板 (含位填充 + 物理差分波形)
# =============================================================================
class CANToolPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        settings = QGroupBox("CAN Bus (ISO 11898) 设置")
        settings.setFixedWidth(280)
        vbox = QVBoxLayout()
        
        vbox.addWidget(QLabel("帧 ID (Hex):"))
        self.txt_id = QLineEdit("123")
        vbox.addWidget(self.txt_id)
        
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["标准帧 (11-bit)", "扩展帧 (29-bit)"])
        vbox.addWidget(QLabel("帧格式:"))
        vbox.addWidget(self.cmb_format)
        
        vbox.addWidget(QLabel("数据载荷 (Hex):"))
        self.txt_data = QLineEdit("11 22 33")
        vbox.addWidget(self.txt_data)
        
        btn_gen = QPushButton("生成 CAN 全引脚波形")
        btn_gen.clicked.connect(self.generate_waveform)
        btn_gen.setStyleSheet("background-color: #d62728; color: white; font-weight: bold; margin-top: 10px;")
        vbox.addWidget(btn_gen)
        
        vbox.addWidget(QLabel("\n显示内容:"))
        vbox.addWidget(QLabel("1. CAN_TX (MCU 逻辑)"))
        vbox.addWidget(QLabel("2. CAN_RX (MCU 逻辑)"))
        vbox.addWidget(QLabel("3. CAN_H (总线, 2.5V/3.5V)"))
        vbox.addWidget(QLabel("4. CAN_L (总线, 1.5V/2.5V)"))
        
        vbox.addWidget(QLabel("\n✨ 特性: 自动位填充 & ACK 模拟"))
        vbox.addStretch()
        settings.setLayout(vbox)
        
        # --- 右侧显示 ---
        right_splitter = QSplitter(Qt.Vertical)
        
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = MplCanvas(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setStyleSheet("background-color: #f8f9fa; font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
        
        right_splitter.addWidget(plot_widget)
        right_splitter.addWidget(self.analysis_text)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)

        layout.addWidget(settings)
        layout.addWidget(right_splitter)

    def generate_waveform(self):
        try:
            can_id = int(self.txt_id.text(), 16)
            data_str = self.txt_data.text().replace(' ', '')
            data_bytes = bytes.fromhex(data_str)
        except ValueError:
            self.canvas.init_canvas()
            self.analysis_text.setText("❌ 错误: 无效的十六进制输入，请检查 ID 或数据格式。")
            return
        except Exception: return
        
        self.canvas.init_canvas()
        self.canvas.axes.set_title("CAN Bus - 完整帧结构 & 物理层电平")
        
        analysis_log = []
        analysis_log.append("🔍 CAN 总线物理层与链路层解析:")
        analysis_log.append("========================================")
        analysis_log.append("1. 显性 vs 隐性 (Dominant vs Recessive):")
        analysis_log.append("   - 逻辑 0 = 显性 (Dominant)。CAN_H=3.5V, CAN_L=1.5V (压差2V)。")
        analysis_log.append("   - 逻辑 1 = 隐性 (Recessive)。CAN_H=2.5V, CAN_L=2.5V (压差0V)。")
        analysis_log.append("   - '线与'逻辑：只要有一个节点发显性(0)，总线就是显性(0)。")
        
        analysis_log.append("\n2. 位填充 (Bit Stuffing):")
        analysis_log.append("   - 规则：连续发送 5 个相同逻辑位后，硬件自动插入一个反向位。")
        analysis_log.append("   - 目的：防止长时间电平不跳变导致接收端同步丢失 (CAN没有独立时钟线)。")

        # --- 1. 构建逻辑位流 (Before Stuffing) ---
        raw_bits = []
        raw_bits.append(0) # SOF
        
        is_extended = self.cmb_format.currentIndex() == 1
        
        if not is_extended:
            # Standard Frame (11-bit ID)
            for i in range(10, -1, -1): raw_bits.append((can_id >> i) & 1)
            raw_bits.extend([0, 0, 0]) # RTR(0), IDE(0), r0(0)
            analysis_log.append("\n3. 帧格式: 标准帧 (11-bit ID)")
            analysis_log.append("   - 结构: SOF -> ID(11) -> RTR -> IDE(0) -> r0 -> DLC(4) -> Data -> CRC")
        else:
            # Extended Frame (29-bit ID)
            id_a = (can_id >> 18) & 0x7FF
            id_b = can_id & 0x3FFFF
            
            # Base ID (11 bits)
            for i in range(10, -1, -1): raw_bits.append((id_a >> i) & 1)
            raw_bits.extend([0, 1]) # SRR(0/1 for data, typically 1 but let's keep it simple as recessive), IDE(1)
            # IDE is recessive in extended frame, SRR is also recessive in extended frame
            raw_bits[-2:] = [1, 1] 
            
            # Extended ID (18 bits)
            for i in range(17, -1, -1): raw_bits.append((id_b >> i) & 1)
            raw_bits.extend([0, 0, 0]) # RTR(0), r1(0), r0(0)
            analysis_log.append(f"\n3. 帧格式: 扩展帧 (29-bit ID), ID=0x{can_id:08X}")
            analysis_log.append("   - 结构: SOF -> BaseID(11) -> SRR(1) -> IDE(1) -> ExtID(18) -> RTR(0) -> r1 -> r0 -> DLC(4) -> Data")
            analysis_log.append("   - 注意: SRR (Substitute Remote Request) 和 IDE (Identifier Extension) 在此必须为隐性(1)。")
        
        # DLC (4 bits)
        dlc = len(data_bytes)
        for i in range(3, -1, -1): raw_bits.append((dlc >> i) & 1)
        
        # Data Payload
        for b in data_bytes:
            for i in range(7, -1, -1): raw_bits.append((b >> i) & 1)
            
        # CRC (15 bits) - Dummy 0x4555 for visual
        crc = 0x4555 
        for i in range(14, -1, -1): raw_bits.append((crc >> i) & 1)
        
        # --- 2. Bit Stuffing (TX View) ---
        stuffed_bits = []
        stuff_indices = [] 
        consecutive = 1
        last_bit = raw_bits[0]
        stuffed_bits.append(last_bit)
        
        for i in range(1, len(raw_bits)):
            bit = raw_bits[i]
            if bit == last_bit:
                consecutive += 1
            else:
                consecutive = 1
                last_bit = bit
            
            stuffed_bits.append(bit)
            
            if consecutive == 5:
                stuff_bit = 1 - last_bit
                stuffed_bits.append(stuff_bit)
                stuff_indices.append(len(stuffed_bits) - 1)
                consecutive = 1 
                last_bit = stuff_bit 
        
        if stuff_indices:
             analysis_log.append(f"\n👉 检测到位填充! 共发生了 {len(stuff_indices)} 次。")
             analysis_log.append("   - 图中红色高亮区域即为填充位 (Stuff Bit)。")
             analysis_log.append("   - 这些位由硬件自动插入和剔除，软件层不可见。")
        else:
             analysis_log.append("\n👉 本次帧数据分布均匀，未触发位填充机制。")

        # --- 3. 添加尾部 (CRC Del, ACK, EOF) ---
        idx_crc_del = len(stuffed_bits) 
        stuffed_bits.append(1) # CRC Delimiter
        
        idx_ack_slot = len(stuffed_bits)
        stuffed_bits.append(1) # ACK Slot (TX sends 1)
        
        stuffed_bits.append(1) # ACK Delimiter
        stuffed_bits.extend([1]*7) # EOF
        
        # --- 4. 生成时间序列和电平 ---
        T_BIT = 10
        t_seq = [0]; t_seq.append(10)
        
        # 初始化电平序列 (Idle 状态)
        l_tx = [1, 1]     # Logic 1
        l_rx = [1, 1]     # Logic 1
        l_can_h = [2.5, 2.5] # 2.5V Recessive
        l_can_l = [2.5, 2.5] # 2.5V Recessive
        
        curr_t = 10
        
        for idx, bit in enumerate(stuffed_bits):
            # 确定当前位的逻辑值
            # 默认情况下，TX = bit, RX = bit (Loopback)
            tx_bit = bit
            rx_bit = bit
            
            # 特殊处理 ACK Slot:
            # TX 发送 1 (释放总线)
            # RX 监测到 0 (被其他节点拉低 - 模拟正常通信)
            if idx == idx_ack_slot:
                tx_bit = 1 # Transmitter releases
                rx_bit = 0 # Bus is driven dominant by receiver
            
            # 物理总线电平由 "实际总线状态" 决定
            bus_bit = rx_bit 
            
            # 映射到电压
            if bus_bit == 0:
                v_h, v_l = 3.5, 1.5
            else:
                v_h, v_l = 2.5, 2.5
            
            # 添加点
            t_seq.extend([curr_t, curr_t + T_BIT])
            l_tx.extend([tx_bit, tx_bit])
            l_rx.extend([rx_bit, rx_bit])
            l_can_h.extend([v_h, v_h])
            l_can_l.extend([v_l, v_l])
            
            # 标注
            mid_t = curr_t + T_BIT/2
            if idx == 0: self.canvas.add_bit_label(mid_t, -0.2, "SOF")
            if idx in stuff_indices:
                self.canvas.add_region_highlight(curr_t, curr_t+T_BIT, "", "red", alpha=0.3, y_min=0, y_max=8)
                self.canvas.axes.text(mid_t, 7.8, "Stuff", fontsize=6, ha='center', color='red')
            if idx == idx_ack_slot:
                self.canvas.add_region_highlight(curr_t, curr_t+T_BIT, "ACK", "green", alpha=0.3, y_min=0, y_max=8)
            
            curr_t += T_BIT

        self.canvas.draw_digital_channel(t_seq, l_tx, y_offset=6.0, label="CAN_TX", color='#2ca02c') # Green
        self.canvas.draw_digital_channel(t_seq, l_rx, y_offset=4.5, label="CAN_RX", color='#1f77b4') # Blue
        
        # 绘制模拟电压 (is_analog=True)
        self.canvas.draw_digital_channel(t_seq, l_can_h, y_offset=0, label="CAN_H (V)", color='#d62728', is_analog=True) # Red
        self.canvas.draw_digital_channel(t_seq, l_can_l, y_offset=0, label="CAN_L (V)", color='#9467bd', is_analog=True) # Purple
        
        self.canvas.axes.set_ylim(0, 8.0)
        self.canvas.draw()
        self.analysis_text.setText("\n".join(analysis_log))

# =============================================================================
# 主容器
# =============================================================================
class WaveformPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ccc; background: white; } 
            QTabBar::tab { height: 30px; min-width: 80px; }
        """)
        
        self.tabs.addTab(SCIPanel(), "SCI (UART)")
        self.tabs.addTab(SPIPanel(), "SPI")
        self.tabs.addTab(IICToolPanel(), "IIC (I2C)")
        self.tabs.addTab(CANToolPanel(), "CAN Bus")
        
        layout.addWidget(self.tabs)