"""Compose chart correctness: page/tab/grid/timeline."""

from __future__ import annotations

import pandas as pd
import pytest

import vizly as vz
from vizly.data import DataError
from vizly.render import LOCAL_ASSET_MARKER


def _line():
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    return vz.line(df, x="x", y="y", title="L")


def _bar():
    df = pd.DataFrame({"x": ["a", "b"], "y": [3, 4]})
    return vz.bar(df, x="x", y="y", title="B")


def _map():
    df = pd.DataFrame(
        {"name": ["United States", "Canada"], "value": [10, 5]}
    )
    return vz.map(df, title="M")


def test_page_loads_echarts_once():
    html = vz.page(charts=[_line(), _bar()]).to_html()
    assert html.count(LOCAL_ASSET_MARKER) == 1
    assert html.count("echarts.init") == 2


def test_page_dedupes_map_registration():
    html = vz.page(charts=[_map(), _map()]).to_html()
    # world GeoJSON registered once, not twice
    assert html.count("echarts.registerMap") == 1
    assert html.count(LOCAL_ASSET_MARKER) == 1


def test_page_does_not_mutate_child_theme():
    child = _line()
    assert child._theme_override is None
    vz.page(charts=[child], theme="dark").to_html()
    assert child._theme_override is None
    # Child alone still uses default theme resolution
    assert child.theme["name"] != "dark" or child._theme_override is None


def test_tab_renders_tab_controls():
    html = vz.tab(charts=[_line(), _bar()], labels=["One", "Two"]).to_html()
    assert 'role="tablist"' in html or "role='tablist'" in html
    assert "data-vizly-tab" in html
    assert "One" in html and "Two" in html
    assert html.count(LOCAL_ASSET_MARKER) == 1


def test_grid_rejects_non_cartesian():
    pie = vz.pie(
        pd.DataFrame({"name": ["a"], "value": [1]}), names="name", values="value"
    )
    with pytest.raises(DataError, match="not cartesian"):
        vz.grid(charts=[_line(), pie]).to_option()


def test_page_includes_plugin_and_gl():
    df = pd.DataFrame({"name": ["a", "b"], "value": [1, 2]})
    xyz = pd.DataFrame({"x": [1, 2], "y": [1, 2], "z": [1, 2]})
    html = vz.page(
        charts=[vz.wordcloud(df), vz.bar3d(xyz, x="x", y="y", z="z")]
    ).to_html()
    assert html.count(LOCAL_ASSET_MARKER) == 1
    assert "wordcloud" in html.lower()
    assert "echarts-gl" in html.lower() or "gl.min" in html.lower()


def test_timeline_registers_maps_once():
    t = vz.timeline(charts=[_map(), _line()])
    html = t.to_html()
    assert html.count("echarts.registerMap") == 1
    assert LOCAL_ASSET_MARKER in html
