"""Chart type registry (Bands A–C)."""

from __future__ import annotations

from typing import Dict, List, Tuple, Type

from vizly.base import BaseChart
from vizly.charts.cartesian import (
    AreaChart,
    BarChart,
    BoxplotChart,
    CandlestickChart,
    HeatmapChart,
    KlineChart,
    LineChart,
    ScatterChart,
)
from vizly.charts.compose import (
    ComboChart,
    GridChart,
    MixChart,
    PageChart,
    TabChart,
    TimelineChart,
)
from vizly.charts.extra import (
    EffectScatterChart,
    LiquidChart,
    PictorialBarChart,
    ThemeRiverChart,
    WaterfallChart,
    WordCloudChart,
)
from vizly.charts.geo import GeoChart, MapChart
from vizly.charts.gl3d import (
    Bar3DChart,
    Line3DChart,
    Scatter3DChart,
    Surface3DChart,
)
from vizly.charts.hierarchical import (
    DonutChart,
    FlowchartChart,
    FunnelChart,
    GaugeChart,
    GraphChart,
    PieChart,
    SankeyChart,
    SunburstChart,
    TreeChart,
    TreemapChart,
)
from vizly.charts.polar import ParallelChart, PolarChart, RadarChart

CHART_TYPES: Dict[str, Type[BaseChart]] = {
    # Band A
    "line": LineChart,
    "bar": BarChart,
    "area": AreaChart,
    "scatter": ScatterChart,
    "pie": PieChart,
    "donut": DonutChart,
    "boxplot": BoxplotChart,
    "heatmap": HeatmapChart,
    "candlestick": CandlestickChart,
    "kline": KlineChart,
    "radar": RadarChart,
    "funnel": FunnelChart,
    "gauge": GaugeChart,
    "sankey": SankeyChart,
    "treemap": TreemapChart,
    "map": MapChart,
    "grid": GridChart,
    "mix": MixChart,
    "combo": ComboChart,
    # Band B
    "effect_scatter": EffectScatterChart,
    "waterfall": WaterfallChart,
    "polar": PolarChart,
    "parallel": ParallelChart,
    "sunburst": SunburstChart,
    "tree": TreeChart,
    "graph": GraphChart,
    "flowchart": FlowchartChart,
    "wordcloud": WordCloudChart,
    "geo": GeoChart,
    "bar3d": Bar3DChart,
    "line3d": Line3DChart,
    "scatter3d": Scatter3DChart,
    "page": PageChart,
    "tab": TabChart,
    "timeline": TimelineChart,
    # Band C
    "pictorial_bar": PictorialBarChart,
    "theme_river": ThemeRiverChart,
    "liquid": LiquidChart,
    "surface3d": Surface3DChart,
}

BAND_A_TYPES = (
    "line",
    "bar",
    "area",
    "scatter",
    "pie",
    "donut",
    "boxplot",
    "heatmap",
    "candlestick",
    "kline",
    "radar",
    "funnel",
    "gauge",
    "sankey",
    "treemap",
    "map",
    "grid",
    "mix",
    "combo",
)

BAND_B_TYPES = (
    "effect_scatter",
    "waterfall",
    "polar",
    "parallel",
    "sunburst",
    "tree",
    "graph",
    "flowchart",
    "wordcloud",
    "geo",
    "bar3d",
    "line3d",
    "scatter3d",
    "page",
    "tab",
    "timeline",
)

BAND_C_TYPES = (
    "pictorial_bar",
    "theme_river",
    "liquid",
    "surface3d",
)

# Chord was removed from modern ECharts; not offered as a working type.
UPSTREAM_UNAVAILABLE: Tuple[Tuple[str, str], ...] = (
    (
        "chord",
        "ECharts no longer ships a first-class chord series in the pinned "
        "5.x engine; use sankey or graph instead.",
    ),
)

# Compose constructors take charts= instead of data=
COMPOSE_TYPES = frozenset({"grid", "page", "tab", "timeline"})


def list_chart_types() -> List[str]:
    """Return registered chart type names (Band A, then B, then C, then extras)."""
    seen: List[str] = []
    for group in (BAND_A_TYPES, BAND_B_TYPES, BAND_C_TYPES):
        for name in group:
            if name in CHART_TYPES and name not in seen:
                seen.append(name)
    for name in sorted(CHART_TYPES):
        if name not in seen:
            seen.append(name)
    return seen


def list_unavailable_chart_types() -> List[Dict[str, str]]:
    """Document matrix gaps that are upstream-unavailable."""
    return [{"type": t, "reason": r} for t, r in UPSTREAM_UNAVAILABLE]


def get_chart_class(chart_type: str) -> Type[BaseChart]:
    key = chart_type.strip().lower()
    if key == "diagram":
        key = "flowchart"
    if key == "chord":
        reason = UPSTREAM_UNAVAILABLE[0][1]
        raise KeyError(f"Chart type 'chord' is upstream-unavailable: {reason}")
    try:
        return CHART_TYPES[key]
    except KeyError as exc:
        available = ", ".join(list_chart_types())
        raise KeyError(
            f"Unknown chart type {chart_type!r}. Available: {available}."
        ) from exc


__all__ = [
    "BAND_A_TYPES",
    "BAND_B_TYPES",
    "BAND_C_TYPES",
    "CHART_TYPES",
    "COMPOSE_TYPES",
    "UPSTREAM_UNAVAILABLE",
    "get_chart_class",
    "list_chart_types",
    "list_unavailable_chart_types",
]
