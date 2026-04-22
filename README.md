# USD Asset Validator

A desktop tool for validating OpenUSD assets against pipeline standards. Built with PySide6 and the OpenUSD Python API.

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![OpenUSD](https://img.shields.io/badge/OpenUSD-required-orange) ![PySide6](https://img.shields.io/badge/PySide6-required-green)

---

## Features

- Browse and load any `.usd`, `.usda`, `.usdc`, `.usdz`, or `.usdnc` file
- Run seven independent validators in one click
- Filter results by status (All / Errors / Warnings / Passed)
- Per-validator settings with a live dialog — no config file editing required
- Export results as a **PDF report** or **CSV spreadsheet**

---

## Validators

| Validator | What it checks |
|---|---|
| **File Size** | Warns or errors when the file exceeds configurable size thresholds |
| **Default Prim** | Checks that a default prim is set, exists in the stage, and matches the expected type |
| **Required Metadata** | Verifies `upAxis`, `metersPerUnit`, and any required custom `layerData` fields |
| **Broken References** | Finds missing external files, unresolved internal prim paths, bad asset attributes, and unresolvable env-var paths |
| **Duplicate Names** | Flags exact sibling duplicates, case-only collisions (e.g. `GEO_body` vs `GEO_Body`), and cross-branch name repetition above a configurable threshold |
| **Empty Prims** | Finds empty Xform/Scope containers, Mesh prims with no geometry data, and hierarchy chains that lead to no meaningful content |
| **Naming Convention** | Checks character legality, type prefix rules (e.g. `GEO_`, `MAT_`), reserved name conflicts, and casing consistency |

All validators are individually toggleable. Sub-checks within each validator can also be enabled or disabled independently.

---

## Requirements

- Python 3.10+
- [OpenUSD](https://openusd.org/release/index.html) Python bindings (`pxr`)
- PySide6
- reportlab *(PDF export only)*

```bash
pip install PySide6 reportlab
```

OpenUSD must be installed separately. Follow the [official build instructions](https://openusd.org/release/index.html) or install a pre-built package for your platform.

---

## Running the tool

```bash
cd src
python tools/usd_validator.py
```

---

## Running the tests

```bash
cd src
python -m pytest tests/ -v
```

The test suite uses in-memory USD stages — no external files are required except for the reference-checking tests, which use the fixture files in `tests/fixtures/`.

---

## Project structure

```
src/
├── tools/
│   ├── usd_validator.py      # Main application entry point
│   └── settings.json         # Persisted user settings
├── validators/
│   ├── file_size.py
│   ├── default_prim.py
│   ├── required_metadata.py
│   ├── broken_references.py
│   ├── duplicate_names.py
│   ├── empty_prims.py
│   └── naming_convention.py
├── ui/
│   ├── settings_dialog.py    # Settings dialog (PySide6)
│   ├── export.py             # PDF and CSV export logic
│   └── styles.py             # Application stylesheet
└── tests/
    ├── fixtures/             # .usda files used by reference tests
    ├── test_broken_references.py
    ├── test_duplicate_names.py
    ├── test_empty_prims.py
    ├── test_naming_convention.py
    └── test_required_metadata.py
```

---

## Exporting results

After running validation, click **Export Report** to save results to disk. A file save dialog lets you choose the location, filename, and format.

### PDF
A formatted report suitable for sharing with a supervisor or client. Includes:
- Tool version and timestamp in the header
- File path, file size, and validation time
- Summary of total errors, warnings, and passed checks
- Full results table with color-coded rows (red / amber / green) matching what you see in the UI
- Generated-on footer

### CSV
A raw data file for use in pipeline scripts or spreadsheets. Columns: `Check`, `Status`, `Details`, `File`, `Timestamp`. The file path and timestamp are included on every row so the export is self-contained when opened later.

---

## Settings

Settings are stored in `tools/settings.json` and edited through the in-app Settings dialog. The file is created automatically on first run using built-in defaults.

### Key settings per validator

**Duplicate Names**
- `cross_branch_threshold` — minimum occurrences before a name is flagged across branches (default: 3)
- `ignore_names` — names to skip for cross-branch checks (default: `["geo", "mtl", "rig"]`)

**Empty Prims**
- `ignore_types` — prim types exempt from all empty checks (default: `["Camera", "Light"]`)

**Broken References**
- `additional_search_paths` — extra directories to search when resolving relative paths
- `ignore_patterns` — glob patterns for paths to skip (e.g. `["*/temp/*"]`)

**Required Metadata**
- `valid_up_axis` — accepted up-axis values (default: `["Y", "Z"]`)
- `valid_meters_per_unit` — accepted scale values (default: `[0.001, 0.01, 0.1, 1.0]`)
- `required_custom_fields` — list of `layerData` keys that must be present

**Naming Convention**
- `prim_type_prefixes` — map of prim type to required prefixes (e.g. `{"Mesh": ["GEO_"]}`)
- `reserved_names` — names that should not be used as prim names
- `max_name_length` — maximum allowed name length (default: 128)
- `style` — force a specific casing style (`camelCase`, `PascalCase`, `snake_case`), or `null` to auto-detect

---

## Adding a new validator

1. Create `validators/my_check.py` with a `check_my_check(stage, settings)` function that returns a list of `(check_name, status, message)` tuples where `status` is `"pass"`, `"warning"`, or `"error"`.
2. Add a default settings block to `DEFAULT_SETTINGS` in `tools/usd_validator.py`.
3. Call your function in `run_validation()` in `tools/usd_validator.py`.
4. Add a settings page in `ui/settings_dialog.py` following the `_build_*` pattern.
5. Add the section to `get_settings()` in `ui/settings_dialog.py`.
