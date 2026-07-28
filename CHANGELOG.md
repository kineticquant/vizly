# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Runtime depends on `pandas` + `numpy` only (no pyecharts dependency).
- `vizly[export]` (PNG/PDF snapshot) is deferred.

[Unreleased]: https://github.com/kineticquant/vizly/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/kineticquant/vizly/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/kineticquant/vizly/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kineticquant/vizly/releases/tag/v0.1.0
