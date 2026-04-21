import os
import re
import fnmatch

from pxr import Usd, Sdf, Ar

_ENV_VAR_PAT = re.compile(r'\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*')

CHECK_NAME = "Broken References"


def check_broken_references(stage, settings):
    brc = settings.get("broken_references", {})

    if not brc.get("enabled", True):
        return []

    if not stage:
        return [(CHECK_NAME, "error", "No stage loaded — cannot check references")]

    enabled = brc.get("enabled_checks", {})
    search_paths = brc.get("additional_search_paths", [])
    ignore_patterns = brc.get("ignore_patterns", [])

    results = []
    seen_refs = set()

    for prim in stage.Traverse():
        prim_path = str(prim.GetPath())

        for prim_spec in prim.GetPrimStack():
            layer = prim_spec.layer
            ref_items = (
                list(prim_spec.referenceList.prependedItems)
                + list(prim_spec.referenceList.appendedItems)
                + list(prim_spec.referenceList.explicitItems)
                + list(prim_spec.payloadList.prependedItems)
                + list(prim_spec.payloadList.appendedItems)
                + list(prim_spec.payloadList.explicitItems)
            )

            for ref in ref_items:
                asset_path = ref.assetPath
                ref_prim_path = str(ref.primPath) if ref.primPath else ""
                key = (prim_path, asset_path, ref_prim_path)
                if key in seen_refs:
                    continue
                seen_refs.add(key)

                if _should_ignore(asset_path or ref_prim_path, ignore_patterns):
                    continue

                if not asset_path:
                    # Internal reference — no file, just a prim path in this stage
                    if enabled.get("internal_references", True) and ref_prim_path:
                        results.extend(_check_internal_ref(stage, prim_path, ref_prim_path))
                else:
                    resolved, is_env_var = _resolve_file(asset_path, layer, search_paths)
                    if is_env_var:
                        if enabled.get("unresolvable_paths", True):
                            results.append((CHECK_NAME, "warning",
                                f"'{prim_path}': reference path '{asset_path}' could not be resolved"))
                    elif enabled.get("external_references", True):
                        if not resolved:
                            results.append((CHECK_NAME, "error",
                                f"'{prim_path}': reference file not found: '{asset_path}'"))
                        elif ref_prim_path:
                            results.extend(
                                _check_prim_in_file(prim_path, resolved, ref_prim_path, asset_path)
                            )

    if enabled.get("asset_paths", True) or enabled.get("unresolvable_paths", True):
        results.extend(_check_asset_path_attrs(stage, enabled, search_paths, ignore_patterns))

    if not results:
        return [(CHECK_NAME, "pass", "All references and asset paths resolved")]

    return results


def _check_internal_ref(stage, prim_path, ref_prim_path):
    target = stage.GetPrimAtPath(ref_prim_path)
    if not target.IsValid():
        return [(CHECK_NAME, "error",
                 f"'{prim_path}': internal reference prim '{ref_prim_path}' not found")]
    return []


def _check_prim_in_file(prim_path, abs_file_path, ref_prim_path, original_asset_path):
    try:
        ref_stage = Usd.Stage.Open(abs_file_path, load=Usd.Stage.LoadNone)
    except Exception:
        return []
    target = ref_stage.GetPrimAtPath(ref_prim_path)
    if not target.IsValid():
        return [(CHECK_NAME, "error",
                 f"'{prim_path}': reference prim '{ref_prim_path}' not found in '{original_asset_path}'")]
    return []


def _check_asset_path_attrs(stage, enabled, search_paths, ignore_patterns):
    results = []
    seen = set()
    root_layer = stage.GetRootLayer()

    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            type_name = attr.GetTypeName()
            is_asset = type_name == Sdf.ValueTypeNames.Asset
            is_asset_array = type_name == Sdf.ValueTypeNames.AssetArray
            if not is_asset and not is_asset_array:
                continue

            value = attr.Get()
            if value is None:
                continue

            raw_paths = [value] if is_asset else list(value)
            attr_path = f"{prim.GetPath()}.{attr.GetName()}"

            for ap in raw_paths:
                raw = ap.path if hasattr(ap, "path") else str(ap)
                if not raw or raw == ".":
                    continue

                key = (attr_path, raw)
                if key in seen:
                    continue
                seen.add(key)

                if _should_ignore(raw, ignore_patterns):
                    continue

                resolved, is_env_var = _resolve_file(raw, root_layer, search_paths)
                if is_env_var:
                    if enabled.get("unresolvable_paths", True):
                        results.append((CHECK_NAME, "warning",
                                        f"'{attr_path}': asset path '{raw}' could not be resolved"))
                elif enabled.get("asset_paths", True):
                    if not resolved:
                        results.append((CHECK_NAME, "warning",
                                        f"'{attr_path}': asset path not found: '{raw}'"))

    return results


def _resolve_file(asset_path, source, search_paths):
    """Return (resolved_abs_path, is_unresolvable_env_var).

    Tries layer.ComputeAbsolutePath first (handles USD-style relative paths), then
    falls back to manual join and the Ar resolver. Returns ('', True) when the path
    contains env-var tokens that expandvars cannot expand.
    """
    if not asset_path:
        return "", False

    expanded = os.path.expandvars(asset_path)
    if _ENV_VAR_PAT.search(expanded):
        return "", True

    layer = source if hasattr(source, "ComputeAbsolutePath") else None
    if layer and layer.realPath:
        try:
            abs_path = layer.ComputeAbsolutePath(expanded)
            if abs_path and os.path.exists(abs_path):
                return abs_path, False
        except Exception:
            pass

    # Fallback: manual join relative to source directory
    anchor_dir = ""
    if isinstance(source, str):
        anchor_dir = source
    elif layer and layer.realPath:
        anchor_dir = os.path.dirname(layer.realPath)

    if anchor_dir:
        candidate = os.path.normpath(os.path.join(anchor_dir, expanded))
        if os.path.exists(candidate):
            return candidate, False

    if os.path.isabs(expanded) and os.path.exists(expanded):
        return expanded, False

    for sp in search_paths:
        candidate = os.path.normpath(os.path.join(sp, expanded))
        if os.path.exists(candidate):
            return candidate, False

    try:
        resolved = Ar.GetResolver().Resolve(expanded)
        if resolved and os.path.exists(resolved):
            return resolved, False
    except Exception:
        pass

    return "", False


def _should_ignore(path, ignore_patterns):
    if not path or not ignore_patterns:
        return False
    base = os.path.basename(path)
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(base, p) for p in ignore_patterns)
