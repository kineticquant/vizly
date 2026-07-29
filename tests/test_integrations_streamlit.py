"""Streamlit helper tests."""

from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("streamlit")

import vizly as vz
from vizly.integrations.streamlit import st_dashboard, st_vizly
from vizly.render import LOCAL_ASSET_MARKER


def test_st_vizly_calls_components_html(monkeypatch):
    captured = {}

    def fake_html(html, height=None, scrolling=False, **kwargs):
        captured["html"] = html
        captured["height"] = height
        return "ok"

    import streamlit.components.v1 as components

    monkeypatch.setattr(components, "html", fake_html)
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    chart = vz.bar(df, x="x", y="y")
    # events=False uses components.html (asset / document contract).
    assert st_vizly(chart, height=400, events=False) == "ok"
    assert LOCAL_ASSET_MARKER in captured["html"]
    assert "<!DOCTYPE html>" in captured["html"]
    assert captured["height"] == 400
    assert 'locale: "EN"' in captured["html"]
    assert "vizly:event" in captured["html"]


def test_st_dashboard_loads_echarts_once(monkeypatch):
    captured = {}

    def fake_html(html, height=None, scrolling=False, **kwargs):
        captured["html"] = html
        captured["height"] = height
        return "ok"

    import streamlit.components.v1 as components

    monkeypatch.setattr(components, "html", fake_html)
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    a = vz.bar(df, x="x", y="y", title="A")
    b = vz.line(df, x="x", y="y", title="B")
    assert st_dashboard([a, b], height=800, events=False) == "ok"
    assert captured["html"].count(LOCAL_ASSET_MARKER) == 1
    assert captured["html"].count("echarts.init") == 2
    assert st_vizly([a, b], height=800, events=False) == "ok"
    assert captured["html"].count(LOCAL_ASSET_MARKER) == 1


def test_st_dashboard_threads_message_origin(monkeypatch):
    captured = {}

    def fake_declare(name, path):  # noqa: ARG001
        def comp(*, html, height, key=None, default=None):  # noqa: ARG001
            captured["html"] = html
            return default

        return comp

    import streamlit.components.v1 as components

    monkeypatch.setattr(components, "declare_component", fake_declare)
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    a = vz.bar(df, x="x", y="y", title="A")
    b = vz.line(df, x="x", y="y", title="B")
    st_dashboard([a, b], height=800, events=True)
    html = captured["html"]
    assert html.count('postMessage(payload, "*")') >= 2
    assert "window.location.origin" not in html
