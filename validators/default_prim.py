def check_default_prim(stage, settings):
    dpc = settings["default_prim_check"]

    if not dpc["enabled"]:
        return []

    if not stage:
        return [("Default Prim", "error", "No stage loaded — cannot check default prim")]

    prim = stage.GetDefaultPrim()

    if not prim.IsValid():
        default_prim_name = stage.GetRootLayer().defaultPrim
        if default_prim_name:
            return [("Default Prim", "error", f"Default prim '{default_prim_name}' not found in stage")]
        return [("Default Prim", "error", "No default prim is set")]

    prim_path = str(prim.GetPath())

    if not prim.IsActive():
        return [("Default Prim", "error", f"Default prim '{prim_path}' exists but is inactive")]

    actual_type = prim.GetTypeName()
    expected_type = dpc.get("expected_type", "").strip()

    if not expected_type:
        return [("Default Prim", "pass", f"Default prim '{prim_path}' ({actual_type}) — type check skipped (no expected type configured)")]

    if actual_type != expected_type:
        return [("Default Prim", "warning", f"Default prim '{prim_path}' is '{actual_type}', expected '{expected_type}'")]

    return [("Default Prim", "pass", f"Default prim '{prim_path}' ({actual_type})")]
