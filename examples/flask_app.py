"""Minimal Flask demo for vizly (single chart + multi-chart dashboard)."""

from __future__ import annotations

import pandas as pd
from flask import Flask, render_template_string

import vizly as vz
from vizly.integrations.flask import (
    assets_html,
    chart_html,
    chart_response,
    dashboard_response,
)

app = Flask(__name__)
vz.set_theme("corporate")

# Single chart: fragment may inline assets (convenient default).
SINGLE = """
<!doctype html>
<html lang="en-US">
<head><meta charset="utf-8"/><title>vizly Flask</title></head>
<body>
  <h1>vizly + Flask</h1>
  <p><a href="/dashboard">Multi-chart dashboard</a></p>
  {{ chart_markup|safe }}
</body>
</html>
"""

# Dashboard: load ECharts once in <head>, fragments omit assets.
DASHBOARD = """
<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8"/>
  <title>vizly Flask dashboard</title>
  {{ assets|safe }}
</head>
<body>
  <h1>Dashboard (assets once)</h1>
  {{ chart_a|safe }}
  {{ chart_b|safe }}
</body>
</html>
"""


def _bar():
    df = pd.DataFrame({"region": ["East", "West", "South"], "sales": [40, 32, 28]})
    return vz.bar(df, x="region", y="sales", title="Sales")


def _line():
    df = pd.DataFrame({"date": ["2026-01-01", "2026-01-02", "2026-01-03"], "n": [3, 5, 4]})
    return vz.line(df, x="date", y="n", title="Events")


@app.get("/")
def index():
    markup = chart_html(_bar(), fragment=True)
    return render_template_string(SINGLE, chart_markup=markup)


@app.get("/dashboard")
def dashboard():
    # Pattern A: shell + assets_html + include_assets=False per chart
    return render_template_string(
        DASHBOARD,
        assets=assets_html(),
        chart_a=chart_html(_bar(), fragment=True, include_assets=False, height="320px"),
        chart_b=chart_html(_line(), fragment=True, include_assets=False, height="320px"),
    )


@app.get("/dashboard/full")
def dashboard_full():
    # Pattern B: one response, assets embedded once via PageChart
    return dashboard_response([_bar(), _line()], title="Ops")


@app.get("/full")
def full_page():
    return chart_response(_bar(), fragment=False)
