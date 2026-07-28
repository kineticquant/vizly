# vizly

Fully themable, low-boilerplate charting over Apache ECharts.

`vizly` is built for teams that want Apache ECharts without inheriting pyecharts’ China-primary defaults — English-first APIs/docs, local/allowlisted JS, and a Kineticquant-maintained trust posture. That is **not** USA-only geography:

- Local / allowlisted JS assets (no China-primary CDN defaults)
- English APIs/docs/errors (`en-US` chrome)
- No Baidu Map provider
- **Worldwide** map atlas by default; bundled `usa` regional pack; China administrative packs **opt-in only**

```python
import vizly as vz
vz.map(df)                 # world (default)
vz.map(df, map="usa")      # US states
vz.register_map_pack(...)  # e.g. China GeoJSON you supply
```

## Install

```bash
pip install -e ".[dev,examples]"
python -m pytest -m "not browser" -v
```

**CI targets:** Python **3.9–3.13**. Full testing & validation runbook: **[TESTING.md](TESTING.md)**. Also [CHANGELOG.md](CHANGELOG.md) and [RELEASE.md](RELEASE.md).

| Level | Command | Role |
|-------|---------|------|
| 1+2 (CI gate) | `pytest -m "not browser"` | Contracts + sample/golden HTML |
| 3 Browser | `pytest -m browser` | Headless hero charts (Playwright) |
| Local visual review | `python scripts/validate_samples_browser.py --gallery` | Headed Chromium + gallery |

Refresh option goldens: `python scripts/update_sample_goldens.py`

Framework extras: `vizly[streamlit]`, `vizly[fastapi]`, `vizly[flask]`, `vizly[django]`.

PyPI: `pip install vizly` (when published).

### Export (deferred)

PNG/PDF snapshot export (`vizly[export]`) is **not** shipped yet. ECharts draws in JavaScript, so image export needs a JS canvas runtime (Node + `node-canvas` per Apache’s SSR guide, or a headless browser) — not a pure-Python conversion of the option dict. Use `to_html()` / `to_option()` meanwhile.

## 30-second example

```python
import pandas as pd
import vizly as vz

vz.set_theme("corporate")
df = pd.DataFrame({"date": ["2026-01-01", "2026-01-02"], "revenue": [10, 20]})
chart = vz.line(df, x="date", y="revenue", title="Revenue")
chart.to_html()       # self-contained local ECharts
chart.to_option()     # plain dict for APIs / agents
```

## Theming

```python
vz.set_theme("corporate")
# builtins: default, light, dark, corporate, minimal, contrast,
#           ops_grafana, ops_cloudwatch, ops_kibana  # ops-inspired (see below)
vz.set_theme({"palette": ["#0B1F33", "#2F6FED"]})  # deep-merge override
vz.register_theme("acme", {"background": "#FFFFFF", "palette": ["#111111"]})
vz.load_theme("examples/themes/atlantic.json", activate=True, register=True)
vz.export_theme("acme", "acme.json")

# Per-chart override does not mutate the session theme
vz.bar(df, x="region", y="sales", theme="dark")
```

### Ops-inspired themes

`ops_grafana`, `ops_cloudwatch`, and `ops_kibana` are **visual inspiration only** — denser grids, muted animation, step-friendly lines so charts feel at home next to common ops UIs. They are **not affiliated** with Grafana Labs, Amazon Web Services, or Elastic; no logos or proprietary design-system assets are shipped. Theme IDs use an `ops_` prefix intentionally (zero trademark surface).

CDN asset URLs are allowlisted to `cdn.jsdelivr.net` and `unpkg.com` only. See `src/vizly/assets/README.md` for vendored file provenance.

## Ops metric helpers

Agents/ops often receive Prometheus, CloudWatch, or Elasticsearch JSON. Shape it, then chart:

```python
import vizly as vz

df = vz.from_prometheus(prom_api_json)          # timestamp, value, series
df = vz.from_cloudwatch(cw_datapoints)          # timestamp, value [, unit|series]
df = vz.from_elasticsearch(es_search_json)      # timestamp, value  (alias: from_elk)

vz.set_theme("ops_grafana")
vz.line(df, x="timestamp", y="value")           # single series
# multi-series Prometheus matrix → group or filter by `series` column
```

These helpers **do not** call live APIs — they only normalize payloads you already have.

## Trust / asset policy

| Mode | Behavior |
|------|----------|
| `assets.mode = "local"` (default) | Inline vendored `echarts.min.js` (+ GL/plugins only when needed) |
| `assets.mode = "cdn"` | Allowlisted hosts only |
| Banned by default | bootcdn, npmmirror, assets.pyecharts.org, Baidu Map, etc. |

Maps: bundled `world` + `usa`; China packs via `register_map_pack` only.

## Chart inventory

```python
vz.list_chart_types()
vz.list_unavailable_chart_types()  # e.g. chord (upstream-unavailable)
```

**Band A:** line, bar, area, scatter, pie, donut, boxplot, heatmap, candlestick/kline, radar, funnel, gauge, sankey, treemap, map, grid, mix/combo  

**Band B:** effect_scatter, waterfall, polar, parallel, sunburst, tree, graph, wordcloud, geo, bar3d, line3d, scatter3d, page, tab, timeline  

**Band C:** pictorial_bar, theme_river, liquid, surface3d  

China administrative map packs are **not** chart types — register them with `vz.register_map_pack` when you need them.

## Integrations

Shared embed contract (`vizly.integrations`):

| Mode | Helper idea | Output |
|------|-------------|--------|
| Full document | Streamlit / FastAPI page | `<!DOCTYPE html>…` |
| Fragment | Flask/Django/HTMX | `div.vizly-embed` + scripts |
| Dashboard | `dashboard_html` / `vz.page` / `st_dashboard` | many charts, **ECharts once** |
| JSON | APIs / SPA | `to_option()` / `to_json()` |

### Multi-chart / dashboard (important)

Single-chart helpers can include the ECharts library so one embed works alone. For **several charts on one page**, load assets **once** — otherwise each chart ships ~1MB of JS.

```python
from vizly.integrations import assets_html, chart_html, dashboard_html

# Pattern A — shell page (auto GL/plugins from charts=)
head = assets_html(charts=[c1, c2])
a = chart_html(c1, fragment=True, include_assets=False)
b = chart_html(c2, fragment=True, include_assets=False)

# Pattern B — one HTML blob (assets once internally)
html = dashboard_html([c1, c2], title="Ops")
# same idea: vz.page(charts=[c1, c2]).to_html()
```

Django:

```django
{% load vizly_tags %}
<head>{% vizly_assets charts=charts %}</head>
{% vizly_chart c1 %}
{% vizly_chart c2 %}
{{ c3|vizly_html }}
{# or one blob: {% vizly_dashboard charts %} #}
```

HTMX fragments already default `include_assets=False` (see `examples/htmx_demo`).

### Streamlit

Each `components.html` call is a separate iframe. Prefer one iframe for many charts:

```python
from vizly.integrations.streamlit import st_vizly, st_dashboard

st_vizly(chart, height=420)                 # one chart
st_dashboard([c1, c2], height=900)          # many charts, ECharts once
st_vizly([c1, c2], height=900)              # same as st_dashboard
# examples/streamlit_app.py
```

### FastAPI

```python
from vizly.integrations.fastapi import html_response, json_response, dashboard_response
# examples/fastapi_app.py  →  /  /dashboard  /option
```

### Flask

```python
from vizly.integrations.flask import assets_html, chart_html, dashboard_response
# examples/flask_app.py  →  /  /dashboard  /dashboard/full
```

### Django templates

```python
INSTALLED_APPS = [..., "vizly.integrations.django"]
```

```django
{% load vizly_tags %}
{% vizly_assets charts=charts %}
{% vizly_chart chart height="420px" %}
{{ chart|vizly_html }}
{# single chart without assets tag: {{ chart|vizly_html:"assets" }} #}
```

See `examples/django_demo/`.

### HTMX

```python
from vizly.integrations.htmx import htmx_chart_fragment, htmx_or_full
# examples/htmx_demo/app.py — button hx-get swaps #chart
```

### Jupyter

Open `examples/jupyter_gallery.ipynb` — charts display via `_repr_html_()`.

## Known limitations

- **SPA / JSON + maps:** `to_option()` / `json_response` return the ECharts option only. They do **not** embed GeoJSON. HTML rendering calls `echarts.registerMap` for you; SPA clients must register map packs themselves (or use HTML embeds).
- **PNG/PDF export:** not shipped yet (see Install).
- **page / tab JSON:** `to_option()` returns a compose descriptor under `_vizly_compose` (child options). Use HTML embeds (`dashboard_html` / `to_html`) for browser layout.

## Less boilerplate than raw option builders

**Verbose option-builder style (illustrative):** many nested calls for series, axes, tooltip, and theme (~15–25 lines).

**vizly after one theme call:**

```python
vz.set_theme("corporate")
vz.bar(df, x="region", y="sales", title="Sales")  # ~1–2 lines
```

Escape hatches remain: `chart.update(...)`, `chart.merge_option({...})`, `vz.from_option(option)`.

## Examples

| Path | Purpose |
|------|---------|
| `examples/streamlit_app.py` | Streamlit (single + dashboard) |
| `examples/fastapi_app.py` | FastAPI HTML/JSON/dashboard |
| `examples/flask_app.py` | Flask + Jinja fragment / dashboard |
| `examples/django_demo/` | Django `{% vizly_chart %}` + `{% vizly_assets %}` |
| `examples/htmx_demo/app.py` | HTMX partial swap |
| `examples/jupyter_gallery.ipynb` | Notebook |
| `examples/themes/atlantic.json` | Custom theme |
| `examples/band_a_gallery.py` / `band_bc_gallery.py` | Chart HTML gallery seeds |
