def check_required_metadata(stage, settings):
    rmc = settings.get("required_metadata", {})

    if not rmc.get("enabled", True):
        return []

    if not stage:
        return [("Required Metadata", "error", "No stage loaded — cannot check metadata")]

    enabled_checks = rmc.get("enabled_checks", {})
    results = []

    if enabled_checks.get("up_axis", True):
        results.extend(_check_up_axis(stage, rmc))

    if enabled_checks.get("meters_per_unit", True):
        results.extend(_check_meters_per_unit(stage, rmc))

    if enabled_checks.get("custom_metadata", True):
        results.extend(_check_custom_metadata(stage, rmc))

    if not results:
        return [("Required Metadata", "pass", "All required metadata present")]

    return results


def _check_up_axis(stage, rmc):
    valid = rmc.get("valid_up_axis", ["Y", "Z"])
    pseudo = stage.GetRootLayer().pseudoRoot

    if not pseudo.HasInfo("upAxis"):
        return [("Required Metadata", "error", "Stage is missing 'upAxis' metadata")]

    up_axis = pseudo.GetInfo("upAxis")
    if up_axis not in valid:
        return [("Required Metadata", "error",
                 f"Stage 'upAxis' is '{up_axis}', must be one of: {', '.join(valid)}")]

    return []


def _check_meters_per_unit(stage, rmc):
    valid = rmc.get("valid_meters_per_unit", [0.001, 0.01, 0.1, 1.0])
    pseudo = stage.GetRootLayer().pseudoRoot

    if not pseudo.HasInfo("metersPerUnit"):
        return [("Required Metadata", "warning", "Stage is missing 'metersPerUnit' metadata")]

    mpu = pseudo.GetInfo("metersPerUnit")
    if not any(abs(mpu - v) < 1e-9 for v in valid):
        valid_str = ", ".join(f"{v:g}" for v in valid)
        return [("Required Metadata", "warning",
                 f"Stage 'metersPerUnit' is {mpu:g}, expected one of: {valid_str}")]

    return []


def _check_custom_metadata(stage, rmc):
    required_fields = rmc.get("required_custom_fields", [])

    if not required_fields:
        return []

    custom = stage.GetRootLayer().customLayerData
    results = []
    for field in required_fields:
        if field not in custom:
            results.append(("Required Metadata", "warning",
                            f"Stage is missing required custom metadata: '{field}'"))

    return results
