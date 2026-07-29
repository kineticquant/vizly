# vizly

**Status**

[![PyPI](https://img.shields.io/pypi/v/vizly.svg?logo=pypi&logoColor=white)](https://pypi.org/project/vizly/)
[![Python versions](https://img.shields.io/pypi/pyversions/vizly.svg?logo=python&logoColor=white)](https://pypi.org/project/vizly/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/kineticquant/vizly/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/kineticquant/vizly/ci.yml?branch=main&label=CI&logo=github)](https://github.com/kineticquant/vizly/actions/workflows/ci.yml)

**Built on**

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](#install)
[![Apache%20ECharts](https://img.shields.io/badge/Apache%20ECharts-AA344D?logo=apache&logoColor=white)](#chart-inventory)
[![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)](#data-in)
[![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy&logoColor=white)](#data-in)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)](#data-in)
[![openpyxl](https://img.shields.io/badge/openpyxl-217346?logo=microsoftexcel&logoColor=white)](#data-in)

**Frameworks supported**

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](#integrations)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](#integrations)
[![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)](#integrations)
[![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)](#integrations)
[![HTMX](https://img.shields.io/badge/HTMX-3366CC?logo=htmx&logoColor=white)](#integrations)
[![Jupyter](https://img.shields.io/badge/Jupyter-F37626?logo=jupyter&logoColor=white)](#integrations)

**Databases supported** (via SQLAlchemy `from_sql`; install the DBAPI/dialect yourself)

SQLAlchemy **included** dialects (ship with SQLAlchemy; add the driver):

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](#data-in)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)](#data-in)
[![MariaDB](https://img.shields.io/badge/MariaDB-003545?logo=mariadb&logoColor=white)](#data-in)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)](#data-in)
[![Oracle](https://img.shields.io/badge/Oracle-F80000?logo=oracle&logoColor=white)](#data-in)
[![SQL%20Server](https://img.shields.io/badge/SQL%20Server-CC2927?logo=microsoftsqlserver&logoColor=white)](#data-in)

Also reachable when you install an **external** SQLAlchemy dialect (examples; not a closed list):

[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)](#data-in)
[![BigQuery](https://img.shields.io/badge/BigQuery-669DF6?logo=googlebigquery&logoColor=white)](#data-in)
[![Redshift](https://img.shields.io/badge/Redshift-8C4FFF?logo=amazonredshift&logoColor=white)](#data-in)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?logo=clickhouse&logoColor=black)](#data-in)
[![Databricks](https://img.shields.io/badge/Databricks-FF3621?logo=databricks&logoColor=white)](#data-in)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?logo=mongodb&logoColor=white)](#data-in)

vizly does **not** vendor DB drivers or run CI against every database. If SQLAlchemy can connect and return rows, `from_sql` can chart them. Full dialect tables: [CHANGELOG](CHANGELOG.md) / [v1.0.1 release notes](releases/v1.0.1/RELEASE.md).

**Formal v1.** High-performance, low-boilerplate, fully themable Python charting over Apache ECharts.

Detailed documentation is publicly available at [Rancero](https://docs.rancero.com/docs/category/vizly/).

Ship production charts in a few lines of Python: DataFrame, records, columnar dict, file, or SQL in; HTML, JSON, or browser PNG out. No nested option builders. Built for speed (local assets, one ECharts load per page) and for native embeds in the stacks you already use.

- **Easy to use**: set a theme, call `vz.line` / `vz.bar` / …, export with `to_html()`, `to_option()`, or browser `toDataURL` / `downloadImage`
- **Data without forced DataFrames**: pass `list[dict]`, `dict[list]`, loader output, or pandas (pandas remains a dependency, not a required call-site API)
- **SQL and files in base**: `from_sql`, `from_csv`, `from_tsv`, `from_json`, `from_excel` (no `vizly[sql]` extra)
- **Highly performant**: vendored JS by default; GL and plugins load only when a chart needs them
- **Worldwide maps by default**: bundled world atlas plus `usa`; GeoJSON **overlays** via `overlay_geojson` (separate from basemap packs)
- **Drill / live update**: click events for Streamlit and HTMX; `set_data` / `window.__vizly[id].setOption` for refresh without full re-embed
- **Trusted asset defaults**: no Chinese CDN forced (unlike many other Python ECharts wrappers)
- **Wide chart coverage**: cartesian, statistical, geo, flowchart, graph, 3D, compose (`page` / `tab` / `timeline`), and more
- **Native integrations**: Streamlit, FastAPI, Flask, Django, HTMX, and Jupyter

```python
import vizly as vz
vz.map(df)                 # world (default)
vz.map(df, map="usa")      # US states
vz.register_map_pack(...)  # basemap GeoJSON you supply
vz.overlay_geojson(...)    # overlay layer (not a basemap pack)
```

## Install

Requires Python **3.9** or later.

```bash
pip install vizly
```

Base runtime includes `pandas`, `numpy`, `sqlalchemy`, and `openpyxl`. Install DBAPI drivers yourself for the databases you use.

Framework extras (install only what you use): `vizly[streamlit]`, `vizly[fastapi]`, `vizly[flask]`, `vizly[django]`.

Browser tests (optional): `vizly[browser]` + `playwright install chromium`.

HTMX helpers (`vizly.integrations.htmx`) ship in the base package. No `vizly[htmx]` extra.

## 30-second example

```python
import vizly as vz

vz.set_theme("corporate")
# No DataFrame required:
chart = vz.line(
    {"date": ["2026-01-01", "2026-01-02"], "revenue": [10, 20]},
    x="date",
    y="revenue",
    title="Revenue",
)
chart.to_html()       # self-contained local ECharts
chart.to_option()     # plain dict for APIs / agents
# Browser image (after embed): window.__vizly[id].downloadImage("revenue.png")
```

## Data in

Every chart factory accepts these shapes (and loader output):

| Source | How |
|--------|-----|
| pandas `DataFrame` | Pass directly |
| `list[dict]` (records) | Pass directly or `vz.from_records(...)` |
| `dict[str, sequence]` (columnar) | Pass directly or `vz.from_columnar(...)` |
| CSV | `vz.from_csv(path_or_text)` |
| TSV | `vz.from_tsv(...)` |
| JSON | `vz.from_json(...)` (records / columnar / nested `data` key) |
| Excel | `vz.from_excel(path)` |
| SQL | `vz.from_sql(statement, bind=engine)` or `url=` |
| Prometheus / CloudWatch / Elasticsearch JSON | `vz.from_prometheus` / `from_cloudwatch` / `from_elasticsearch` (`from_elk`) |
| Optional Polars / Arrow | Duck-typed when installed (not hard dependencies) |

```python
import vizly as vz
from sqlalchemy import create_engine

table = vz.from_csv("sales.csv")
vz.bar(table, x="region", y="sales")

engine = create_engine("postgresql+psycopg://...")
sql_table = vz.from_sql("SELECT day, value FROM metrics", bind=engine)
vz.line(sql_table, x="day", y="value")
```

**SQLAlchemy coverage:** vizly charts any result set SQLAlchemy can return. vizly does **not** bundle every DB driver or external dialect. If SQLAlchemy can connect, vizly can chart the rows. See [CHANGELOG.md](CHANGELOG.md) for the full included-dialect and external-dialect tables (re-verified at release against SQLAlchemy docs).

## Theming

```python
vz.set_theme("corporate")
# Product: default, light, dark, corporate, minimal, contrast
# Ops-inspired: ops_grafana, ops_cloudwatch, ops_kibana
# Editor-inspired: editor_monokai, editor_tokyo_night, editor_dracula,
#   editor_nord, editor_solarized_light, editor_solarized_dark, editor_one_dark
vz.set_theme({"palette": ["#0B1F33", "#2F6FED"]})  # deep-merge override
vz.register_theme("acme", {"background": "#FFFFFF", "palette": ["#111111"]})
vz.load_theme("examples/themes/atlantic.json", activate=True, register=True)
vz.export_theme("acme", "acme.json")

vz.bar(df, x="region", y="sales", theme="editor_tokyo_night")
```

Ops and editor theme IDs are **visual inspiration only** (not affiliated with Grafana Labs, AWS, Elastic, Monokai, Tokyo Night, Dracula, Nord, Solarized, or One Dark).

CDN asset URLs are allowlisted to `cdn.jsdelivr.net` and `unpkg.com` only. See `src/vizly/assets/README.md` for vendored file provenance.

## Ops metric helpers

```python
import vizly as vz

table = vz.from_prometheus(prom_api_json)          # timestamp, value, series
table = vz.from_cloudwatch(cw_datapoints)          # timestamp, value [, unit|series]
table = vz.from_elasticsearch(es_search_json)      # timestamp, value  (alias: from_elk)

vz.set_theme("ops_grafana")
vz.line(table, x="timestamp", y="value")
```

These helpers **do not** call live APIs. They only normalize payloads you already have.

## Drilldowns, events, and live update

HTML embeds emit a structured `vizly:event` CustomEvent and `postMessage` payload on click (name, value, region, breadcrumb for sunburst/treemap/tree).

```python
from vizly.events import filter_by_click

# Host receives payload → filter sibling chart data
child = vz.bar(filter_by_click(detail_table, payload), x="category", y="sales")

# Live refresh without full page reload (host already has ECharts):
chart.set_data(new_table)
# In the browser: window.__vizly[chartId].setOption(partialOption)
```

- **Streamlit:** `st_vizly(..., events=True)` returns the last click payload via a small declared component.
- **HTMX:** `htmx_event_listener_js("/detail")` POSTs clicks without reloading ECharts (`include_assets=False` on fragments).
- **SPA / JSON:** `to_option()` / `to_json()` do **not** auto-wire drill. Attach `chart.on('click', …)` yourself after `echarts.init`.

Multi-chart pages (`vz.page` / `dashboard_html` / `st_dashboard`) use `echarts.connect` by default for linked tooltip/brush (`connect=False` to opt out).

## Maps and geo layers

| Path | API | Role |
|------|-----|------|
| Basemap packs | `register_map_pack`, bundled `world` / `usa`, `vz.map` | Choropleth via `echarts.registerMap` |
| Geo overlays | `overlay_geojson` / `GeoLayer`, `layers=` on `vz.map` / `vz.geo` | Points, lines, polygons on a geo coordinate system |

Join keys on choropleth: `name_field=` / `id_field=` beyond fragile name-only matching. China administrative packs remain **opt-in** via `register_map_pack` only. No Baidu Map defaults.

See `examples/mapping_dashboard.py`.

## Trust / asset policy

| Mode | Behavior |
|------|----------|
| `assets.mode = "local"` (default) | Inline vendored `echarts.min.js` (+ GL/plugins only when needed) |
| `assets.mode = "cdn"` | Allowlisted hosts only |
| Banned by default | China-primary CDN hosts (bootcdn, npmmirror, assets.pyecharts.org, …) |

## Chart inventory

```python
vz.list_chart_types()
vz.list_unavailable_chart_types()  # e.g. chord (upstream-unavailable)
```

`line`, `bar`, `area`, `scatter`, `pie`, `donut`, `boxplot`, `heatmap`, `candlestick` / `kline`, `radar`, `funnel`, `gauge`, `sankey`, `treemap`, `map`, `grid`, `mix` / `combo`, `effect_scatter`, `waterfall`, `polar`, `parallel`, `sunburst`, `tree`, `graph`, `flowchart` (alias `diagram`), `wordcloud`, `geo`, `bar3d`, `line3d`, `scatter3d`, `page`, `tab`, `timeline`, `pictorial_bar`, `theme_river`, `liquid`, `surface3d`

| Type | Role |
|------|------|
| `flowchart` / `diagram` | Process / dependency boxes (ECharts graph; **not** Mermaid) |
| `graph` | General networks |
| `tree` | Single-parent hierarchy |
| `sunburst` / `treemap` | Hierarchical part-to-whole (+ drill breadcrumbs) |
| `sankey` | Quantitative flow |

Extra map packs and geo layers are **not** chart types.

## Export (PNG / image)

Images come from the **browser that already rendered the chart** (ECharts
`getDataURL`). vizly does **not** ship Chromium.

```javascript
// After any HTML embed: chart id is on the root .vizly-chart element
const id = document.querySelector(".vizly-chart").id;
window.__vizly[id].toDataURL({ type: "png", pixelRatio: 2 });
window.__vizly[id].downloadImage("chart.png");
```

Optional toolbox button (no custom JS):

```python
chart.merge_option({"toolbox": {"feature": {"saveAsImage": {"type": "png"}}}})
```

Live option push without re-loading ECharts:

```python
chart.set_data(new_rows)
html_fragment = chart.live_update_script(chart_id)  # inject where the chart lives
```

For headless batch PNG/PDF, run Playwright (or similar) on `chart.to_html()`
yourself. That stack is outside the vizly package (`vizly[browser]` is only for
gallery tests).

## Integrations

Shared embed contract (`vizly.integrations`):

| Mode | Helper idea | Output |
|------|-------------|--------|
| Full document | Streamlit / FastAPI page | `<!DOCTYPE html>…` |
| Fragment | Flask/Django/HTMX | `div.vizly-embed` + scripts |
| Dashboard | `dashboard_html` / `vz.page` / `st_dashboard` | many charts, **ECharts once**, linked by default |
| JSON | APIs / SPA | `to_option()` / `to_json()` |

### Multi-chart / dashboard

```python
from vizly.integrations import assets_html, chart_html, dashboard_html

head = assets_html(charts=[c1, c2])
a = chart_html(c1, fragment=True, include_assets=False)
b = chart_html(c2, fragment=True, include_assets=False)

html = dashboard_html([c1, c2], title="Ops")  # connect=True by default
```

### Streamlit

```python
from vizly.integrations.streamlit import st_vizly, st_dashboard

event = st_vizly(chart, height=420)           # last click payload or None
st_dashboard([c1, c2], height=900)            # many charts, ECharts once
```

### FastAPI / Flask / Django

Same as before. See `examples/fastapi_app.py`, `examples/flask_app.py`, `examples/django_demo/`.

### HTMX

```python
from vizly.integrations.htmx import htmx_chart_fragment, htmx_event_listener_js
# Parent page: assets once + htmx_event_listener_js("/detail")
# Fragments: include_assets=False
```

### Jupyter

Charts display via `_repr_html_()`.

## Less boilerplate than raw option builders

```python
vz.set_theme("corporate")
vz.bar(df, x="region", y="sales", title="Sales")  # ~1-2 lines
```

Escape hatches: `chart.update(...)`, `chart.merge_option({...})`, `chart.set_data(...)`, `chart.set_option_patch(...)`, `vz.from_option(option)`.

### Title / legend layout

Defaults keep chrome clear of the plot: title **left**, legend **top-right**, and cartesian `grid` padding with `containLabel`. These are defaults only. Override any time:

```python
chart.merge_option({
    "title": {"left": "center", "top": 0},
    "legend": {"top": "bottom", "left": "center"},
    "grid": {"top": 40, "bottom": 72, "containLabel": True},
})
```

Or set `title` / `legend` layout keys on a custom theme (`register_theme` / `theme=`).

## Examples

| Path | Purpose |
|------|---------|
| `artifacts/docs_showcase/` | Full v1 interactive showcase (rebuild: `python scripts/build_docs_showcase.py`) |
| `examples/streamlit_app.py` | Streamlit (single + dashboard) |
| `examples/fastapi_app.py` | FastAPI HTML/JSON/dashboard |
| `examples/flask_app.py` | Flask + Jinja fragment / dashboard |
| `examples/django_demo/` | Django template tags |
| `examples/htmx_demo/app.py` | HTMX partial swap |
| `examples/mapping_dashboard.py` | Map + overlays + linked charts |
| `examples/ingest_demo.py` | CSV / SQL / flowchart ingest |
| `examples/jupyter_gallery.ipynb` | Notebook |
| `examples/themes/atlantic.json` | Custom theme |
| `examples/band_a_gallery.py` / `band_bc_gallery.py` | Chart HTML gallery seeds |

## Development

```bash
pip install -e ".[dev,examples]"
python -m pytest -m "not browser" -v
```

| Level | Command | Role |
|-------|---------|------|
| 1+2 (CI gate) | `pytest -m "not browser"` | Contracts + sample/golden HTML |
| 3 Browser | `pytest -m browser` | Headless hero charts (Playwright) |
| Local visual review | `python scripts/validate_samples_browser.py --gallery` | Headed Chromium + gallery |

Refresh option goldens: `python scripts/update_sample_goldens.py`

Docs showcase (all chart types + v1 features + themes):

```bash
python scripts/build_docs_showcase.py
# → artifacts/docs_showcase/index.html + EXAMPLES.md
```

Full testing runbook: **[TESTING.md](TESTING.md)**. Also [CHANGELOG.md](CHANGELOG.md) and [RELEASE.md](RELEASE.md).

Detailed documentation: [Rancero vizly docs](https://docs.rancero.com/docs/category/vizly/).

## Known limitations

- **SPA / JSON + maps:** `to_option()` / `json_response` return the ECharts option only. They do **not** embed GeoJSON. HTML rendering calls `echarts.registerMap` for you; SPA clients must register map packs themselves (or use HTML embeds).
- **page / tab JSON:** `to_option()` returns a compose descriptor under `_vizly_compose` (child options). Use HTML embeds (`dashboard_html` / `to_html`) for browser layout.
- **Flowchart:** process/dependency diagrams, not Mermaid syntax, BPMN, swimlanes, or sequence diagrams.
- **Export:** PNG/JPEG/SVG via browser `toDataURL` / `downloadImage`. No server-side Chromium in vizly.
