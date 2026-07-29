# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-07-29

Formal **v1** distribution. Same product surface as the 1.0.0 notes.

### Changed

- Version **1.0.1** (distribution fixes)
- Official notes: [releases/v1.0.1/RELEASE.md](releases/v1.0.1/RELEASE.md)

## [1.0.0] - 2026-07-28

Formal **v1** product surface (documented here). Prefer **1.0.1** for installs from PyPI.

Formal **v1** release of vizly: high-performance, low-boilerplate, fully themable charting over Apache ECharts with native embeds, multi-source data ingest, drill/events, flowchart, expanded themes, mapping dashboards, geo-layer overlays, live update, linked brush, and browser-side image export.

### Added

#### Data ingest (TabularView spine)

- `TabularView` protocol + `as_tabular` / `ColumnarTable` — charts work without a caller-built DataFrame
- Loaders (base package): `from_csv`, `from_tsv`, `from_json`, `from_excel`, `from_records`, `from_columnar`, `from_sql`
- SQLAlchemy is a **base** dependency (no `vizly[sql]` extra). DBAPI drivers remain the caller's install
- Optional duck-typed Polars / Arrow inputs when those packages are present
- `filter_tabular` / `filter_by_click` for categorical and map drill paths

#### Data → chart conversion paths (complete list)

**In-process / Python shapes**

- pandas `DataFrame`
- `list[dict]` (records)
- `dict[str, sequence]` (columnar)
- Optional Polars DataFrame / Arrow table (duck-typed; not hard dependencies)

**Files / text**

- CSV (`from_csv`)
- TSV (`from_tsv`)
- JSON (`from_json`)
- Excel (`from_excel`, openpyxl)

**Ops JSON normalizers**

- Prometheus API JSON (`from_prometheus`)
- CloudWatch datapoints / MetricDataResults (`from_cloudwatch`)
- Elasticsearch / ELK search & aggregation JSON (`from_elasticsearch` / `from_elk`)

**SQL via SQLAlchemy**

- Any SQLAlchemy `Engine`, `Connection`, or URL string + SQL statement via `from_sql`

#### SQLAlchemy database coverage

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

#### Charts, themes, maps, interaction

- `vz.flowchart` (+ `vz.diagram` alias) — process/dependency diagrams via ECharts graph (not Mermaid)
- Editor-inspired themes: `editor_monokai`, `editor_tokyo_night`, `editor_dracula`, `editor_nord`, `editor_solarized_light`, `editor_solarized_dark`, `editor_one_dark`
- GeoJSON overlay path (`overlay_geojson` / `GeoLayer`) segregated from `register_map_pack`
- Map join keys: `name_field`, `id_field`; `layers=` on `vz.map` / `vz.geo`
- Click/drill event bridge (`vizly:event` + `postMessage`); Streamlit component return; HTMX `htmx_event_listener_js`
- `set_data` / `set_option_patch`; embed `window.__vizly[id].setOption` for live update
- Linked brush / shared tooltip via `echarts.connect` on `page` / `dashboard_html` (`connect=True` default)
- Browser image export: `window.__vizly[id].toDataURL` / `downloadImage` (ECharts `getDataURL`); optional toolbox `saveAsImage`. No `vizly[export]` / Chromium in-package.
- `chart.live_update_script(chart_id)` for partial option push without re-embed
- Geo polygon overlays: outline lines + HTML custom fill series; shared `geo` roam with choropleth when `layers=` is set
- Click `postMessage` defaults to same-origin; Streamlit opts into `"*"` for the component bridge

#### Examples

- `examples/mapping_dashboard.py`, `examples/ingest_demo.py`
- Docs showcase builder for v1 features: `python scripts/build_docs_showcase.py`

### Changed

- Version **1.0.0** (product surface; distribution continues as **1.0.1**)
- Base dependencies: `pandas`, `numpy`, `sqlalchemy`, `openpyxl`
- Data layer centers on TabularView; `standardize()` remains as DataFrame escape hatch
- Default chart chrome: title left, legend top-right, cartesian plot `grid` padding (`containLabel`). Override via theme `title`/`legend` keys or `merge_option` (not locked).
- Map series options include `nameProperty` when join fields are set
- Page compose descriptor includes `connect`

### Trust / assets (pinned for this release)

| Asset | Version | Hosting |
|-------|---------|---------|
| `echarts.min.js` | **5.5.1** | Vendored (jsDelivr source) |
| `echarts-gl.min.js` | **2.0.9** | Vendored; loaded only for 3D |
| `echarts-wordcloud.min.js` | **2.1.0** | Vendored; wordcloud only |
| `echarts-liquidfill.min.js` | **3.1.0** | Vendored; liquid only |
| Maps | `world` + `usa` | Bundled GeoJSON |

CDN mode (optional) allowlists `cdn.jsdelivr.net` and `unpkg.com` only.

## [0.2.1] - 2026-07-28

### Added
- Release workflow verify gate (ruff + Level 1/2 pytest) before build/publish
- GitHub Release on ``v*`` tags (CHANGELOG body + ``dist/`` artifacts)
- Packaging contract tests: ``__version__`` sync with ``pyproject.toml``; runtime requires ``pandas`` and ``numpy``

### Changed
- PyPI / package summary: high-performance, low-boilerplate, fully-themable charting over Apache ECharts (local assets, native web embeds)
- Declare runtime dependencies ``pandas`` and ``numpy`` in package metadata
- Release workflow fails when ``ENABLE_PYPI_PUBLISH`` is not set (no silent skipped upload)

## [0.2.0] - 2026-07-28

### Added
- Streamlit ``st_dashboard`` / multi-chart ``st_vizly([...])`` (one iframe, ECharts once)
- Django ``{% vizly_dashboard %}``; ``{% vizly_assets charts=... %}`` auto GL/plugins
- ``assets_html(charts=...)`` aggregates GL/plugin needs for shell pages
- Public ``list_bundled_maps`` / ``list_opt_in_maps``
- GitHub Actions CI (lint, pytest + coverage on core modules, build) for Python 3.9-3.13
- Release workflow scaffolding for TestPyPI / PyPI on version tags
- Level 2 sample / golden chart suite (`tests/samples/`, committed `goldens/options/`, gitignored `artifacts/html/`)
- Level 3 Playwright hero-chart browser smoke (`tests/browser/`, `vizly[browser]`, nightly/tag workflow)
- `scripts/update_sample_goldens.py`, `scripts/validate_samples_browser.py`, and [TESTING.md](TESTING.md) validation runbook
- `pytest --update-goldens` for intentional golden refreshes

### Changed
- Theme ``locale`` (default ``en-US``) is passed to ``echarts.init`` as ``EN`` / ``ZH``
- Django ``vizly_chart`` / ``vizly_html`` default to fragments **without** reloading ECharts
- Trust scanner checks ``<script src>`` hosts only (not option JSON labels)
- Metrics helpers warn and set ``DataFrame.attrs['vizly_skipped']`` when dropping bad rows
- Page/tab ``to_option()`` compose payload no longer includes a fake empty ``series`` stub
- Wording aligned to ease-of-use / performance / worldwide maps / native integrations (trusted asset defaults; no Chinese CDN forced)

### Trust / assets (pinned for this release)

| Asset | Version | Hosting |
|-------|---------|---------|
| `echarts.min.js` | **5.5.1** | Vendored (jsDelivr source) |
| `echarts-gl.min.js` | **2.0.9** | Vendored; loaded only for 3D |
| `echarts-wordcloud.min.js` | **2.1.0** | Vendored; wordcloud only |
| `echarts-liquidfill.min.js` | **3.1.0** | Vendored; liquid only |
| Maps | `world` + `usa` | Bundled GeoJSON |

CDN mode (optional) allowlists `cdn.jsdelivr.net` and `unpkg.com` only.

## [0.1.0] - 2026-07-27

Initial public preview of **vizly**: fully themable, low-boilerplate charting over Apache ECharts. Easy DataFrame API, high performance, worldwide maps by default, and native web-stack embeds.

### Added
- Theme engine (presets, registry, deep-merge, per-chart override)
- Data layer + `BaseChart` + trust-safe HTML/JSON renderer (local assets default)
- Full chart matrix Bands A-C (`list_chart_types()`); `chord` documented upstream-unavailable
- Integrations: Streamlit, FastAPI, Flask, Django template tags, HTMX fragments
- Ops metric helpers: `from_prometheus`, `from_cloudwatch`, `from_elasticsearch` / `from_elk`
- Worldwide map atlas by default; bundled `usa` regional pack; extra packs via `register_map_pack`

### Trust / assets (pinned for this release)

| Asset | Version | Hosting |
|-------|---------|---------|
| `echarts.min.js` | **5.5.1** | Vendored (jsDelivr source) |
| `echarts-gl.min.js` | **2.0.9** | Vendored; loaded only for 3D |
| `echarts-wordcloud.min.js` | **2.1.0** | Vendored; wordcloud only |
| `echarts-liquidfill.min.js` | **3.1.0** | Vendored; liquid only |
| Maps | `world` + `usa` | Bundled GeoJSON |

CDN mode (optional) allowlists `cdn.jsdelivr.net` and `unpkg.com` only.

### Notes
- Preview quality; APIs may still evolve before 1.0
