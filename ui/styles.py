STYLESHEET = """
    QMainWindow {
        background-color: #ffffff;
    }
    QWidget {
        background-color: #ffffff;
        color: #1e1e1e;
        font-family: Arial;
        font-size: 13px;
    }
    QGroupBox {
        border: 1px solid #cccccc;
        border-radius: 5px;
        margin-top: 10px;
        padding: 10px;
        font-weight: bold;
        color: #1e1e1e;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    QLineEdit {
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 8px;
        color: #1e1e1e;
    }
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1084d8;
    }
    QPushButton:disabled {
        background-color: #e0e0e0;
        color: #999999;
    }
    QTreeWidget {
        background-color: #ffffff;
        border: 1px solid #cccccc;
        alternate-background-color: #f5f5f5;
    }
    QTreeWidget::item {
        padding: 4px;
    }
    QTreeWidget::item:selected {
        background-color: #0078d4;
        color: white;
    }
    QHeaderView::section {
        background-color: #e8e8e8;
        color: #1e1e1e;
        padding: 6px;
        border: 1px solid #cccccc;
        font-weight: bold;
    }
    QComboBox {
        background-color: #f5f5f5;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 5px;
        color: #1e1e1e;
    }
    QComboBox::drop-down {
        border: none;
    }
    QStatusBar {
        background-color: #0078d4;
        color: white;
        font-size: 12px;
    }
    #errorLabel {
        color: #cc0000;
        font-weight: bold;
        font-size: 14px;
    }
    #warningLabel {
        color: #b8860b;
        font-weight: bold;
        font-size: 14px;
    }
    #passLabel {
        color: #2e7d32;
        font-weight: bold;
        font-size: 14px;
    }
"""
