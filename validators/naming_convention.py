import os
import re
from collections import Counter

_ILLEGAL_PAT = re.compile(r'[^A-Za-z0-9_]')

# Names shorter than this skip semantic checks (leading/trailing underscore,
# prefix patterns, max length) — only structural errors like double underscore
# still fire on very short names.
_MIN_SEMANTIC_LEN = 3

# Tie-breaking order for _check_consistency. Must include every style that
# _detect_style can return (other than "unknown"). Lower value = higher priority.
STYLE_ORDER = {"camelCase": 0, "PascalCase": 1, "snake_case": 2}


def check_naming_convention(stage, settings):
    nc = settings["naming_check"]

    if not nc["enabled"]:
        return []

    if not stage:
        return [("Naming", "error", "No stage loaded \u2014 cannot check naming")]

    identifier = stage.GetRootLayer().identifier
    if identifier and not identifier.startswith("anon:"):
        file_stem = os.path.splitext(os.path.basename(identifier))[0]
    else:
        file_stem = ""

    # Flatten all known prefixes for use in consistency style detection.
    all_prefixes = [
        p
        for prefixes in nc.get("prim_type_prefixes", {}).values()
        for p in prefixes
    ]

    results = []
    name_path_pairs = []

    for prim in stage.TraverseAll():
        name = prim.GetName()
        path = str(prim.GetPath())
        prim_type = prim.GetTypeName()
        short_name = len(name) < _MIN_SEMANTIC_LEN

        prim_results = []
        has_char_error = False

        if nc.get("check_chars", True):
            char_results = _check_prim_chars(name, path, nc)
            prim_results.extend(char_results)
            has_char_error = any(s == "error" for s, _ in char_results)

        # Skip prefix check when the name is too short or already has a char error
        # (prefix hint would be misleading alongside an error on the same name).
        if nc.get("check_patterns", True) and not short_name and not has_char_error:
            prim_results.extend(_check_prim_patterns(name, path, prim_type, file_stem, nc))

        if nc.get("check_reserved", True):
            prim_results.extend(_check_prim_reserved(name, path, nc.get("reserved_names", [])))

        # Group all issues for this prim into one result row.
        if prim_results:
            worst = "error" if any(s == "error" for s, _ in prim_results) else "warning"
            path_prefix = f"'{path}': "
            stripped_msgs = [
                msg[len(path_prefix):] if msg.startswith(path_prefix) else msg
                for _, msg in prim_results
            ]
            results.append(("Naming", worst, path_prefix + "; ".join(stripped_msgs)))

        name_path_pairs.append((name, path))

    if nc.get("check_consistency", True):
        for status, msg in _check_consistency(name_path_pairs, nc.get("style"), all_prefixes):
            results.append(("Naming", status, msg))

    if not results:
        results.append(("Naming", "pass", "No naming issues found"))

    return results


def _check_prim_chars(name, path, settings):
    results = []
    max_len = settings.get("max_name_length", 128)
    extra_illegal = set(settings.get("illegal_characters", ""))
    short_name = len(name) < _MIN_SEMANTIC_LEN

    for char in name:
        if _ILLEGAL_PAT.search(char) or char in extra_illegal:
            results.append(("error", f"'{path}': illegal character '{char}' in name"))
            # report only the first illegal character to avoid flooding results
            break

    # Digit-start is a separate rule: digits are valid in [A-Za-z0-9_] so they
    # don't trigger _ILLEGAL_PAT, but leading digits are still disallowed.
    if name and name[0].isdigit():
        results.append(("error", f"'{path}': name starts with a digit"))

    # Double-underscore fires even on short names — it's a concrete pattern match,
    # not a stylistic judgment. Leading/trailing underscore checks are skipped for
    # short names to avoid noise on single-char or two-char helper prims.
    if "__" in name:
        results.append(("error", f"'{path}': name contains double underscore"))

    if not short_name:
        if name.startswith("_"):
            results.append(("warning", f"'{path}': name has a leading underscore"))

        if name.endswith("_"):
            results.append(("warning", f"'{path}': name has a trailing underscore"))

        if len(name) > max_len:
            results.append(("warning", f"'{path}': name is {len(name)} characters (max: {max_len})"))

    return results


def _detect_style(name):
    if len(name) < 4:
        return "unknown"
    if "_" in name:
        return "snake_case"
    if name[0].isupper() and any(c.islower() for c in name):
        return "PascalCase"
    if name[0].islower() and any(c.isupper() for c in name[1:]):
        return "camelCase"
    return "unknown"


def _strip_known_prefix(name, known_prefixes):
    """Strip a known prim-type prefix before style detection.

    'GEO_upperTorso' → 'upperTorso' so the suffix is classified as camelCase
    rather than snake_case (which the underscore in the prefix would trigger).
    Only strips when a non-empty suffix remains after the prefix.
    """
    for prefix in known_prefixes:
        if name.startswith(prefix) and len(name) > len(prefix):
            return name[len(prefix):]
    return name


def _check_prim_reserved(name, path, reserved_names):
    name_lower = name.lower()
    # Exact match only (case-insensitive). "class_node" is NOT flagged — only
    # the exact reserved word "class" itself would match.
    # Returns on first match only. Duplicate-cased entries in reserved_names
    # (e.g. "default" and "DEFAULT") are silently deduplicated by this early return.
    for reserved in reserved_names:
        if name_lower == reserved.lower():
            if name_lower == "default":
                return [("error", f"'{path}': name 'default' is a reserved USD keyword")]
            else:
                return [("warning", f"'{path}': name '{name}' is a reserved USD keyword")]
    return []


def _check_prim_patterns(name, path, prim_type, file_stem, settings):
    results = []

    path_parts = [p for p in path.split("/") if p]
    if len(path_parts) == 1 and file_stem:
        if name != file_stem:
            results.append(("warning", f"'{path}': root prim name '{name}' does not match file name '{file_stem}'"))

    prim_type_prefixes = settings.get("prim_type_prefixes", {})
    if prim_type in prim_type_prefixes:
        valid_prefixes = prim_type_prefixes[prim_type]
        if not any(name.startswith(p) for p in valid_prefixes):
            first3 = name[:3]
            prefixes_str = ", ".join(valid_prefixes)
            results.append(("warning", f"'{path}': {prim_type} prims should start with one of: {prefixes_str} (found: '{first3}')"))

    return results


def _check_consistency(name_path_pairs, preferred_style, known_prefixes=None):
    if not name_path_pairs:
        return []

    known_prefixes = known_prefixes or []
    styles = [
        (name, path, _detect_style(_strip_known_prefix(name, known_prefixes)))
        for name, path in name_path_pairs
    ]

    if preferred_style:
        dominant = preferred_style
    else:
        style_counts = Counter(s for _, _, s in styles if s != "unknown")
        if not style_counts:
            return []
        max_count = max(style_counts.values())
        top_styles = sorted(
            [s for s, c in style_counts.items() if c == max_count],
            key=lambda s: STYLE_ORDER.get(s, 99)
        )
        dominant = top_styles[0]

    results = []
    for name, path, style in styles:
        if style != "unknown" and style != dominant:
            results.append(("warning", f"'{path}': name uses {style} but dominant style is {dominant}"))

    return results
