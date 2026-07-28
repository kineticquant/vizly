"""Shared embed contract tests (no framework deps)."""

from __future__ import annotations

import pandas as pd

import vizly as vz
from vizly.integrations._embed import assets_html, chart_html, chart_json, chart_option
from vizly.render import LOCAL_ASSET_MARKER


def _chart():
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    return vz.bar(df, x="x", y="y", title="T")


def test_full_document_has_doctype_and_local_assets():
    html = chart_html(_chart(), fragment=False)
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert LOCAL_ASSET_MARKER in html
    assert "bootcdn" not in html.lower()
    assert '"data": [1, 2]' in html or "[1, 2]" in html


def test_fragment_lacks_doctype_has_single_root():
    html = chart_html(_chart(), fragment=True)
    assert "<!DOCTYPE" not in html
    assert 'data-vizly-fragment="1"' in html
    assert html.strip().startswith("<div")
    assert LOCAL_ASSET_MARKER in html


def test_fragment_can_omit_assets():
    html = chart_html(_chart(), fragment=True, include_assets=False)
    assert LOCAL_ASSET_MARKER not in html
    assert "echarts.init" in html


def test_assets_html_auto_detects_gl_from_charts():
    df = pd.DataFrame({"x": [1, 2], "y": [3, 4], "z": [5, 6]})
    chart = vz.bar3d(df, x="x", y="y", z="z")
    scripts = assets_html(charts=[chart])
    assert LOCAL_ASSET_MARKER in scripts
    assert "echarts-gl" in scripts


def test_assets_html_loads_once():
    scripts = assets_html()
    assert LOCAL_ASSET_MARKER in scripts
    assert scripts.count(LOCAL_ASSET_MARKER) == 1


def test_dashboard_html_assets_once():
    from vizly.integrations._embed import dashboard_html

    html = dashboard_html([_chart(), _chart()])
    assert html.count(LOCAL_ASSET_MARKER) == 1
    assert html.count("echarts.init") == 2


def test_chart_html_does_not_mutate_chart():
    chart = _chart()
    before_w, before_h = chart.width, chart.height
    chart_html(chart, fragment=True, width="80%", height="500px")
    assert chart.width == before_w
    assert chart.height == before_h


def test_json_and_option():
    opt = chart_option(_chart())
    assert opt["series"][0]["type"] == "bar"
    text = chart_json(_chart())
    assert '"bar"' in text
