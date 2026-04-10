from PySide6 import QtWidgets


class SettingsDialog(QtWidgets.QDialog):

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(350)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        # ── File Size Check group ──
        group = QtWidgets.QGroupBox("File Size Check")
        group_layout = QtWidgets.QFormLayout(group)

        self.enabled_cb = QtWidgets.QCheckBox("Enable file size check")
        fsc = settings.get("file_size_check", {})
        self.enabled_cb.setChecked(fsc.get("enabled", True))
        group_layout.addRow(self.enabled_cb)

        self.warn_spin = QtWidgets.QDoubleSpinBox()
        self.warn_spin.setRange(0.1, 99999)
        self.warn_spin.setDecimals(1)
        self.warn_spin.setValue(fsc.get("warn_threshold", 50.0))
        group_layout.addRow("Warn threshold:", self.warn_spin)

        self.error_spin = QtWidgets.QDoubleSpinBox()
        self.error_spin.setRange(0.1, 99999)
        self.error_spin.setDecimals(1)
        self.error_spin.setValue(fsc.get("error_threshold", 200.0))
        group_layout.addRow("Error threshold:", self.error_spin)

        self.unit_combo = QtWidgets.QComboBox()
        self.unit_combo.addItems(["MB", "GB"])
        idx = self.unit_combo.findText(fsc.get("unit", "MB"))
        self.unit_combo.setCurrentIndex(idx if idx >= 0 else 0)
        group_layout.addRow("Unit:", self.unit_combo)

        layout.addWidget(group)

        # ── OK / Cancel ──
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self):
        return {
            "file_size_check": {
                "enabled": self.enabled_cb.isChecked(),
                "warn_threshold": self.warn_spin.value(),
                "error_threshold": self.error_spin.value(),
                "unit": self.unit_combo.currentText(),
            }
        }

    def accept(self):
        if self.warn_spin.value() >= self.error_spin.value():
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Thresholds",
                "Warn threshold must be less than the error threshold.",
            )
            return
        super().accept()
