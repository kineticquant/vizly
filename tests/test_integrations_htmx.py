"""HTMX helper tests."""

from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("flask")

import vizly as vz
from vizly.integrations.htmx import (
    htmx_chart_fragment,
    htmx_or_full,
    is_htmx_request,
)
from vizly.render import LOCAL_ASSET_MARKER


def _chart(y: str = "revenue"):
    df = pd.DataFrame(
        {"date": ["2026-01-01", "2026-01-02"], "revenue": [1, 2], "cost": [3, 4]}
    )
    return vz.line(df, x="date", y=y, title=y)


def test_htmx_fragment_omits_assets_by_default():
    html = htmx_chart_fragment(_chart())
    assert html.strip().startswith("<div")
    assert 'data-vizly-fragment="1"' in html
    assert "<!DOCTYPE" not in html
    assert LOCAL_ASSET_MARKER not in html
    assert "bootcdn" not in html.lower()
    assert "echarts.init" in html


def test_htmx_fragment_can_include_assets():
    html = htmx_chart_fragment(_chart(), include_assets=True)
    assert LOCAL_ASSET_MARKER in html


def test_htmx_request_detection_and_or_full():
    assert is_htmx_request({"HX-Request": "true"})
    assert not is_htmx_request({"Accept": "text/html"})
    frag = htmx_or_full(_chart("cost"), {"HX-Request": "true"})
    assert "<!DOCTYPE" not in frag
    assert LOCAL_ASSET_MARKER not in frag
    assert "cost" in frag
    full = htmx_or_full(_chart("cost"), {})
    assert full.lstrip().startswith("<!DOCTYPE")
    assert LOCAL_ASSET_MARKER in full


def test_htmx_demo_app_swap():
    from examples.htmx_demo.app import app

    client = app.test_client()
    r = client.get("/")
    assert r.status_code == 200
    page = r.get_data(as_text=True)
    # Assets once in page head; initial fragment does not re-embed.
    assert page.count(LOCAL_ASSET_MARKER) == 1
    r2 = client.get("/chart?metric=cost", headers={"HX-Request": "true"})
    assert r2.status_code == 200
    body = r2.get_data(as_text=True)
    assert "<!DOCTYPE" not in body
    assert 'data-vizly-fragment="1"' in body
    assert LOCAL_ASSET_MARKER not in body
    assert "cost" in body.lower() or '"cost"' in body
