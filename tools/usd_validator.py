import sys
import os
import json
import copy

# Ensure src/ is on the path so ui.* imports work regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxr import Usd
from PySide6 import QtWidgets, QtCore, QtGui

from ui.styles import STYLESHEET
from ui.settings_dialog import SettingsDialog
from validators.file_size import check_file_size
from validators.default_prim import check_default_prim
from validators.naming_convention import check_naming_convention
from validators.required_metadata import check_required_metadata
from validators.broken_references import check_broken_references

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "file_size_check": {
        "enabled": True,
        "warn_threshold": 50.0,
        "error_threshold": 200.0,
        "unit": "MB",
    },
    "default_prim_check": {
        "enabled": True,
        "expected_type": "Xform",
    },
    "broken_references": {
        "enabled": True,
        "enabled_checks": {
            "external_references": True,
            "internal_references": True,
            "asset_paths": True,
            "unresolvable_paths": True,
        },
        "additional_search_paths": [],
        "ignore_patterns": [],
    },
    "required_metadata": {
        "enabled": True,
        "enabled_checks": {
            "up_axis": True,
            "meters_per_unit": True,
            "custom_metadata": True,
        },
        "valid_up_axis": ["Y", "Z"],
        "valid_meters_per_unit": [0.001, 0.01, 0.1, 1.0],
        "required_custom_fields": [],
    },
    "naming_check": {
        "enabled": True,
        "check_chars": True,
        "check_patterns": True,
        "check_reserved": True,
        "check_consistency": True,
        "illegal_characters": "",
        "max_name_length": 128,
        "style": None,
        "prim_type_prefixes": {
            "Mesh": ["GEO_"],
            "Material": ["MAT_"],
            "Scope": ["GRP_"],
        },
        "reserved_names": [
            "default", "class", "material", "geometry",
            "xform", "scope", "mesh", "camera",
        ],
    },
}



class USDValidator(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        # Store stage and file path
        self.stage = None
        self.current_file = None

        # Load settings
        self.settings = self._load_settings()

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

        # Settings button
        self.settings_btn = QtWidgets.QPushButton("Settings")
        self.settings_btn.setFixedHeight(40)
        self.settings_btn.setFixedWidth(100)
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

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
            "USD Files (*.usd *.usda *.usdc *.usdz *.usdnc)"
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
    # VALIDATION
    # ─────────────────────────────────────────────

    def run_validation(self):
        if not self.stage:
            return

        # Clear previous results
        self.results_tree.clear()
        self.reset_summary()

        self.status_bar.showMessage("Running validation...")

        self.add_result(
            check_name="File Loaded",
            status="pass",
            message="USD file loaded successfully",
            details=[]
        )

        for name, status, msg in check_file_size(self.current_file, self.settings):
            self.add_result(check_name=name, status=status, message=msg)

        for name, status, msg in check_default_prim(self.stage, self.settings):
            self.add_result(check_name=name, status=status, message=msg)

        for name, status, msg in check_required_metadata(self.stage, self.settings):
            self.add_result(check_name=name, status=status, message=msg)

        for name, status, msg in check_broken_references(self.stage, self.settings):
            self.add_result(check_name=name, status=status, message=msg)

        for name, status, msg in check_naming_convention(self.stage, self.settings):
            self.add_result(check_name=name, status=status, message=msg)

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
        QtWidgets.QMessageBox.information(
            self,
            "Export",
            "Export coming in Day 8!"
        )


    # ─────────────────────────────────────────────
    # SETTINGS
    # ─────────────────────────────────────────────

    def _load_settings(self):
        settings = copy.deepcopy(DEFAULT_SETTINGS)
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for section, values in loaded.items():
                    if section in settings and isinstance(values, dict):
                        settings[section].update(values)
                    else:
                        settings[section] = values
            except (json.JSONDecodeError, OSError) as e:
                print(f"[USDValidator] Could not load settings: {e}", file=sys.stderr)
        return settings

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except OSError as e:
            QtWidgets.QMessageBox.warning(
                self,
                "Settings Not Saved",
                f"Could not write settings file:\n{e}"
            )

    def open_settings(self):
        dialog = SettingsDialog(self.settings, parent=self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.settings = dialog.get_settings()
            self._save_settings()

    def apply_stylesheet(self):
        self.setStyleSheet(STYLESHEET)


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