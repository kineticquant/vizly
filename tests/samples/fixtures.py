"""Deterministic sample kwargs for every registered chart type.

Shared by Level 1 smoke tests and Level 2 sample/golden suite.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

import vizly as vz


def _xyz() -> pd.DataFrame:
    return pd.DataFrame({"x": [0, 1, 2], "y": [0, 1, 0], "z": [1, 2, 3]})


def samples_for(chart_type: str) -> Dict[str, Any]:
    """Return kwargs for ``vz.chart(chart_type, **kwargs)`` with fixed tiny data."""
    line_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
            "revenue": [10, 20, 15],
            "cost": [4, 8, 6],
        }
    )
    bar_df = pd.DataFrame({"region": ["East", "West", "South"], "sales": [3, 5, 2]})
    scatter_df = pd.DataFrame({"height": [1.5, 1.7, 1.8], "weight": [50, 70, 80]})
    pie_df = pd.DataFrame({"name": ["A", "B", "C"], "value": [10, 20, 30]})
    box_df = pd.DataFrame(
        {"group": ["g1", "g1", "g1", "g2", "g2", "g2"], "score": [1, 2, 3, 4, 5, 6]}
    )
    heat_df = pd.DataFrame(
        {"x": ["a", "a", "b", "b"], "y": ["m", "n", "m", "n"], "value": [1, 2, 3, 4]}
    )
    ohlc = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "open": [10, 11, 12],
            "close": [11, 10, 13],
            "low": [9, 9.5, 11],
            "high": [12, 11.5, 14],
        }
    )
    radar_df = pd.DataFrame(
        {"name": ["A", "B"], "speed": [80, 70], "power": [60, 90], "range": [70, 50]}
    )
    sankey_df = pd.DataFrame(
        {"source": ["A", "A", "B"], "target": ["X", "Y", "Y"], "value": [5, 3, 2]}
    )
    tree_df = pd.DataFrame(
        {"name": ["Root", "Child"], "parent": [None, "Root"], "value": [10, 4]}
    )
    map_df = pd.DataFrame(
        {"name": ["United States", "Canada", "Brazil"], "value": [40, 20, 25]}
    )
    geo_df = pd.DataFrame(
        {
            "name": ["NYC", "LA", "Chicago"],
            "lng": [-74.0, -118.2, -87.6],
            "lat": [40.7, 34.0, 41.9],
            "value": [10, 20, 15],
        }
    )
    river_df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02"],
            "value": [10, 20, 15, 25],
            "name": ["A", "B", "A", "B"],
        }
    )
    waterfall_df = pd.DataFrame(
        {"step": ["Start", "Sales", "Cost", "Tax"], "delta": [100, 40, -20, -10]}
    )
    parallel_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
    word_df = pie_df.copy()

    mapping: Dict[str, Dict[str, Any]] = {
        "line": dict(data=line_df, x="date", y="revenue"),
        "bar": dict(data=bar_df, x="region", y="sales"),
        "area": dict(data=line_df, x="date", y="revenue"),
        "scatter": dict(data=scatter_df, x="height", y="weight"),
        "pie": dict(data=pie_df, names="name", values="value"),
        "donut": dict(data=pie_df, names="name", values="value"),
        "boxplot": dict(data=box_df, x="group", y="score"),
        "heatmap": dict(data=heat_df, x="x", y="y", values="value"),
        "candlestick": dict(data=ohlc, x="date"),
        "kline": dict(data=ohlc, x="date"),
        "radar": dict(data=radar_df, names="name", values=["speed", "power", "range"]),
        "funnel": dict(data=pie_df, names="name", values="value"),
        "gauge": dict(value=72),
        "sankey": dict(data=sankey_df),
        "treemap": dict(data=pie_df),
        "map": dict(data=map_df),
        "mix": dict(data=line_df, x="date", bar="cost", line="revenue"),
        "combo": dict(data=line_df, x="date", bar="cost", line="revenue"),
        "effect_scatter": dict(data=scatter_df, x="height", y="weight"),
        "waterfall": dict(data=waterfall_df, x="step", y="delta"),
        "polar": dict(data=bar_df, x="region", y="sales"),
        "parallel": dict(data=parallel_df, dimensions=["a", "b", "c"]),
        "sunburst": dict(data=tree_df, names="name", values="value", parent="parent"),
        "tree": dict(data=tree_df, names="name", parent="parent"),
        "graph": dict(data=sankey_df),
        "wordcloud": dict(data=word_df),
        "geo": dict(data=geo_df, names="name", lng="lng", lat="lat", values="value"),
        "bar3d": dict(data=_xyz(), x="x", y="y", z="z"),
        "line3d": dict(data=_xyz(), x="x", y="y", z="z"),
        "scatter3d": dict(data=_xyz(), x="x", y="y", z="z"),
        "pictorial_bar": dict(data=bar_df, x="region", y="sales"),
        "theme_river": dict(data=river_df),
        "liquid": dict(value=0.55),
        "surface3d": dict(data=_xyz(), x="x", y="y", z="z"),
    }
    if chart_type == "grid":
        return {"charts": [vz.line(**mapping["line"]), vz.bar(**mapping["bar"])]}
    if chart_type == "page":
        return {"charts": [vz.line(**mapping["line"]), vz.pie(**mapping["pie"])]}
    if chart_type == "tab":
        return {"charts": [vz.bar(**mapping["bar"]), vz.pie(**mapping["pie"])]}
    if chart_type == "timeline":
        return {
            "charts": [
                vz.line(line_df, x="date", y="revenue", title="t0"),
                vz.line(line_df, x="date", y="cost", title="t1"),
            ]
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
