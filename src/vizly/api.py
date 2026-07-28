"""Public function API: chart(), from_option(), and sugar constructors."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from vizly.base import BaseChart, OptionChart
from vizly.charts import COMPOSE_TYPES, get_chart_class
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

ThemeLike = Union[str, Mapping[str, Any]]


def chart(chart_type: str, data: Any = None, **kwargs: Any) -> BaseChart:
    """Universal constructor: ``vz.chart("line", df, x=..., y=...)``."""
    cls = get_chart_class(chart_type)
    key = chart_type.strip().lower()
    if key in COMPOSE_TYPES:
        return cls(**kwargs)
    return cls(data, **kwargs)


def from_option(
    option: Mapping[str, Any],
    *,
    title: Optional[str] = None,
    width: Optional[str] = None,
    height: Optional[str] = None,
    theme: Optional[ThemeLike] = None,
    needs_gl: bool = False,
    **kwargs: Any,
) -> OptionChart:
    """Wrap a raw ECharts option dict as a vizly chart."""
    return OptionChart(
        option,
        title=title,
        width=width,
        height=height,
        theme=theme,
        needs_gl=needs_gl,
        **kwargs,
    )


def line(data: Any = None, **kwargs: Any) -> LineChart:
    return LineChart(data, **kwargs)


def bar(data: Any = None, **kwargs: Any) -> BarChart:
    return BarChart(data, **kwargs)


def area(data: Any = None, **kwargs: Any) -> AreaChart:
    return AreaChart(data, **kwargs)


def scatter(data: Any = None, **kwargs: Any) -> ScatterChart:
    return ScatterChart(data, **kwargs)


def pie(data: Any = None, **kwargs: Any) -> PieChart:
    return PieChart(data, **kwargs)


def donut(data: Any = None, **kwargs: Any) -> DonutChart:
    return DonutChart(data, **kwargs)


def boxplot(data: Any = None, **kwargs: Any) -> BoxplotChart:
    return BoxplotChart(data, **kwargs)


def heatmap(data: Any = None, **kwargs: Any) -> HeatmapChart:
    return HeatmapChart(data, **kwargs)


def candlestick(data: Any = None, **kwargs: Any) -> CandlestickChart:
    return CandlestickChart(data, **kwargs)


def kline(data: Any = None, **kwargs: Any) -> KlineChart:
    return KlineChart(data, **kwargs)


def radar(data: Any = None, **kwargs: Any) -> RadarChart:
    return RadarChart(data, **kwargs)


def funnel(data: Any = None, **kwargs: Any) -> FunnelChart:
    return FunnelChart(data, **kwargs)


def gauge(data: Any = None, **kwargs: Any) -> GaugeChart:
    return GaugeChart(data, **kwargs)


def sankey(data: Any = None, **kwargs: Any) -> SankeyChart:
    return SankeyChart(data, **kwargs)


def treemap(data: Any = None, **kwargs: Any) -> TreemapChart:
    return TreemapChart(data, **kwargs)


def map_chart(data: Any = None, **kwargs: Any) -> MapChart:
    return MapChart(data, **kwargs)


map = map_chart  # noqa: A001


def grid(*, charts: Any, **kwargs: Any) -> GridChart:
    return GridChart(charts=charts, **kwargs)


def mix(data: Any = None, **kwargs: Any) -> MixChart:
    return MixChart(data, **kwargs)


def combo(data: Any = None, **kwargs: Any) -> ComboChart:
    return ComboChart(data, **kwargs)


def effect_scatter(data: Any = None, **kwargs: Any) -> EffectScatterChart:
    return EffectScatterChart(data, **kwargs)


def waterfall(data: Any = None, **kwargs: Any) -> WaterfallChart:
    return WaterfallChart(data, **kwargs)


def polar(data: Any = None, **kwargs: Any) -> PolarChart:
    return PolarChart(data, **kwargs)


def parallel(data: Any = None, **kwargs: Any) -> ParallelChart:
    return ParallelChart(data, **kwargs)


def sunburst(data: Any = None, **kwargs: Any) -> SunburstChart:
    return SunburstChart(data, **kwargs)


def tree(data: Any = None, **kwargs: Any) -> TreeChart:
    return TreeChart(data, **kwargs)


def graph(data: Any = None, **kwargs: Any) -> GraphChart:
    return GraphChart(data, **kwargs)


def wordcloud(data: Any = None, **kwargs: Any) -> WordCloudChart:
    return WordCloudChart(data, **kwargs)


def geo(data: Any = None, **kwargs: Any) -> GeoChart:
    return GeoChart(data, **kwargs)


def bar3d(data: Any = None, **kwargs: Any) -> Bar3DChart:
    return Bar3DChart(data, **kwargs)


def line3d(data: Any = None, **kwargs: Any) -> Line3DChart:
    return Line3DChart(data, **kwargs)


def scatter3d(data: Any = None, **kwargs: Any) -> Scatter3DChart:
    return Scatter3DChart(data, **kwargs)


def page(*, charts: Any, **kwargs: Any) -> PageChart:
    return PageChart(charts=charts, **kwargs)


def tab(*, charts: Any, **kwargs: Any) -> TabChart:
    return TabChart(charts=charts, **kwargs)


def timeline(*, charts: Any, **kwargs: Any) -> TimelineChart:
    return TimelineChart(charts=charts, **kwargs)


def pictorial_bar(data: Any = None, **kwargs: Any) -> PictorialBarChart:
    return PictorialBarChart(data, **kwargs)


def theme_river(data: Any = None, **kwargs: Any) -> ThemeRiverChart:
    return ThemeRiverChart(data, **kwargs)


def liquid(data: Any = None, **kwargs: Any) -> LiquidChart:
    return LiquidChart(data, **kwargs)


def surface3d(data: Any = None, **kwargs: Any) -> Surface3DChart:
    return Surface3DChart(data, **kwargs)


__all__ = [
    "area",
    "bar",
    "bar3d",
    "boxplot",
    "candlestick",
    "chart",
    "combo",
    "donut",
    "effect_scatter",
    "from_option",
    "funnel",
    "gauge",
    "geo",
    "graph",
    "grid",
    "heatmap",
    "kline",
    "line",
    "line3d",
    "liquid",
    "map",
    "map_chart",
    "mix",
    "page",
    "parallel",
    "pictorial_bar",
    "pie",
    "polar",
    "radar",
    "sankey",
    "scatter",
    "scatter3d",
    "sunburst",
    "surface3d",
    "tab",
    "theme_river",
    "timeline",
    "tree",
    "treemap",
    "waterfall",
    "wordcloud",
]
