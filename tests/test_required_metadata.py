import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pxr import Usd, UsdGeom
from validators.required_metadata import check_required_metadata


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _settings(**overrides):
    rmc = {
        "enabled": True,
        "enabled_checks": {
            "up_axis": True,
            "meters_per_unit": True,
            "custom_metadata": True,
        },
        "valid_up_axis": ["Y", "Z"],
        "valid_meters_per_unit": [0.001, 0.01, 0.1, 1.0],
        "required_custom_fields": [],
    }
    rmc.update(overrides)
    return {"required_metadata": rmc}


def _stage_with(up_axis=None, meters_per_unit=None, custom_layer_data=None):
    stage = Usd.Stage.CreateInMemory()
    if up_axis is not None:
        stage.SetMetadata("upAxis", up_axis)
    if meters_per_unit is not None:
        stage.SetMetadata("metersPerUnit", meters_per_unit)
    if custom_layer_data is not None:
        stage.GetRootLayer().customLayerData = custom_layer_data
    return stage


# ─────────────────────────────────────────────
# upAxis
# ─────────────────────────────────────────────

class TestUpAxis:

    def test_missing_up_axis_is_error(self):
        stage = _stage_with()
        result = check_required_metadata(stage, _settings())
        assert any(s == "error" and "missing 'upAxis'" in m for _, s, m in result)

    def test_invalid_up_axis_is_error(self):
        stage = _stage_with(up_axis="X")
        result = check_required_metadata(stage, _settings())
        assert any(s == "error" and "'upAxis' is 'X'" in m for _, s, m in result)

    def test_invalid_up_axis_message_lists_valid_values(self):
        stage = _stage_with(up_axis="X")
        result = check_required_metadata(stage, _settings())
        assert any("Y, Z" in m for _, s, m in result)

    def test_valid_up_axis_y_passes(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        result = check_required_metadata(stage, _settings(required_custom_fields=[]))
        assert not any(s in ("error", "warning") and "upAxis" in m for _, s, m in result)

    def test_valid_up_axis_z_passes(self):
        stage = _stage_with(up_axis="Z", meters_per_unit=1.0)
        result = check_required_metadata(stage, _settings(required_custom_fields=[]))
        assert not any(s in ("error", "warning") and "upAxis" in m for _, s, m in result)

    def test_up_axis_check_skipped_when_disabled(self):
        stage = _stage_with()
        settings = _settings(enabled_checks={
            "up_axis": False, "meters_per_unit": False, "custom_metadata": False
        })
        result = check_required_metadata(stage, settings)
        assert not any("upAxis" in m for _, s, m in result)


# ─────────────────────────────────────────────
# metersPerUnit
# ─────────────────────────────────────────────

class TestMetersPerUnit:

    def test_missing_meters_per_unit_is_warning(self):
        stage = _stage_with(up_axis="Y")
        result = check_required_metadata(stage, _settings())
        assert any(s == "warning" and "missing 'metersPerUnit'" in m for _, s, m in result)

    def test_non_standard_meters_per_unit_is_warning(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=500.0)
        result = check_required_metadata(stage, _settings())
        assert any(s == "warning" and "500" in m for _, s, m in result)

    def test_non_standard_message_lists_valid_values(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=500.0)
        result = check_required_metadata(stage, _settings())
        assert any("0.001, 0.01, 0.1, 1" in m for _, s, m in result)

    def test_standard_meters_per_unit_1_passes(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        result = check_required_metadata(stage, _settings(required_custom_fields=[]))
        assert not any(s in ("error", "warning") and "metersPerUnit" in m for _, s, m in result)

    def test_standard_meters_per_unit_001_passes(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=0.001)
        result = check_required_metadata(stage, _settings(required_custom_fields=[]))
        assert not any(s in ("error", "warning") and "metersPerUnit" in m for _, s, m in result)

    def test_meters_per_unit_check_skipped_when_disabled(self):
        stage = _stage_with(up_axis="Y")
        settings = _settings(enabled_checks={
            "up_axis": True, "meters_per_unit": False, "custom_metadata": False
        })
        result = check_required_metadata(stage, settings)
        assert not any("metersPerUnit" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Custom metadata fields
# ─────────────────────────────────────────────

class TestCustomMetadata:

    def test_empty_required_fields_config_skips_check(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        result = check_required_metadata(stage, _settings(required_custom_fields=[]))
        assert not any("custom metadata" in m for _, s, m in result)

    def test_missing_custom_field_is_warning(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        result = check_required_metadata(stage, _settings(required_custom_fields=["asset_version"]))
        assert any(s == "warning" and "'asset_version'" in m for _, s, m in result)

    def test_missing_multiple_custom_fields_each_reported(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        result = check_required_metadata(
            stage, _settings(required_custom_fields=["asset_version", "author"])
        )
        assert any("'asset_version'" in m for _, s, m in result)
        assert any("'author'" in m for _, s, m in result)

    def test_present_custom_fields_pass(self):
        stage = _stage_with(
            up_axis="Y",
            meters_per_unit=1.0,
            custom_layer_data={"asset_version": "1.0"},
        )
        result = check_required_metadata(stage, _settings(required_custom_fields=["asset_version"]))
        assert not any("'asset_version'" in m for _, s, m in result)

    def test_partial_custom_fields_reports_missing_only(self):
        stage = _stage_with(
            up_axis="Y",
            meters_per_unit=1.0,
            custom_layer_data={"asset_version": "1.0"},
        )
        result = check_required_metadata(
            stage, _settings(required_custom_fields=["asset_version", "author"])
        )
        assert not any("'asset_version'" in m for _, s, m in result)
        assert any("'author'" in m for _, s, m in result)

    def test_custom_check_skipped_when_disabled(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        settings = _settings(
            required_custom_fields=["asset_version"],
            enabled_checks={"up_axis": True, "meters_per_unit": True, "custom_metadata": False},
        )
        result = check_required_metadata(stage, settings)
        assert not any("custom metadata" in m for _, s, m in result)


# ─────────────────────────────────────────────
# Overall pass / guard rails
# ─────────────────────────────────────────────

class TestOverall:

    def test_all_pass_returns_single_pass_result(self):
        stage = _stage_with(up_axis="Y", meters_per_unit=1.0)
        result = check_required_metadata(stage, _settings())
        assert result == [("Required Metadata", "pass", "All required metadata present")]

    def test_disabled_check_returns_empty(self):
        stage = _stage_with()
        result = check_required_metadata(stage, {"required_metadata": {"enabled": False}})
        assert result == []

    def test_no_stage_returns_error(self):
        result = check_required_metadata(None, _settings())
        assert result == [("Required Metadata", "error", "No stage loaded — cannot check metadata")]
