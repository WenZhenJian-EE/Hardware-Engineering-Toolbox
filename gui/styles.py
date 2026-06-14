# gui/styles.py

STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f4f7f9;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    color: #333333;
}
QScrollArea { border: none; background: transparent; }
QLabel#GroupTitle {
    font-size: 14px;
    font-weight: bold;
    color: #2c3e50;
    margin-top: 15px;
    margin-bottom: 8px;
    padding-left: 8px;
    border-left: 5px solid #3498db;
    background-color: #eaf2f8;
    padding-top: 4px;
    padding-bottom: 4px;
    border-radius: 4px;
}
QPushButton#ToolButton {
    background-color: #ffffff;
    border: 1px solid #e1e8ed;
    border-radius: 8px;
    text-align: center;
    color: #2f3542;
    padding: 6px;
    line-height: 1.3;
}
QPushButton#ToolButton:hover {
    background-color: #ffffff;
    border: 1px solid #3498db;
    color: #2980b9;
    font-weight: bold;
}
QPushButton#ToolButton:pressed {
    background-color: #ebf5fb;
    border: 1px solid #a9cce3;
    margin-top: 1px; margin-left: 1px;
}
QPushButton#ToolButton:disabled {
    background-color: #f0f0f0;
    color: #bdc3c7;
    border: 1px dashed #dcdcdc;
}

/* 子窗口 TabWidget 统一样式 */
QTabWidget::pane {
    border: 1px solid #e1e4e8;
    background: #fff;
    border-radius: 6px;
}
QTabBar::tab {
    background: #f4f6f9;
    border: 1px solid #e1e4e8;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom-color: #ffffff;
    font-weight: bold;
    color: #3498db;
}

/* 结果框与警告框样式 */
QLineEdit[readOnly="true"] {
    background-color: #e8f8f5;
    font-weight: bold;
    color: #27ae60;
}
"""

STYLE_RESULT_OK = "background-color: #e8f8f5; font-weight: bold; color: #27ae60;"
STYLE_RESULT_WARN = "background-color: #fdebd0; font-weight: bold; color: #d35400;"
STYLE_RESULT_ALERT = "background-color: #fdedec; font-weight: bold; color: #c0392b;"
STYLE_RESULT_DEFAULT = "background-color: #ffffff; color: #333333;"
