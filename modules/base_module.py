# modules/base_module.py

from gui.base_window import BaseWindow

class BaseModule(BaseWindow):
    """
    所有计算器功能模块的基类。
    继承自 BaseWindow，包含额外的模块元信息以支持动态加载和主界面网格布局。
    """
    # 模块元信息定义 (由具体子类实现)
    category = "未分类"         # 专业分组名称 (例如："1. 磁性元件与电源拓扑")
    display_name = "未命名模块"  # 主界面按钮显示的标题
    description = "无描述"       # 主界面按钮显示的副标题
    window_id = ""               # 唯一的模块ID (用于记录窗口开启状态等)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_module_ui()

    def init_module_ui(self):
        """
        子类重写此方法来进行特定的 UI 初始化。
        """
        pass
