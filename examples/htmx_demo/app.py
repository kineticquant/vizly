"""HTMX partial-refresh demo (Flask).

ECharts is loaded **once** in the page head. HTMX swaps only chart
fragments (no re-embedding of the ~1MB library).

Run::

    pip install 'vizly[flask]'
    python examples/htmx_demo/app.py
"""

from __future__ import annotations

import pandas as pd
from flask import Flask, request

import vizly as vz
from vizly.integrations._embed import assets_html
from vizly.integrations.htmx import (
    htmx_chart_fragment,
    htmx_event_listener_js,
    htmx_or_full,
)

app = Flask(__name__)
vz.set_theme("corporate")

PAGE = """
<!doctype html>
<html lang="en-US">
<head>
  <meta charset="utf-8"/>
  <title>vizly HTMX</title>
  <script src="https://cdn.jsdelivr.net/npm/htmx.org@1.9.12/dist/htmx.min.js"></script>
  %s
  %s
</head>
<body>
  <h1>vizly + HTMX</h1>
  <p>
    <button hx-get="/chart?metric=revenue" hx-target="#chart" hx-swap="innerHTML">Revenue</button>
    <button hx-get="/chart?metric=cost" hx-target="#chart" hx-swap="innerHTML">Cost</button>
  </p>
  <div id="chart">%s</div>
  <div id="vizly-detail"><em>Click a chart point to POST a vizly:event here.</em></div>
</body>
</html>
"""


def _chart(metric: str = "revenue"):
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "revenue": [10, 20, 15],
            "cost": [4, 8, 6],
        }
    )
    col = metric if metric in df.columns else "revenue"
    return vz.line(df, x="date", y=col, title=col.title())


@app.get("/")
def index():
    # Assets once in <head>; initial fragment without re-embedding ECharts.
    head = assets_html()
    listener = htmx_event_listener_js("/detail", target="#vizly-detail")
    frag = htmx_chart_fragment(_chart("revenue"), height="360px", include_assets=False)
    return PAGE % (head, listener, frag)


@app.get("/chart")
def chart():
    metric = request.args.get("metric", "revenue")
    headers = {k: v for k, v in request.headers.items()}
    # HTMX → fragment without assets; direct navigation → full document.
    return htmx_or_full(_chart(metric), headers, height="360px")


@app.post("/detail")
def detail():
    payload = request.form.get("vizly_event", "{}")
    return f"<pre>{payload}</pre>"


if __name__ == "__main__":
    app.run(debug=True, port=5055)
