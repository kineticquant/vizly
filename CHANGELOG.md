# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Streamlit ``st_dashboard`` / multi-chart ``st_vizly([...])`` (one iframe, ECharts once)
- Django ``{% vizly_dashboard %}``; ``{% vizly_assets charts=... %}`` auto GL/plugins
- ``assets_html(charts=...)`` aggregates GL/plugin needs for shell pages
- Public ``list_bundled_maps`` / ``list_opt_in_maps``
- GitHub Actions CI (lint, pytest + coverage on core modules, build) for Python 3.9–3.13
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
- Wording aligned to English-first / trusted software chain (worldwide maps by default)

## [0.1.0] — 2026-07-27

Initial public preview of **vizly**: English-first, fully themable charting over Apache ECharts.

### Added
- Theme engine (presets, registry, deep-merge, per-chart override)
- Data layer + `BaseChart` + trust-safe HTML/JSON renderer (local assets default)
- Full chart matrix Bands A–C (`list_chart_types()`); `chord` documented upstream-unavailable
- Integrations: Streamlit, FastAPI, Flask, Django template tags, HTMX fragments
- Ops metric helpers: `from_prometheus`, `from_cloudwatch`, `from_elasticsearch` / `from_elk`
- Worldwide map atlas by default; bundled `usa` regional pack; China packs opt-in only

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
- Runtime depends on `pandas` + `numpy` only (no pyecharts dependency).
- `vizly[export]` (PNG/PDF snapshot) is deferred.

[Unreleased]: https://github.com/kineticquant/vizly/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kineticquant/vizly/releases/tag/v0.1.0
