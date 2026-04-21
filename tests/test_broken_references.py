import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxr import Usd, Sdf
from validators.broken_references import check_broken_references


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _settings(**overrides):
    brc = {
        "enabled": True,
        "enabled_checks": {
            "external_references": True,
            "internal_references": True,
            "asset_paths": True,
            "unresolvable_paths": True,
        },
        "additional_search_paths": [],
        "ignore_patterns": [],
    }
    brc.update(overrides)
    return {"broken_references": brc}


def _write(path, content):
    path.write_text(content, encoding="utf-8")
    return str(path)


def _open(path_str):
    return Usd.Stage.Open(path_str)


# ─────────────────────────────────────────────
# External references
# ─────────────────────────────────────────────

class TestExternalReferences:

    def test_valid_external_ref_passes(self, tmp_path):
        prop = _write(tmp_path / "chair.usda", '#usda 1.0\ndef Xform "Chair" {}\n')
        main = _write(tmp_path / "main.usda",
                      f'#usda 1.0\ndef Xform "World" (references = @./chair.usda@) {{}}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert result == [("Broken References", "pass", "All references and asset paths resolved")]

    def test_broken_external_ref_file_not_found_is_error(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" (references = @./missing.usd@) {}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert any(s == "error" and "reference file not found" in m and "missing.usd" in m
                   for _, s, m in result)

    def test_file_exists_but_ref_prim_missing_is_error(self, tmp_path):
        _write(tmp_path / "chair.usda", '#usda 1.0\ndef Xform "Chair" {}\n')
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" (references = @./chair.usda@</WrongPrim>) {}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert any(s == "error" and "/WrongPrim" in m and "chair.usda" in m
                   for _, s, m in result)

    def test_external_refs_skipped_when_disabled(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" (references = @./missing.usd@) {}\n')
        stage = _open(main)
        settings = _settings(enabled_checks={
            "external_references": False,
            "internal_references": True,
            "asset_paths": True,
            "unresolvable_paths": True,
        })
        result = check_broken_references(stage, settings)
        assert not any("reference file not found" in m for _, s, m in result)

    def test_valid_ref_with_prim_path_passes(self, tmp_path):
        _write(tmp_path / "chair.usda", '#usda 1.0\ndef Xform "Chair" {}\n')
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" (references = @./chair.usda@</Chair>) {}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert result == [("Broken References", "pass", "All references and asset paths resolved")]


# ─────────────────────────────────────────────
# Internal references
# ─────────────────────────────────────────────

class TestInternalReferences:

    def test_valid_internal_ref_passes(self):
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/Target", "Xform")
        stage.DefinePrim("/World", "Xform").GetReferences().AddInternalReference("/Target")
        result = check_broken_references(stage, _settings())
        assert result == [("Broken References", "pass", "All references and asset paths resolved")]

    def test_broken_internal_ref_prim_not_found_is_error(self):
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/World", "Xform").GetReferences().AddInternalReference("/NonExistent")
        result = check_broken_references(stage, _settings())
        assert any(s == "error" and "internal reference prim" in m and "/NonExistent" in m
                   for _, s, m in result)

    def test_internal_refs_skipped_when_disabled(self):
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/World", "Xform").GetReferences().AddInternalReference("/NonExistent")
        settings = _settings(enabled_checks={
            "external_references": True,
            "internal_references": False,
            "asset_paths": True,
            "unresolvable_paths": True,
        })
        result = check_broken_references(stage, settings)
        assert not any("internal reference" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Asset path attributes
# ─────────────────────────────────────────────

class TestAssetPaths:

    def test_valid_asset_path_passes(self, tmp_path):
        texture = tmp_path / "diffuse.png"
        texture.write_bytes(b"")  # dummy file — validator only checks existence
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" {\n  custom asset myTex = @./diffuse.png@\n}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert result == [("Broken References", "pass", "All references and asset paths resolved")]

    def test_broken_asset_path_is_warning(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" {\n  custom asset myTex = @./missing.png@\n}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert any(s == "warning" and "asset path not found" in m and "missing.png" in m
                   for _, s, m in result)

    def test_asset_paths_skipped_when_disabled(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" {\n  custom asset myTex = @./missing.png@\n}\n')
        stage = _open(main)
        settings = _settings(enabled_checks={
            "external_references": True,
            "internal_references": True,
            "asset_paths": False,
            "unresolvable_paths": True,
        })
        result = check_broken_references(stage, settings)
        assert not any("asset path not found" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Unresolvable / environment-variable paths
# ─────────────────────────────────────────────

class TestUnresolvablePaths:

    def test_unresolvable_env_var_ref_is_warning(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" (references = @${UNSET_VAR_XYZ}/chair.usd@) {}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert any(s == "warning" and "could not be resolved" in m
                   for _, s, m in result)

    def test_unresolvable_env_var_asset_is_warning(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" {\n'
                      '  custom asset myTex = @${UNSET_VAR_XYZ}/diffuse.png@\n}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        assert any(s == "warning" and "could not be resolved" in m
                   for _, s, m in result)

    def test_unresolvable_paths_skipped_when_disabled(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" (references = @${UNSET_VAR_XYZ}/chair.usd@) {}\n')
        stage = _open(main)
        settings = _settings(enabled_checks={
            "external_references": True,
            "internal_references": True,
            "asset_paths": True,
            "unresolvable_paths": False,
        })
        result = check_broken_references(stage, settings)
        assert not any("could not be resolved" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Ignore patterns
# ─────────────────────────────────────────────

class TestIgnorePatterns:

    def test_ignore_pattern_suppresses_result(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" {\n  custom asset myHdri = @./sky.hdri@\n}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings(ignore_patterns=["*.hdri"]))
        assert not any("sky.hdri" in m for _, s, m in result)

    def test_non_matching_pattern_does_not_suppress(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\ndef Xform "World" {\n  custom asset myTex = @./missing.png@\n}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings(ignore_patterns=["*.hdri"]))
        assert any("missing.png" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Overall / guard rails
# ─────────────────────────────────────────────

class TestOverall:

    def test_disabled_returns_empty(self):
        stage = Usd.Stage.CreateInMemory()
        result = check_broken_references(stage, {"broken_references": {"enabled": False}})
        assert result == []

    def test_no_stage_returns_error(self):
        result = check_broken_references(None, _settings())
        assert result == [("Broken References", "error", "No stage loaded — cannot check references")]

    def test_clean_stage_no_refs_returns_pass(self):
        stage = Usd.Stage.CreateInMemory()
        stage.DefinePrim("/World", "Xform")
        result = check_broken_references(stage, _settings())
        assert result == [("Broken References", "pass", "All references and asset paths resolved")]

    def test_multiple_broken_refs_all_reported(self, tmp_path):
        main = _write(tmp_path / "main.usda",
                      '#usda 1.0\n'
                      'def Xform "A" (references = @./missing_a.usd@) {}\n'
                      'def Xform "B" (references = @./missing_b.usd@) {}\n')
        stage = _open(main)
        result = check_broken_references(stage, _settings())
        errors = [m for _, s, m in result if s == "error"]
        assert any("missing_a.usd" in m for m in errors)
        assert any("missing_b.usd" in m for m in errors)
