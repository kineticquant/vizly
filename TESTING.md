# Testing & validation guide (vizly)

This document is the maintainer / contributor runbook for **how to validate vizly** locally and in CI. It covers contract tests, sample/golden charts, browser rendering checks, lint/coverage, packaging checks, and release confidence.

If you only need a quick command, jump to [Quick start](#quick-start). For “does this chart actually draw in a browser?”, see [Level 3](#level-3--browser--visual-validation) and [Local visible sample review](#local-visible-sample-review-recommended).

---

## Table of contents

1. [Mental model](#mental-model)
2. [Quick start](#quick-start)
3. [Prerequisites & extras](#prerequisites--extras)
4. [Level 1 — Contract suite](#level-1--contract-suite)
5. [Level 2 — Sample / golden charts](#level-2--sample--golden-charts)
6. [Level 3 — Browser / visual validation](#level-3--browser--visual-validation)
7. [Local visible sample review (recommended)](#local-visible-sample-review-recommended)
8. [Lint, coverage, and packaging](#lint-coverage-and-packaging)
9. [Integration & examples smoke](#integration--examples-smoke)
10. [What CI runs](#what-ci-runs)
11. [What “verified” means](#what-verified-means)
12. [Updating goldens safely](#updating-goldens-safely)
13. [Troubleshooting](#troubleshooting)
14. [Command cheat sheet](#command-cheat-sheet)

---

## Mental model

vizly’s tests are intentionally **multi-level**. Pytest alone cannot prove that Apache ECharts drew pixels in a browser.

| Level | Proves | Browser? | Required on every PR? |
|-------|--------|----------|------------------------|
| **L1 Contract** | API shape, themes, data layer, trust policy, JSON-serializable options | No | **Yes** |
| **L2 Samples + goldens** | Every registered chart builds from fixed data; `to_option()` matches committed goldens; HTML is self-contained / trust-safe | No (generates HTML files) | **Yes** |
| **L3 Browser** | Sample HTML loads in Chromium; `echarts.init` works; canvas/SVG present; no console errors | Yes (usually headless) | **No** — release / weekly / manual |
| **Local review script** | Same HTML checks as L3, optionally in a **visible** window + click-through gallery | Yes | Optional — for humans |

**Important distinction**

- **`goldens/options/*.json`** — checked-in snapshots of `to_option()` (dict/JSON). Compared by pytest. **Not** opened in a browser.
- **`artifacts/html/*.html`** — generated self-contained chart pages (gitignored). **These** are what browsers load for visual / render validation.

---

## Quick start

From the repo root, with a virtualenv recommended:

```bash
# Install package + test tools
pip install -e ".[dev,examples]"

# Default CI-like gate (Level 1 + Level 2; skip Playwright)
python -m pytest -m "not browser" -q

# Visible browser validation of sample HTML (all charts, theme=default)
pip install -e ".[browser]"
python -m playwright install chromium
python scripts/validate_samples_browser.py --gallery
```

---

## Prerequisites & extras

| Extra | Install | Purpose |
|-------|---------|---------|
| (core) | `pip install -e .` | Runtime: pandas, numpy, sqlalchemy, openpyxl |
| `dev` | `pip install -e ".[dev]"` | pytest, coverage, ruff, build, twine (mypy optional; not a CI gate) |
| `examples` | `pip install -e ".[examples]"` | Streamlit / FastAPI / Flask / Django for integration tests |
| `browser` | `pip install -e ".[browser]"` | Playwright for Level 3 + local review script |

PNG/JPEG export uses the browser embed (`toDataURL` / `downloadImage`), not a package extra.

After installing `browser`:

```bash
python -m playwright install chromium
# On Linux CI we also use: python -m playwright install --with-deps chromium
```

**Python versions:** 3.9–3.13 are CI targets (`requires-python >= 3.9`).

---

## Level 1 — Contract suite

**Purpose:** Fast, deterministic checks with no network and no browser.

**Location:** `tests/` (excluding sample/browser-marked suites when deselected)

**Typical command:**

```bash
# Fast gate only (skip samples + browser)
python -m pytest -m "not samples and not browser" -v

# Or everything except browser (includes Level 2 — what CI runs)
python -m pytest -m "not browser" -q
```

### What it covers

- Theme merge / registry / CDN allowlist
- Data standardization + role inference
- `to_option()` / `to_json()` smoke across registered chart types
- Local HTML asset markers; banned-host regressions
- English error messages; public API (`__all__`) audit
- Integrations (Streamlit helpers, FastAPI/Flask/Django/HTMX embeds) when extras are installed
- Metrics helpers (`from_prometheus`, `from_cloudwatch`, `from_elasticsearch` / `from_elk`)

### Pass criteria

Green pytest; no flaky network; no Chromium required.

---

## Level 2 — Sample / golden charts

**Purpose:** Generate **real chart artifacts** from fixed tiny datasets so humans and CI verify more than dict shape.

**Layout:**

```text
tests/samples/
  fixtures.py                 # deterministic kwargs per chart type
  normalize.py                # stable JSON canonicalization
  paths.py                    # goldens/ + artifacts/ paths
  test_sample_charts.py       # builds every registered type × themes
goldens/
  options/                    # COMMITTED — to_option() JSON goldens
  README.md
artifacts/                    # GITIGNORED — generated HTML
  html/
    <chart>__<theme>.html
scripts/
  update_sample_goldens.py    # rewrite option goldens
```

**Themes exercised:** `default` and `dark`  
**Chart coverage:** every key in `vizly.charts.CHART_TYPES` (Bands A–C)

### Run Level 2

```bash
python -m pytest -m samples -v
```

Each sample test:

1. Builds the chart with fixed sample data (`tests/samples/fixtures.py`)
2. Writes `artifacts/html/<chart>__<theme>.html` (local/vendored ECharts, no banned hosts)
3. Compares `to_option()` to `goldens/options/<chart>__<theme>.json`
4. Asserts structural truths (series present, map `registerMap` when relevant, GL/plugin markers, sane HTML size)

### Refresh option goldens

Only after **intentional** theme or option-structure changes:

```bash
python scripts/update_sample_goldens.py
# equivalent:
python -m pytest -m samples --update-goldens -q
```

Then review the diff under `goldens/options/` and commit with a note explaining why options changed.

### Pass criteria

All Band A/B/C sample charts generate; goldens match unless deliberately refreshed.

---

## Level 3 — Browser / visual validation

**Purpose:** Prove ECharts actually initializes and charts are visually sane enough for release confidence.

**Location:** `tests/browser/test_hero_charts.py`  
**Mark:** `@pytest.mark.browser`  
**Cadence:** Not a required per-commit gate (cost + environment). CI runs this on a separate workflow.

### Hero set (automated pytest)

| Chart | Why |
|-------|-----|
| `line` | Core cartesian |
| `bar` | Core cartesian |
| `pie` | Non-cartesian |
| `map` | Bundled GeoJSON / `registerMap` |
| `mix` | Multi-series composition |

Theme: `default`.

```bash
pip install -e ".[dev,browser]"
python -m playwright install chromium
python -m pytest -m browser -v
```

**What each test asserts**

1. Sample HTML file exists under `artifacts/html/`
2. Page loads in Chromium (`file://` URI)
3. `echarts` global is present; canvas or SVG exists with non-zero size
4. An ECharts instance is attached to a vizly chart root
5. No page errors / console errors (favicon noise filtered)

Default pytest run is **headless** (no visible window).

### Pass criteria (minimum)

Sample HTML loads; `echarts.init` succeeds; no console errors; hero set reviewed for theme/trust look before release (see local review below).

---

## Local visible sample review (recommended)

Use this when you want to **watch** charts render, click through the matrix, or validate more than the hero set.

**Script:** [`scripts/validate_samples_browser.py`](scripts/validate_samples_browser.py)

It validates the generated **HTML** (not the JSON goldens) by driving Chromium with the same render checks as Level 3.

### One-time setup

```bash
pip install -e ".[dev,browser]"
python -m playwright install chromium
```

### Recommended commands

```bash
# Visible Chromium window — all registered chart types, theme=default
python scripts/validate_samples_browser.py

# Same checks + open a click-through gallery in your system browser
python scripts/validate_samples_browser.py --gallery

# Slow walkthrough so you can watch each chart
python scripts/validate_samples_browser.py --gallery --pause-ms 800

# Hero set only (faster)
python scripts/validate_samples_browser.py --hero

# Both themes (default + dark)
python scripts/validate_samples_browser.py --all-themes

# Force regenerate HTML before validating
python scripts/validate_samples_browser.py --rebuild

# Headless (CI-style, no window)
python scripts/validate_samples_browser.py --headless --hero
```

### Flags reference

| Flag | Meaning |
|------|---------|
| `--hero` | Only `line`, `bar`, `pie`, `map`, `mix` |
| `--all-themes` | Validate `default` and `dark` |
| `--theme NAME` | Single theme when not using `--all-themes` (default: `default`) |
| `--headless` | No Chromium window |
| `--gallery` | Write `artifacts/html/index.html` and open it with the system browser |
| `--pause-ms N` | Wait N ms between charts (useful with headed mode) |
| `--rebuild` | Always regenerate HTML before checks |

### Gallery

With `--gallery`, the script writes `artifacts/html/index.html`: a sidebar of links and an iframe preview. That file is gitignored with the rest of `artifacts/`. Open it anytime after samples have been generated:

```bash
python -m pytest -m samples -q   # ensure HTML exists
# then open artifacts/html/index.html after running with --gallery
# or: python scripts/validate_samples_browser.py --gallery
```

### Exit codes

- `0` — all selected pages rendered successfully  
- `1` — one or more pages failed validation  
- `2` — Playwright not installed  

---

## Lint, coverage, and packaging

### Ruff

```bash
ruff check src/vizly tests
# scripts are also fine to include:
ruff check src/vizly tests scripts
```

### Coverage (core modules)

CI enforces ≥70% on theme / data / base / api:

```bash
coverage run --source=vizly -m pytest -q -m "not browser"
coverage report \
  --include='*/vizly/theme/*,*/vizly/data.py,*/vizly/base.py,*/vizly/api.py' \
  --fail-under=70
```

### Build + metadata (pre-release)

```bash
python -m pip install --upgrade build twine
python -m build
twine check dist/*
```

See [RELEASE.md](RELEASE.md) for tagging / PyPI Trusted Publishing.

---

## Integration & examples smoke

Unit/integration coverage for embeds lives under `tests/test_integrations_*.py` and runs with Level 1 when `.[examples]` is installed.

Manual / demo scripts (not CI gates):

| Path | Notes |
|------|-------|
| `examples/band_a_gallery.py` | Writes Band A HTML under `examples/_gallery_out/` |
| `examples/band_bc_gallery.py` | Band B/C samples |
| `examples/streamlit_app.py` | Streamlit helper demo |
| `examples/fastapi_app.py` / `flask_app.py` / `django_demo/` / `htmx_demo/` | Web embed demos |

These are useful for product demos; prefer Level 2/3 + `validate_samples_browser.py` for systematic validation.

---

## What CI runs

| Workflow | Trigger | What |
|----------|---------|------|
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | Push/PR to `main` | Ruff; pytest `-m "not browser"` (L1+L2); coverage gate; build/twine on 3.12; uploads `artifacts/html` |
| [`.github/workflows/browser.yml`](.github/workflows/browser.yml) | Weekly schedule, `v*` tags, `workflow_dispatch` | Playwright hero smoke (L3); uploads hero HTML |
| [`.github/workflows/release.yml`](.github/workflows/release.yml) | `v*` tags / manual | Build + optional TestPyPI/PyPI publish |

**Downloading CI sample HTML:** open the CI run → artifact `vizly-sample-html` → unzip and open files locally (or point `validate_samples_browser.py` at a regenerated tree).

---

## What “verified” means

Use these labels when talking about chart quality:

| Label | Meaning |
|-------|---------|
| **Contract-tested** | Level 1 covers the type / behavior |
| **Sample-verified** | Level 2 generated HTML + option golden for `default` and at least one alternate theme (`dark`) |
| **Visually verified** | Level 3 or `validate_samples_browser.py` has loaded the HTML in Chromium at least once for that type (hero set may be a subset) |

A PR that only changes docs does not need L3. A PR that changes theme defaults or series option structure **must** refresh goldens deliberately (see below).

---

## Updating goldens safely

1. Make your code/theme change.
2. Run Level 1 + Level 2 without updating:

   ```bash
   python -m pytest -m "not browser" -q
   ```

3. If golden mismatches are expected, regenerate:

   ```bash
   python scripts/update_sample_goldens.py
   ```

4. Inspect `git diff goldens/options/` — confirm only intended keys changed.
5. Optionally re-validate HTML in a browser:

   ```bash
   python scripts/validate_samples_browser.py --rebuild --gallery
   ```

6. Commit goldens with a message that explains **why** options changed (not only “update goldens”).

Do **not** commit `artifacts/html/` (gitignored; large duplicated vendored JS).

---

## Troubleshooting

### `Missing golden …`

Generate and commit goldens:

```bash
python scripts/update_sample_goldens.py
```

### Golden mismatch you did not expect

Do **not** blind-update. Diff the JSON; fix the library bug if the new option is wrong.

### Browser tests skipped / Playwright missing

```bash
pip install -e ".[browser]"
python -m playwright install chromium
```

### `validate_samples_browser.py` exit code 2

Playwright package not importable — install the `browser` extra (above).

### Console errors in Chromium

Read the FAIL line from the script. Common causes: missing plugin asset for wordcloud/liquid, GL not loaded for 3D, or a JS exception in compose (`page` / `tab`) HTML. Re-run with `--rebuild` after fixing render code.

### Sample HTML missing

```bash
python -m pytest -m samples -q
# or
python scripts/validate_samples_browser.py --rebuild
```

### Tests too slow locally

```bash
python -m pytest -m "not samples and not browser" -q   # L1 only
python scripts/validate_samples_browser.py --hero      # small browser set
```

### Banned host / trust failures

Local HTML must embed vendored assets and must not reference China-primary CDN substrings. See `vizly.render.BANNED_HOST_SUBSTRINGS` and Level 1/2 HTML assertions.

---

## Command cheat sheet

```bash
# Install
pip install -e ".[dev,examples]"
pip install -e ".[browser]" && python -m playwright install chromium

# Level 1 only (fast)
python -m pytest -m "not samples and not browser" -q

# Level 1 + 2 (CI gate)
python -m pytest -m "not browser" -q

# Level 2 only
python -m pytest -m samples -v

# Update option goldens
python scripts/update_sample_goldens.py

# Level 3 hero (headless)
python -m pytest -m browser -v

# Visible full-matrix HTML validation + gallery
python scripts/validate_samples_browser.py --gallery --pause-ms 600

# Lint + coverage + package check
ruff check src/vizly tests
coverage run --source=vizly -m pytest -q -m "not browser"
coverage report --include='*/vizly/theme/*,*/vizly/data.py,*/vizly/base.py,*/vizly/api.py' --fail-under=70
python -m build && twine check dist/*
```

---

## Related docs

| Doc | Role |
|-----|------|
| [README.md](README.md) | Product overview + short testing pointer |
| [RELEASE.md](RELEASE.md) | Version bumps, tags, PyPI publish |
| [CHANGELOG.md](CHANGELOG.md) | User-facing changes / asset pins |
| [goldens/README.md](goldens/README.md) | Short note on option golden files |
| [`.github/workflows/ci.yml`](.github/workflows/ci.yml) | L1+L2 CI |
| [`.github/workflows/browser.yml`](.github/workflows/browser.yml) | L3 CI |

---

*When in doubt: run `pytest -m "not browser"` before opening a PR, and run `python scripts/validate_samples_browser.py --gallery` before cutting a release.*
