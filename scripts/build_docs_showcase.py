#!/usr/bin/env python3
"""Build one self-contained HTML showcase for docs handoff.

Produces:
  artifacts/docs_showcase/index.html   — all chart types, all builtin themes,
                                         interactive ECharts, Python snippets
  artifacts/docs_showcase/EXAMPLES.md  — same Python snippets for Docusaurus

Does **not** change library runtime code. Uses sample fixtures only.

Usage::

    python scripts/build_docs_showcase.py
    python scripts/build_docs_showcase.py --out path/to/dir
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

import vizly as vz  # noqa: E402
from vizly.charts import CHART_TYPES  # noqa: E402
from vizly.integrations import assets_html  # noqa: E402
from vizly.theme.presets import list_presets  # noqa: E402

from tests.samples.fixtures import make_chart, samples_for  # noqa: E402

COMPOSE_MULTI = frozenset({"page", "tab"})
DEFAULT_OUT = ROOT / "artifacts" / "docs_showcase"
CHART_HEIGHT = "420px"


def _df_literal(df: pd.DataFrame) -> str:
    cols = {}
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            cols[col] = [ts.strftime("%Y-%m-%d") for ts in series]
        else:
            cols[col] = [None if pd.isna(v) else v for v in series.tolist()]
    # Prefer a compact constructor when values are simple.
    return f"pd.DataFrame({_py_literal(cols)})"


def _py_literal(value: Any, *, indent: int = 0) -> str:
    pad = "    " * indent
    if isinstance(value, pd.DataFrame):
        return _df_literal(value)
    if isinstance(value, Mapping):
        if not value:
            return "{}"
        lines = ["{"]
        for key, item in value.items():
            lines.append(f"{pad}    {key!r}: {_py_literal(item, indent=indent + 1)},")
        lines.append(f"{pad}}}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return "[]"
        if all(not isinstance(v, (dict, list, pd.DataFrame)) for v in value):
            return repr(value)
        lines = ["["]
        for item in value:
            lines.append(f"{pad}    {_py_literal(item, indent=indent + 1)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)
    if isinstance(value, tuple):
        return repr(value)
    return repr(value)


def _python_snippet(chart_type: str, theme: str = "corporate") -> str:
    """Readable Python that rebuilds the sample chart."""
    if chart_type in ("grid", "page", "tab", "timeline"):
        return _compose_snippet(chart_type, theme)

    kwargs = dict(samples_for(chart_type))
    lines = [
        "import pandas as pd",
        "import vizly as vz",
        "",
    ]
    call_parts: List[str] = []
    data = kwargs.pop("data", None)
    if data is not None:
        lines.append(f"df = {_df_literal(data)}")
        call_parts.append("df")
    for key, value in kwargs.items():
        call_parts.append(f"{key}={_py_literal(value)}")
    call_parts.append(f"theme={theme!r}")
    joined = ",\n    ".join(call_parts)
    lines.append(f"chart = vz.{chart_type}(")
    lines.append(f"    {joined},")
    lines.append(")")
    lines.append("# chart.render(\"chart.html\")  # or chart.to_html() / st_vizly(chart)")
    return "\n".join(lines)


def _compose_snippet(chart_type: str, theme: str) -> str:
    """Fully expanded compose examples using the same fixture data."""
    lines = ["import pandas as pd", "import vizly as vz", "", f"vz.set_theme({theme!r})", ""]
    if chart_type == "grid":
        parts = []
        for name in ("line", "bar", "area", "scatter"):
            kw = dict(samples_for(name))
            data = kw.pop("data")
            var = f"df_{name}"
            lines.append(f"{var} = {_df_literal(data)}")
            args = ", ".join(
                [var] + [f"{k}={_py_literal(v)}" for k, v in kw.items()]
            )
            parts.append(f"vz.{name}({args})")
        lines.append(
            "chart = vz.grid(\n    charts=[\n        "
            + ",\n        ".join(parts)
            + ",\n    ],\n    title=\"Grid showcase\",\n)"
        )
    elif chart_type == "page":
        parts = []
        for name in ("line", "pie", "map"):
            kw = dict(samples_for(name))
            data = kw.pop("data")
            var = f"df_{name}"
            lines.append(f"{var} = {_df_literal(data)}")
            args = ", ".join(
                [var] + [f"{k}={_py_literal(v)}" for k, v in kw.items()]
            )
            parts.append(f"vz.{name}({args})")
        lines.append(
            "chart = vz.page(\n    charts=[\n        "
            + ",\n        ".join(parts)
            + ",\n    ],\n    title=\"Page showcase\",\n)"
        )
    elif chart_type == "tab":
        parts = []
        for name in ("bar", "pie", "radar"):
            kw = dict(samples_for(name))
            data = kw.pop("data")
            var = f"df_{name}"
            lines.append(f"{var} = {_df_literal(data)}")
            args = ", ".join(
                [var] + [f"{k}={_py_literal(v)}" for k, v in kw.items()]
            )
            parts.append(f"vz.{name}({args})")
        lines.append(
            "chart = vz.tab(\n    charts=[\n        "
            + ",\n        ".join(parts)
            + ",\n    ],\n    title=\"Tab showcase\",\n)"
        )
    else:  # timeline
        line_kw = dict(samples_for("line"))
        line_df = line_kw["data"]
        lines.append(f"df = {_df_literal(line_df)}")
        lines.append(
            "chart = vz.timeline(\n"
            "    charts=[\n"
            "        vz.line(df, x=\"date\", y=\"revenue\", title=\"Revenue\"),\n"
            "        vz.line(df, x=\"date\", y=\"cost\", title=\"Cost\"),\n"
            "        vz.mix(df, x=\"date\", bar=\"cost\", line=\"revenue\", title=\"Combined\"),\n"
            "    ],\n"
            "    title=\"Timeline showcase\",\n"
            ")"
        )
    lines.append("# chart.render(\"chart.html\")")
    return "\n".join(lines)


def _collect_payload(
    themes: Sequence[str],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any], List[Any], Dict[str, str]]:
    """Return options matrix, maps, asset seed charts, python snippets."""
    options: Dict[str, Dict[str, Any]] = {}
    maps: Dict[str, Any] = {}
    seeds: List[Any] = []
    snippets: Dict[str, str] = {}

    for chart_type in sorted(CHART_TYPES):
        snippets[chart_type] = _python_snippet(chart_type, theme="corporate")
        options[chart_type] = {}
        for theme in themes:
            chart = make_chart(chart_type, theme=theme, height=CHART_HEIGHT)
            if hasattr(chart, "_ensure_maps"):
                chart._ensure_maps()
            for name, geo in (chart._register_maps or {}).items():
                maps.setdefault(name, geo)
            # Also collect maps from compose children.
            for child in getattr(chart, "charts", []) or []:
                if hasattr(child, "_ensure_maps"):
                    child._ensure_maps()
                for name, geo in (child._register_maps or {}).items():
                    maps.setdefault(name, geo)
            opt = chart.to_option()
            if chart_type in COMPOSE_MULTI:
                compose = opt.get("_vizly_compose") or {}
                options[chart_type][theme] = {
                    "_compose": compose.get("type"),
                    "options": compose.get("options") or [],
                }
            else:
                # Drop internal markers that ECharts does not need.
                clean = dict(opt)
                clean.pop("_vizly_compose", None)
                options[chart_type][theme] = clean
            if theme == themes[0]:
                seeds.append(chart)
    return options, maps, seeds, snippets


def _build_html(
    *,
    themes: Sequence[str],
    options: Mapping[str, Mapping[str, Any]],
    maps: Mapping[str, Any],
    seeds: Sequence[Any],
    snippets: Mapping[str, str],
) -> str:
    asset_tags = assets_html(charts=list(seeds))
    chart_types = sorted(options.keys())
    nav = "\n".join(
        f'<a href="#chart-{html.escape(ct)}">{html.escape(ct)}</a>'
        for ct in chart_types
    )
    theme_buttons = "\n".join(
        f'<button type="button" class="theme-btn" data-theme="{html.escape(t)}">'
        f"{html.escape(t)}</button>"
        for t in themes
    )

    sections: List[str] = []
    for ct in chart_types:
        code = html.escape(snippets[ct])
        if ct in COMPOSE_MULTI:
            # Multiple child mounts filled by JS from compose options.
            mounts = (
                f'<div class="compose-grid" data-chart-type="{html.escape(ct)}">'
                f'<div class="vizly-chart compose-child" id="vizly-{html.escape(ct)}-0" '
                f'style="width:100%;height:{CHART_HEIGHT};"></div>'
                f'<div class="vizly-chart compose-child" id="vizly-{html.escape(ct)}-1" '
                f'style="width:100%;height:{CHART_HEIGHT};"></div>'
                f'<div class="vizly-chart compose-child" id="vizly-{html.escape(ct)}-2" '
                f'style="width:100%;height:{CHART_HEIGHT};"></div>'
                f"</div>"
            )
        else:
            mounts = (
                f'<div id="vizly-{html.escape(ct)}" class="vizly-chart" '
                f'data-chart-type="{html.escape(ct)}" '
                f'style="width:100%;height:{CHART_HEIGHT};"></div>'
            )
        sections.append(
            f"""
<section class="chart-section" id="chart-{html.escape(ct)}">
  <header>
    <h2>{html.escape(ct)}</h2>
    <a class="top" href="#top">Top</a>
  </header>
  <div class="pane">
    <div class="chart-wrap">{mounts}</div>
    <details open>
      <summary>Python</summary>
      <pre><code>{code}</code></pre>
    </details>
  </div>
</section>
"""
        )

    payload = {
        "themes": list(themes),
        "defaultTheme": "corporate" if "corporate" in themes else themes[0],
        "options": options,
        "composeMulti": sorted(COMPOSE_MULTI),
    }
    payload_json = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace(
        "</", "<\\/"
    )
    maps_json = json.dumps(maps, ensure_ascii=False, allow_nan=False).replace(
        "</", "<\\/"
    )

    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>vizly chart showcase</title>
  <style>
    :root {{
      --bg: #0f1419;
      --panel: #171d25;
      --text: #e7ecf3;
      --muted: #9aa7b8;
      --accent: #3db8a0;
      --line: #2a3442;
      --code: #0b1016;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .layout {{
      display: grid;
      grid-template-columns: 220px 1fr;
      min-height: 100vh;
    }}
    aside {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: var(--panel);
      padding: 1rem;
    }}
    aside h1 {{ font-size: 1.05rem; margin: 0 0 0.35rem; }}
    aside p {{ color: var(--muted); font-size: 0.82rem; margin: 0 0 1rem; }}
    aside nav {{ display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.86rem; }}
    main {{ padding: 1.25rem 1.5rem 3rem; }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
      padding: 0.75rem 0;
      margin-bottom: 1rem;
      background: linear-gradient(var(--bg), var(--bg) 80%, transparent);
    }}
    .toolbar strong {{ margin-right: 0.35rem; }}
    .theme-btn {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      border-radius: 6px;
      padding: 0.35rem 0.65rem;
      cursor: pointer;
    }}
    .theme-btn.active, .theme-btn:hover {{
      border-color: var(--accent);
      color: #fff;
    }}
    .chart-section {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel);
      margin-bottom: 1.25rem;
      overflow: hidden;
    }}
    .chart-section header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid var(--line);
    }}
    .chart-section h2 {{ margin: 0; font-size: 1.05rem; }}
    .pane {{ display: grid; grid-template-columns: 1.2fr 1fr; gap: 0; }}
    @media (max-width: 1100px) {{
      .layout {{ grid-template-columns: 1fr; }}
      aside {{ position: relative; height: auto; }}
      .pane {{ grid-template-columns: 1fr; }}
    }}
    .chart-wrap {{ padding: 0.75rem; background: #11161d; }}
    .compose-grid {{ display: grid; gap: 0.75rem; }}
    details {{ border-left: 1px solid var(--line); }}
    summary {{
      cursor: pointer;
      padding: 0.65rem 0.9rem;
      color: var(--muted);
      border-bottom: 1px solid var(--line);
    }}
    pre {{
      margin: 0;
      padding: 0.9rem;
      overflow: auto;
      max-height: 420px;
      background: var(--code);
      font-size: 0.78rem;
      line-height: 1.4;
    }}
    code {{ font-family: ui-monospace, Consolas, monospace; }}
  </style>
</head>
<body>
  <div class="layout" id="top">
    <aside>
      <h1>vizly showcase</h1>
      <p>All chart types · all builtin themes · local ECharts. Copy Python from each section for docs.</p>
      <nav>{nav}</nav>
    </aside>
    <main>
      <div class="toolbar">
        <strong>Theme</strong>
        {theme_buttons}
      </div>
      {"".join(sections)}
    </main>
  </div>
  {asset_tags}
  <script>
  window.__VIZLY_SHOWCASE__ = {payload_json};
  window.__VIZLY_MAPS__ = {maps_json};
  </script>
  <script>
  (function () {{
    var data = window.__VIZLY_SHOWCASE__;
    var maps = window.__VIZLY_MAPS__ || {{}};
    var instances = {{}};
    var composeMulti = {{}};
    (data.composeMulti || []).forEach(function (t) {{ composeMulti[t] = true; }});

    Object.keys(maps).forEach(function (name) {{
      echarts.registerMap(name, maps[name]);
    }});

    function applyTheme(theme) {{
      document.querySelectorAll(".theme-btn").forEach(function (btn) {{
        btn.classList.toggle("active", btn.getAttribute("data-theme") === theme);
      }});
      Object.keys(data.options).forEach(function (chartType) {{
        var bag = data.options[chartType][theme];
        if (!bag) return;
        if (composeMulti[chartType]) {{
          var opts = bag.options || [];
          for (var i = 0; i < 3; i++) {{
            var id = "vizly-" + chartType + "-" + i;
            var el = document.getElementById(id);
            if (!el) continue;
            if (!instances[id]) instances[id] = echarts.init(el, null, {{locale: "EN"}});
            if (opts[i]) {{
              el.style.display = "";
              instances[id].clear();
              instances[id].setOption(opts[i], true);
            }} else {{
              el.style.display = "none";
            }}
          }}
          return;
        }}
        var el = document.getElementById("vizly-" + chartType);
        if (!el) return;
        if (!instances[chartType]) {{
          instances[chartType] = echarts.init(el, null, {{locale: "EN"}});
        }}
        instances[chartType].clear();
        instances[chartType].setOption(bag, true);
      }});
      window.__VIZLY_ACTIVE_THEME__ = theme;
    }}

    document.querySelectorAll(".theme-btn").forEach(function (btn) {{
      btn.addEventListener("click", function () {{
        applyTheme(btn.getAttribute("data-theme"));
      }});
    }});

    window.addEventListener("resize", function () {{
      Object.keys(instances).forEach(function (key) {{
        instances[key].resize();
      }});
    }});

    applyTheme(data.defaultTheme);
  }})();
  </script>
</body>
</html>
"""


def _build_examples_md(snippets: Mapping[str, str], themes: Sequence[str]) -> str:
    lines = [
        "# vizly chart examples",
        "",
        "Generated by `scripts/build_docs_showcase.py`.",
        f"Builtin themes: {', '.join(themes)}.",
        "Interactive HTML: `index.html` (theme switcher + live charts).",
        "",
    ]
    for chart_type in sorted(snippets):
        lines.append(f"## `{chart_type}`")
        lines.append("")
        lines.append("```python")
        lines.append(snippets[chart_type])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args(argv)
    themes = list_presets()
    options, maps, seeds, snippets = _collect_payload(themes)
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / "index.html"
    md_path = out_dir / "EXAMPLES.md"
    html_path.write_text(
        _build_html(
            themes=themes,
            options=options,
            maps=maps,
            seeds=seeds,
            snippets=snippets,
        ),
        encoding="utf-8",
    )
    md_path.write_text(_build_examples_md(snippets, themes), encoding="utf-8")
    size_mb = html_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {html_path} ({size_mb:.1f} MiB)")
    print(f"Wrote {md_path}")
    print(f"Charts: {len(options)} · Themes: {', '.join(themes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
