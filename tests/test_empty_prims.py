import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxr import Usd, Gf, Sdf
from validators.empty_prims import check_empty_prims


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _settings(**overrides):
    epc = {
        "enabled": True,
        "enabled_checks": {
            "empty_xform_scope": True,
            "empty_mesh": True,
            "empty_hierarchy": True,
        },
        "ignore_types": ["Camera", "Light"],
    }
    epc.update(overrides)
    return {"empty_prims": epc}


def _stage():
    return Usd.Stage.CreateInMemory()


def _warnings(result):
    return [m for _, s, m in result if s == "warning"]


def _passes(result):
    return [m for _, s, m in result if s == "pass"]


# ─────────────────────────────────────────────
# Empty Xform / Scope
# ─────────────────────────────────────────────

class TestEmptyXformScope:

    def test_empty_xform_is_warning(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_empty", "Xform")
        result = check_empty_prims(stage, _settings())
        assert any("GRP_empty" in m and "Xform prim has no children or properties" in m
                   for m in _warnings(result))

    def test_empty_scope_is_warning(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_placeholder", "Scope")
        result = check_empty_prims(stage, _settings())
        assert any("GRP_placeholder" in m and "Scope prim has no children or properties" in m
                   for m in _warnings(result))

    def test_xform_with_child_passes(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_group", "Xform")
        stage.DefinePrim("/World/GRP_group/GEO_mesh", "Mesh")
        result = check_empty_prims(stage, _settings())
        assert not any("GRP_group" in m and "no children" in m for m in _warnings(result))

    def test_scope_with_child_passes(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_scope", "Scope")
        stage.DefinePrim("/World/GRP_scope/GEO_mesh", "Mesh")
        result = check_empty_prims(stage, _settings())
        assert not any("GRP_scope" in m and "no children" in m for m in _warnings(result))

    def test_locator_xform_passes(self):
        # Xform with only xformOp properties, no children — treated as locator
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        locator = stage.DefinePrim("/World/GRP_locator", "Xform")
        translate = locator.CreateAttribute("xformOp:translate", Sdf.ValueTypeNames.Double3)
        translate.Set(Gf.Vec3d(10.0, 0.0, 5.0))
        result = check_empty_prims(stage, _settings())
        assert not any("GRP_locator" in m and "no children" in m for m in _warnings(result))

    def test_root_prim_skipped(self):
        stage = _stage()
        # Root prim itself is empty but must not be flagged
        root = stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(root)
        result = check_empty_prims(stage, _settings())
        assert not any("/World" in m and "no children" in m for m in _warnings(result))

    def test_check_disabled(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_empty", "Xform")
        settings = _settings(enabled_checks={
            "empty_xform_scope": False,
            "empty_mesh": True,
            "empty_hierarchy": True,
        })
        result = check_empty_prims(stage, settings)
        assert not any("no children or properties" in m for m in _warnings(result))


# ─────────────────────────────────────────────
# Empty Mesh
# ─────────────────────────────────────────────

class TestEmptyMesh:

    def test_mesh_with_no_points_is_warning(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GEO_empty", "Mesh")
        result = check_empty_prims(stage, _settings())
        assert any("GEO_empty" in m and "no geometry data" in m for m in _warnings(result))

    def test_mesh_with_points_passes(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        mesh = stage.DefinePrim("/World/GEO_chair", "Mesh")
        pts_attr = mesh.CreateAttribute("points", Sdf.ValueTypeNames.Point3fArray)
        pts_attr.Set([(0, 0, 0), (1, 0, 0), (1, 1, 0)])
        result = check_empty_prims(stage, _settings())
        assert not any("GEO_chair" in m and "no geometry data" in m for m in _warnings(result))

    def test_mesh_with_empty_points_array_is_warning(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        mesh = stage.DefinePrim("/World/GEO_empty2", "Mesh")
        pts_attr = mesh.CreateAttribute("points", Sdf.ValueTypeNames.Point3fArray)
        pts_attr.Set([])
        result = check_empty_prims(stage, _settings())
        assert any("GEO_empty2" in m and "no geometry data" in m for m in _warnings(result))

    def test_check_disabled(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GEO_empty", "Mesh")
        settings = _settings(enabled_checks={
            "empty_xform_scope": True,
            "empty_mesh": False,
            "empty_hierarchy": True,
        })
        result = check_empty_prims(stage, settings)
        assert not any("no geometry data" in m for m in _warnings(result))


# ─────────────────────────────────────────────
# Empty Hierarchy
# ─────────────────────────────────────────────

class TestEmptyHierarchy:

    def test_nested_empty_containers_flagged_at_top(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_nested", "Xform")
        stage.DefinePrim("/World/GRP_nested/GRP_deeper", "Xform")
        stage.DefinePrim("/World/GRP_nested/GRP_deeper/GRP_deepest", "Xform")
        result = check_empty_prims(stage, _settings())
        warns = _warnings(result)
        assert any("GRP_nested" in m and "hierarchy leads to no meaningful prims" in m
                   for m in warns)

    def test_inner_containers_not_double_reported(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_nested", "Xform")
        stage.DefinePrim("/World/GRP_nested/GRP_deeper", "Xform")
        stage.DefinePrim("/World/GRP_nested/GRP_deeper/GRP_deepest", "Xform")
        result = check_empty_prims(stage, _settings())
        warns = _warnings(result)
        # Only GRP_nested should appear, not GRP_deeper or GRP_deepest
        assert not any("GRP_deeper" in m for m in warns)
        assert not any("GRP_deepest" in m for m in warns)

    def test_hierarchy_containing_mesh_passes(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_furniture", "Scope")
        stage.DefinePrim("/World/GRP_furniture/GEO_chair", "Mesh")
        result = check_empty_prims(stage, _settings())
        assert not any("GRP_furniture" in m and "hierarchy" in m for m in _warnings(result))

    def test_check_disabled(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_nested", "Xform")
        stage.DefinePrim("/World/GRP_nested/GRP_deeper", "Xform")
        settings = _settings(enabled_checks={
            "empty_xform_scope": True,
            "empty_mesh": True,
            "empty_hierarchy": False,
        })
        result = check_empty_prims(stage, settings)
        assert not any("hierarchy leads to" in m for m in _warnings(result))

    def test_hierarchy_containing_only_scope_with_mesh_passes(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_outer", "Xform")
        stage.DefinePrim("/World/GRP_outer/GRP_inner", "Scope")
        stage.DefinePrim("/World/GRP_outer/GRP_inner/GEO_body", "Mesh")
        result = check_empty_prims(stage, _settings())
        assert not any("GRP_outer" in m and "hierarchy" in m for m in _warnings(result))


# ─────────────────────────────────────────────
# ignore_types
# ─────────────────────────────────────────────

class TestIgnoreTypes:

    def test_ignored_type_not_flagged_as_empty_xform(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/cam_main", "Camera")
        result = check_empty_prims(stage, _settings())
        assert not any("cam_main" in m for m in _warnings(result))

    def test_non_ignored_xform_still_flagged(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_empty", "Xform")
        stage.DefinePrim("/World/cam_main", "Camera")
        result = check_empty_prims(stage, _settings())
        assert any("GRP_empty" in m for m in _warnings(result))


# ─────────────────────────────────────────────
# Overall / guard rails
# ─────────────────────────────────────────────

class TestOverall:

    def test_disabled_returns_empty(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_empty", "Xform")
        result = check_empty_prims(stage, {"empty_prims": {"enabled": False}})
        assert result == []

    def test_no_stage_returns_error(self):
        result = check_empty_prims(None, _settings())
        assert result == [("Empty Prims", "error", "No stage loaded — cannot check empty prims")]

    def test_clean_stage_returns_pass(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_furniture", "Scope")
        mesh = stage.DefinePrim("/World/GRP_furniture/GEO_chair", "Mesh")
        pts_attr = mesh.CreateAttribute("points", Sdf.ValueTypeNames.Point3fArray)
        pts_attr.Set([(0, 0, 0), (1, 0, 0), (1, 1, 0)])
        result = check_empty_prims(stage, _settings())
        assert result == [("Empty Prims", "pass", "No empty prims found")]

    def test_mixed_issues_all_reported(self):
        stage = _stage()
        stage.DefinePrim("/World", "Xform")
        stage.SetDefaultPrim(stage.GetPrimAtPath("/World"))
        stage.DefinePrim("/World/GRP_empty", "Xform")           # empty_xform_scope
        stage.DefinePrim("/World/GEO_no_points", "Mesh")         # empty_mesh
        stage.DefinePrim("/World/GRP_nested", "Xform")           # empty_hierarchy
        stage.DefinePrim("/World/GRP_nested/GRP_child", "Xform")
        result = check_empty_prims(stage, _settings())
        warns = _warnings(result)
        assert any("GRP_empty" in m for m in warns)
        assert any("GEO_no_points" in m for m in warns)
        assert any("GRP_nested" in m and "hierarchy" in m for m in warns)
