import sys
import os
from pxr import Usd
from PySide6 import QtWidgets, QtCore, QtGui



class USDValidator(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        # Store stage and file path
        self.stage = None
        self.current_file = None

        # Build UI
        self.setup_ui()
        self.apply_stylesheet()

    # ─────────────────────────────────────────────
    # UI SETUP
    # ─────────────────────────────────────────────

    def setup_ui(self):

        # Window settings
        self.setWindowTitle("USD Asset Validator v1.0")
        self.setMinimumSize(900, 700)

        # Central widget
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Section 1 — File loader
        file_section = self.build_file_section()
        main_layout.addWidget(file_section)

        # Section 2 — Action buttons
        button_section = self.build_button_section()
        main_layout.addWidget(button_section)

        # Section 3 — Results area
        results_section = self.build_results_section()
        main_layout.addWidget(results_section)

        # Section 4 — Summary bar
        summary_section = self.build_summary_section()
        main_layout.addWidget(summary_section)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — Open a USD file to begin")

    def build_file_section(self):
        group = QtWidgets.QGroupBox("USD File")
        layout = QtWidgets.QHBoxLayout(group)

        # File path input
        self.file_input = QtWidgets.QLineEdit()
        self.file_input.setPlaceholderText(
            "Select a USD file to validate..."
        )
        self.file_input.setReadOnly(True)
        layout.addWidget(self.file_input)

        # Browse button
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self.open_file)
        layout.addWidget(self.browse_btn)

        return group

    def build_button_section(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Validate button
        self.validate_btn = QtWidgets.QPushButton("▶  Run Validation")
        self.validate_btn.setFixedHeight(40)
        self.validate_btn.setEnabled(False)
        self.validate_btn.clicked.connect(self.run_validation)
        layout.addWidget(self.validate_btn)

        # Filter dropdown
        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItems([
            "Show All",
            "Errors Only",
            "Warnings Only",
            "Passed Only"
        ])
        self.filter_combo.setFixedWidth(150)
        self.filter_combo.currentTextChanged.connect(self.filter_results)
        layout.addWidget(self.filter_combo)

        layout.addStretch()

        # Export button
        self.export_btn = QtWidgets.QPushButton("Export Report")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setFixedWidth(150)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_report)
        layout.addWidget(self.export_btn)

        return widget

    def build_results_section(self):
        group = QtWidgets.QGroupBox("Validation Results")
        layout = QtWidgets.QVBoxLayout(group)

        # Results tree
        self.results_tree = QtWidgets.QTreeWidget()
        self.results_tree.setHeaderLabels(["Check", "Status", "Details"])
        self.results_tree.setColumnWidth(0, 250)
        self.results_tree.setColumnWidth(1, 100)
        self.results_tree.setAlternatingRowColors(True)
        self.results_tree.setAnimated(True)
        layout.addWidget(self.results_tree)

        return group

    def build_summary_section(self):
        group = QtWidgets.QGroupBox("Summary")
        layout = QtWidgets.QHBoxLayout(group)

        # Error count
        self.error_label = QtWidgets.QLabel("❌ Errors: 0")
        self.error_label.setObjectName("errorLabel")
        layout.addWidget(self.error_label)

        layout.addStretch()

        # Warning count
        self.warning_label = QtWidgets.QLabel("⚠️ Warnings: 0")
        self.warning_label.setObjectName("warningLabel")
        layout.addWidget(self.warning_label)

        layout.addStretch()

        # Pass count
        self.pass_label = QtWidgets.QLabel("✅ Passed: 0")
        self.pass_label.setObjectName("passLabel")
        layout.addWidget(self.pass_label)

        return group

    # ─────────────────────────────────────────────
    # FILE OPERATIONS
    # ─────────────────────────────────────────────

    def open_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open USD File",
            "",
            "USD Files (*.usd *.usda *.usdc *.usdz)"
        )

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            # Open the stage
            self.stage = Usd.Stage.Open(file_path)
            self.current_file = file_path

            # Update UI
            self.file_input.setText(file_path)
            self.validate_btn.setEnabled(True)

            # Count prims
            prim_count = sum(1 for _ in self.stage.Traverse())

            self.status_bar.showMessage(
                f"Loaded: {os.path.basename(file_path)}"
                f" | {prim_count} prims found"
            )

            # Clear previous results
            self.results_tree.clear()
            self.reset_summary()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error Loading File",
                f"Could not open USD file:\n{str(e)}"
            )

    # ─────────────────────────────────────────────
    # VALIDATION — PLACEHOLDER FOR NOW
    # ─────────────────────────────────────────────

    def run_validation(self):
        if not self.stage:
            return

        # Clear previous results
        self.results_tree.clear()
        self.reset_summary()

        self.status_bar.showMessage("Running validation...")

        # We will add checks here tomorrow
        # For now just show a placeholder result
        self.add_result(
            check_name="File Loaded",
            status="pass",
            message="USD file loaded successfully",
            details=[]
        )

        # Update summary
        self.update_summary()

        # Enable export
        self.export_btn.setEnabled(True)

        self.status_bar.showMessage("Validation complete")

    # ─────────────────────────────────────────────
    # RESULTS DISPLAY
    # ─────────────────────────────────────────────

    def add_result(self, check_name, status, message, details=None):

        # Status config
        status_config = {
            "pass":    ("✅ PASS",    "#6a9955"),
            "warning": ("⚠️ WARNING", "#dcdcaa"),
            "error":   ("❌ ERROR",   "#f44747"),
        }

        label, color = status_config.get(
            status, ("❓ UNKNOWN", "#888888")
        )

        # Create main row
        item = QtWidgets.QTreeWidgetItem(self.results_tree)
        item.setText(0, check_name)
        item.setText(1, label)
        item.setText(2, message)

        # Store status for filtering
        item.setData(0, QtCore.Qt.UserRole, status)

        # Color the row
        for col in range(3):
            item.setForeground(col, QtGui.QBrush(QtGui.QColor(color)))

        # Add detail rows if any
        if details:
            for detail in details:
                child = QtWidgets.QTreeWidgetItem(item)
                child.setText(2, f"  └─ {detail}")
                child.setForeground(
                    2, QtGui.QBrush(QtGui.QColor("#888888"))
                )

            # Auto expand if there are errors
            if status == "error":
                item.setExpanded(True)

    def filter_results(self, filter_text):
        filter_map = {
            "Show All":      None,
            "Errors Only":   "error",
            "Warnings Only": "warning",
            "Passed Only":   "pass"
        }

        selected = filter_map.get(filter_text)

        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item_status = item.data(0, QtCore.Qt.UserRole)

            if selected is None:
                item.setHidden(False)
            else:
                item.setHidden(item_status != selected)

    # ─────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────

    def reset_summary(self):
        self.error_label.setText("❌ Errors: 0")
        self.warning_label.setText("⚠️ Warnings: 0")
        self.pass_label.setText("✅ Passed: 0")

    def update_summary(self):
        errors = 0
        warnings = 0
        passed = 0

        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            status = item.data(0, QtCore.Qt.UserRole)

            if status == "error":
                errors += 1
            elif status == "warning":
                warnings += 1
            elif status == "pass":
                passed += 1

        self.error_label.setText(f"❌ Errors: {errors}")
        self.warning_label.setText(f"⚠️ Warnings: {warnings}")
        self.pass_label.setText(f"✅ Passed: {passed}")

    # ─────────────────────────────────────────────
    # EXPORT — PLACEHOLDER FOR NOW
    # ─────────────────────────────────────────────

    def export_report(self):
        # We will build this properly later
        QtWidgets.QMessageBox.information(
            self,
            "Export",
            "Export coming in Day 8!"
        )

    # ─────────────────────────────────────────────
    # STYLESHEET
    # ─────────────────────────────────────────────

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Arial;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
                font-weight: bold;
                color: #d4d4d4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px;
                color: #d4d4d4;
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
                background-color: #3c3c3c;
                color: #666;
            }
            QTreeWidget {
                background-color: #252526;
                border: 1px solid #444;
                alternate-background-color: #2a2a2b;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 6px;
                border: 1px solid #444;
                font-weight: bold;
            }
            QComboBox {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #d4d4d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
                font-size: 12px;
            }
            #errorLabel {
                color: #f44747;
                font-weight: bold;
                font-size: 14px;
            }
            #warningLabel {
                color: #dcdcaa;
                font-weight: bold;
                font-size: 14px;
            }
            #passLabel {
                color: #6a9955;
                font-weight: bold;
                font-size: 14px;
            }
        """)


# ─────────────────────────────────────────────
# LAUNCH
# ─────────────────────────────────────────────

def main():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    window = USDValidator()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()