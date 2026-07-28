"""FastAPI helper tests."""

from __future__ import annotations

import pandas as pd
import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

import vizly as vz
from examples.fastapi_app import app
from vizly.integrations.fastapi import html_response, json_response
from vizly.render import LOCAL_ASSET_MARKER


def _chart():
    df = pd.DataFrame({"x": ["a", "b"], "y": [1, 2]})
    return vz.bar(df, x="x", y="y", title="Sales")


def test_html_and_json_helpers():
    html = html_response(_chart())
    assert html.status_code == 200
    assert LOCAL_ASSET_MARKER in html.body.decode("utf-8")
    assert b"<!DOCTYPE html>" in html.body

    frag = html_response(_chart(), fragment=True)
    assert b"<!DOCTYPE" not in frag.body
    assert b'data-vizly-fragment="1"' in frag.body

    js = json_response(_chart())
    assert js.status_code == 200
    assert js.body


def test_example_app_routes():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert LOCAL_ASSET_MARKER in r.text
    r2 = client.get("/fragment")
    assert r2.status_code == 200
    assert "<!DOCTYPE" not in r2.text
    r3 = client.get("/option")
    assert r3.status_code == 200
    assert r3.json()["series"][0]["type"] == "bar"
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    assert dash.text.count(LOCAL_ASSET_MARKER) == 1
    shell = client.get("/dashboard/shell")
    assert shell.status_code == 200
    assert shell.text.count(LOCAL_ASSET_MARKER) == 1
