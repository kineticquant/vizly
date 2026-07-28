"""Band A chart smoke tests, inference, and multi-theme coverage."""

from __future__ import annotations

import json

import pandas as pd
import pytest

import vizly as vz
from vizly.charts import BAND_A_TYPES
from vizly.config import reset_config
from vizly.data import DataError
from vizly.theme.registry import reset_registry

BAND_A = list(BAND_A_TYPES)


@pytest.fixture(autouse=True)
def _clean():
    reset_registry()
    reset_config()
    yield
    reset_registry()
    reset_config()


def _samples():
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
        {
            "group": ["g1", "g1", "g1", "g2", "g2", "g2"],
            "score": [1, 2, 3, 4, 5, 6],
        }
    )
    heat_df = pd.DataFrame(
        {
            "x": ["a", "a", "b", "b"],
            "y": ["m", "n", "m", "n"],
            "value": [1, 2, 3, 4],
        }
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
    funnel_df = pie_df.copy()
    sankey_df = pd.DataFrame(
        {
            "source": ["A", "A", "B"],
            "target": ["X", "Y", "Y"],
            "value": [5, 3, 2],
        }
    )
    tree_df = pd.DataFrame({"name": ["Root", "Leaf"], "value": [10, 4]})
    return {
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
        "funnel": dict(data=funnel_df, names="name", values="value"),
        "gauge": dict(value=72),
        "sankey": dict(data=sankey_df),
        "treemap": dict(data=tree_df),
        "map": dict(
            data=pd.DataFrame(
                {"name": ["United States", "Canada", "Brazil"], "value": [40, 20, 25]}
            )
        ),
        "mix": dict(data=line_df, x="date", bar="cost", line="revenue"),
        "combo": dict(data=line_df, x="date", bar="cost", line="revenue"),
    }


def _make(chart_type: str, **extra):
    samples = _samples()
    if chart_type == "grid":
        line = vz.line(**samples["line"])
        bar = vz.bar(**samples["bar"])
        return vz.grid(charts=[line, bar], cols=2, **extra)
    kwargs = dict(samples[chart_type])
    kwargs.update(extra)
    return vz.chart(chart_type, **kwargs)


@pytest.mark.parametrize("chart_type", BAND_A)
@pytest.mark.parametrize("theme", ["default", "dark", {"background": "#FAFAFA"}])
def test_band_a_to_option_under_themes(chart_type, theme):
    c = _make(chart_type, theme=theme)
    option = c.to_option()
    assert isinstance(option, dict)
    assert "series" in option
    # JSON-serializable
    json.dumps(option, allow_nan=False)
    if chart_type not in {"grid", "radar", "gauge", "sankey", "treemap", "map", "pie", "donut", "funnel"}:
        assert "xAxis" in option or chart_type == "scatter"
    if chart_type in {"pie", "donut", "funnel", "gauge", "sankey", "treemap", "radar"}:
        assert "xAxis" not in option
        assert "yAxis" not in option


def test_list_chart_types_includes_band_a():
    names = vz.list_chart_types()
    for t in ("line", "bar", "pie", "map", "mix", "kline"):
        assert t in names


def test_sugar_and_chart_equivalent():
    df = _samples()["line"]["data"]
    a = vz.line(df, x="date", y="revenue").to_option()
    b = vz.chart("line", df, x="date", y="revenue").to_option()
    assert a["series"][0]["data"] == b["series"][0]["data"]


def test_multi_series_and_stacked():
    df = _samples()["line"]["data"]
    opt = vz.bar(df, x="date", y=["revenue", "cost"], stacked=True).to_option()
    assert len(opt["series"]) == 2
    assert opt["series"][0]["stack"] == "total"
    assert opt["series"][1]["type"] == "bar"


def test_area_stacked():
    df = _samples()["line"]["data"]
    opt = vz.area(df, x="date", y=["revenue", "cost"], stacked=True).to_option()
    assert opt["series"][0].get("areaStyle") == {}
    assert opt["series"][0]["stack"] == "total"


def test_inference_line_and_pie():
    line_df = _samples()["line"]["data"][["date", "revenue"]]
    opt = vz.line(line_df).to_option()
    assert opt["series"][0]["type"] == "line"
    pie_df = _samples()["pie"]["data"]
    opt2 = vz.pie(pie_df).to_option()
    assert opt2["series"][0]["type"] == "pie"


def test_missing_column_english_error():
    df = _samples()["bar"]["data"]
    with pytest.raises(DataError, match="Available columns"):
        vz.bar(df, x="region", y="missing").to_option()


def test_from_option():
    opt = {"series": [{"type": "bar", "data": [1, 2]}], "xAxis": {}, "yAxis": {}}
    chart = vz.from_option(opt, theme="corporate")
    out = chart.to_option()
    assert out["series"][0]["data"] == [1, 2]
    assert out["color"][0] == "#0B1F33"


def test_map_registers_geojson_in_html():
    c = _make("map")
    # GeoJSON is lazy-loaded for HTML only (keeps to_option cheap).
    assert c._register_maps == {}
    assert c.map_name == "world"
    c._ensure_maps()
    assert "world" in c._register_maps
    opt = c.to_option()
    assert opt["series"][0]["type"] == "map"
    assert opt["series"][0]["map"] == "world"


def test_map_usa_regional_pack():
    df = pd.DataFrame({"name": ["Alabama", "Alaska"], "value": [10, 20]})
    c = vz.map(df, map="usa")
    assert c.map_name == "usa"
    assert c.to_option()["series"][0]["map"] == "usa"


def test_kline_chart_type_distinct():
    c = _make("kline")
    assert c.chart_type == "kline"
    assert vz.chart("candlestick", **_samples()["candlestick"]).chart_type == "candlestick"


def test_scatter_size_encoded_per_point():
    df = pd.DataFrame({"height": [1.5, 1.8], "weight": [50, 80], "s": [10, 40]})
    opt = vz.scatter(df, x="height", y="weight", size="s").to_option()
    data = opt["series"][0]["data"]
    assert isinstance(data[0], dict)
    assert data[0]["value"] == [1.5, 50]
    assert data[0]["symbolSize"] == 10
    assert data[1]["symbolSize"] == 40


def test_option_cache_reused_until_update():
    c = _make("line")
    a = c.to_option()
    b = c.to_option()
    assert a == b
    assert c._cached_option is not None
    c.update(title="New")
    assert c._cached_option is None
    assert c.to_option()["title"]["text"] == "New"


def test_line_html_smoke_local_assets():
    c = _make("line", theme="default")
    html = c.to_html()
    assert "vizly-asset:echarts@" in html
    assert "bootcdn" not in html.lower()
