"""Tests for theme presets, registry, config, and apply precedence."""

import json
from pathlib import Path

import pytest

import vizly as vz
from vizly.config import reset_config, resolve_theme
from vizly.theme.apply import theme_to_echarts_option
from vizly.theme.presets import PRESETS
from vizly.theme.registry import reset_registry
from vizly.theme.schema import ThemeValidationError, validate_theme


@pytest.fixture(autouse=True)
def _clean_theme_state():
    reset_registry()
    reset_config()
    yield
    reset_registry()
    reset_config()


def test_builtin_presets_present_and_valid():
    expected = {
        "default",
        "light",
        "dark",
        "corporate",
        "minimal",
        "contrast",
        "ops_grafana",
        "ops_cloudwatch",
        "ops_kibana",
    }
    assert set(PRESETS) == expected
    for name, theme in PRESETS.items():
        validated = validate_theme(theme, partial=False)
        assert validated["name"] == name
        assert validated["locale"] == "en-US"
        assert validated["assets"]["mode"] == "local"
        # US-trust: no Inter / indigo-violet marketing defaults
        assert "Inter" not in validated["font_family"]
        assert "#6366F1" not in validated["palette"]


def test_set_theme_by_name():
    theme = vz.set_theme("corporate")
    assert theme["name"] == "corporate"
    assert vz.get_theme()["name"] == "corporate"
    assert theme["palette"][0] == "#0B1F33"


def test_set_theme_partial_dict_merges_over_current():
    vz.set_theme("default")
    updated = vz.set_theme({"background": "#FAFAFA", "palette": ["#000000"]})
    assert updated["background"] == "#FAFAFA"
    assert updated["palette"] == ["#000000"]
    # Unspecified keys preserved from prior theme
    assert updated["locale"] == "en-US"
    assert updated["name"] == "default"


def test_chart_theme_override_does_not_mutate_global():
    vz.set_theme("default")
    before = vz.get_theme()
    resolved = resolve_theme({"background": "#111111"})
    assert resolved["background"] == "#111111"
    assert vz.get_theme() == before
    assert vz.get_theme()["background"] == "#FFFFFF"


def test_resolve_theme_named_override():
    vz.set_theme("default")
    dark = resolve_theme("dark")
    assert dark["name"] == "dark"
    assert vz.get_theme()["name"] == "default"


def test_register_and_list_themes():
    vz.register_theme("brand", {"background": "#EEF2FF", "palette": ["#0B1F33"]})
    names = vz.list_themes()
    assert "default" in names
    assert "brand" in names
    brand = resolve_theme("brand")
    assert brand["background"] == "#EEF2FF"
    assert brand["locale"] == "en-US"  # filled from default base


def test_cannot_overwrite_builtin_theme():
    with pytest.raises(ThemeValidationError, match="builtin"):
        vz.register_theme("dark", {"background": "#000000"})


def test_export_load_round_trip(tmp_path: Path):
    vz.register_theme(
        "roundtrip",
        {"background": "#F5F5F5", "palette": ["#112233", "#445566"]},
    )
    out = tmp_path / "roundtrip.json"
    text = vz.export_theme("roundtrip", out)
    assert out.exists()
    loaded = json.loads(text)
    assert loaded["name"] == "roundtrip"
    assert loaded["background"] == "#F5F5F5"

    reset_registry()
    again = vz.load_theme(out, register=True, name="roundtrip")
    assert again["background"] == "#F5F5F5"
    assert "roundtrip" in vz.list_themes()


def test_load_theme_activate():
    example = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "themes"
        / "atlantic.json"
    )
    theme = vz.load_theme(example, activate=True)
    assert theme["name"] == "atlantic"
    assert vz.get_theme()["name"] == "atlantic"
    assert vz.get_theme()["palette"][0] == "#0B1F33"


def test_merge_precedence_preset_registered_set_chart():
    """preset < registered base < set_theme dict < chart theme override."""
    # Start from corporate preset via registration base merge path
    vz.register_theme("finance", {"name": "finance", "palette": ["#0B1F33"]})
    vz.set_theme("finance")
    # Session override
    vz.set_theme({"background": "#F0F4F8"})
    assert vz.get_theme()["background"] == "#F0F4F8"
    assert vz.get_theme()["palette"] == ["#0B1F33"]
    # Chart override wins for its resolution only
    chart_theme = resolve_theme({"background": "#ABCDEF"})
    assert chart_theme["background"] == "#ABCDEF"
    assert chart_theme["palette"] == ["#0B1F33"]
    assert vz.get_theme()["background"] == "#F0F4F8"


def test_theme_to_echarts_option_fragments():
    vz.set_theme("corporate")
    option = theme_to_echarts_option(vz.get_theme())
    assert option["color"][0] == "#0B1F33"
    assert option["backgroundColor"] == "#FFFFFF"
    assert option["textStyle"]["fontFamily"].startswith('"IBM Plex Sans"')
    assert "animationDuration" in option


def test_unknown_theme_key_rejected():
    with pytest.raises(ThemeValidationError, match="Unknown theme key"):
        validate_theme({"not_a_real_key": 1}, partial=True)


def test_cdn_allowlist_rejects_bootcdn():
    with pytest.raises(ThemeValidationError, match="not allowlisted"):
        validate_theme(
            {
                "assets": {
                    "mode": "cdn",
                    "cdn": "https://cdn.bootcdn.net/ajax/libs/echarts/5.0.0/echarts.min.js",
                }
            },
            partial=True,
        )


def test_cdn_allowlist_accepts_jsdelivr():
    validated = validate_theme(
        {
            "assets": {
                "mode": "cdn",
                "cdn": "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js",
            }
        },
        partial=True,
    )
    assert "jsdelivr.net" in validated["assets"]["cdn"]


def test_load_theme_activate_replaces_previous_theme():
    """activate=True must replace, not merge onto, the prior session theme."""
    vz.set_theme("dark")
    example = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "themes"
        / "atlantic.json"
    )
    vz.load_theme(example, activate=True)
    theme = vz.get_theme()
    assert theme["name"] == "atlantic"
    assert theme["background"] == "#F8FAFC"
    # Must not retain dark tooltip chrome
    assert theme["tooltip"]["bg"].startswith("rgba(255")
    assert theme["text_color"] == "#0F172A"


def test_apply_theme_preserves_list_axes():
    from vizly.theme.apply import apply_theme_to_option

    vz.set_theme("corporate")
    structural = {
        "title": {"text": "Revenue"},
        "xAxis": [{"type": "category", "data": ["Mon", "Tue"]}],
        "yAxis": [{"type": "value"}],
        "series": [{"type": "bar", "data": [1, 2]}],
    }
    merged = apply_theme_to_option(
        structural,
        vz.get_theme(),
        {"backgroundColor": "#ABCDEF"},
    )
    assert isinstance(merged["xAxis"], list)
    assert merged["xAxis"][0]["data"] == ["Mon", "Tue"]
    assert merged["xAxis"][0]["type"] == "category"
    assert "axisLabel" in merged["xAxis"][0]
    assert isinstance(merged["yAxis"], list)
    assert merged["yAxis"][0]["type"] == "value"
    assert merged["backgroundColor"] == "#ABCDEF"
    assert merged["title"]["text"] == "Revenue"
    assert merged["color"][0] == "#0B1F33"


def test_series_defaults_for_line():
    from vizly.theme.apply import series_defaults_for

    vz.set_theme("minimal")
    defaults = series_defaults_for(vz.get_theme(), "line")
    assert defaults["smooth"] is False
    assert defaults["show_symbol"] is False


def test_preset_fonts_quote_family_names():
    for name in ("default", "corporate", "dark"):
        font = resolve_theme(name)["font_family"]
        assert '"IBM Plex Sans"' in font
        assert '"Segoe UI"' in font

