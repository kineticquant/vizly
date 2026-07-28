"""Tests for trusted asset rendering and BaseChart HTML smoke."""

from pathlib import Path

import pytest

import vizly as vz
from vizly.base import OptionChart
from vizly.config import reset_config
from vizly.render import (
    LOCAL_ASSET_MARKER,
    assert_html_trust_safe,
    load_map_geojson,
    map_path,
    render_html,
)
from vizly.theme.registry import reset_registry
from vizly.theme.schema import ThemeValidationError


@pytest.fixture(autouse=True)
def _clean_theme_state():
    reset_registry()
    reset_config()
    yield
    reset_registry()
    reset_config()


def _sample_option():
    return {
        "xAxis": {"type": "category", "data": ["A", "B", "C"]},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": [1, 2, 3]}],
    }


def test_bundled_maps_exist():
    world = map_path("world")
    usa = map_path("usa")
    assert world.is_file()
    assert usa.is_file()
    assert load_map_geojson("world")["type"] in ("FeatureCollection", "GeometryCollection") or "features" in load_map_geojson("world")
    usa_geo = load_map_geojson("usa")
    assert isinstance(usa_geo, dict)


def test_local_html_embeds_marker_and_no_banned_hosts():
    chart = OptionChart(_sample_option(), title="Smoke", theme="default")
    html = chart.to_html()
    assert LOCAL_ASSET_MARKER in html
    assert "echarts.init" in html or "echarts" in html
    assert 'data-vizly-asset-mode="local"' in html
    assert "assets.pyecharts.org" not in html
    assert "bootcdn" not in html.lower()
    # No remote script tags in local mode (trust gate scans src URLs only).
    assert "<script src=" not in html
    assert_html_trust_safe(html, asset_mode="local")


def test_to_option_json_serializable_and_themed():
    chart = OptionChart(_sample_option(), theme="corporate")
    option = chart.to_option()
    assert option["series"][0]["data"] == [1, 2, 3]
    assert option["xAxis"]["data"] == ["A", "B", "C"]  # axis data preserved
    assert option["color"][0] == "#0B1F33"
    assert option["backgroundColor"] == "#FFFFFF"
    text = chart.to_json()
    assert '"A"' in text
    # Round-trip JSON
    import json

    json.loads(text)


def test_axis_style_merged_not_replaced():
    chart = OptionChart(_sample_option(), theme="dark")
    option = chart.to_option()
    assert isinstance(option["xAxis"], dict)
    assert option["xAxis"]["type"] == "category"
    assert option["xAxis"]["data"] == ["A", "B", "C"]
    assert "axisLabel" in option["xAxis"]


def test_chart_theme_override_does_not_mutate_global():
    vz.set_theme("default")
    chart = OptionChart(_sample_option(), theme="dark")
    assert chart.theme["name"] == "dark"
    assert vz.get_theme()["name"] == "default"


def test_update_and_merge_option():
    chart = OptionChart(_sample_option())
    chart.update(title="Updated")
    chart.merge_option({"legend": {"show": False}})
    option = chart.to_option()
    assert option["title"]["text"] == "Updated"
    assert option["legend"]["show"] is False


def test_render_writes_file(tmp_path: Path):
    chart = OptionChart(_sample_option())
    out = tmp_path / "chart.html"
    result = chart.render(out)
    assert result == str(out)
    assert out.exists()
    assert LOCAL_ASSET_MARKER in out.read_text(encoding="utf-8")


def test_repr_html():
    chart = OptionChart(_sample_option())
    html = chart._repr_html_()
    assert "vizly-chart" in html


def test_cdn_mode_allowlisted_only():
    vz.set_theme(
        {
            "assets": {
                "mode": "cdn",
                "cdn": "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js",
            }
        }
    )
    html = render_html(_sample_option(), theme=vz.get_theme())
    assert 'src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"' in html
    assert_html_trust_safe(html, asset_mode="cdn")


def test_cdn_mode_rejects_bootcdn_in_theme():
    with pytest.raises(ThemeValidationError, match="allowlisted"):
        vz.set_theme(
            {
                "assets": {
                    "mode": "cdn",
                    "cdn": "https://cdn.bootcdn.net/ajax/libs/echarts/5.5.1/echarts.min.js",
                }
            }
        )


def test_banned_host_detector():
    with pytest.raises(Exception, match="banned"):
        assert_html_trust_safe(
            '<script src="https://cdn.bootcdn.net/echarts.js"></script>',
            asset_mode="cdn",
        )


def test_trust_safe_ignores_banned_substring_in_option_data():
    """Category labels must not trip the script-src trust scanner."""
    chart = OptionChart(
        {
            "xAxis": {"type": "category", "data": ["bootcdn test", "npmmirror"]},
            "yAxis": {"type": "value"},
            "series": [{"type": "bar", "data": [1, 2]}],
        }
    )
    html = chart.to_html()
    assert LOCAL_ASSET_MARKER in html
    assert_html_trust_safe(html, asset_mode="local")


def test_echarts_init_uses_en_locale():
    chart = OptionChart(_sample_option(), theme="default")
    html = chart.to_html()
    assert 'locale: "EN"' in html


def test_sanitize_css_size_rejects_injection():
    from vizly.render import RenderError, sanitize_css_size

    assert sanitize_css_size("420px", field="height") == "420px"
    assert sanitize_css_size("100%", field="width") == "100%"
    with pytest.raises(RenderError, match="Invalid"):
        sanitize_css_size("100%;} body{display:none", field="width")
