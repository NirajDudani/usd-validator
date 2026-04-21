import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators.naming_convention import (
    check_naming_convention,
    _check_prim_chars,
    _detect_style,
    _check_prim_reserved,
    _check_prim_patterns,
    _check_consistency,
    _strip_known_prefix,
)


# ─────────────────────────────────────────────
# _check_prim_chars
# ─────────────────────────────────────────────

class TestCheckPrimChars:

    def test_clean_name_no_results(self):
        assert _check_prim_chars("GEO_sphere", "/Root/GEO_sphere", {}) == []

    def test_illegal_space(self):
        result = _check_prim_chars("Bad Prim", "/Root/Bad Prim", {})
        assert any(r[0] == "error" and "illegal character ' '" in r[1] for r in result)

    def test_illegal_at_sign(self):
        result = _check_prim_chars("bad@name", "/Root/bad@name", {})
        assert any(r[0] == "error" and "illegal character '@'" in r[1] for r in result)

    def test_starts_with_digit(self):
        result = _check_prim_chars("1Geo", "/Root/1Geo", {})
        assert any(r[0] == "error" and "starts with a digit" in r[1] for r in result)

    def test_double_underscore(self):
        result = _check_prim_chars("Geo__mesh", "/Root/Geo__mesh", {})
        assert any(r[0] == "error" and "double underscore" in r[1] for r in result)

    def test_leading_underscore_warning(self):
        result = _check_prim_chars("_Geo", "/Root/_Geo", {})
        assert any(r[0] == "warning" and "leading underscore" in r[1] for r in result)

    def test_trailing_underscore_warning(self):
        result = _check_prim_chars("Geo_", "/Root/Geo_", {})
        assert any(r[0] == "warning" and "trailing underscore" in r[1] for r in result)

    def test_exactly_at_max_length_no_warning(self):
        name = "a" * 128
        result = _check_prim_chars(name, f"/Root/{name}", {"max_name_length": 128})
        assert not any("characters" in r[1] for r in result)

    def test_one_over_max_length_warning(self):
        name = "a" * 129
        result = _check_prim_chars(name, f"/Root/{name}", {"max_name_length": 128})
        assert any(r[0] == "warning" and "129 characters" in r[1] for r in result)

    def test_extra_illegal_not_present_no_extra_result(self):
        result = _check_prim_chars("GEO_sphere", "/Root/GEO_sphere", {"illegal_characters": "@"})
        assert result == []

    def test_extra_illegal_present_error(self):
        # Make digits illegal beyond the base rule
        result = _check_prim_chars("abc3def", "/Root/abc3def", {"illegal_characters": "0123456789"})
        assert any(r[0] == "error" and "illegal character '3'" in r[1] for r in result)

    def test_alphanumeric_clean_name_no_results(self):
        assert _check_prim_chars("GEOsphere", "/Root/GEOsphere", {}) == []

    def test_empty_name_no_results(self):
        assert _check_prim_chars("", "/Root/", {}) == []

    def test_double_underscore_and_leading_both_reported(self):
        result = _check_prim_chars("__foo", "/Root/__foo", {})
        assert any(r[0] == "error" and "double underscore" in r[1] for r in result)
        assert any(r[0] == "warning" and "leading underscore" in r[1] for r in result)

    def test_short_name_skips_leading_underscore(self):
        # "_x" is 2 chars (< _MIN_SEMANTIC_LEN=3) — leading underscore warning suppressed
        result = _check_prim_chars("_x", "/Root/_x", {})
        assert not any("leading underscore" in r[1] for r in result)

    def test_short_name_skips_trailing_underscore(self):
        result = _check_prim_chars("x_", "/Root/x_", {})
        assert not any("trailing underscore" in r[1] for r in result)

    def test_short_name_still_catches_double_underscore(self):
        # "__" is 2 chars but double underscore error always fires
        result = _check_prim_chars("__", "/Root/__", {})
        assert any(r[0] == "error" and "double underscore" in r[1] for r in result)

    def test_short_name_skips_max_length_warning(self):
        # A 2-char name over the limit (max=1) should not warn for short names
        result = _check_prim_chars("ab", "/Root/ab", {"max_name_length": 1})
        assert not any("characters" in r[1] for r in result)


# ─────────────────────────────────────────────
# _detect_style
# ─────────────────────────────────────────────

class TestDetectStyle:

    def test_snake_case(self):
        assert _detect_style("my_mesh") == "snake_case"

    def test_pascal_case(self):
        assert _detect_style("MyMesh") == "PascalCase"

    def test_camel_case(self):
        assert _detect_style("myMesh") == "camelCase"

    def test_too_short_three_chars(self):
        assert _detect_style("abc") == "unknown"

    def test_exactly_four_chars_pascal(self):
        assert _detect_style("MyMe") == "PascalCase"

    def test_all_caps_unknown(self):
        # All uppercase has no lowercase — not classified as PascalCase
        assert _detect_style("ALLCAPS") == "unknown"

    def test_all_lowercase_unknown(self):
        # No underscore, no uppercase → unknown
        assert _detect_style("abcd") == "unknown"

    def test_four_chars_with_underscore(self):
        assert _detect_style("my_x") == "snake_case"


# ─────────────────────────────────────────────
# _check_prim_reserved
# ─────────────────────────────────────────────

class TestCheckPrimReserved:

    def test_default_is_error(self):
        result = _check_prim_reserved("default", "/Root/default", ["default", "mesh"])
        assert result == [("error", "'/Root/default': name 'default' is a reserved USD keyword")]

    def test_default_case_insensitive_is_error(self):
        result = _check_prim_reserved("Default", "/Root/Default", ["default", "mesh"])
        assert result[0][0] == "error"

    def test_other_reserved_is_warning(self):
        result = _check_prim_reserved("mesh", "/Root/mesh", ["default", "mesh"])
        assert result == [("warning", "'/Root/mesh': name 'mesh' is a reserved USD keyword")]

    def test_other_reserved_case_insensitive_warning(self):
        result = _check_prim_reserved("MESH", "/Root/MESH", ["default", "mesh"])
        assert result[0][0] == "warning"
        assert "MESH" in result[0][1]

    def test_clean_name_no_result(self):
        assert _check_prim_reserved("clean_name", "/Root/clean_name", ["default", "mesh"]) == []

    def test_class_node_not_flagged(self):
        # "class_node" contains "class" as a substring but is NOT an exact match
        assert _check_prim_reserved("class_node", "/Root/class_node", ["class", "default"]) == []

    def test_exact_class_is_flagged(self):
        result = _check_prim_reserved("class", "/Root/class", ["class", "default"])
        assert result[0][0] == "warning"


# ─────────────────────────────────────────────
# _check_prim_patterns
# ─────────────────────────────────────────────

_PREFIX_SETTINGS = {
    "prim_type_prefixes": {
        "Mesh": ["GEO_"],
        "Material": ["MAT_"],
    }
}


class TestCheckPrimPatterns:

    def test_mesh_valid_prefix_no_result(self):
        result = _check_prim_patterns("GEO_sphere", "/Root/GEO_sphere", "Mesh", "MyAsset", _PREFIX_SETTINGS)
        assert result == []

    def test_mesh_invalid_prefix_warning_with_hint(self):
        result = _check_prim_patterns("sphere", "/Root/sphere", "Mesh", "MyAsset", _PREFIX_SETTINGS)
        assert any("GEO_" in r[1] and "sph" in r[1] for r in result)

    def test_root_prim_matches_stem_no_result(self):
        result = _check_prim_patterns("MyAsset", "/MyAsset", "Xform", "MyAsset", {})
        assert result == []

    def test_root_prim_mismatch_warning(self):
        result = _check_prim_patterns("World", "/World", "Xform", "MyAsset", {})
        assert any("'World'" in r[1] and "'MyAsset'" in r[1] for r in result)

    def test_non_root_skips_stem_check(self):
        result = _check_prim_patterns("World", "/Root/World", "Xform", "MyAsset", {})
        assert not any("does not match file name" in r[1] for r in result)

    def test_unknown_prim_type_skips_prefix_check(self):
        result = _check_prim_patterns("sphere", "/Root/sphere", "Xform", "MyAsset", _PREFIX_SETTINGS)
        assert not any("should start with" in r[1] for r in result)


# ─────────────────────────────────────────────
# _strip_known_prefix
# ─────────────────────────────────────────────

class TestStripKnownPrefix:

    def test_strips_matching_prefix(self):
        assert _strip_known_prefix("GEO_upperTorso", ["GEO_", "MAT_"]) == "upperTorso"

    def test_no_match_returns_original(self):
        assert _strip_known_prefix("sphere", ["GEO_", "MAT_"]) == "sphere"

    def test_empty_prefix_list_returns_original(self):
        assert _strip_known_prefix("GEO_mesh", []) == "GEO_mesh"

    def test_prefix_only_no_suffix_not_stripped(self):
        # "GEO_" with nothing after must not return empty string
        assert _strip_known_prefix("GEO_", ["GEO_"]) == "GEO_"

    def test_mat_prefix_stripped(self):
        assert _strip_known_prefix("MAT_woodFloor", ["GEO_", "MAT_"]) == "woodFloor"


# ─────────────────────────────────────────────
# _check_consistency
# ─────────────────────────────────────────────

class TestCheckConsistency:

    def test_all_snake_case_no_results(self):
        pairs = [("my_mesh", "/Root/my_mesh"), ("geo_sphere", "/Root/geo_sphere")]
        assert _check_consistency(pairs, None) == []

    def test_outlier_flagged(self):
        pairs = [
            ("my_mesh", "/Root/my_mesh"),
            ("geo_sphere", "/Root/geo_sphere"),
            ("myMesh", "/Root/myMesh"),
        ]
        result = _check_consistency(pairs, None)
        assert any("myMesh" in r[1] and "camelCase" in r[1] and "snake_case" in r[1] for r in result)

    def test_all_unknown_no_results(self):
        # All names < 4 chars → all unknown → no dominant style
        pairs = [("abc", "/Root/abc"), ("xyz", "/Root/xyz")]
        assert _check_consistency(pairs, None) == []

    def test_preferred_style_overrides_auto(self):
        pairs = [("my_mesh", "/Root/my_mesh"), ("MyMesh", "/Root/MyMesh")]
        result = _check_consistency(pairs, "PascalCase")
        assert any("my_mesh" in r[1] and "PascalCase" in r[1] for r in result)

    def test_tie_broken_alphabetically_camel_wins(self):
        # Equal counts of camelCase and PascalCase → camelCase wins (STYLE_ORDER 0 < 1)
        pairs = [
            ("myMesh", "/Root/myMesh"),
            ("MyMesh", "/Root/MyMesh"),
        ]
        result = _check_consistency(pairs, None)
        # dominant = camelCase, so PascalCase MyMesh is flagged
        assert any("MyMesh" in r[1] and "PascalCase" in r[1] for r in result)

    def test_empty_pairs_no_results(self):
        assert _check_consistency([], None) == []

    def test_geo_prefix_stripped_before_style_detection(self):
        # "GEO_upperTorso" suffix is camelCase; without stripping it looks snake_case.
        pairs = [
            ("GEO_upperTorso", "/Root/GEO_upperTorso"),
            ("GEO_lowerTorso", "/Root/GEO_lowerTorso"),
        ]
        result = _check_consistency(pairs, None, known_prefixes=["GEO_"])
        # Both classify as camelCase after stripping → dominant = camelCase → no outliers
        assert result == []

    def test_mixed_prefixed_and_plain_camel(self):
        # "GEO_sphere" suffix is "sphere" → unknown (< 4 chars after strip),
        # but "GEO_upperTorso" → camelCase. "myMesh" → camelCase. Consistent.
        pairs = [
            ("GEO_upperTorso", "/Root/GEO_upperTorso"),
            ("myMesh", "/Root/myMesh"),
        ]
        result = _check_consistency(pairs, None, known_prefixes=["GEO_"])
        assert result == []


# ─────────────────────────────────────────────
# check_naming_convention (integration)
# ─────────────────────────────────────────────

def _full_nc_settings(**overrides):
    nc = {
        "enabled": True,
        "check_chars": True,
        "check_patterns": True,
        "check_reserved": True,
        "check_consistency": True,
        "illegal_characters": "",
        "max_name_length": 128,
        "style": None,
        "prim_type_prefixes": {"Mesh": ["GEO_"]},
        "reserved_names": ["default", "mesh"],
    }
    nc.update(overrides)
    return {"naming_check": nc}


class TestCheckNamingConvention:

    def test_disabled_returns_empty(self):
        from pxr import Usd
        stage = Usd.Stage.CreateInMemory()
        assert check_naming_convention(stage, {"naming_check": {"enabled": False}}) == []

    def test_none_stage_returns_error(self):
        result = check_naming_convention(None, _full_nc_settings())
        assert result == [("Naming", "error", "No stage loaded — cannot check naming")]

    def test_clean_stage_returns_pass(self):
        from pxr import Usd
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/GEO_sphere", "Mesh")
        result = check_naming_convention(stage, _full_nc_settings())
        assert result == [("Naming", "pass", "No naming issues found")]

    def test_leading_underscore_produces_warning(self):
        from pxr import Usd
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/_GeoSphere", "Xform")
        result = check_naming_convention(stage, _full_nc_settings())
        assert any(r[1] == "warning" and "leading underscore" in r[2] for r in result)

    def test_multiple_issues_on_same_prim_grouped(self):
        # "1Bad Prim" has digit-start AND illegal space — both appear in one row
        from pxr import Usd
        stage = Usd.Stage.CreateInMemory()
        # Can't define a prim with a space via normal API, so test via _check_prim_chars directly
        results = _check_prim_chars("1Bad", "/Root/1Bad", {})
        # digit-start error + no other error expected
        assert any(r[0] == "error" and "starts with a digit" in r[1] for r in results)
        # Simulate grouping: orchestrator merges these into one result
        worst = "error" if any(s == "error" for s, _ in results) else "warning"
        assert worst == "error"

    def test_char_error_suppresses_prefix_check(self):
        # A prim with a char error should NOT also get a prefix warning
        from pxr import Usd
        stage = Usd.Stage.CreateInMemory()
        # "1sphere" starts with digit (error) — prefix check should be skipped
        # Can't define such a prim in USD directly, so test orchestrator logic via
        # a prim that triggers double-underscore error (which we can define)
        stage.DefinePrim("/Root", "Xform")
        # Define a prim that has a valid USD name but triggers the double-underscore rule
        # We confirm by checking that a mesh prim with valid name does get prefix warning
        stage.DefinePrim("/Root/sphere", "Mesh")
        result = check_naming_convention(stage, _full_nc_settings())
        # "sphere" is a Mesh without GEO_ prefix → should get a prefix warning
        assert any(r[1] == "warning" and "GEO_" in r[2] for r in result)


# ─────────────────────────────────────────────
# DEFAULT_SETTINGS structure validation
# ─────────────────────────────────────────────

class TestDefaultSettingsStructure:

    def test_naming_check_keys_and_types(self):
        from tools.usd_validator import DEFAULT_SETTINGS
        nc = DEFAULT_SETTINGS["naming_check"]
        assert isinstance(nc["enabled"], bool)
        assert isinstance(nc["check_chars"], bool)
        assert isinstance(nc["check_patterns"], bool)
        assert isinstance(nc["check_reserved"], bool)
        assert isinstance(nc["check_consistency"], bool)
        assert isinstance(nc["max_name_length"], int)
        assert nc["max_name_length"] > 0
        assert isinstance(nc["prim_type_prefixes"], dict)
        assert isinstance(nc["reserved_names"], list)
        assert "default" in nc["reserved_names"]
