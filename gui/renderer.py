# gui/renderer.py

import matplotlib
matplotlib.use('Agg') # 确保在 GUI 下不弹窗，绘图在后台线程安全完成

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from io import BytesIO
from functools import lru_cache
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class FormulaRenderer:
    """
    通用 LaTeX 公式渲染器 (带 LRU 缓存优化)
    所有模块共享此缓存，以避免由于重复生成 matplotlib Figure 导致的卡顿。
    """
    
    @staticmethod
    @lru_cache(maxsize=256)
    def render(formula_str, target_height=45, fontsize=16, color='#555555', dpi=200):
        """
        将 LaTeX 字符串渲染为 QPixmap。
        """
        try:
            # 1. 配置字体
            matplotlib.rcParams.update({
                'mathtext.default': 'regular', 
                'font.family': 'sans-serif',
                'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans']
            })

            # 2. 使用 Figure 对象直接绘图
            fig = Figure(figsize=(12, 1.5), dpi=dpi)
            canvas = FigureCanvasAgg(fig)
            
            # 3. 绘制文字 (居中)
            fig.text(0.5, 0.5, f'${formula_str}$', fontsize=fontsize, 
                     ha='center', va='center', color=color)
            
            # 4. 渲染到内存 buffer
            buf = BytesIO()
            fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0.1)
            
            # 5. 转换为 QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            
            # 6. 高质量缩放
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaledToHeight(target_height, Qt.SmoothTransformation)
                scaled_pixmap.setDevicePixelRatio(1.0)
                return scaled_pixmap
            return QPixmap()

        except Exception as e:
            print(f"[FormulaRenderer] Error rendering '{formula_str}': {e}")
            return QPixmap()

def render_formula(formula_str, target_height=45, **kwargs):
    return FormulaRenderer.render(formula_str, target_height, **kwargs)
