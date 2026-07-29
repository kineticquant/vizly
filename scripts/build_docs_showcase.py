#!/usr/bin/env python3
"""Build one self-contained HTML showcase for docs handoff.

Produces:
  artifacts/docs_showcase/index.html   — all chart types, all builtin themes,
                                         v1 feature demos, interactive ECharts,
                                         Python snippets
  artifacts/docs_showcase/EXAMPLES.md  — same Python snippets for Docusaurus

Does **not** change library runtime code. Uses sample fixtures + small v1 demos.

Rebuild::

    python scripts/build_docs_showcase.py
    python scripts/build_docs_showcase.py --out path/to/dir
"""

from __future__ import annotations

import argparse
import html
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

import vizly as vz  # noqa: E402
from vizly.charts import CHART_TYPES  # noqa: E402
from vizly.geo_layers import overlay_geojson  # noqa: E402
from vizly.integrations import assets_html  # noqa: E402
from vizly.theme.presets import list_presets  # noqa: E402

from tests.samples.fixtures import make_chart, samples_for  # noqa: E402

COMPOSE_MULTI = frozenset({"page", "tab"})
DEFAULT_OUT = ROOT / "artifacts" / "docs_showcase"
CHART_HEIGHT = "420px"
FEATURE_HEIGHT = "480px"


def _df_literal(df: pd.DataFrame) -> str:
    cols = {}
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            cols[col] = [ts.strftime("%Y-%m-%d") for ts in series]
        else:
            cols[col] = [None if pd.isna(v) else v for v in series.tolist()]
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


def _feature_demos(theme: str = "corporate") -> List[Dict[str, Any]]:
    """Build v1 feature showcase entries (id, title, blurb, snippet, chart)."""
    demos: List[Dict[str, Any]] = []

    # --- ingest ---
    csv_text = "region,sales\nEast,42\nWest,31\nNorth,27\n"
    table_csv = vz.from_csv(io.StringIO(csv_text))
    ingest_csv = vz.bar(
        table_csv, x="region", y="sales", title="from_csv → bar", theme=theme, height=FEATURE_HEIGHT
    )
    records = [{"region": "East", "sales": 42}, {"region": "West", "sales": 31}]
    ingest_records = vz.bar(
        vz.from_records(records),
        x="region",
        y="sales",
        title="from_records → bar",
        theme=theme,
        height=FEATURE_HEIGHT,
    )
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sales (region TEXT, amount INTEGER)"))
        conn.execute(
            text("INSERT INTO sales VALUES ('East', 42), ('West', 31), ('North', 27)")
        )
    sql_table = vz.from_sql("SELECT region, amount AS sales FROM sales", bind=engine)
    ingest_sql = vz.bar(
        sql_table,
        x="region",
        y="sales",
        title="from_sql (SQLite) → bar",
        theme=theme,
        height=FEATURE_HEIGHT,
    )
    demos.append(
        {
            "id": "feature-ingest",
            "title": "Data ingest",
            "blurb": "CSV, records, and SQLAlchemy → TabularView → any chart. No caller DataFrame required.",
            "snippet": '''import io
from sqlalchemy import create_engine, text
import vizly as vz

table = vz.from_csv(io.StringIO("region,sales\\nEast,42\\nWest,31\\n"))
vz.bar(table, x="region", y="sales", title="from_csv")

vz.bar(vz.from_records([{"region": "East", "sales": 42}]), x="region", y="sales")

engine = create_engine("sqlite:///:memory:")
# ... create/load tables ...
vz.bar(vz.from_sql("SELECT region, amount AS sales FROM sales", bind=engine),
       x="region", y="sales")
''',
            "charts": [ingest_csv, ingest_records, ingest_sql],
            "compose": False,
        }
    )

    # --- geo layers ---
    demand = [
        {"name": "United States", "value": 86},
        {"name": "Canada", "value": 41},
        {"name": "Brazil", "value": 33},
        {"name": "United Kingdom", "value": 52},
        {"name": "Germany", "value": 47},
        {"name": "India", "value": 61},
        {"name": "Japan", "value": 44},
        {"name": "Australia", "value": 29},
    ]
    sites = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "NYC"},
                "geometry": {"type": "Point", "coordinates": [-74.0, 40.7]},
            },
            {
                "type": "Feature",
                "properties": {"name": "London"},
                "geometry": {"type": "Point", "coordinates": [-0.12, 51.5]},
            },
            {
                "type": "Feature",
                "properties": {"name": "Tokyo"},
                "geometry": {"type": "Point", "coordinates": [139.7, 35.7]},
            },
        ],
    }
    zone = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "North Atlantic box"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-80.0, 25.0], [-10.0, 25.0], [-10.0, 60.0], [-80.0, 60.0], [-80.0, 25.0]]
                    ],
                },
            }
        ],
    }
    geo_chart = vz.map(
        demand,
        layers=[
            overlay_geojson(sites, name="ops_sites", kind="point"),
            overlay_geojson(zone, name="zone", kind="polygon"),
        ],
        title="Choropleth + GeoJSON overlays",
        theme=theme,
        height=FEATURE_HEIGHT,
    )
    demos.append(
        {
            "id": "feature-geo",
            "title": "GeoJSON overlays",
            "blurb": "Basemap packs stay on register_map_pack. Overlays use overlay_geojson / layers= (points, lines, polygons).",
            "snippet": '''import vizly as vz
from vizly.geo_layers import overlay_geojson

layer = overlay_geojson(sites_geojson, name="ops_sites", kind="point")
poly = overlay_geojson(zone_geojson, name="zone", kind="polygon")
vz.map(demand, layers=[layer, poly], title="Demand + overlays")
''',
            "charts": [geo_chart],
            "compose": False,
        }
    )

    # --- mapping dashboard page ---
    by_region = vz.bar(
        [{"region": r["name"], "sales": r["value"]} for r in demand],
        x="region",
        y="sales",
        title="Demand by region",
        theme=theme,
        height="360px",
    )
    map_only = vz.map(
        demand,
        layers=[overlay_geojson(sites, name="ops_sites", kind="point")],
        title="Global demand",
        theme=theme,
        height="360px",
    )
    mapping_page = vz.page(
        charts=[map_only, by_region],
        title="Mapping ops dashboard",
        connect=True,
        theme=theme,
    )
    demos.append(
        {
            "id": "feature-mapping",
            "title": "Mapping dashboard",
            "blurb": "Multi-chart page with map + linked bar (echarts.connect). Region clicks use the vizly:event bridge in host apps.",
            "snippet": '''import vizly as vz
from vizly.geo_layers import overlay_geojson

world = vz.map(demand, layers=[overlay_geojson(sites, kind="point")], title="Global demand")
bars = vz.bar(rows, x="region", y="sales", title="Demand by region")
page = vz.page(charts=[world, bars], title="Mapping ops", connect=True)
page.render("mapping.html")
''',
            "charts": [mapping_page],
            "compose": True,
        }
    )

    # --- events / live / export (single chart + notes) ---
    live_chart = vz.line(
        {
            "date": [f"2026-0{i}-01" for i in range(1, 7)],
            "requests": [120, 140, 135, 160, 175, 190],
        },
        x="date",
        y="requests",
        title="Live update + client image export",
        theme=theme,
        height=FEATURE_HEIGHT,
    )
    demos.append(
        {
            "id": "feature-events-export",
            "title": "Events, live update, image export",
            "blurb": "Clicks emit vizly:event. Refresh with set_data + live_update_script. PNG via browser toDataURL / downloadImage (no Chromium in vizly).",
            "snippet": '''import vizly as vz

chart = vz.line(df, x="date", y="requests", title="Requests")
html = chart.to_html()  # embeds window.__vizly[id]

# After embed in the browser:
#   window.__vizly[id].toDataURL({ type: "png", pixelRatio: 2 })
#   window.__vizly[id].downloadImage("chart.png")
#   window.__vizly[id].setOption(partialOption)

chart.set_data(new_df)
script = chart.live_update_script(chart_id)  # inject without reloading ECharts

# Optional layout / toolbox customize (defaults are overridable):
chart.merge_option({
    "toolbox": {"feature": {"saveAsImage": {"type": "png"}}},
    "legend": {"top": "bottom", "left": "center"},
})
''',
            "charts": [live_chart],
            "compose": False,
            "extra_html": (
                '<p class="feature-note">Open DevTools on this chart mount: '
                "<code>window.__vizly[Object.keys(window.__vizly)[0]].downloadImage('demo.png')</code></p>"
            ),
        }
    )

    # --- chrome customize ---
    chrome = vz.bar(
        {"region": ["A", "B", "C"], "sales": [3, 5, 2], "cost": [1, 2, 1]},
        x="region",
        y=["sales", "cost"],
        title="Custom chrome (legend bottom)",
        theme=theme,
        height=FEATURE_HEIGHT,
    ).merge_option(
        {
            "title": {"left": "center", "top": 4},
            "legend": {"top": "bottom", "left": "center"},
            "grid": {"top": 48, "bottom": 64, "containLabel": True},
        }
    )
    demos.append(
        {
            "id": "feature-chrome",
            "title": "Layout chrome (defaults + overrides)",
            "blurb": "Defaults: title left, legend top-right, cartesian grid padding. Override with theme keys or merge_option — never locked.",
            "snippet": '''chart.merge_option({
    "title": {"left": "center", "top": 0},
    "legend": {"top": "bottom", "left": "center"},
    "grid": {"top": 40, "bottom": 72, "containLabel": True},
})
# Or via theme: register_theme(..., {"legend": {"top": "bottom", "left": "center"}, ...})
''',
            "charts": [chrome],
            "compose": False,
        }
    )

    return demos


def _collect_payload(
    themes: Sequence[str],
) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Any],
    List[Any],
    Dict[str, str],
    List[Dict[str, Any]],
]:
    """Return options matrix, maps, asset seeds, snippets, feature demo payloads."""
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
                clean = dict(opt)
                clean.pop("_vizly_compose", None)
                options[chart_type][theme] = clean
            if theme == themes[0]:
                seeds.append(chart)

    feature_payload: List[Dict[str, Any]] = []
    for demo in _feature_demos(theme="corporate"):
        entry: Dict[str, Any] = {
            "id": demo["id"],
            "title": demo["title"],
            "blurb": demo["blurb"],
            "snippet": demo["snippet"],
            "compose": bool(demo.get("compose")),
            "extra_html": demo.get("extra_html") or "",
            "mounts": [],
        }
        for i, chart in enumerate(demo["charts"]):
            if hasattr(chart, "_ensure_maps"):
                chart._ensure_maps()
            for name, geo in (chart._register_maps or {}).items():
                maps.setdefault(name, geo)
            for child in getattr(chart, "charts", []) or []:
                if hasattr(child, "_ensure_maps"):
                    child._ensure_maps()
                for name, geo in (child._register_maps or {}).items():
                    maps.setdefault(name, geo)
            seeds.append(chart)
            if demo.get("compose") and getattr(chart, "charts", None):
                # Page: expose child options for multi-mount
                child_opts = []
                for child in chart.charts:
                    child_opts.append(child.to_option())
                entry["mounts"].append(
                    {"kind": "compose", "options": child_opts, "labels": [
                        c.title or c.chart_type for c in chart.charts
                    ]}
                )
            else:
                # Prefer HTML-capable option for geo polygons
                opt = chart._option_for_html() if hasattr(chart, "_option_for_html") else chart.to_option()
                entry["mounts"].append({"kind": "single", "option": opt})
        feature_payload.append(entry)
        snippets[demo["id"]] = demo["snippet"]

    return options, maps, seeds, snippets, feature_payload


def _build_html(
    *,
    themes: Sequence[str],
    options: Mapping[str, Mapping[str, Any]],
    maps: Mapping[str, Any],
    seeds: Sequence[Any],
    snippets: Mapping[str, str],
    features: Sequence[Mapping[str, Any]],
) -> str:
    asset_tags = assets_html(charts=list(seeds))
    chart_types = sorted(options.keys())

    chart_nav = "\n".join(
        f'<a href="#chart-{html.escape(ct)}">{html.escape(ct)}</a>'
        for ct in chart_types
    )
    feature_nav = "\n".join(
        f'<a href="#{html.escape(str(f["id"]))}">{html.escape(str(f["title"]))}</a>'
        for f in features
    )
    theme_buttons = "\n".join(
        f'<button type="button" class="theme-btn" data-theme="{html.escape(t)}">'
        f"{html.escape(t)}</button>"
        for t in themes
    )

    feature_sections: List[str] = []
    for feat in features:
        fid = html.escape(str(feat["id"]))
        mounts_html: List[str] = []
        for i, mount in enumerate(feat["mounts"]):
            mid = f"{fid}-m{i}"
            if mount["kind"] == "compose":
                children = []
                for j, _opt in enumerate(mount["options"]):
                    children.append(
                        f'<div class="vizly-chart feature-child" id="{mid}-c{j}" '
                        f'style="width:100%;height:360px;"></div>'
                    )
                mounts_html.append(
                    f'<div class="compose-grid" data-feature-mount="{mid}">'
                    + "".join(children)
                    + "</div>"
                )
            else:
                mounts_html.append(
                    f'<div id="{mid}" class="vizly-chart" '
                    f'style="width:100%;height:{FEATURE_HEIGHT};"></div>'
                )
        code = html.escape(str(feat["snippet"]))
        extra = feat.get("extra_html") or ""
        feature_sections.append(
            f"""
<section class="chart-section feature-section" id="{fid}">
  <header>
    <h2>{html.escape(str(feat["title"]))}</h2>
    <a class="top" href="#top">Top</a>
  </header>
  <p class="blurb">{html.escape(str(feat["blurb"]))}</p>
  {extra}
  <div class="pane">
    <div class="chart-wrap">{"".join(mounts_html)}</div>
    <details open>
      <summary>Python</summary>
      <pre><code>{code}</code></pre>
    </details>
  </div>
</section>
"""
        )

    sections: List[str] = []
    for ct in chart_types:
        code = html.escape(snippets[ct])
        if ct in COMPOSE_MULTI:
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
        "features": features,
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
  <title>vizly v1 showcase</title>
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
    aside .nav-label {{
      margin: 1rem 0 0.35rem;
      font-size: 0.72rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--muted);
    }}
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
    .blurb {{
      margin: 0;
      padding: 0.65rem 1rem;
      color: var(--muted);
      font-size: 0.9rem;
      border-bottom: 1px solid var(--line);
    }}
    .feature-note {{
      margin: 0;
      padding: 0.5rem 1rem;
      font-size: 0.82rem;
      color: var(--muted);
      border-bottom: 1px solid var(--line);
    }}
    .feature-note code {{ color: var(--accent); }}
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
      <h1>vizly v1 showcase</h1>
      <p>Charts · themes · ingest · geo · events · client image export. Local ECharts.</p>
      <div class="nav-label">Features</div>
      <nav>{feature_nav}</nav>
      <div class="nav-label">Charts</div>
      <nav>{chart_nav}</nav>
    </aside>
    <main>
      <div class="toolbar">
        <strong>Theme</strong>
        {theme_buttons}
      </div>
      <h2 id="features" style="margin:0 0 0.75rem;font-size:1.1rem;">v1 features</h2>
      {"".join(feature_sections)}
      <h2 id="charts" style="margin:1.5rem 0 0.75rem;font-size:1.1rem;">Chart types</h2>
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

    function applyPolygons(option) {{
      var polys = option && option._vizly_geo_polygons;
      if (option && option._vizly_geo_polygons) {{ delete option._vizly_geo_polygons; }}
      if (option && option._vizly_layer_maps) {{ delete option._vizly_layer_maps; }}
      if (!polys || !polys.length) {{ return option; }}
      var series = (option.series || []).slice();
      for (var i = 0; i < polys.length; i++) {{
        (function (poly) {{
          series.push({{
            type: "custom",
            name: poly.name || "overlay",
            coordinateSystem: "geo",
            zlevel: poly.zlevel != null ? poly.zlevel : 2,
            data: [{{ name: poly.name || "overlay", value: 0 }}],
            renderItem: function (params, api) {{
              var rings = poly.rings || [];
              if (!rings.length || !rings[0] || !rings[0].length) {{ return null; }}
              var children = [];
              for (var r = 0; r < rings.length; r++) {{
                var pts = [];
                var ring = rings[r];
                for (var p = 0; p < ring.length; p++) {{
                  pts.push(api.coord(ring[p]));
                }}
                children.push({{
                  type: "polygon",
                  shape: {{ points: pts }},
                  style: {{
                    fill: poly.fill || "rgba(47, 111, 237, 0.28)",
                    stroke: poly.stroke || "#2F6FED",
                    lineWidth: poly.lineWidth != null ? poly.lineWidth : 1.5
                  }}
                }});
              }}
              return {{ type: "group", children: children }};
            }}
          }});
        }})(polys[i]);
      }}
      option.series = series;
      return option;
    }}

    function setChart(id, option) {{
      var el = document.getElementById(id);
      if (!el || !option) return;
      if (!instances[id]) {{
        instances[id] = echarts.init(el, null, {{ locale: "EN" }});
      }}
      var opt = JSON.parse(JSON.stringify(option));
      applyPolygons(opt);
      instances[id].clear();
      instances[id].setOption(opt, true);
      window.__vizly = window.__vizly || {{}};
      window.__vizly[id] = {{
        chart: instances[id],
        setOption: function (o, notMerge) {{ instances[id].setOption(o, notMerge === true); }},
        resize: function () {{ instances[id].resize(); }},
        toDataURL: function (opts) {{
          return instances[id].getDataURL(opts || {{ type: "png", pixelRatio: 2 }});
        }},
        downloadImage: function (filename, opts) {{
          var url = this.toDataURL(opts);
          var a = document.createElement("a");
          a.href = url;
          a.download = filename || "vizly-chart.png";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return url;
        }}
      }};
    }}

    function applyFeatures() {{
      (data.features || []).forEach(function (feat) {{
        (feat.mounts || []).forEach(function (mount, i) {{
          var mid = feat.id + "-m" + i;
          if (mount.kind === "compose") {{
            (mount.options || []).forEach(function (opt, j) {{
              setChart(mid + "-c" + j, opt);
            }});
          }} else {{
            setChart(mid, mount.option);
          }}
        }});
      }});
    }}

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
            if (opts[i]) {{
              el.style.display = "";
              setChart(id, opts[i]);
            }} else {{
              el.style.display = "none";
            }}
          }}
          return;
        }}
        setChart("vizly-" + chartType, bag);
      }});
      // Feature demos stay on corporate seed options (stable demos).
      applyFeatures();
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


def _build_examples_md(
    snippets: Mapping[str, str],
    themes: Sequence[str],
    features: Sequence[Mapping[str, Any]],
) -> str:
    lines = [
        "# vizly chart examples",
        "",
        "Generated by `scripts/build_docs_showcase.py`.",
        f"Builtin themes: {', '.join(themes)}.",
        "Interactive HTML: `index.html` (theme switcher + live charts + v1 features).",
        "",
        "## v1 features",
        "",
    ]
    for feat in features:
        lines.append(f"### {feat['title']}")
        lines.append("")
        lines.append(str(feat["blurb"]))
        lines.append("")
        lines.append("```python")
        lines.append(str(feat["snippet"]).rstrip())
        lines.append("```")
        lines.append("")
    lines.append("## Chart types")
    lines.append("")
    for chart_type in sorted(k for k in snippets if not str(k).startswith("feature-")):
        lines.append(f"## `{chart_type}`")
        lines.append("")
        lines.append("```python")
        lines.append(snippets[chart_type])
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args(argv)
    themes = list_presets()
    options, maps, seeds, snippets, features = _collect_payload(themes)
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
            features=features,
        ),
        encoding="utf-8",
    )
    md_path.write_text(_build_examples_md(snippets, themes, features), encoding="utf-8")
    size_mb = html_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {html_path} ({size_mb:.1f} MiB)")
    print(f"Wrote {md_path}")
    print(
        f"Charts: {len(options)} · Features: {len(features)} · Themes: {', '.join(themes)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
