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
        self._build_naming_check(settings.get("naming_check", {}))

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

    def _build_naming_check(self, nc):
        """Create the Naming Check settings page and register it."""
        # Store JSON-only keys so get_settings() can round-trip them unchanged.
        self._nc_extra = {
            k: v for k, v in nc.items()
            if k not in ("enabled", "check_chars", "check_patterns", "check_reserved", "check_consistency")
        }

        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.nc_enabled_cb = QtWidgets.QCheckBox("Enable naming check")
        self.nc_enabled_cb.setChecked(nc.get("enabled", True))
        form.addRow(self.nc_enabled_cb)

        self.nc_chars_cb = QtWidgets.QCheckBox("Check illegal characters & format")
        self.nc_chars_cb.setChecked(nc.get("check_chars", True))
        self.nc_chars_cb.setToolTip(
            "Flags prim names that contain spaces, special characters,\n"
            "or start with a digit — USD only allows letters, digits, and underscores."
        )
        form.addRow(self.nc_chars_cb)

        self.nc_patterns_cb = QtWidgets.QCheckBox("Check prefix/suffix patterns")
        self.nc_patterns_cb.setChecked(nc.get("check_patterns", True))
        self.nc_patterns_cb.setToolTip(
            "Checks that each prim type matches its required prefix or suffix.\n"
            "e.g. Mesh prims must start with GEO_, Materials with MAT_."
        )
        form.addRow(self.nc_patterns_cb)

        self.nc_reserved_cb = QtWidgets.QCheckBox("Check reserved names")
        self.nc_reserved_cb.setChecked(nc.get("check_reserved", True))
        self.nc_reserved_cb.setToolTip(
            "Warns when a prim uses a reserved word as its name\n"
            "(e.g. 'default', 'material', 'mesh') which can cause USD conflicts."
        )
        form.addRow(self.nc_reserved_cb)

        self.nc_consistency_cb = QtWidgets.QCheckBox("Check casing consistency")
        self.nc_consistency_cb.setChecked(nc.get("check_consistency", True))
        self.nc_consistency_cb.setToolTip(
            "Ensures all prim names in the scene follow the same casing style\n"
            "(e.g. all snake_case or all CamelCase — no mixing)."
        )
        form.addRow(self.nc_consistency_cb)

        # Disable sub-checks when master is unchecked
        for cb in (self.nc_chars_cb, self.nc_patterns_cb, self.nc_reserved_cb, self.nc_consistency_cb):
            cb.setEnabled(self.nc_enabled_cb.isChecked())
        self.nc_enabled_cb.toggled.connect(self.nc_chars_cb.setEnabled)
        self.nc_enabled_cb.toggled.connect(self.nc_patterns_cb.setEnabled)
        self.nc_enabled_cb.toggled.connect(self.nc_reserved_cb.setEnabled)
        self.nc_enabled_cb.toggled.connect(self.nc_consistency_cb.setEnabled)

        self._list.addItem("Naming Check")
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
            "naming_check": {
                **self._nc_extra,
                "enabled": self.nc_enabled_cb.isChecked(),
                "check_chars": self.nc_chars_cb.isChecked(),
                "check_patterns": self.nc_patterns_cb.isChecked(),
                "check_reserved": self.nc_reserved_cb.isChecked(),
                "check_consistency": self.nc_consistency_cb.isChecked(),
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
