"""Flask helper tests."""

from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("flask")

from examples.flask_app import app

import vizly as vz
from vizly.integrations.flask import (
    assets_html,
    chart_html,
    chart_response,
    dashboard_html,
)
from vizly.render import LOCAL_ASSET_MARKER


def _chart():
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    return vz.bar(df, x="x", y="y", title="Sales")


def test_flask_helpers():
    frag = chart_html(_chart(), fragment=True)
    assert "<!DOCTYPE" not in frag
    assert LOCAL_ASSET_MARKER in frag
    resp = chart_response(_chart(), fragment=False)
    assert resp.status_code == 200
    assert resp.mimetype.startswith("text/html")
    assert LOCAL_ASSET_MARKER in resp.get_data(as_text=True)


def test_flask_dashboard_assets_once():
    html = dashboard_html([_chart(), _chart()], title="D")
    assert html.count(LOCAL_ASSET_MARKER) == 1
    assert html.count("echarts.init") == 2
    # Shell pattern
    head = assets_html()
    a = chart_html(_chart(), fragment=True, include_assets=False)
    assert LOCAL_ASSET_MARKER in head
    assert LOCAL_ASSET_MARKER not in a


def test_flask_example_app():
    client = app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    assert LOCAL_ASSET_MARKER in r.get_data(as_text=True)
    assert b"<!doctype" in r.data.lower()  # page shell
    r2 = client.get("/full")
    assert r2.status_code == 200
    assert LOCAL_ASSET_MARKER in r2.get_data(as_text=True)
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    body = dash.get_data(as_text=True)
    assert body.count(LOCAL_ASSET_MARKER) == 1
    full = client.get("/dashboard/full")
    assert full.status_code == 200
    assert full.get_data(as_text=True).count(LOCAL_ASSET_MARKER) == 1
