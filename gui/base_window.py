# gui/base_window.py

from PyQt5.QtWidgets import QWidget
from gui.styles import STYLESHEET
from gui.renderer import render_formula

class BaseWindow(QWidget):
    """
    所有计算器子窗口的基类。
    提供统一的主题样式加载与高性能的 LaTeX 公式渲染接口。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLESHEET)

    def render_formula(self, formula_str, target_height=45, **kwargs):
        """
        在界面中快速渲染 LaTeX 公式并返回 QPixmap。
        所有继承此类的子窗口都可以直接调用 self.render_formula(...)。
        """
        # 默认使用类中统一的字体大小和色调，但允许外部传参覆盖
        if 'color' not in kwargs:
            kwargs['color'] = '#2c3e50'  # 默认使用一致的深灰蓝色
        return render_formula(formula_str, target_height, **kwargs)
