import csv
import os
from datetime import datetime

from PySide6 import QtCore, QtWidgets

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable, SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph,
    )
    _REPORTLAB_OK = True
except ImportError:
    _REPORTLAB_OK = False

_VERSION = "v1.0"


# ─────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────

def export_report(parent, results_tree, current_file):
    """
    Open a save-file dialog and write a PDF or CSV report.
    Called directly from the main window's Export Report button.
    """
    results = _collect_results(results_tree)
    if not results:
        QtWidgets.QMessageBox.information(
            parent,
            "No Results",
            "Please run validation before exporting.",
        )
        return

    default_name = _default_filename(current_file)

    file_path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
        parent,
        "Export Report",
        default_name,
        "PDF Report (*.pdf);;CSV Spreadsheet (*.csv)",
    )

    if not file_path:
        return  # user cancelled

    # Guarantee the right extension (user may have omitted it)
    _, ext = os.path.splitext(file_path)
    if not ext:
        ext = ".csv" if "csv" in selected_filter.lower() else ".pdf"
        file_path += ext

    file_info = {
        "file_path":   current_file or "Unknown",
        "file_size":   _readable_size(current_file),
        "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        if ext.lower() == ".csv":
            _write_csv(file_path, results, file_info)
        else:
            if not _REPORTLAB_OK:
                QtWidgets.QMessageBox.critical(
                    parent,
                    "Missing Dependency",
                    "PDF export requires reportlab.\n\nInstall it with:\n    pip install reportlab",
                )
                return
            _write_pdf(file_path, results, file_info)
    except OSError as e:
        QtWidgets.QMessageBox.critical(
            parent,
            "Export Failed",
            f"Could not write to:\n{file_path}\n\n{e}",
        )
        return
    except Exception as e:
        QtWidgets.QMessageBox.critical(
            parent,
            "Export Failed",
            f"An unexpected error occurred during export:\n{e}",
        )
        return

    QtWidgets.QMessageBox.information(
        parent,
        "Export Complete",
        f"Report saved to:\n{file_path}",
    )


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _collect_results(tree):
    results = []
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        results.append({
            "check":   item.text(0),
            "status":  item.data(0, QtCore.Qt.UserRole),  # "pass" / "warning" / "error"
            "message": item.text(2),
        })
    return results


def _default_filename(current_file):
    stem = os.path.splitext(os.path.basename(current_file))[0] if current_file else "usd"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_report_{ts}"


def _readable_size(file_path):
    if not file_path or not os.path.exists(file_path):
        return "Unknown"
    b = os.path.getsize(file_path)
    if b >= 1024 ** 2:
        return f"{b / 1024 ** 2:.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"


# ─────────────────────────────────────────────
# CSV export
# ─────────────────────────────────────────────

def _write_csv(file_path, results, file_info):
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Check", "Status", "Details", "File", "Timestamp"])
        for r in results:
            writer.writerow([
                r["check"],
                r["status"].upper(),
                r["message"],
                file_info["file_path"],
                file_info["validated_at"],
            ])


# ─────────────────────────────────────────────
# PDF export
# ─────────────────────────────────────────────

# Text colors for each status level
_STATUS_TEXT_COLOR = {
    "error":   "#cc0000",
    "warning": "#8a6300",
    "pass":    "#2e7d32",
}

# Light background tint per row
_STATUS_ROW_BG = {
    "error":   "#fff0f0",
    "warning": "#fffbe6",
    "pass":    "#f0faf0",
}

_STATUS_LABEL = {
    "error":   "ERROR",
    "warning": "WARNING",
    "pass":    "PASS",
}


def _write_pdf(file_path, results, file_info):
    PAGE_W, _ = A4
    MARGIN = 20 * mm
    USABLE_W = PAGE_W - 2 * MARGIN

    styles = getSampleStyleSheet()

    def _style(name, **kw):
        base = kw.pop("parent", "Normal")
        return ParagraphStyle(name, parent=styles[base], **kw)

    title_st = _style("Title",
        fontSize=18, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e1e1e"), spaceAfter=1 * mm)
    sub_st = _style("Sub",
        fontSize=10, fontName="Helvetica",
        textColor=colors.HexColor("#555555"), spaceAfter=4 * mm)
    section_st = _style("Section",
        fontSize=11, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e1e1e"),
        spaceBefore=5 * mm, spaceAfter=2 * mm)
    cell_st = _style("Cell",
        fontSize=9, fontName="Helvetica",
        textColor=colors.HexColor("#1e1e1e"), leading=12)
    footer_st = _style("Footer",
        fontSize=8, fontName="Helvetica",
        textColor=colors.HexColor("#888888"))

    def p(text, style=None):
        return Paragraph(text, style or cell_st)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    hr = lambda: HRFlowable(
        width="100%", thickness=0.5,
        color=colors.HexColor("#cccccc"), spaceAfter=3 * mm,
    )

    story = []

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(p("USD Asset Validator Report", title_st))
    story.append(p(f"Tool version {_VERSION}", sub_st))
    story.append(hr())

    # ── File information ──────────────────────────────────────────────────────
    story.append(p("File Information", section_st))

    info_col = 28 * mm
    info_rows = [
        [p("<b>File</b>"),      p(file_info["file_path"])],
        [p("<b>Size</b>"),      p(file_info["file_size"])],
        [p("<b>Validated</b>"), p(file_info["validated_at"])],
    ]
    info_tbl = Table(info_rows, colWidths=[info_col, USABLE_W - info_col])
    info_tbl.setStyle(TableStyle([
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f5f5f5"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING",     (0, 0), (-1, -1), 4),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(info_tbl)

    # ── Summary ───────────────────────────────────────────────────────────────
    errors   = sum(1 for r in results if r["status"] == "error")
    warnings = sum(1 for r in results if r["status"] == "warning")
    passed   = sum(1 for r in results if r["status"] == "pass")

    story.append(p("Summary", section_st))
    summary_rows = [[
        p(f"<font color='#cc0000'><b>Errors: {errors}</b></font>"),
        p(f"<font color='#8a6300'><b>Warnings: {warnings}</b></font>"),
        p(f"<font color='#2e7d32'><b>Passed: {passed}</b></font>"),
    ]]
    col3 = USABLE_W / 3
    summary_tbl = Table(summary_rows, colWidths=[col3, col3, col3])
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("PADDING",    (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_tbl)

    # ── Results table ─────────────────────────────────────────────────────────
    story.append(p("Validation Results", section_st))

    col_check  = 48 * mm
    col_status = 22 * mm
    col_detail = USABLE_W - col_check - col_status

    header = [p("<b>Check</b>"), p("<b>Status</b>"), p("<b>Details</b>")]
    rows = [header]
    row_styles = [
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#e8e8e8")),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING",     (0, 0), (-1, -1), 4),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
    ]

    for i, r in enumerate(results, start=1):
        status = r["status"]
        text_col = _STATUS_TEXT_COLOR.get(status, "#555555")
        label    = _STATUS_LABEL.get(status, status.upper())
        bg       = colors.HexColor(_STATUS_ROW_BG.get(status, "#ffffff"))

        rows.append([
            p(r["check"]),
            p(f"<font color='{text_col}'><b>{label}</b></font>"),
            p(r["message"]),
        ])
        row_styles.append(("BACKGROUND", (0, i), (-1, i), bg))

    results_tbl = Table(
        rows,
        colWidths=[col_check, col_status, col_detail],
        repeatRows=1,
    )
    results_tbl.setStyle(TableStyle(row_styles))
    story.append(results_tbl)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(hr())
    story.append(p(
        f"Generated by USD Asset Validator {_VERSION} "
        f"on {file_info['validated_at']}",
        footer_st,
    ))

    doc.build(story)
