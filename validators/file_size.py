import os


def check_file_size(current_file, settings):
    fsc = settings["file_size_check"]

    if not fsc["enabled"]:
        return []

    if not current_file or not os.path.exists(current_file):
        return [("File Size", "error", "File path unavailable — cannot check size")]

    try:
        size_bytes = os.path.getsize(current_file)
    except OSError as e:
        return [("File Size", "error", f"Could not read file size: {e}")]

    unit = fsc["unit"]
    unit_divisors = {"MB": 1024 ** 2, "GB": 1024 ** 3}
    divisor = unit_divisors.get(unit)
    if divisor is None:
        return [("File Size", "error", f"Unknown file size unit in settings: '{unit}'")]

    size = size_bytes / divisor
    warn = fsc["warn_threshold"]
    error = fsc["error_threshold"]

    if size >= error:
        status = "error"
    elif size >= warn:
        status = "warning"
    else:
        status = "pass"

    return [("File Size", status, f"{size:.1f} {unit}")]
