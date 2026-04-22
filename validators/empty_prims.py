CHECK_NAME = "Empty Prims"

_CONTAINER_TYPES = frozenset({"Xform", "Scope", ""})


def check_empty_prims(stage, settings):
    epc = settings.get("empty_prims", {})

    if not epc.get("enabled", True):
        return []

    if not stage:
        return [(CHECK_NAME, "error", "No stage loaded — cannot check empty prims")]

    enabled = epc.get("enabled_checks", {})
    ignore_types = set(epc.get("ignore_types", []))

    default_prim = stage.GetDefaultPrim()
    root_path = str(default_prim.GetPath()) if default_prim.IsValid() else None

    all_prims = {}
    for prim in stage.TraverseAll():
        all_prims[str(prim.GetPath())] = prim

    # Hierarchy check runs first so its flagged paths can suppress empty_xform_scope
    # warnings on prims that are already covered by a parent-level hierarchy warning.
    hierarchy_results = []
    hierarchy_paths = set()
    if enabled.get("empty_hierarchy", True):
        hierarchy_results, hierarchy_paths = _check_empty_hierarchy(
            all_prims, ignore_types, root_path
        )

    results = []

    if enabled.get("empty_xform_scope", True):
        results.extend(
            _check_empty_xform_scope(all_prims, ignore_types, root_path, hierarchy_paths)
        )

    if enabled.get("empty_mesh", True):
        results.extend(_check_empty_mesh(all_prims, ignore_types))

    results.extend(hierarchy_results)

    if not results:
        return [(CHECK_NAME, "pass", "No empty prims found")]

    return results


def _check_empty_xform_scope(all_prims, ignore_types, root_path, hierarchy_paths):
    results = []
    for path_str in sorted(all_prims):
        prim = all_prims[path_str]
        prim_type = prim.GetTypeName()

        if prim_type not in ("Xform", "Scope"):
            continue
        if path_str == root_path:
            continue
        if prim_type in ignore_types:
            continue
        # Skip prims already covered by a parent hierarchy warning
        if any(path_str.startswith(hp + "/") for hp in hierarchy_paths):
            continue
        if prim.GetChildren():
            continue
        # Any authored property (xformOp locators, visibility, etc.) means not empty
        if prim.GetAuthoredProperties():
            continue

        results.append((CHECK_NAME, "warning",
            f"'{path_str}': {prim_type} prim has no children or properties"))

    return results


def _check_empty_mesh(all_prims, ignore_types):
    results = []
    for path_str in sorted(all_prims):
        prim = all_prims[path_str]
        if prim.GetTypeName() != "Mesh":
            continue
        if "Mesh" in ignore_types:
            continue

        points_attr = prim.GetAttribute("points")
        if not points_attr.IsValid() or not points_attr.HasAuthoredValue():
            results.append((CHECK_NAME, "warning",
                f"'{path_str}': Mesh prim has no geometry data (missing points)"))
            continue
        pts = points_attr.Get()
        if pts is None or len(pts) == 0:
            results.append((CHECK_NAME, "warning",
                f"'{path_str}': Mesh prim has no geometry data (missing points)"))

    return results


def _subtree_has_meaningful(prim):
    """Return True if any descendant of prim has a non-container prim type."""
    for child in prim.GetChildren():
        if child.GetTypeName() not in _CONTAINER_TYPES:
            return True
        if _subtree_has_meaningful(child):
            return True
    return False


def _check_empty_hierarchy(all_prims, ignore_types, root_path):
    results = []
    flagged_paths = set()

    for path_str in sorted(all_prims):
        prim = all_prims[path_str]
        prim_type = prim.GetTypeName()

        if prim_type not in ("Xform", "Scope"):
            continue
        if path_str == root_path:
            continue
        if prim_type in ignore_types:
            continue
        # Must have children — childless containers are handled by empty_xform_scope
        if not prim.GetChildren():
            continue
        # Only flag the top of the chain — skip descendants of already-flagged prims
        if any(path_str.startswith(fp + "/") for fp in flagged_paths):
            continue
        if not _subtree_has_meaningful(prim):
            results.append((CHECK_NAME, "warning",
                f"'{path_str}': hierarchy leads to no meaningful prims"))
            flagged_paths.add(path_str)

    return results, flagged_paths
