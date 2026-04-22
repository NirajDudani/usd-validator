from collections import defaultdict

CHECK_NAME = "Duplicate Names"


def check_duplicate_names(stage, settings):
    dnc = settings.get("duplicate_names", {})

    if not dnc.get("enabled", True):
        return []

    if not stage:
        return [(CHECK_NAME, "error", "No stage loaded — cannot check duplicate names")]

    enabled = dnc.get("enabled_checks", {})
    threshold = dnc.get("cross_branch_threshold", 3)
    ignore_names = {n.lower() for n in dnc.get("ignore_names", [])}

    # Single traversal — collect parent→children map and global name→paths map.
    # parent_children[parent_path][child_name] = [full_prim_path, ...]
    parent_children = defaultdict(lambda: defaultdict(list))
    name_locations = defaultdict(list)

    for prim in stage.TraverseAll():
        path_str = str(prim.GetPath())
        name = prim.GetName()
        parent_str = str(prim.GetPath().GetParentPath())
        parent_children[parent_str][name].append(path_str)
        name_locations[name].append(path_str)

    results = []

    if enabled.get("exact_siblings", True):
        results.extend(_check_exact_siblings(parent_children))

    if enabled.get("case_siblings", True):
        results.extend(_check_case_siblings(parent_children))

    if enabled.get("cross_branch", True):
        results.extend(_check_cross_branch(name_locations, threshold, ignore_names))

    if not results:
        return [(CHECK_NAME, "pass", "No duplicate prim names found")]

    return results


def _check_exact_siblings(parent_children):
    results = []
    for parent_path in sorted(parent_children):
        for name, paths in sorted(parent_children[parent_path].items()):
            if len(paths) > 1:
                results.append((CHECK_NAME, "error",
                    f"'{parent_path}': duplicate child prim name '{name}' found {len(paths)} times"))
    return results


def _check_case_siblings(parent_children):
    results = []
    for parent_path in sorted(parent_children):
        lower_to_variants = defaultdict(list)
        for name in parent_children[parent_path]:
            lower_to_variants[name.lower()].append(name)

        for variants in sorted(lower_to_variants.values(), key=lambda v: sorted(v)[0].lower()):
            # More than one distinct name with the same lowercase form = case-only collision.
            if len(variants) > 1:
                names_str = _format_name_list(sorted(variants))
                results.append((CHECK_NAME, "error",
                    f"'{parent_path}': prim names {names_str} differ only by case"))
    return results


def _check_cross_branch(name_locations, threshold, ignore_names):
    results = []
    for name in sorted(name_locations):
        if name.lower() in ignore_names:
            continue
        paths = name_locations[name]
        if len(paths) >= threshold:
            paths_str = ", ".join(f"'{p}'" for p in paths)
            results.append((CHECK_NAME, "warning",
                f"Prim name '{name}' appears in {len(paths)} locations: {paths_str}"))
    return results


def _format_name_list(names):
    """Format ['a'] → \"'a'\", ['a','b'] → \"'a' and 'b'\", ['a','b','c'] → \"'a', 'b' and 'c'\"."""
    quoted = [f"'{n}'" for n in names]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"
    return ", ".join(quoted[:-1]) + f" and {quoted[-1]}"
