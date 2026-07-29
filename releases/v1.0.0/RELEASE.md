# vizly v1.0.0 release notes

**Release date:** 2026-07-29  
**Python:** 3.9 or later (CI: 3.9–3.13)  
**Runtime deps:** `pandas`, `numpy`, `sqlalchemy`, `openpyxl` (no pyecharts)  
**Maintainer:** Kineticquant

These are the **official Formal v1** release notes for vizly. They describe the full product as shipped in **1.0.0**: every supported capability, not only the delta from a prior preview tag. Chronological diffs live in [CHANGELOG.md](../../CHANGELOG.md) and under `releases/v0.2.x/`.

---

## Product statement

**vizly** is a high-performance, low-boilerplate, fully themable Python charting library over Apache ECharts.

Ship production charts in a few lines of Python: DataFrame, records, columnar dict, file, or SQL in; HTML, JSON, or browser image out. No nested option builders. Built for speed (local assets, one ECharts load per page) and for native embeds in the stacks you already use.

| Pillar | What 1.0.0 delivers |
|--------|---------------------|
| Easy to use | Set a theme, call `vz.line` / `vz.bar` / …, export with `to_html()`, `to_option()`, or browser `toDataURL` / `downloadImage` |
| Data without forced DataFrames | Pass `list[dict]`, `dict[list]`, loader output, or pandas (pandas is a dependency, not a required call-site API) |
| SQL and files in base | `from_sql`, `from_csv`, `from_tsv`, `from_json`, `from_excel` (no `vizly[sql]` extra) |
| Highly performant | Vendored JS by default; GL and plugins load only when a chart needs them |
| Worldwide maps by default | Bundled world atlas plus `usa`; GeoJSON overlays via `overlay_geojson` (separate from basemap packs) |
| Drill / live update | Click events for Streamlit and HTMX; `set_data` / `window.__vizly[id].setOption` for refresh without full re-embed |
| Trusted asset defaults | No Chinese CDN forced (unlike many other Python ECharts wrappers) |
| Wide chart coverage | Cartesian, statistical, geo, flowchart, graph, 3D, compose (`page` / `tab` / `timeline`), and more |
| Native integrations | Streamlit, FastAPI, Flask, Django, HTMX, and Jupyter |

---

## Capability summary (full Formal v1 surface)

1. **Chart factories:** sugar constructors, universal `vz.chart`, `vz.from_option`, theme + merge escape hatches.
2. **40 chart types:** including flowchart/diagram, 3D (GL), wordcloud, liquid, and compose layouts.
3. **TabularView ingest:** pandas, records, columnar, CSV/TSV/JSON/Excel, SQL via SQLAlchemy, optional Polars/Arrow duck-typing.
4. **Ops JSON normalizers:** Prometheus, CloudWatch, Elasticsearch / ELK (no live API calls).
5. **Theme engine:** builtins (product, ops-inspired, editor-inspired), register/load/export, session + per-chart override, `en-US` locale default.
6. **Default chrome:** title left, legend top-right, cartesian `grid` padding with `containLabel` (overridable).
7. **Maps:** world default, bundled `usa`, opt-in `register_map_pack`, join keys, GeoJSON overlays segregated from basemap packs.
8. **Events and dashboards:** click/`postMessage`, Streamlit component return, HTMX listener, linked brush via `echarts.connect`, live update helpers.
9. **Browser image export:** ECharts `getDataURL` via `toDataURL` / `downloadImage`; optional toolbox `saveAsImage`. No in-package Chromium.
10. **Shared embed contract:** full document, fragment, dashboard (one ECharts load), JSON. Used by every framework helper.
11. **Trust posture:** vendored assets default; CDN allowlist only; banned China-primary CDN/map defaults.
12. **Quality gates:** contract tests, sample/option goldens, Playwright browser smoke, CI + tag-based PyPI publish.

---

## Install

```bash
pip install vizly
```

Base runtime includes `pandas`, `numpy`, `sqlalchemy`, and `openpyxl`. Install DBAPI drivers yourself for the databases you use.

| Extra | Purpose |
|-------|---------|
| `vizly[streamlit]` | Streamlit helpers |
| `vizly[fastapi]` | FastAPI helpers |
| `vizly[flask]` | Flask helpers |
| `vizly[django]` | Django template tags |
| `vizly[examples]` | Framework demo deps |
| `vizly[browser]` | Playwright for gallery / L3 tests |
| `vizly[dev]` | Pytest, ruff, build tooling |

HTMX helpers (`vizly.integrations.htmx`) ship in the **base** package. There is **no** `vizly[htmx]` extra and **no** `vizly[export]` / `vizly[sql]` extra.

From a source checkout:

```bash
pip install -e ".[dev,examples]"
```

---

## 30-second example

```python
import vizly as vz

vz.set_theme("corporate")
chart = vz.line(
    {"date": ["2026-01-01", "2026-01-02"], "revenue": [10, 20]},
    x="date",
    y="revenue",
    title="Revenue",
)
chart.to_html()    # self-contained local ECharts
chart.to_option()  # plain dict for APIs / agents
# After embed: window.__vizly[id].downloadImage("revenue.png")
```

Maps:

```python
vz.map(df)                 # world (default)
vz.map(df, map="usa")      # US states
vz.register_map_pack(...)  # basemap GeoJSON you supply
vz.overlay_geojson(...)    # overlay layer (not a basemap pack)
```

---

## Core API

Every chart factory lives on the `vizly` namespace (`import vizly as vz`).

| Export path | Role |
|-------------|------|
| `vz.line`, `vz.bar`, … | Sugar constructors for each chart type |
| `vz.chart(type, data, …)` | Universal constructor by type name |
| `vz.from_option(dict, …)` | Wrap a raw ECharts option as a vizly chart |
| `chart.to_html()` | Self-contained HTML with local ECharts |
| `chart.to_option()` / `to_json()` | Plain dict/JSON for APIs, SPAs, or agents |
| `chart.update(…)` / `merge_option({…})` | Escape hatches for fine control |
| `chart.set_data(…)` / `set_option_patch(…)` | Live data / partial option updates |
| `chart.live_update_script(chart_id)` | Partial option push without full re-embed |

**Base lifecycle:** data standardization → `_build()` → theme apply → user merge → export.

Less boilerplate than raw option builders: set a theme, call one factory, export. Escape hatches stay available when you need them.

---

## Chart inventory

**40 registered types.** Use `vz.list_chart_types()` and `vz.list_unavailable_chart_types()`.

`line`, `bar`, `area`, `scatter`, `pie`, `donut`, `boxplot`, `heatmap`, `candlestick`, `kline`, `radar`, `funnel`, `gauge`, `sankey`, `treemap`, `map`, `grid`, `mix`, `combo`, `effect_scatter`, `waterfall`, `polar`, `parallel`, `sunburst`, `tree`, `graph`, `flowchart`, `wordcloud`, `geo`, `bar3d`, `line3d`, `scatter3d`, `page`, `tab`, `timeline`, `pictorial_bar`, `theme_river`, `liquid`, `surface3d`

Alias: `diagram` → `flowchart`.

| Type | Role |
|------|------|
| `flowchart` / `diagram` | Process / dependency boxes (ECharts graph; **not** Mermaid) |
| `graph` | General networks |
| `tree` | Single-parent hierarchy |
| `sunburst` / `treemap` | Hierarchical part-to-whole (+ drill breadcrumbs) |
| `sankey` | Quantitative flow |

Extra map packs and geo layers are **not** chart types.

### Upstream unavailable

`chord`: ECharts 5.x no longer ships a first-class chord series; use `sankey` or `graph` instead.

### Compose charts

`grid`, `page`, `tab`, and `timeline` take `charts=` instead of `data=`. `page` / `tab` `to_option()` returns a compose descriptor under `_vizly_compose` (child options), including `connect` when linked. Use HTML embeds (`dashboard_html` / `to_html`) for browser layout.

---

## Data ingest

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

Spine helpers: `as_tabular` / `ColumnarTable`, `filter_tabular` / `filter_by_click`, `standardize(data)` (DataFrame escape hatch), `infer_roles`, `DataError` at trust boundaries.

```python
import vizly as vz
from sqlalchemy import create_engine

table = vz.from_csv("sales.csv")
vz.bar(table, x="region", y="sales")

engine = create_engine("postgresql+psycopg://...")
sql_table = vz.from_sql("SELECT day, value FROM metrics", bind=engine)
vz.line(sql_table, x="day", y="value")
```

### SQLAlchemy database coverage

vizly does **not** bundle every DB driver or every external dialect package. If SQLAlchemy can connect, vizly can chart the result set through `from_sql`. vizly does not open live vendor APIs beyond executing the SQL you provide.

**Included dialects** (shipped with SQLAlchemy; install the matching DBAPI):

| Database | Dialect key(s) | Typical drivers / URLs |
|----------|----------------|------------------------|
| PostgreSQL | `postgresql` | `psycopg2`, `psycopg` (v3), `pg8000`, `asyncpg`, etc. |
| MySQL | `mysql` | `mysqlclient`, `PyMySQL`, `mysql-connector-python`, etc. |
| MariaDB | `mysql` / MariaDB via MySQL dialect | same driver family as MySQL where applicable |
| SQLite | `sqlite` | stdlib `sqlite3`, `aiosqlite` |
| Oracle | `oracle` | `oracledb`, `cx_Oracle` |
| Microsoft SQL Server | `mssql` | `pyodbc`, `pymssql`, etc. |

**External dialects** (install dialect + DBAPI; pass Engine/URL into vizly). Re-verified 2026-07-28 against [SQLAlchemy Dialects](https://docs.sqlalchemy.org/en/20/dialects/):

| Database | Dialect / package |
|----------|-------------------|
| Actian Data Platform, Vector, Actian X, Ingres | sqlalchemy-ingres |
| Amazon Athena | pyathena |
| Amazon Aurora DSQL | aurora-dsql-sqlalchemy |
| Amazon DynamoDB | pydynamodb |
| Amazon Redshift (via psycopg2) | sqlalchemy-redshift |
| Apache Drill | sqlalchemy-drill |
| Apache Druid | pydruid |
| Apache Hive and Presto | PyHive |
| Apache Solr | sqlalchemy-solr |
| ClickHouse | clickhouse-sqlalchemy |
| CockroachDB | sqlalchemy-cockroachdb |
| CrateDB | sqlalchemy-cratedb |
| Databend | databend-sqlalchemy |
| Databricks | Databricks SQLAlchemy dialect |
| Denodo | denodo-sqlalchemy |
| EXASolution | sqlalchemy_exasol |
| Elasticsearch (readonly) | elasticsearch-dbapi |
| Firebird | sqlalchemy-firebird |
| Firebolt | firebolt-sqlalchemy |
| Google BigQuery | sqlalchemy-bigquery |
| Google Sheets | gsheets |
| Greenplum | sqlalchemy-greenplum |
| HyperSQL (hsqldb) | sqlalchemy-hsqldb |
| IBM DB2 and Informix | ibm-db-sa |
| IBM Netezza Performance Server | nzalchemy |
| Impala | impyla |
| Kinetica | sqlalchemy-kinetica |
| Microsoft Access (via pyodbc) | sqlalchemy-access |
| Microsoft SQL Server (via python-tds) | sqlalchemy-pytds |
| Microsoft SQL Server (via turbodbc) | sqlalchemy-turbodbc |
| Mimer SQL | sqlalchemy-mimer |
| MonetDB | sqlalchemy-monetdb |
| MongoDB | pymongosql |
| OceanBase | oceanbase-sqlalchemy |
| OpenGauss | openGauss-sqlalchemy |
| Rockset | rockset-sqlalchemy |
| SAP ASE | sqlalchemy-sybase |
| SAP HANA | sqlalchemy-hana |
| SAP Sybase SQL Anywhere | sqlalchemy-sqlany |
| Snowflake | snowflake-sqlalchemy |
| Teradata Vantage | teradatasqlalchemy |
| TiDB | sqlalchemy-tidb |
| YDB | ydb-sqlalchemy |
| YugabyteDB | sqlalchemy-yugabytedb |

---

## Theming

### Builtin presets

**Product:** `default`, `light`, `dark`, `corporate`, `minimal`, `contrast`  
**Ops-inspired:** `ops_grafana`, `ops_cloudwatch`, `ops_kibana`  
**Editor-inspired:** `editor_monokai`, `editor_tokyo_night`, `editor_dracula`, `editor_nord`, `editor_solarized_light`, `editor_solarized_dark`, `editor_one_dark`

Ops and editor theme IDs are **visual inspiration only** (not affiliated with Grafana Labs, AWS, Elastic, Monokai, Tokyo Night, Dracula, Nord, Solarized, or One Dark).

### Theme API

| Function | Purpose |
|----------|---------|
| `vz.set_theme(name_or_dict)` | Session theme (dict deep-merges) |
| `vz.get_theme()` / `resolve_theme()` | Read or resolve theme |
| `vz.register_theme(name, dict)` | Register a custom preset |
| `vz.load_theme(path, activate=, register=)` | Load theme from JSON file |
| `vz.export_theme(name, path)` | Export a registered theme |
| `vz.list_themes()` | List available theme names |
| Per-chart `theme=` kwarg | Override without mutating session theme |

Theme `locale` defaults to `en-US` and is passed to `echarts.init` as `EN` / `ZH`.

### Title / legend layout (chrome)

Defaults keep chrome clear of the plot: title **left**, legend **top-right**, and cartesian `grid` padding with `containLabel`. These are defaults only. Override any time via `merge_option` or theme `title` / `legend` keys.

```python
chart.merge_option({
    "title": {"left": "center", "top": 0},
    "legend": {"top": "bottom", "left": "center"},
    "grid": {"top": 40, "bottom": 72, "containLabel": True},
})
```

---

## Ops metric helpers

Normalize observability JSON you already have: **no live API calls**.

| Function | Input shape |
|----------|-------------|
| `from_prometheus(json)` | Prometheus API / matrix → `timestamp`, `value`, `series` |
| `from_cloudwatch(json)` | CloudWatch datapoints → `timestamp`, `value` [, `unit` \| `series`] |
| `from_elasticsearch(json)` | ES search hits → `timestamp`, `value` |
| `from_elk(json)` | Alias for `from_elasticsearch` |

Bad rows are dropped with a warning and `DataFrame.attrs['vizly_skipped']` set.

```python
table = vz.from_prometheus(prom_api_json)
vz.set_theme("ops_grafana")
vz.line(table, x="timestamp", y="value")
```

---

## Maps and geography

| Path | API | Role |
|------|-----|------|
| Basemap packs | `register_map_pack`, bundled `world` / `usa`, `vz.map` | Choropleth via `echarts.registerMap` |
| Geo overlays | `overlay_geojson` / `GeoLayer`, `layers=` on `vz.map` / `vz.geo` | Points, lines, polygons on a geo coordinate system |
| Join keys | `name_field=` / `id_field=` | Beyond fragile name-only matching |
| Introspection | `list_bundled_maps()`, `list_opt_in_maps()` | Bundled vs opt-in geography |
| Low-level | `load_map_geojson(name)`, `map_path(name)` | Path / GeoJSON helpers |

Default atlas is **world**. Bundled regional pack: `usa`. Extra regional packs are **not** bundled by default. Register them when you need them. China administrative packs remain **opt-in** via `register_map_pack` only. No Baidu Map defaults.

Polygon overlays use outline lines plus HTML custom fill series; map + layers can share `geo` roam when `layers=` is set.

**SPA / JSON note:** `to_option()` / `json_response` return the ECharts option only. They do **not** embed GeoJSON. HTML rendering calls `echarts.registerMap` for you; SPA clients must register map packs themselves (or use HTML embeds).

---

## Drilldowns, events, and live update

HTML embeds emit a structured `vizly:event` CustomEvent and `postMessage` payload on click (name, value, region, breadcrumb for sunburst/treemap/tree).

| Path | Behavior |
|------|----------|
| Click `postMessage` | Defaults to same-origin; Streamlit opts into `"*"` for the component bridge |
| Streamlit | `st_vizly(..., events=True)` returns the last click payload via a declared component |
| HTMX | `htmx_event_listener_js("/detail")` POSTs clicks without reloading ECharts |
| SPA / JSON | `to_option()` does **not** auto-wire drill. Attach `chart.on('click', …)` after `echarts.init` |
| Filter helpers | `filter_by_click` / `filter_tabular` for categorical and map drill |
| Live refresh | `chart.set_data(...)`; browser `window.__vizly[id].setOption(...)` |
| Linked dashboards | `echarts.connect` on `page` / `dashboard_html` / `st_dashboard` (`connect=True` default; `connect=False` to opt out) |
| Message origin | `message_origin` on page/tab/timeline/`dashboard_html` / chart HTML |

```python
from vizly.events import filter_by_click

child = vz.bar(filter_by_click(detail_table, payload), x="category", y="sales")
chart.set_data(new_table)
html_fragment = chart.live_update_script(chart_id)
```

---

## Image export (PNG / JPEG / SVG)

Images come from the **browser that already rendered the chart** (ECharts `getDataURL`). vizly does **not** ship Chromium.

```javascript
const id = document.querySelector(".vizly-chart").id;
window.__vizly[id].toDataURL({ type: "png", pixelRatio: 2 });
window.__vizly[id].downloadImage("chart.png");
```

Optional toolbox button (no custom JS):

```python
chart.merge_option({"toolbox": {"feature": {"saveAsImage": {"type": "png"}}}})
```

For headless batch PNG/PDF, run Playwright (or similar) on `chart.to_html()` yourself. That stack is outside the vizly package (`vizly[browser]` is only for gallery tests).

---

## Trust and assets

| Rule | Detail |
|------|--------|
| Default mode | `assets.mode = "local"` (vendored JS inlined or linked from package) |
| Optional CDN | Allowlist only: `cdn.jsdelivr.net`, `unpkg.com` |
| Banned by default | China-primary CDN hosts (bootcdn, npmmirror, assets.pyecharts.org, …) |
| Plugin loading | GL, wordcloud, liquidfill load **only** when the chart needs them |
| Trust scanner | Checks `<script src>` hosts only (not option JSON labels) |
| Locale | English-first APIs, docs, and errors (`en-US` chrome) |

### Pinned vendored assets (1.0.0)

| File | Version |
|------|---------|
| `echarts.min.js` | 5.5.1 |
| `echarts-gl.min.js` | 2.0.9 |
| `echarts-wordcloud.min.js` | 2.1.0 |
| `echarts-liquidfill.min.js` | 3.1.0 |
| `maps/world.json` | echarts 4.9.0 map pack |
| `maps/usa.json` | apache/echarts-examples |

Provenance: `src/vizly/assets/README.md`.

Smart asset loading: `assets_html(charts=...)` and Django `{% vizly_assets charts=... %}` auto-include GL and plugin scripts when child charts need them.

---

## Integrations

Shared embed contract in `vizly.integrations`. Do not fork embed logic per framework.

| Helper | Output |
|--------|--------|
| `assets_html(charts=…)` | ECharts `<script>` tags for page `<head>` (load once) |
| `chart_html(chart, fragment=, include_assets=, message_origin=)` | Single chart HTML or fragment |
| `dashboard_html(charts, …)` | Many charts, ECharts loaded once; `connect` / `message_origin` |
| `chart_option(chart)` / `chart_json(chart)` | JSON for APIs |

### Embed modes

| Mode | Use case |
|------|----------|
| Full document | Streamlit page, standalone FastAPI response |
| Fragment | Flask/Django templates, HTMX swaps (`include_assets=False` when parent loaded assets) |
| Dashboard | `dashboard_html` / `vz.page` / `st_dashboard` (many charts, one ECharts load, linked by default) |
| JSON | `to_option()` / `to_json()` for SPAs and agents |

### Framework helpers

| Framework | Key entry points |
|-----------|------------------|
| **Streamlit** | `st_vizly(chart)`, `st_dashboard([c1, c2])`, `st_vizly([c1, c2])` |
| **FastAPI** | `html_response`, `json_response`, `dashboard_response` |
| **Flask** | `assets_html`, `chart_html`, `dashboard_response` |
| **Django** | `{% vizly_assets charts=… %}`, `{% vizly_chart … %}`, `{% vizly_dashboard … %}`, `{{ chart\|vizly_html }}` |
| **HTMX** | `htmx_chart_fragment`, `htmx_or_full`, `htmx_event_listener_js` (base package; fragments default `include_assets=False`) |
| **Jupyter** | `_repr_html_()` on chart objects |

Django `vizly_chart` / `vizly_html` default to fragments **without** reloading ECharts. Prefer `st_dashboard` over many single `st_vizly` calls when you need one ECharts load.

```python
from vizly.integrations import assets_html, chart_html, dashboard_html
from vizly.integrations.streamlit import st_vizly, st_dashboard

head = assets_html(charts=[c1, c2])
html = dashboard_html([c1, c2], title="Ops")  # connect=True by default
event = st_vizly(chart, height=420)           # last click payload or None
```

---

## Testing and CI

| Level | Command | Role |
|-------|---------|------|
| L1+L2 (CI gate) | `pytest -m "not browser"` | Contracts + sample/golden HTML |
| L3 Browser | `pytest -m browser` | Headless hero charts (Playwright) |
| Local visual | `python scripts/validate_samples_browser.py --gallery` | Headed Chromium gallery |

Refresh option goldens: `python scripts/update_sample_goldens.py` (or `pytest --update-goldens` when intentional).

Docs showcase (all chart types + Formal v1 features + themes):

```bash
python scripts/build_docs_showcase.py
# → artifacts/docs_showcase/index.html + EXAMPLES.md
```

| Workflow | Trigger | Action |
|----------|---------|--------|
| `ci.yml` | Push/PR to `main` | Lint, L1+L2 tests, coverage, build |
| `browser.yml` | Weekly / `v*` tag / manual | L3 Playwright smoke |
| `release.yml` | `v*` tag or manual | Verify → build → optional TestPyPI/PyPI → GitHub Release |

Full runbook: [TESTING.md](../../TESTING.md). Publish process: [RELEASE.md](../../RELEASE.md).

---

## Examples

| Path | Purpose |
|------|---------|
| `artifacts/docs_showcase/` | Full Formal v1 interactive showcase (rebuild: `python scripts/build_docs_showcase.py`) |
| `examples/streamlit_app.py` | Streamlit (single + dashboard) |
| `examples/fastapi_app.py` | FastAPI HTML/JSON/dashboard |
| `examples/flask_app.py` | Flask + Jinja fragment / dashboard |
| `examples/django_demo/` | Django template tags |
| `examples/htmx_demo/app.py` | HTMX partial swap + events |
| `examples/mapping_dashboard.py` | Map + overlays + linked charts |
| `examples/ingest_demo.py` | CSV / SQL / flowchart ingest |
| `examples/jupyter_gallery.ipynb` | Notebook |
| `examples/themes/atlantic.json` | Custom theme |
| `examples/band_a_gallery.py` / `band_bc_gallery.py` | Chart HTML gallery seeds |

---

## Known limitations

- **SPA / JSON + maps:** `to_option()` / `json_response` return the ECharts option only. They do **not** embed GeoJSON. HTML rendering calls `echarts.registerMap` for you; SPA clients must register map packs themselves (or use HTML embeds).
- **page / tab JSON:** `to_option()` returns a compose descriptor under `_vizly_compose` (child options). Use HTML embeds for browser layout.
- **Flowchart:** process/dependency diagrams, not Mermaid syntax, BPMN, swimlanes, or sequence diagrams.
- **Export:** PNG/JPEG/SVG via browser `toDataURL` / `downloadImage`. No server-side Chromium in vizly.
- **SQL drivers:** vizly depends on SQLAlchemy; install the DBAPI / dialect for your database yourself.
- **Streamlit:** each single-chart `st_vizly` call uses a separate iframe; prefer `st_dashboard` for many charts.

---

## Upgrade notes (any 0.x → 1.0.0)

1. Install or upgrade to `vizly==1.0.0` (pulls `sqlalchemy` and `openpyxl` as direct deps).
2. Prefer loaders / tabular inputs where you previously always built DataFrames by hand.
3. For maps with overlays, use `layers=` / `overlay_geojson`. Do not treat geo layers as `register_map_pack` substitutes for choropleth packs.
4. For images, use client `toDataURL` / `downloadImage` (or external headless on `to_html()`). Do not expect `vizly[export]`.
5. Review default chrome if you relied on earlier title/legend placement; override via theme or `merge_option` if needed.
6. Multi-chart Django/Streamlit pages: load assets once (`{% vizly_assets %}` / `st_dashboard`) and use fragments without reloading ECharts.
7. Run `pytest -m "not browser"` after upgrade (refresh goldens only for intentional option changes).

Preview packaging notes from **0.2.1** (verify gate, GitHub Release on tags, pandas/numpy metadata) remain part of the Formal v1 publish path.

---

## Prior preview releases

Formal **1.0.0** supersedes the 0.x preview line as the supported product surface. Earlier notes remain for history:

| Tag | Notes |
|-----|-------|
| [v0.2.1](../v0.2.1/RELEASE.md) | Packaging / release workflow hardening |
| [v0.2.0](../v0.2.0/RELEASE.md) | Dashboards, smarter assets, test suite, CI |
| 0.1.0 | Initial public preview (see [CHANGELOG](../../CHANGELOG.md)) |

For line-by-line deltas, use [CHANGELOG.md](../../CHANGELOG.md).

---

## Links

- [README](../../README.md): user-facing overview
- [CHANGELOG](../../CHANGELOG.md): full change log
- [TESTING.md](../../TESTING.md): validation runbook
- [RELEASE.md](../../RELEASE.md): publish from GitHub Actions
- [Asset provenance](../../src/vizly/assets/README.md)
