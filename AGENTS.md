# AGENTS.md — vizly

Guidance for AI agents and human contributors who work in this repository.

Lead with the next action. Keep answers short. Number multi-step work. Restate state across turns. Suppress tangents. Give specific time estimates when useful. Make wins visible.

---

## 1. Project overview

**vizly** is a Python charting library over Apache ECharts. It targets teams that need:

- Low-boilerplate, fully themable charts
- High performance (local assets, one ECharts load per page, lean option builds)
- **Native** embeds in Streamlit, Django, FastAPI, Flask, HTMX, and Jupyter
- A **trusted software chain** (no China-primary CDN defaults; English-first APIs/docs)

Public intent and user-facing claims live in [README.md](README.md). Keep agent work aligned with that document. Do not invent product goals that the README does not support.

Maintainer: Kineticquant. Package layout: `src/vizly/` (setuptools `src` layout). Python: **3.9–3.13**.

---

## 2. End goal (critical)

### 2.1 Product outcome

Ship a **highly performant**, low-boilerplate visualization library that feels **native** inside common Python web stacks — not a thin wrapper that dumps raw option dicts and leaves host apps to invent embed logic.

Native integration is **strictly critical**. High performance is **strictly critical**. Prefer:

- Shared embed contract (`vizly.integrations._embed`) used by every framework helper
- Full document vs fragment vs dashboard vs JSON modes (see README Integrations)
- **One** ECharts asset load for multi-chart pages (`assets_html` / `dashboard_html` / `vz.page`)
- Vendored JS by default; optional CDN only on allowlisted hosts

### 2.2 Trusted software chain (non-negotiable)

vizly exists partly because similar provider libraries default to China-primary CDNs and maps. Preserve this trust posture:

| Rule | Detail |
|------|--------|
| Default assets | Local / vendored `echarts*.js` under `src/vizly/assets/` |
| Optional CDN | Allowlist only: `cdn.jsdelivr.net`, `unpkg.com` |
| Banned by default | bootcdn, npmmirror, assets.pyecharts.org, Baidu Map, and similar |
| Maps | Bundled `world` + `usa`; China administrative packs **opt-in** via `register_map_pack` only |
| Language | English APIs, docs, and errors (`en-US` chrome) |

Provenance: `src/vizly/assets/README.md`. Trust behavior: `src/vizly/render.py`, theme/CDN schema, contract tests.

**Never** reintroduce blocked hosts, silent remote script injection, or China-primary defaults. Treat trust regressions as release blockers.

### 2.3 Performance expectations

- Cache vendored JS in memory where the codebase already does
- Load GL / wordcloud / liquidfill plugins **only** when the chart needs them
- Avoid duplicate asset tags on dashboards and HTMX swaps (`include_assets=False` when the parent already loaded assets)
- Prefer small, JSON-serializable options; do not ship speculative option bloat

---

## 3. Architecture (for agents)

```
src/vizly/
  api.py              # Public chart factories (vz.line, vz.bar, …)
  base.py             # BaseChart lifecycle: build → theme → update → export
  data.py             # TabularView spine / role inference
  loaders.py          # CSV/TSV/JSON/Excel/SQL/records → TabularView
  events.py           # Click/drill payloads + live-update + client image helpers
  export.py           # Client export docs/helpers (getDataURL; no Chromium)
  config.py           # Session theme get/set/resolve
  render.py           # HTML embed + trusted local/CDN assets + maps
  maps.py             # Basemap pack registration (choropleth)
  geo_layers.py       # GeoJSON overlays (segregated from map packs)
  metrics.py          # Prometheus / CloudWatch / Elasticsearch payload normalizers
  charts/             # Chart builders by family (cartesian, geo, gl3d, …)
  theme/              # Presets, registry, merge, apply, schema (CDN allowlist)
  integrations/       # Shared embed + Streamlit, FastAPI, Flask, Django, HTMX
  assets/             # Vendored JS + map GeoJSON
examples/             # Framework demos (keep in sync with integration APIs)
tests/                # Contract + samples + browser suites
goldens/options/      # Committed to_option() snapshots
scripts/              # Golden update + browser gallery validation
```

**Flow (typical chart):**

1. Caller uses `vz.<chart>(df, …)` from `api.py`
2. Chart subclass in `charts/` implements `_build()` → structural ECharts option
3. `BaseChart` applies theme chrome and user merges
4. Export: `to_option()` / `to_json()` / `to_html()` via `render.py`
5. Frameworks call `integrations._embed` (`chart_html`, `assets_html`, `dashboard_html`, …)

**Do not** fork embed logic per framework. Extend the shared contract, then thin wrappers.

**Export:** Browser `toDataURL` / `downloadImage` via `window.__vizly`. No in-package Chromium. SQL/file loaders and geo layers are **base** library — do not add `vizly[sql]` or similar.

---

## 4. Use cases

Agents should optimize for these real uses:

1. **Ops / observability UIs** — normalize Prometheus, CloudWatch, or Elasticsearch JSON (`metrics.py`), then chart with ops-inspired themes
2. **Streamlit apps** — `st_vizly(chart)` with local assets
3. **FastAPI** — HTML responses, JSON option endpoints, dashboards
4. **Flask / Django templates** — fragments + `{% vizly_assets %}` / `{% vizly_chart %}`
5. **HTMX** — partial swaps without reloading ECharts (`include_assets=False` by default on fragments)
6. **Jupyter** — `_repr_html_()` gallery notebooks
7. **API / agent pipelines** — `to_option()` / `to_json()` for SPA or LLM tool output (note: maps need client-side `registerMap` for JSON-only paths)
8. **Themed product charts** — builtins + `register_theme` / JSON theme files

Examples under `examples/` are the reference implementations. Prefer matching those patterns over inventing new embed shapes.

---

## 5. Testing guidance

**Source of truth:** [TESTING.md](TESTING.md). Read it before you change tests, goldens, browser scripts, or CI markers.

| Level | Command (typical) | Role |
|-------|-------------------|------|
| L1+L2 CI gate | `python -m pytest -m "not browser"` | Contracts + sample/golden HTML |
| L3 Browser | `python -m pytest -m browser` | Headless hero charts (Playwright) |
| Local visual | `python scripts/validate_samples_browser.py --gallery` | Headed Chromium + gallery |

Refresh option goldens only when intentional: `python scripts/update_sample_goldens.py`.

**Rules for agents:**

- After behavior changes that affect options or HTML trust, run at least the CI gate (`not browser`) unless the change is docs-only
- Do not update goldens to “make tests pass” without stating why the option change is correct
- Browser tests are not a per-commit gate; still run them when you touch `render.py`, assets, or embed scripts
- Packaging / extras: see `pyproject.toml` (`dev`, `browser`, `examples`, framework extras)

---

## 6. Engineering rules

### 6.1 Senior-developer posture

Work as a senior engineer: efficient, precise, and surgical. Small diffs that look simple are often correct. That is not low achievement — it is discipline. Prefer the smallest change that fully solves the requested problem.

### 6.2 Stop at the first run that holds

Before you write code, walk this ladder. Stop at the first step that solves the need:

1. **Must this exist at all?** Apply YAGNI when relevant — but still ensure the library handles major edge cases users will hit in production charts and embeds.
2. **Does the Python standard library already do it?** Use it, or build a thin layer on top of it.
3. **Does a native platform feature cover it?** Use Streamlit / Django / FastAPI / Flask / HTMX / ECharts features and integrate them into this source.
4. **Does an already-installed dependency solve it?** Use it. Do not add a new package.
5. **Can this be one line?** Make it one line.
6. **Only then** write the minimum code that works.

### 6.3 Code hygiene

- Practice DRY. One function, prompt, taxonomy, or list owns each behavior.
- Add no abstraction that was not explicitly requested.
- Add no dependency when the platform, standard library, or an installed dependency is enough.
- Add no boilerplate, speculative extension point, compatibility layer, or fallback nobody asked for.
- Prefer deletion over addition. Prefer boring code over clever code.
- Fewer lines may be better.
- Avoid cascading or repetitive fallbacks. Multiple fallback levels for one edge case often mean over-design.
- Question complex requests: “Do you actually need X, or does Y cover it?”
- Avoid extremely long function names. Use clear domain terms. Do not encode the whole implementation in the name.
- Split new functions into focused modules when ownership needs it. Do not grow huge Python files (for example, 10,000+ lines).
- Commentary is not required, but may help. **Never strip existing commentary.** If comments become wrong, update them and keep useful context.
- When an intentional simplification has a known scaling or correctness ceiling, mark that ceiling in the code.

### 6.4 Validation, errors, and fallbacks

Never be lazy about:

- Input validation at trust boundaries
- Error handling that prevents data loss
- Security
- Accessibility
- Real-hardware calibration (when applicable)
- Anything the user explicitly requested

That does **not** authorize validation and fallback clutter in every internal helper.

A fallback must have:

1. A specific failure mode
2. A safe result
3. Observable log or metadata
4. A test

Otherwise fail clearly.

Do **not** use:

- Blanket `except Exception: pass`
- Silent empty config
- Generic best-effort fallbacks that hide a broken required path

### 6.5 Documentation language (ADS-STE100)

Use **ADS-STE100 Simplified Technical English** for any and all documentation you write or edit (README, TESTING, RELEASE, CHANGELOG notes, module docs intended for humans, this file, and similar).

If you find docs in README or other project `.md` files that do not follow these standards, update them as part of relevant work.

**Do not** edit implementation-plan Markdown under `.working_sessions/`.

### 6.6 See something, say something

If you find stale code, duplicated behavior, divergent lists, an unsafe fallback, a security or data-loss risk, or unnecessary complexity, report it with:

1. File or component
2. Concrete impact
3. Smallest recommended direction

Do **not** silently fix unrelated findings or expand the requested task. Findings are still required even when they stay out of scope.

---

## 7. Communication with humans

Developers may skim or misread dense text. Shape output for a reader with ADHD:

1. Lead with the **next action** when possible
2. Number multi-step work
3. Restate state across turns (“Done: X. Next: Y.”)
4. Suppress tangents
5. Give specific time estimates when useful
6. Make wins visible

---

## 8. Final handoff (required every turn that changes the repo)

Every final handoff must briefly state, combined naturally (no empty boilerplate headings):

1. **What changed**
2. **Tests/checks run and results**
3. **What was tested and why**
4. **Performance or operational implications** (or say briefly if none)
5. **Repository debt noticed while working** (required; if none, say none)

If one item is genuinely inapplicable, say so in one short clause instead of adding empty sections.

---

## 9. Quick pointers

| Need | Go here |
|------|---------|
| Product / API story | [README.md](README.md) |
| How to validate | [TESTING.md](TESTING.md) |
| Release process | [RELEASE.md](RELEASE.md) |
| Version history | [CHANGELOG.md](CHANGELOG.md) |
| Asset provenance | `src/vizly/assets/README.md` |
| Shared embeds | `src/vizly/integrations/_embed.py` |
| Trust / CDN / HTML | `src/vizly/render.py` |

Do not treat `.working_sessions/` plans as user-facing docs or edit them under the STE rule above.
