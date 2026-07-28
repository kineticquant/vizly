"""Parametrized smoke tests across all registered chart types (Bands A–C)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

import vizly as vz
from vizly.charts import (
    BAND_B_TYPES,
    BAND_C_TYPES,
    CHART_TYPES,
    list_unavailable_chart_types,
)
from vizly.config import reset_config
from vizly.data import DataError
from vizly.maps import reset_opt_in_maps
from vizly.theme.registry import reset_registry

from tests.samples.fixtures import make_chart, samples_for


@pytest.fixture(autouse=True)
def _clean():
    reset_registry()
    reset_config()
    reset_opt_in_maps()
    yield
    reset_registry()
    reset_config()
    reset_opt_in_maps()


ALL_TYPES = list(CHART_TYPES.keys())


@pytest.mark.parametrize("chart_type", ALL_TYPES)
def test_all_registered_types_to_option(chart_type):
    c = make_chart(chart_type, theme="default")
    option = c.to_option()
    assert isinstance(option, dict)
    if chart_type in ("page", "tab"):
        assert "_vizly_compose" in option
        assert option["_vizly_compose"]["type"] == chart_type
    else:
        assert "series" in option
    json.dumps(option, allow_nan=False)
    assert c.chart_type == chart_type or (
        chart_type == "combo" and c.chart_type == "mix"
    )


def test_list_chart_types_covers_bands():
    names = vz.list_chart_types()
    for t in BAND_B_TYPES + BAND_C_TYPES:
        assert t in names
    assert "chord" not in names
    unavailable = list_unavailable_chart_types()
    assert any(u["type"] == "chord" for u in unavailable)


def test_chord_raises_unavailable():
    with pytest.raises(KeyError, match="upstream-unavailable"):
        vz.chart("chord", {"a": [1]})


def test_gl_flag_only_on_3d():
    assert make_chart("bar3d")._needs_gl is True
    assert make_chart("line")._needs_gl is False


def test_wordcloud_and_liquid_plugins():
    assert "wordcloud" in make_chart("wordcloud")._plugins
    assert "liquidfill" in make_chart("liquid")._plugins


def test_china_map_opt_in_only():
    with pytest.raises(DataError, match="opt-in only"):
        vz.map(
            pd.DataFrame({"name": ["Beijing"], "value": [1]}),
            map="china",
        ).to_html()

    vz.register_map_pack(
        "china",
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Beijing"},
                    "geometry": {"type": "Point", "coordinates": [116.4, 39.9]},
                }
            ],
        },
    )
    # Registration succeeds; to_option does not need geojson load
    opt = vz.map(
        pd.DataFrame({"name": ["Beijing"], "value": [1]}), map="china"
    ).to_option()
    assert opt["series"][0]["map"] == "china"


def test_page_accepts_vizly_children():
    page = vz.page(
        charts=[
            vz.line(**samples_for("line")),
            vz.bar(**samples_for("bar")),
        ]
    )
    opt = page.to_option()
    assert opt["_vizly_compose"]["type"] == "page"
    assert len(opt["_vizly_compose"]["options"]) == 2


def test_kline_distinct_chart_type():
    assert vz.kline(**samples_for("kline")).chart_type == "kline"
    assert vz.candlestick(**samples_for("candlestick")).chart_type == "candlestick"
