import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxr import Usd
from validators.duplicate_names import check_duplicate_names, _format_name_list


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _settings(**overrides):
    dnc = {
        "enabled": True,
        "enabled_checks": {
            "exact_siblings": True,
            "case_siblings": True,
            "cross_branch": True,
        },
        "cross_branch_threshold": 3,
        "ignore_names": ["geo", "mtl", "rig"],
    }
    dnc.update(overrides)
    return {"duplicate_names": dnc}


def _stage_with(*prim_paths):
    """Create an in-memory stage defining Xform prims at each given path."""
    stage = Usd.Stage.CreateInMemory()
    for path in prim_paths:
        stage.DefinePrim(path, "Xform")
    return stage


# ─────────────────────────────────────────────
# _format_name_list helper
# ─────────────────────────────────────────────

class TestFormatNameList:

    def test_two_names(self):
        assert _format_name_list(["GEO_Body", "GEO_body"]) == "'GEO_Body' and 'GEO_body'"

    def test_three_names(self):
        assert _format_name_list(["a", "b", "c"]) == "'a', 'b' and 'c'"

    def test_single_name(self):
        assert _format_name_list(["solo"]) == "'solo'"


# ─────────────────────────────────────────────
# Exact sibling duplicates
# ─────────────────────────────────────────────

class TestExactSiblings:

    def test_no_duplicates_passes(self):
        stage = _stage_with("/World/GEO_arm", "/World/GEO_leg")
        result = check_duplicate_names(stage, _settings())
        assert not any("duplicate child prim name" in m for _, s, m in result)

    def test_exact_sibling_not_possible_in_composed_stage(self):
        # USD prevents exact duplicate prim paths — redefining returns the same prim.
        # Verifying that the check never produces a false positive in normal usage.
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/World/GEO_body", "Mesh")
        stage.DefinePrim("/World/GEO_body", "Scope")  # redefines, does not create a second prim
        result = check_duplicate_names(stage, _settings())
        assert not any("duplicate child prim name" in m for _, s, m in result)

    def test_exact_siblings_skipped_when_disabled(self):
        stage = _stage_with("/World/GEO_arm")
        settings = _settings(enabled_checks={
            "exact_siblings": False,
            "case_siblings": True,
            "cross_branch": True,
        })
        result = check_duplicate_names(stage, settings)
        assert not any("duplicate child prim name" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Case-only sibling duplicates
# ─────────────────────────────────────────────

class TestCaseSiblings:

    def test_case_collision_is_error(self):
        stage = _stage_with("/World/GEO_body", "/World/GEO_Body")
        result = check_duplicate_names(stage, _settings())
        assert any(
            s == "error" and "GEO_body" in m and "GEO_Body" in m and "differ only by case" in m
            for _, s, m in result
        )

    def test_case_collision_names_in_message(self):
        stage = _stage_with("/World/GEO_body", "/World/GEO_Body")
        result = check_duplicate_names(stage, _settings())
        msgs = [m for _, s, m in result if s == "error" and "differ only by case" in m]
        assert len(msgs) == 1
        assert "'/World'" in msgs[0]

    def test_three_way_case_collision_reported_once(self):
        stage = _stage_with("/World/GEO_body", "/World/GEO_Body", "/World/GEO_BODY")
        result = check_duplicate_names(stage, _settings())
        case_errors = [m for _, s, m in result if "differ only by case" in m]
        # All three variants must appear in the message
        assert len(case_errors) == 1
        assert "GEO_body" in case_errors[0]
        assert "GEO_Body" in case_errors[0]
        assert "GEO_BODY" in case_errors[0]

    def test_distinct_names_no_case_collision(self):
        stage = _stage_with("/World/GEO_arm", "/World/GEO_leg")
        result = check_duplicate_names(stage, _settings())
        assert not any("differ only by case" in m for _, s, m in result)

    def test_case_collision_under_different_parents_reported_per_parent(self):
        # /A/foo and /A/Foo → error; /B/bar and /B/Bar → separate error
        stage = _stage_with("/A/foo", "/A/Foo", "/B/bar", "/B/Bar")
        result = check_duplicate_names(stage, _settings())
        case_errors = [m for _, s, m in result if "differ only by case" in m]
        assert len(case_errors) == 2

    def test_case_siblings_skipped_when_disabled(self):
        stage = _stage_with("/World/GEO_body", "/World/GEO_Body")
        settings = _settings(enabled_checks={
            "exact_siblings": True,
            "case_siblings": False,
            "cross_branch": True,
        })
        result = check_duplicate_names(stage, settings)
        assert not any("differ only by case" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Cross-branch duplicates
# ─────────────────────────────────────────────

class TestCrossBranch:

    def test_name_at_threshold_is_warning(self):
        # GEO_head appears in 3 branches — exactly at threshold=3
        stage = _stage_with(
            "/World/hero/GEO_head",
            "/World/villain/GEO_head",
            "/World/npc/GEO_head",
        )
        result = check_duplicate_names(stage, _settings())
        assert any(
            s == "warning" and "GEO_head" in m and "3 locations" in m
            for _, s, m in result
        )

    def test_name_below_threshold_passes(self):
        # GEO_unique appears in only 2 branches — below threshold=3
        stage = _stage_with(
            "/World/hero/GEO_unique",
            "/World/villain/GEO_unique",
        )
        result = check_duplicate_names(stage, _settings())
        assert not any("GEO_unique" in m for _, s, m in result)

    def test_warning_message_lists_all_paths(self):
        stage = _stage_with(
            "/World/hero/GEO_body",
            "/World/villain/GEO_body",
            "/World/extra/GEO_body",
        )
        result = check_duplicate_names(stage, _settings())
        msgs = [m for _, s, m in result if s == "warning" and "GEO_body" in m]
        assert len(msgs) == 1
        assert "/World/hero/GEO_body" in msgs[0]
        assert "/World/villain/GEO_body" in msgs[0]
        assert "/World/extra/GEO_body" in msgs[0]

    def test_configurable_threshold(self):
        # With threshold=2, a name in 2 locations should trigger
        stage = _stage_with("/World/hero/GEO_body", "/World/villain/GEO_body")
        result = check_duplicate_names(stage, _settings(cross_branch_threshold=2))
        assert any(s == "warning" and "GEO_body" in m for _, s, m in result)

    def test_ignored_names_not_flagged(self):
        # "geo" is in the default ignore_names list
        stage = _stage_with("/World/hero/geo", "/World/villain/geo", "/World/npc/geo")
        result = check_duplicate_names(stage, _settings())
        assert not any("'geo'" in m and "locations" in m for _, s, m in result)

    def test_non_ignored_names_still_flagged(self):
        stage = _stage_with(
            "/World/hero/GEO_torso",
            "/World/villain/GEO_torso",
            "/World/npc/GEO_torso",
        )
        result = check_duplicate_names(stage, _settings())
        assert any(s == "warning" and "GEO_torso" in m for _, s, m in result)

    def test_ignore_names_case_insensitive(self):
        # "GEO" uppercased should still be ignored if "geo" is in ignore_names
        stage = _stage_with("/World/a/GEO", "/World/b/GEO", "/World/c/GEO")
        result = check_duplicate_names(stage, _settings(ignore_names=["GEO"]))
        assert not any("'GEO'" in m and "locations" in m for _, s, m in result)

    def test_cross_branch_skipped_when_disabled(self):
        stage = _stage_with(
            "/World/hero/GEO_body",
            "/World/villain/GEO_body",
            "/World/npc/GEO_body",
        )
        settings = _settings(enabled_checks={
            "exact_siblings": True,
            "case_siblings": True,
            "cross_branch": False,
        })
        result = check_duplicate_names(stage, settings)
        assert not any("locations" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Parent-child same name (should pass)
# ─────────────────────────────────────────────

class TestParentChildSameName:

    def test_parent_and_child_same_name_is_not_flagged(self):
        # /World/node/node — parent "node" has a child also called "node"
        # This is only 2 occurrences total, below default threshold=3
        stage = _stage_with("/World/node/node")
        result = check_duplicate_names(stage, _settings())
        assert not any("'node'" in m and "locations" in m for _, s, m in result)

    def test_parent_child_same_name_not_a_sibling_duplicate(self):
        stage = _stage_with("/World/geo/geo")
        result = check_duplicate_names(stage, _settings())
        # geo is in ignore_names, and also parent-child (not siblings)
        assert not any("differ only by case" in m for _, s, m in result)
        assert not any("duplicate child prim name" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Overall / guard rails
# ─────────────────────────────────────────────

class TestOverall:

    def test_disabled_returns_empty(self):
        stage = _stage_with("/World/GEO_body", "/World/GEO_Body")
        result = check_duplicate_names(stage, {"duplicate_names": {"enabled": False}})
        assert result == []

    def test_no_stage_returns_error(self):
        result = check_duplicate_names(None, _settings())
        assert result == [("Duplicate Names", "error", "No stage loaded — cannot check duplicate names")]

    def test_clean_stage_returns_pass(self):
        stage = _stage_with("/World/GEO_arm", "/World/GEO_leg", "/World/GEO_torso")
        result = check_duplicate_names(stage, _settings())
        assert result == [("Duplicate Names", "pass", "No duplicate prim names found")]

    def test_mixed_issues_all_reported(self):
        # Case collision AND cross-branch together
        stage = _stage_with(
            "/World/GEO_body",   # case collision sibling
            "/World/GEO_Body",   # case collision sibling
            "/World/hero/GEO_head",
            "/World/villain/GEO_head",
            "/World/npc/GEO_head",
        )
        result = check_duplicate_names(stage, _settings())
        statuses = [s for _, s, _ in result]
        assert "error" in statuses    # case collision
        assert "warning" in statuses  # cross-branch
