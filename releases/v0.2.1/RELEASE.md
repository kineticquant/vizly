# vizly v0.2.1

**Release date:** 2026-07-28  
**Python:** 3.9 or later (CI: 3.9-3.13)  
**Runtime deps:** `pandas`, `numpy` only (no pyecharts)

vizly v0.2.1 includes the full v0.2.0 feature set. vizly is a fully themable, low-boilerplate charting library over Apache ECharts. Ship production charts in a few lines of Python (DataFrame in, HTML or JSON out) with high performance (local assets, one ECharts load per page) and native embeds for Streamlit, FastAPI, Flask, Django, HTMX, and Jupyter. Trusted defaults: no Chinese CDN forced in the backend (unlike many other Python ECharts wrappers). Worldwide maps by default.

---

## Highlights (new since v0.1.0)

1. **Multi-chart dashboards**: load ECharts once per page across Streamlit, Django, Flask, FastAPI, and HTMX.
2. **Smarter asset loading**: `assets_html(charts=...)` and Django `{% vizly_assets charts=... %}` auto-include GL and plugin scripts when child charts need them.
3. **Public map introspection**: `list_bundled_maps()` and `list_opt_in_maps()` document bundled vs opt-in geography.
4. **Three-level test suite**: contract tests, sample/golden option snapshots, and Playwright browser smoke.
5. **GitHub Actions CI and release**: lint, pytest with coverage, build on every PR; TestPyPI/PyPI publish on version tags.
6. **Locale and asset trust refinements**: theme `locale` passed to `echarts.init`; trust scanner checks `<script src>` hosts only.

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

**Base lifecycle:** data standardization → `_build()` → theme apply → user merge → export.

---

## Chart inventory

**39 registered types.** Use `vz.list_chart_types()` and `vz.list_unavailable_chart_types()`.

`line`, `bar`, `area`, `scatter`, `pie`, `donut`, `boxplot`, `heatmap`, `candlestick`, `kline`, `radar`, `funnel`, `gauge`, `sankey`, `treemap`, `map`, `grid`, `mix`, `combo`, `effect_scatter`, `waterfall`, `polar`, `parallel`, `sunburst`, `tree`, `graph`, `wordcloud`, `geo`, `bar3d`, `line3d`, `scatter3d`, `page`, `tab`, `timeline`, `pictorial_bar`, `theme_river`, `liquid`, `surface3d`

### Upstream unavailable

`chord`: ECharts 5.x no longer ships a first-class chord series; use `sankey` or `graph` instead.

### Compose charts

`grid`, `page`, `tab`, and `timeline` take `charts=` instead of `data=`. `page` / `tab` `to_option()` returns a compose descriptor under `_vizly_compose` (child options). Use HTML embeds for browser layout.

---

## Theming

### Builtin presets

`default`, `light`, `dark`, `corporate`, `minimal`, `contrast`, `ops_grafana`, `ops_cloudwatch`, `ops_kibana`

Ops presets are visual inspiration only, not affiliated with Grafana Labs, AWS, or Elastic.

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

---

## Data layer

| Function | Purpose |
|----------|---------|
| `standardize(data)` | Normalize DataFrame-like input |
| `infer_roles(df, …)` | Infer x/y/series column roles |
| `DataError` | Raised on invalid data at trust boundaries |

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

---

## Maps and geography

| Item | Detail |
|------|--------|
| Default atlas | **World** (`vz.map(df)`) |
| Bundled regional | `usa` (`vz.map(df, map="usa")`) |
| Opt-in packs | `register_map_pack(name, geojson_path)` for custom GeoJSON you supply |
| Introspection | `list_bundled_maps()`, `list_opt_in_maps()` |
| Low-level | `load_map_geojson(name)`, `map_path(name)` |

Extra regional map packs are **not** bundled by default. Register them when you need them.

**SPA / JSON note:** `to_option()` / `json_response` return the ECharts option only. HTML rendering calls `echarts.registerMap` for you; SPA clients must register map packs themselves.

---

## Trust and assets

| Rule | Detail |
|------|--------|
| Default mode | `assets.mode = "local"` (vendored JS inlined or linked from package) |
| Optional CDN | Allowlist only: `cdn.jsdelivr.net`, `unpkg.com` |
| Banned by default | China-primary CDN hosts (bootcdn, npmmirror, assets.pyecharts.org, …) |
| Plugin loading | GL, wordcloud, liquidfill load **only** when the chart needs them |
| Trust scanner | Checks `<script src>` hosts only (not option JSON labels) |

### Pinned vendored assets

| File | Version |
|------|---------|
| `echarts.min.js` | 5.5.1 |
| `echarts-gl.min.js` | 2.0.9 |
| `echarts-wordcloud.min.js` | 2.1.0 |
| `echarts-liquidfill.min.js` | 3.1.0 |
| `maps/world.json` | echarts 4.9.0 map pack |
| `maps/usa.json` | apache/echarts-examples |

Provenance: `src/vizly/assets/README.md`.

---

## Integrations

Shared embed contract in `vizly.integrations`:

| Helper | Output |
|--------|--------|
| `assets_html(charts=…)` | ECharts `<script>` tags for page `<head>` (load once) |
| `chart_html(chart, fragment=, include_assets=)` | Single chart HTML or fragment |
| `dashboard_html(charts, …)` | Many charts, ECharts loaded once |
| `chart_option(chart)` / `chart_json(chart)` | JSON for APIs |

### Embed modes

| Mode | Use case |
|------|----------|
| Full document | Streamlit page, standalone FastAPI response |
| Fragment | Flask/Django templates, HTMX swaps (`include_assets=False` when parent loaded assets) |
| Dashboard | `dashboard_html` / `vz.page` / `st_dashboard` (many charts, one ECharts load) |
| JSON | `to_option()` / `to_json()` for SPAs and agents |

### Framework helpers

| Framework | Key entry points |
|-----------|------------------|
| **Streamlit** | `st_vizly(chart)`, `st_dashboard([c1, c2])`, `st_vizly([c1, c2])` |
| **FastAPI** | `html_response`, `json_response`, `dashboard_response` |
| **Flask** | `assets_html`, `chart_html`, `dashboard_response` |
| **Django** | `{% vizly_assets charts=… %}`, `{% vizly_chart … %}`, `{% vizly_dashboard … %}`, `{{ chart\|vizly_html }}` |
| **HTMX** | `htmx_chart_fragment`, `htmx_or_full` in the base package (no `vizly[htmx]` extra; fragments default `include_assets=False`) |
| **Jupyter** | `_repr_html_()` on chart objects |

Django `vizly_chart` / `vizly_html` default to fragments **without** reloading ECharts.

Install extras: `vizly[streamlit]`, `vizly[fastapi]`, `vizly[flask]`, `vizly[django]`, `vizly[examples]`. HTMX helpers ship in the base package (no `vizly[htmx]` extra).

Examples: `examples/streamlit_app.py`, `fastapi_app.py`, `flask_app.py`, `django_demo/`, `htmx_demo/app.py`, `jupyter_gallery.ipynb`.

---

## Changes since v0.1.0 (detail)

### Added

- Streamlit `st_dashboard` / multi-chart `st_vizly([...])` (one iframe, ECharts once)
- Django `{% vizly_dashboard %}`; `{% vizly_assets charts=... %}` auto GL/plugins
- `assets_html(charts=...)` aggregates GL/plugin needs for shell pages
- Public `list_bundled_maps` / `list_opt_in_maps`
- GitHub Actions CI (lint, pytest + coverage on core modules, build) for Python 3.9-3.13
- Release workflow scaffolding for TestPyPI / PyPI on version tags
- Level 2 sample / golden chart suite (`tests/samples/`, committed `goldens/options/`)
- Level 3 Playwright hero-chart browser smoke (`tests/browser/`, `vizly[browser]`)
- `scripts/update_sample_goldens.py`, `scripts/validate_samples_browser.py`, and `TESTING.md` runbook
- `pytest --update-goldens` for intentional golden refreshes

### Changed

- Theme `locale` (default `en-US`) passed to `echarts.init` as `EN` / `ZH`
- Django `vizly_chart` / `vizly_html` default to fragments without reloading ECharts
- Trust scanner checks `<script src>` hosts only (not option JSON labels)
- Metrics helpers warn and set `DataFrame.attrs['vizly_skipped']` when dropping bad rows
- Page/tab `to_option()` compose payload no longer includes a fake empty `series` stub
- Wording aligned to ease-of-use / performance / worldwide maps / native integrations (trusted asset defaults; no Chinese CDN forced)

---

## Testing and CI

| Level | Command | Role |
|-------|---------|------|
| L1+L2 (CI gate) | `pytest -m "not browser"` | Contracts + sample/golden HTML |
| L3 Browser | `pytest -m browser` | Headless hero charts (Playwright) |
| Local visual | `python scripts/validate_samples_browser.py --gallery` | Headed Chromium gallery |

| Workflow | Trigger | Action |
|----------|---------|--------|
| `ci.yml` | Push/PR to `main` | Lint, L1+L2 tests, coverage, build |
| `browser.yml` | Weekly / `v*` tag / manual | L3 Playwright smoke |
| `release.yml` | `v*` tag or manual | Build + optional TestPyPI/PyPI publish |

Full runbook: [TESTING.md](../../TESTING.md). Release process: [RELEASE.md](../../RELEASE.md).

---

## Install

```bash
pip install vizly
```

From a source checkout (contributors):

```bash
pip install -e ".[dev,examples]"
```

Optional extras: `dev`, `browser`, `streamlit`, `fastapi`, `flask`, `django`, `examples`.

HTMX helpers (`vizly.integrations.htmx`) ship in the base package. No `vizly[htmx]` extra.

---

## Known limitations

- **PNG/PDF export**: `vizly[export]` is deferred; use `to_html()` / `to_option()` meanwhile.
- **SPA JSON + maps**: client must call `echarts.registerMap` for map/geo charts.
- **Streamlit**: each `st_vizly` single-chart call uses a separate iframe; prefer `st_dashboard` for many charts.

---

## Upgrade from v0.1.0

1. Bump is semver-minor. No breaking API removals documented.
2. If you embed multiple charts in Django templates, adopt `{% vizly_assets charts=… %}` once in `<head>` and rely on fragment defaults on `{% vizly_chart %}`.
3. If you use Streamlit dashboards, switch multi-chart pages to `st_dashboard` or `st_vizly([...])`.
4. Run `pytest -m "not browser"` after upgrade to confirm option goldens still match (or refresh with `pytest --update-goldens` if you intentionally changed themes).

---

## Links

- [README](../../README.md): user-facing overview
- [CHANGELOG](../../CHANGELOG.md): full change log
- [TESTING.md](../../TESTING.md): validation runbook
- [Asset provenance](../../src/vizly/assets/README.md)

---

## Changes in v0.2.1 (packaging and release)

Patch release focused on packaging metadata and a safer publish path. Product API and chart behavior match v0.2.0.

### Added

- Release workflow **verify gate** (ruff + Level 1/2 pytest) before build/publish
- **GitHub Release** on `v*` tags (CHANGELOG body + `dist/` artifacts)
- Packaging contract tests: `__version__` sync with `pyproject.toml`; runtime requires `pandas` and `numpy`

### Changed

- PyPI / package summary: high-performance, low-boilerplate, fully-themable charting over Apache ECharts (local assets, native web embeds)
- Declare runtime dependencies `pandas` and `numpy` in package metadata (Browser CI and bare installs no longer miss them)
- Release workflow **fails** when `ENABLE_PYPI_PUBLISH` is not set (no silent skipped upload)

### Upgrade from v0.2.0

1. Install or upgrade to `vizly==0.2.1`.
2. No chart API changes. Confirm install pulls `pandas` and `numpy` as direct dependencies.
3. Maintainers: tag `v0.2.1` to run verify → build → PyPI → GitHub Release.
