"""Deterministic sample kwargs for every registered chart type.

Shared by Level 1 smoke tests and Level 2 sample/golden suite.
Data is sized to look like a product gallery, not a 3-point stub.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

import vizly as vz


def _xyz() -> pd.DataFrame:
    """Small 4x4 surface for 3D charts (deterministic, visually dense)."""
    rows = []
    for i, x in enumerate((-1.0, -0.3, 0.4, 1.0)):
        for j, y in enumerate((-1.0, -0.3, 0.4, 1.0)):
            z = float(np.sin(x * 2.1) * np.cos(y * 1.7) + 0.15 * (i - j))
            rows.append({"x": x, "y": y, "z": round(z, 3)})
    return pd.DataFrame(rows)


def samples_for(chart_type: str) -> Dict[str, Any]:
    """Return kwargs for ``vz.chart(chart_type, **kwargs)`` with fixed showcase data."""
    line_df = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=14, freq="D"),
            "revenue": [42, 48, 45, 61, 58, 72, 68, 81, 76, 90, 84, 95, 88, 102],
            "cost": [18, 20, 19, 24, 22, 28, 26, 31, 29, 34, 32, 37, 35, 40],
        }
    )
    bar_df = pd.DataFrame(
        {
            "region": ["Northeast", "Southeast", "Midwest", "Southwest", "West", "Canada"],
            "sales": [86, 64, 71, 58, 93, 47],
        }
    )
    rng = np.random.default_rng(42)
    scatter_n = 36
    scatter_df = pd.DataFrame(
        {
            "height": np.round(1.55 + rng.random(scatter_n) * 0.4, 3),
            "weight": np.round(52 + rng.random(scatter_n) * 48, 1),
        }
    )
    pie_df = pd.DataFrame(
        {
            "name": ["Enterprise", "Mid-market", "SMB", "Startup", "Partner"],
            "value": [34, 26, 18, 12, 10],
        }
    )
    box_rows = []
    for group, center, spread in (
        ("Alpha", 62, 8),
        ("Beta", 71, 11),
        ("Gamma", 55, 14),
        ("Delta", 78, 9),
    ):
        for offset in (-18, -10, -4, 0, 3, 7, 12, 16, 22):
            box_rows.append({"group": group, "score": center + int(offset * spread / 12)})
    box_df = pd.DataFrame(box_rows)
    heat_df = pd.DataFrame(
        [
            {"x": day, "y": hour, "value": int(20 + ((i * 3 + j * 5) % 17) * 4)}
            for i, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            for j, hour in enumerate(["9am", "12pm", "3pm", "6pm", "9pm"])
        ]
    )
    ohlc = pd.DataFrame(
        {
            "date": [f"2026-01-{d:02d}" for d in range(1, 13)],
            "open": [100, 104, 101, 108, 112, 109, 115, 118, 114, 121, 125, 122],
            "close": [104, 101, 108, 112, 109, 115, 118, 114, 121, 125, 122, 129],
            "low": [98, 99, 100, 106, 107, 108, 113, 112, 113, 119, 120, 121],
            "high": [106, 105, 110, 114, 114, 117, 120, 119, 123, 127, 126, 131],
        }
    )
    radar_df = pd.DataFrame(
        {
            "name": ["Atlas", "Nova", "Pulse"],
            "speed": [88, 72, 95],
            "power": [76, 91, 68],
            "range": [81, 64, 87],
            "accuracy": [90, 85, 78],
            "efficiency": [70, 88, 82],
        }
    )
    sankey_df = pd.DataFrame(
        {
            "source": [
                "Traffic",
                "Traffic",
                "Traffic",
                "Organic",
                "Paid",
                "Referral",
                "Signup",
                "Signup",
                "Trial",
            ],
            "target": [
                "Organic",
                "Paid",
                "Referral",
                "Signup",
                "Signup",
                "Signup",
                "Trial",
                "Churn",
                "Paid plan",
            ],
            "value": [48, 32, 20, 36, 24, 14, 42, 12, 30],
        }
    )
    tree_df = pd.DataFrame(
        {
            "name": [
                "Product",
                "Platform",
                "Analytics",
                "Charts",
                "Maps",
                "Integrations",
                "Streamlit",
                "FastAPI",
                "Docs",
            ],
            "parent": [
                None,
                "Product",
                "Product",
                "Platform",
                "Platform",
                "Product",
                "Integrations",
                "Integrations",
                "Product",
            ],
            "value": [100, 40, 28, 22, 18, 24, 12, 12, 16],
        }
    )
    map_df = pd.DataFrame(
        {
            "name": [
                "United States",
                "Canada",
                "Brazil",
                "Germany",
                "United Kingdom",
                "France",
                "India",
                "Japan",
                "Australia",
                "South Africa",
            ],
            "value": [92, 54, 61, 48, 57, 44, 73, 66, 39, 28],
        }
    )
    geo_df = pd.DataFrame(
        {
            "name": ["NYC", "LA", "Chicago", "Houston", "Miami", "Seattle", "Denver", "Boston"],
            "lng": [-74.0, -118.2, -87.6, -95.4, -80.2, -122.3, -104.9, -71.1],
            "lat": [40.7, 34.0, 41.9, 29.8, 25.8, 47.6, 39.7, 42.4],
            "value": [88, 74, 61, 55, 49, 67, 42, 58],
        }
    )
    river_dates = [f"2026-01-{d:02d}" for d in range(1, 9)]
    river_rows = []
    # Fixed per-series offsets (avoid hash() — not stable across processes).
    baselines = (("Mobile", 18, 3), ("Desktop", 28, 0), ("Tablet", 10, 2), ("API", 14, 1))
    for i, date in enumerate(river_dates):
        for name, base, offset in baselines:
            bump = (i % 3) * 3 + offset
            river_rows.append({"date": date, "name": name, "value": base + bump + i})
    river_df = pd.DataFrame(river_rows)
    waterfall_df = pd.DataFrame(
        {
            "step": [
                "Starting ARR",
                "New logos",
                "Expansion",
                "Churn",
                "Discount",
                "Ending ARR",
            ],
            "delta": [120, 45, 28, -18, -12, 0],
        }
    )
    # Varied profiles so parallel axes are not collinear.
    parallel_df = pd.DataFrame(
        {
            "latency": [12, 18, 9, 28, 15, 22, 11, 31, 17, 8],
            "throughput": [820, 640, 910, 420, 760, 580, 880, 390, 700, 950],
            "errors": [0.2, 1.1, 0.1, 3.4, 0.6, 1.8, 0.3, 4.1, 0.9, 0.05],
            "cpu": [34, 51, 28, 78, 42, 63, 31, 86, 47, 22],
            "memory": [48, 62, 41, 88, 55, 71, 39, 92, 58, 36],
        }
    )
    word_df = pd.DataFrame(
        {
            "name": [
                "latency",
                "throughput",
                "dashboard",
                "alert",
                "pipeline",
                "theme",
                "embed",
                "streamlit",
                "fastapi",
                "heatmap",
                "sankey",
                "geo",
            ],
            "value": [96, 88, 74, 69, 61, 55, 50, 47, 44, 40, 36, 31],
        }
    )

    mapping: Dict[str, Dict[str, Any]] = {
        "line": dict(data=line_df, x="date", y=["revenue", "cost"], title="Revenue vs cost"),
        "bar": dict(data=bar_df, x="region", y="sales", title="Sales by region"),
        "area": dict(data=line_df, x="date", y="revenue", title="Revenue trend"),
        "scatter": dict(data=scatter_df, x="height", y="weight", title="Height vs weight"),
        "pie": dict(data=pie_df, names="name", values="value", title="Segment mix"),
        "donut": dict(data=pie_df, names="name", values="value", title="Segment mix"),
        "boxplot": dict(data=box_df, x="group", y="score", title="Score distribution"),
        "heatmap": dict(data=heat_df, x="x", y="y", values="value", title="Weekly activity"),
        "candlestick": dict(data=ohlc, x="date", title="Price action"),
        "kline": dict(data=ohlc, x="date", title="Price action"),
        "radar": dict(
            data=radar_df,
            names="name",
            values=["speed", "power", "range", "accuracy", "efficiency"],
            title="Capability radar",
        ),
        "funnel": dict(data=pie_df, names="name", values="value", title="Pipeline stages"),
        "gauge": dict(value=72, title="Capacity used"),
        "sankey": dict(data=sankey_df, title="Acquisition flow"),
        "treemap": dict(data=pie_df, title="Segment mix"),
        "map": dict(data=map_df, title="Global demand"),
        "mix": dict(
            data=line_df, x="date", bar="cost", line="revenue", title="Revenue vs cost"
        ),
        "combo": dict(
            data=line_df, x="date", bar="cost", line="revenue", title="Revenue vs cost"
        ),
        "effect_scatter": dict(
            data=scatter_df, x="height", y="weight", title="Height vs weight"
        ),
        "waterfall": dict(data=waterfall_df, x="step", y="delta", title="ARR bridge"),
        "polar": dict(data=bar_df, x="region", y="sales", title="Sales by region"),
        "parallel": dict(
            data=parallel_df,
            dimensions=["latency", "throughput", "errors", "cpu", "memory"],
            title="Service profiles",
        ),
        "sunburst": dict(
            data=tree_df, names="name", values="value", parent="parent", title="Product tree"
        ),
        "tree": dict(data=tree_df, names="name", parent="parent", title="Product tree"),
        "graph": dict(data=sankey_df, title="Acquisition graph"),
        "flowchart": dict(
            data=sankey_df,
            source="source",
            target="target",
            layout="hierarchical",
            title="Process flow",
        ),
        "wordcloud": dict(data=word_df, title="Topic cloud"),
        "geo": dict(
            data=geo_df,
            names="name",
            lng="lng",
            lat="lat",
            values="value",
            title="City demand",
        ),
        "bar3d": dict(data=_xyz(), x="x", y="y", z="z", title="3D bars"),
        "line3d": dict(data=_xyz(), x="x", y="y", z="z", title="3D path"),
        "scatter3d": dict(data=_xyz(), x="x", y="y", z="z", title="3D scatter"),
        "pictorial_bar": dict(data=bar_df, x="region", y="sales", title="Sales by region"),
        "theme_river": dict(data=river_df, title="Channel mix over time"),
        "liquid": dict(value=0.72, title="Fill level"),
        "surface3d": dict(data=_xyz(), x="x", y="y", z="z", title="3D surface"),
    }
    if chart_type == "grid":
        return {
            "charts": [
                vz.line(**mapping["line"]),
                vz.bar(**mapping["bar"]),
                vz.area(**mapping["area"]),
                vz.scatter(**mapping["scatter"]),
            ],
            "title": "Grid showcase",
        }
    if chart_type == "page":
        return {
            "charts": [vz.line(**mapping["line"]), vz.pie(**mapping["pie"]), vz.map(**mapping["map"])],
            "title": "Page showcase",
        }
    if chart_type == "tab":
        return {
            "charts": [
                vz.bar(**mapping["bar"]),
                vz.pie(**mapping["pie"]),
                vz.radar(**mapping["radar"]),
            ],
            "title": "Tab showcase",
        }
    if chart_type == "timeline":
        return {
            "charts": [
                vz.line(line_df, x="date", y="revenue", title="Revenue"),
                vz.line(line_df, x="date", y="cost", title="Cost"),
                vz.mix(
                    line_df, x="date", bar="cost", line="revenue", title="Combined"
                ),
            ],
            "title": "Timeline showcase",
        }
    return mapping[chart_type]


def make_chart(chart_type: str, **extra: Any):
    """Build a chart from :func:`samples_for` plus optional overrides."""
    kwargs = dict(samples_for(chart_type))
    kwargs.update(extra)
    return vz.chart(chart_type, **kwargs)


# Hero set for Level 3 browser smoke — subset of the full matrix.
HERO_CHART_TYPES = ("line", "bar", "pie", "map", "mix")

SAMPLE_THEMES = ("default", "dark")
