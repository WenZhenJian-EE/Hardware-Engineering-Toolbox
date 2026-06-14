from modules.base_module import BaseModule
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon

# 导入所有通信子面板
from comm_sci_panel import SCIPanel
from comm_decoder_panel import DecoderPanel
from comm_bit_viewer import BitViewerPanel
from comm_crc_tool import CRCToolPanel
from comm_float_hex import FloatHexConverter
from comm_can_tool import CANToolPanel
from comm_spi_tool import SPIToolPanel
from comm_iic_tool import IICToolPanel
from comm_waveform_gen import WaveformPanel

class PowerCommTool(BaseModule):
    category = "4. 信号链、通信与传感 (Signal Chain, Comm & Sensing)"
    display_name = "通信助手"
    description = "多合一通信/寄存器/波形综合测试工具"
    window_id = "comm_powercomm"

    def init_module_ui(self):
        
        self.setWindowTitle("PowerComm - 电力电子通信调试助手 (Dev Edition)")
        self.resize(1100, 750)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建 Tab Widget
        self.tabs = QTabWidget()
        
        # 修复在 stylesheet 中设置 bold 引发的 tab 尺寸计算不足，导致长文本截断的问题
        font = self.tabs.font()
        font.setFamily("Microsoft YaHei")
        font.setPixelSize(13)
        font.setBold(True)
        self.tabs.setFont(font)

        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 6px 16px;
                min-width: 65px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-weight: bold;
                font-size: 13px;
                background-color: #f0f0f0;
                border: 1px solid #dcdcdc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #007bff;
                color: white;
                border-bottom-color: #007bff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e2e6ea;
            }
            QTabWidget::pane {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: #ffffff;
            }
        """)

        # 实例化并添加子标签页
        self._add_tab(SCIPanel, "发送 (Tx)")
        self._add_tab(DecoderPanel, "解码 (Rx)")
        self._add_tab(BitViewerPanel, "位域 (Bit)")
        self._add_tab(CRCToolPanel, "CRC")
        self._add_tab(FloatHexConverter, "浮点 (Conv)")
        self._add_tab(CANToolPanel, "CAN")
        self._add_tab(SPIToolPanel, "SPI")
        self._add_tab(IICToolPanel, "IIC")
        self._add_tab(WaveformPanel, "波形 (Gen)")

        main_layout.addWidget(self.tabs)

    def _add_tab(self, panel_class, title):
        try:
            panel = panel_class()
            self.tabs.addTab(panel, title)
        except Exception as e:
            from PyQt5.QtWidgets import QLabel
            error_lbl = QLabel(f"加载面板失败: {title}\n错误信息: {e}")
            error_lbl.setStyleSheet("color: red; padding: 10px; font-weight: bold;")
            self.tabs.addTab(error_lbl, title)
