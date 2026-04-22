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
        self._build_required_metadata_check(settings.get("required_metadata", {}))
        self._build_broken_references_check(settings.get("broken_references", {}))
        self._build_duplicate_names_check(settings.get("duplicate_names", {}))
        self._build_empty_prims_check(settings.get("empty_prims", {}))
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

    def _build_required_metadata_check(self, rmc):
        """Create the Required Metadata settings page and register it."""
        self._rmc_extra = {
            k: v for k, v in rmc.items()
            if k not in ("enabled", "enabled_checks")
        }

        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.rmc_enabled_cb = QtWidgets.QCheckBox("Enable required metadata check")
        self.rmc_enabled_cb.setChecked(rmc.get("enabled", True))
        form.addRow(self.rmc_enabled_cb)

        enabled_checks = rmc.get("enabled_checks", {})

        self.rmc_up_axis_cb = QtWidgets.QCheckBox("Check upAxis")
        self.rmc_up_axis_cb.setChecked(enabled_checks.get("up_axis", True))
        self.rmc_up_axis_cb.setToolTip(
            "Verify the stage has a valid up axis set (Y or Z). "
            "Prevents assets opening sideways in other tools."
        )
        form.addRow(self.rmc_up_axis_cb)

        self.rmc_mpu_cb = QtWidgets.QCheckBox("Check metersPerUnit")
        self.rmc_mpu_cb.setChecked(enabled_checks.get("meters_per_unit", True))
        self.rmc_mpu_cb.setToolTip(
            "Verify the stage has a standard units scale. "
            "Prevents assets appearing at wrong size."
        )
        form.addRow(self.rmc_mpu_cb)

        self.rmc_custom_cb = QtWidgets.QCheckBox("Check custom metadata fields")
        self.rmc_custom_cb.setChecked(enabled_checks.get("custom_metadata", True))
        self.rmc_custom_cb.setToolTip(
            "Check for studio-required metadata fields like asset version or author name."
        )
        form.addRow(self.rmc_custom_cb)

        for cb in (self.rmc_up_axis_cb, self.rmc_mpu_cb, self.rmc_custom_cb):
            cb.setEnabled(self.rmc_enabled_cb.isChecked())
        self.rmc_enabled_cb.toggled.connect(self.rmc_up_axis_cb.setEnabled)
        self.rmc_enabled_cb.toggled.connect(self.rmc_mpu_cb.setEnabled)
        self.rmc_enabled_cb.toggled.connect(self.rmc_custom_cb.setEnabled)

        self._list.addItem("Required Metadata")
        self._stack.addWidget(page)

    def _build_broken_references_check(self, brc):
        """Create the Broken References settings page and register it."""
        self._brc_extra = {
            k: v for k, v in brc.items()
            if k not in ("enabled", "enabled_checks")
        }

        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.brc_enabled_cb = QtWidgets.QCheckBox("Enable broken references check")
        self.brc_enabled_cb.setChecked(brc.get("enabled", True))
        form.addRow(self.brc_enabled_cb)

        enabled_checks = brc.get("enabled_checks", {})

        self.brc_ext_cb = QtWidgets.QCheckBox("Check external references")
        self.brc_ext_cb.setChecked(enabled_checks.get("external_references", True))
        self.brc_ext_cb.setToolTip(
            "Check that all referenced USD files exist on disk and contain the expected prims."
        )
        form.addRow(self.brc_ext_cb)

        self.brc_int_cb = QtWidgets.QCheckBox("Check internal references")
        self.brc_int_cb.setChecked(enabled_checks.get("internal_references", True))
        self.brc_int_cb.setToolTip(
            "Check that references to prims within the same file point to prims that exist."
        )
        form.addRow(self.brc_int_cb)

        self.brc_asset_cb = QtWidgets.QCheckBox("Check asset paths")
        self.brc_asset_cb.setChecked(enabled_checks.get("asset_paths", True))
        self.brc_asset_cb.setToolTip(
            "Check that texture, audio, and other asset file paths point to files that exist."
        )
        form.addRow(self.brc_asset_cb)

        self.brc_env_cb = QtWidgets.QCheckBox("Check unresolvable paths")
        self.brc_env_cb.setChecked(enabled_checks.get("unresolvable_paths", True))
        self.brc_env_cb.setToolTip(
            "Flag paths with environment variables or search paths that cannot be resolved."
        )
        form.addRow(self.brc_env_cb)

        sub_cbs = (self.brc_ext_cb, self.brc_int_cb, self.brc_asset_cb, self.brc_env_cb)
        for cb in sub_cbs:
            cb.setEnabled(self.brc_enabled_cb.isChecked())
        self.brc_enabled_cb.toggled.connect(self.brc_ext_cb.setEnabled)
        self.brc_enabled_cb.toggled.connect(self.brc_int_cb.setEnabled)
        self.brc_enabled_cb.toggled.connect(self.brc_asset_cb.setEnabled)
        self.brc_enabled_cb.toggled.connect(self.brc_env_cb.setEnabled)

        self._list.addItem("Broken References")
        self._stack.addWidget(page)

    def _build_duplicate_names_check(self, dnc):
        """Create the Duplicate Names settings page and register it."""
        self._dnc_extra = {
            k: v for k, v in dnc.items()
            if k not in ("enabled", "enabled_checks")
        }

        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.dnc_enabled_cb = QtWidgets.QCheckBox("Enable duplicate names check")
        self.dnc_enabled_cb.setChecked(dnc.get("enabled", True))
        form.addRow(self.dnc_enabled_cb)

        enabled_checks = dnc.get("enabled_checks", {})

        self.dnc_exact_cb = QtWidgets.QCheckBox("Check exact sibling duplicates")
        self.dnc_exact_cb.setChecked(enabled_checks.get("exact_siblings", True))
        self.dnc_exact_cb.setToolTip(
            "Flag prims with identical names under the same parent. "
            "Causes ambiguity in path queries."
        )
        form.addRow(self.dnc_exact_cb)

        self.dnc_case_cb = QtWidgets.QCheckBox("Check case-only sibling duplicates")
        self.dnc_case_cb.setChecked(enabled_checks.get("case_siblings", True))
        self.dnc_case_cb.setToolTip(
            "Flag sibling prims whose names differ only by capitalization. "
            "Breaks on Windows and confuses artists."
        )
        form.addRow(self.dnc_case_cb)

        self.dnc_cross_cb = QtWidgets.QCheckBox("Check cross-branch duplicates")
        self.dnc_cross_cb.setChecked(enabled_checks.get("cross_branch", True))
        self.dnc_cross_cb.setToolTip(
            "Flag prim names that repeat many times across different parts of the scene. "
            "May indicate uninstanced copies."
        )
        form.addRow(self.dnc_cross_cb)

        sub_cbs = (self.dnc_exact_cb, self.dnc_case_cb, self.dnc_cross_cb)
        for cb in sub_cbs:
            cb.setEnabled(self.dnc_enabled_cb.isChecked())
        self.dnc_enabled_cb.toggled.connect(self.dnc_exact_cb.setEnabled)
        self.dnc_enabled_cb.toggled.connect(self.dnc_case_cb.setEnabled)
        self.dnc_enabled_cb.toggled.connect(self.dnc_cross_cb.setEnabled)

        self._list.addItem("Duplicate Names")
        self._stack.addWidget(page)

    def _build_empty_prims_check(self, epc):
        """Create the Empty Prims settings page and register it."""
        self._epc_extra = {
            k: v for k, v in epc.items()
            if k not in ("enabled", "enabled_checks")
        }

        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.epc_enabled_cb = QtWidgets.QCheckBox("Enable empty prims check")
        self.epc_enabled_cb.setChecked(epc.get("enabled", True))
        form.addRow(self.epc_enabled_cb)

        enabled_checks = epc.get("enabled_checks", {})

        self.epc_xform_cb = QtWidgets.QCheckBox("Check empty Xform / Scope")
        self.epc_xform_cb.setChecked(enabled_checks.get("empty_xform_scope", True))
        self.epc_xform_cb.setToolTip(
            "Flag Xform and Scope prims with no children or properties. "
            "Usually leftover containers from deleted geometry."
        )
        form.addRow(self.epc_xform_cb)

        self.epc_mesh_cb = QtWidgets.QCheckBox("Check empty Mesh")
        self.epc_mesh_cb.setChecked(enabled_checks.get("empty_mesh", True))
        self.epc_mesh_cb.setToolTip(
            "Flag Mesh prims with no geometry data. "
            "A Mesh with no points will render as nothing."
        )
        form.addRow(self.epc_mesh_cb)

        self.epc_hier_cb = QtWidgets.QCheckBox("Check empty hierarchy")
        self.epc_hier_cb.setChecked(enabled_checks.get("empty_hierarchy", True))
        self.epc_hier_cb.setToolTip(
            "Flag group prims whose entire subtree contains no meaningful geometry or materials."
        )
        form.addRow(self.epc_hier_cb)

        sub_cbs = (self.epc_xform_cb, self.epc_mesh_cb, self.epc_hier_cb)
        for cb in sub_cbs:
            cb.setEnabled(self.epc_enabled_cb.isChecked())
        self.epc_enabled_cb.toggled.connect(self.epc_xform_cb.setEnabled)
        self.epc_enabled_cb.toggled.connect(self.epc_mesh_cb.setEnabled)
        self.epc_enabled_cb.toggled.connect(self.epc_hier_cb.setEnabled)

        self._list.addItem("Empty Prims")
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
            "required_metadata": {
                **self._rmc_extra,
                "enabled": self.rmc_enabled_cb.isChecked(),
                "enabled_checks": {
                    "up_axis": self.rmc_up_axis_cb.isChecked(),
                    "meters_per_unit": self.rmc_mpu_cb.isChecked(),
                    "custom_metadata": self.rmc_custom_cb.isChecked(),
                },
            },
            "broken_references": {
                **self._brc_extra,
                "enabled": self.brc_enabled_cb.isChecked(),
                "enabled_checks": {
                    "external_references": self.brc_ext_cb.isChecked(),
                    "internal_references": self.brc_int_cb.isChecked(),
                    "asset_paths": self.brc_asset_cb.isChecked(),
                    "unresolvable_paths": self.brc_env_cb.isChecked(),
                },
            },
            "duplicate_names": {
                **self._dnc_extra,
                "enabled": self.dnc_enabled_cb.isChecked(),
                "enabled_checks": {
                    "exact_siblings": self.dnc_exact_cb.isChecked(),
                    "case_siblings": self.dnc_case_cb.isChecked(),
                    "cross_branch": self.dnc_cross_cb.isChecked(),
                },
            },
            "empty_prims": {
                **self._epc_extra,
                "enabled": self.epc_enabled_cb.isChecked(),
                "enabled_checks": {
                    "empty_xform_scope": self.epc_xform_cb.isChecked(),
                    "empty_mesh": self.epc_mesh_cb.isChecked(),
                    "empty_hierarchy": self.epc_hier_cb.isChecked(),
                },
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
