"""Minimal FastAPI demo for vizly."""

from __future__ import annotations

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import vizly as vz
from vizly.integrations.fastapi import (
    assets_html,
    dashboard_response,
    html_response,
    json_response,
)
from vizly.integrations._embed import chart_html

app = FastAPI(title="vizly FastAPI demo")
vz.set_theme("corporate")


def _chart():
    df = pd.DataFrame({"region": ["East", "West", "South"], "sales": [40, 32, 28]})
    return vz.bar(df, x="region", y="sales", title="Sales")


def _line():
    df = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "n": [1, 3]})
    return vz.line(df, x="date", y="n", title="Trend")


@app.get("/")
def index():
    return html_response(_chart())


@app.get("/fragment")
def fragment():
    return html_response(_chart(), fragment=True)


@app.get("/dashboard")
def dashboard():
    return dashboard_response([_chart(), _line()], title="Dashboard")


@app.get("/dashboard/shell")
def dashboard_shell():
    """Shell HTML with assets once + two fragments."""
    head = assets_html()
    a = chart_html(_chart(), fragment=True, include_assets=False, height="300px")
    b = chart_html(_line(), fragment=True, include_assets=False, height="300px")
    page = (
        "<!doctype html><html lang='en-US'><head><meta charset='utf-8'/>"
        f"<title>Shell</title>{head}</head><body>{a}{b}</body></html>"
    )
    return HTMLResponse(page)


@app.get("/option")
def option():
    return json_response(_chart())
