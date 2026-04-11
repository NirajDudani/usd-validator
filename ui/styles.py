import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CHECK_ICON = os.path.join(_HERE, "resources", "check.svg").replace("\\", "/")
_ARROW_DOWN = os.path.join(_HERE, "resources", "arrow_down.svg").replace("\\", "/")

STYLESHEET = f"""
    QMainWindow {{
        background-color: #ffffff;
    }}
    QWidget {{
        background-color: #ffffff;
        color: #1e1e1e;
        font-family: Arial;
        font-size: 13px;
    }}
    QGroupBox {{
        border: 1px solid #cccccc;
        border-radius: 5px;
        margin-top: 10px;
        padding: 10px;
        font-weight: bold;
        color: #1e1e1e;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }}
    QLineEdit {{
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 8px;
        color: #1e1e1e;
    }}
    QPushButton {{
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: #1084d8;
    }}
    QPushButton:disabled {{
        background-color: #e0e0e0;
        color: #999999;
    }}
    QTreeWidget {{
        background-color: #ffffff;
        border: 1px solid #cccccc;
        alternate-background-color: #f5f5f5;
    }}
    QTreeWidget::item {{
        padding: 4px;
    }}
    QTreeWidget::item:selected {{
        background-color: #0078d4;
        color: white;
    }}
    QHeaderView::section {{
        background-color: #e8e8e8;
        color: #1e1e1e;
        padding: 6px;
        border: 1px solid #cccccc;
        font-weight: bold;
    }}
    QComboBox {{
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 5px;
        color: #1e1e1e;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 24px;
        border-left: 1px solid #cccccc;
        border-top-right-radius: 3px;
        border-bottom-right-radius: 3px;
        background-color: #e8e8e8;
    }}
    QComboBox::down-arrow {{
        image: url("{_ARROW_DOWN}");
        width: 10px;
        height: 6px;
    }}
    QCheckBox::indicator {{
        width: 14px;
        height: 14px;
        border: 2px solid #888888;
        border-radius: 2px;
        background-color: #ffffff;
    }}
    QCheckBox::indicator:checked {{
        border-color: #0078d4;
        background-color: #ffffff;
        image: url("{_CHECK_ICON}");
    }}
    QStatusBar {{
        background-color: #0078d4;
        color: white;
        font-size: 12px;
    }}
    #errorLabel {{
        color: #cc0000;
        font-weight: bold;
        font-size: 14px;
    }}
    #warningLabel {{
        color: #b8860b;
        font-weight: bold;
        font-size: 14px;
    }}
    #passLabel {{
        color: #2e7d32;
        font-weight: bold;
        font-size: 14px;
    }}
    QListWidget {{
        background-color: #ffffff;
        border: none;
        border-right: 1px solid #cccccc;
        outline: 0;
    }}
    QListWidget::item {{
        padding: 8px 12px;
        color: #1e1e1e;
    }}
    QListWidget::item:selected {{
        background-color: #0078d4;
        color: white;
    }}
    QListWidget::item:hover:!selected {{
        background-color: #e8f0fe;
    }}
"""
