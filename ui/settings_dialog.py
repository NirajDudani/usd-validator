from PySide6 import QtWidgets, QtCore


class SettingsDialog(QtWidgets.QDialog):

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(550, 350)

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # ── Two-panel area ──
        panels = QtWidgets.QHBoxLayout()
        panels.setSpacing(0)
        panels.setContentsMargins(0, 0, 0, 0)

        # Left: category list
        self._list = QtWidgets.QListWidget()
        self._list.setFixedWidth(150)
        self._list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Right: stacked pages
        self._stack = QtWidgets.QStackedWidget()

        panels.addWidget(self._list)
        panels.addWidget(self._stack)
        root_layout.addLayout(panels)

        # ── Register categories (each _build_* adds one row to _list and one page to _stack) ──
        self._build_file_size_check(settings.get("file_size_check", {}))
        self._build_default_prim_check(settings.get("default_prim_check", {}))

        # Select first item by default
        self._list.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._list.setCurrentRow(0)

        # ── Footer: OK / Cancel ──
        footer = QtWidgets.QHBoxLayout()
        footer.setContentsMargins(12, 8, 12, 8)
        footer.addStretch()
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        footer.addWidget(buttons)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        root_layout.addWidget(separator)
        root_layout.addLayout(footer)

    def _build_file_size_check(self, fsc):
        """Create the File Size Check settings page and register it."""
        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.enabled_cb = QtWidgets.QCheckBox("Enable file size check")
        self.enabled_cb.setChecked(fsc.get("enabled", True))
        form.addRow(self.enabled_cb)

        self.warn_spin = QtWidgets.QDoubleSpinBox()
        self.warn_spin.setRange(0.1, 99999)
        self.warn_spin.setDecimals(1)
        self.warn_spin.setValue(fsc.get("warn_threshold", 50.0))
        form.addRow("Warn threshold:", self.warn_spin)

        self.error_spin = QtWidgets.QDoubleSpinBox()
        self.error_spin.setRange(0.1, 99999)
        self.error_spin.setDecimals(1)
        self.error_spin.setValue(fsc.get("error_threshold", 200.0))
        form.addRow("Error threshold:", self.error_spin)

        self.unit_combo = QtWidgets.QComboBox()
        self.unit_combo.addItems(["MB", "GB"])
        idx = self.unit_combo.findText(fsc.get("unit", "MB"))
        self.unit_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Unit:", self.unit_combo)

        self._list.addItem("File Size Check")
        self._stack.addWidget(page)

    def _build_default_prim_check(self, dpc):
        """Create the Default Prim settings page and register it."""
        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.dpc_enabled_cb = QtWidgets.QCheckBox("Enable default prim check")
        self.dpc_enabled_cb.setChecked(dpc.get("enabled", True))
        form.addRow(self.dpc_enabled_cb)

        self.dpc_type_combo = QtWidgets.QComboBox()
        self.dpc_type_combo.addItems(["Xform", "Scope", "Mesh", "SkelRoot", "Component"])
        idx = self.dpc_type_combo.findText(dpc.get("expected_type", "Xform"))
        self.dpc_type_combo.setCurrentIndex(idx if idx >= 0 else 0)
        form.addRow("Expected type:", self.dpc_type_combo)

        self._list.addItem("Default Prim")
        self._stack.addWidget(page)

    def get_settings(self):
        return {
            "file_size_check": {
                "enabled": self.enabled_cb.isChecked(),
                "warn_threshold": self.warn_spin.value(),
                "error_threshold": self.error_spin.value(),
                "unit": self.unit_combo.currentText(),
            },
            "default_prim_check": {
                "enabled": self.dpc_enabled_cb.isChecked(),
                "expected_type": self.dpc_type_combo.currentText(),
            },
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
