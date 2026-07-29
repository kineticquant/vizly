"""Tests for events, flowchart, geo layers, and client-side export helpers."""

from __future__ import annotations

import vizly as vz
from vizly.events import build_click_payload, filter_by_click
from vizly.export import data_url_help
from vizly.geo_layers import merge_geo_layers, overlay_geojson


def test_click_payload_and_filter():
    payload = build_click_payload(
        chart_id="c1",
        chart_type="bar",
        params={"name": "East", "value": 10, "dataIndex": 0, "seriesName": "sales"},
    )
    assert payload["source"] == "vizly"
    assert payload["name"] == "East"
    data = [
        {"region": "East", "sales": 10},
        {"region": "West", "sales": 20},
    ]
    filtered = filter_by_click(data, payload, column="region")
    assert filtered.nrows == 1
    assert filtered.column("sales") == [10]


def test_html_emits_event_bridge_and_data_url():
    chart = vz.bar({"region": ["A"], "sales": [1]}, x="region", y="sales")
    html = chart.to_html()
    assert "vizly:event" in html
    assert "window.__vizly" in html
    assert "postMessage" in html
    assert "window.location.origin" in html
    assert "toDataURL" in html
    assert "downloadImage" in html
    assert "console.warn('vizly event bridge failed'" in html
    assert "postMessage(payload, '*')" not in html


def test_message_origin_star_opt_in():
    chart = vz.bar({"region": ["A"], "sales": [1]}, x="region", y="sales")
    html = chart.to_html(message_origin="*")
    assert "postMessage(payload, \"*\")" in html or "postMessage(payload, '*')" in html


def test_flowchart_option():
    edges = [
        {"source": "Ingest", "target": "Clean"},
        {"source": "Clean", "target": "Chart"},
    ]
    chart = vz.flowchart(edges, layout="hierarchical", title="Pipeline")
    opt = chart.to_option()
    series = opt["series"][0]
    assert series["type"] == "graph"
    assert series["edgeSymbol"] == ["none", "arrow"]
    assert series["layout"] == "none"
    assert len(series["data"]) == 3
    assert vz.diagram is vz.flowchart


def test_page_connect_js():
    page = vz.page(
        charts=[
            vz.line({"x": [1, 2], "y": [3, 4]}, x="x", y="y", title="A"),
            vz.bar({"region": ["A"], "sales": [1]}, x="region", y="sales", title="B"),
        ],
        connect=True,
    )
    html = page.to_html()
    assert "echarts.connect" in html
    assert "toDataURL" in html
    assert "window.location.origin" in html


def test_page_message_origin_threaded():
    page = vz.page(
        charts=[
            vz.bar({"region": ["A"], "sales": [1]}, x="region", y="sales", title="A"),
            vz.bar({"region": ["B"], "sales": [2]}, x="region", y="sales", title="B"),
        ],
        connect=False,
    )
    html = page.to_html(message_origin="*")
    assert html.count('postMessage(payload, "*")') >= 2
    assert "postMessage(payload, window.location.origin)" not in html


def test_tab_uses_shared_bootstrap():
    tab = vz.tab(
        charts=[
            vz.bar({"region": ["A"], "sales": [1]}, x="region", y="sales", title="A"),
            vz.line({"x": [1, 2], "y": [3, 4]}, x="x", y="y", title="B"),
        ],
        labels=["Bar", "Line"],
    )
    html = tab.to_html(message_origin="https://example.com")
    assert "toDataURL" in html
    assert 'postMessage(payload, "https://example.com")' in html
    assert "charts.push(chart)" in html


def test_geo_layer_overlay_point():
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "HQ"},
                "geometry": {"type": "Point", "coordinates": [-73.9, 40.7]},
            }
        ],
    }
    layer = overlay_geojson(gj, name="sites", kind="point")
    chart = vz.map(
        [{"name": "United States", "value": 10}],
        layers=[layer],
        title="Demand + sites",
    )
    opt = chart.to_option()
    types = [s["type"] for s in opt["series"]]
    assert "map" in types
    assert "scatter" in types
    assert "geo" in opt
    assert opt["series"][0].get("geoIndex") == 0


def test_geo_polygon_overlay_renders_metadata():
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Zone"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0], [-1.0, -1.0]]
                    ],
                },
            }
        ],
    }
    layer = overlay_geojson(gj, name="zone", kind="polygon")
    html_opt = vz.map(
        [{"name": "United States", "value": 1}],
        layers=[layer],
    )._option_for_html()
    assert html_opt.get("_vizly_geo_polygons")
    assert html_opt["_vizly_geo_polygons"][0]["name"] == "Zone"
    assert html_opt["_vizly_geo_polygons"][0]["rings"]
    types = [s["type"] for s in html_opt["series"]]
    assert "lines" in types
    html = vz.map(
        [{"name": "United States", "value": 1}],
        layers=[layer],
    ).to_html()
    assert "_vizly_geo_polygons" in html
    assert "type: 'custom'" in html or 'type: "custom"' in html or "type: 'custom'" in html
    # JSON path strips HTML-only keys
    clean = vz.map(
        [{"name": "United States", "value": 1}],
        layers=[layer],
    ).to_option()
    assert "_vizly_geo_polygons" not in clean


def test_merge_geo_layers_links_map_series():
    base = {
        "series": [{"type": "map", "map": "world", "roam": True, "data": []}],
    }
    layer = overlay_geojson(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "P"},
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                }
            ],
        },
        name="p",
        kind="point",
    )
    out = merge_geo_layers(base, [layer], map_name="world")
    assert out["series"][0].get("geoIndex") == 0
    assert "roam" not in out["series"][0]
    assert out["geo"]["roam"] is True


def test_map_join_keys():
    chart = vz.map(
        [{"region": "United States", "value": 5, "iso": "US"}],
        names="region",
        name_field="region",
        id_field="iso",
    )
    series = chart.to_option()["series"][0]
    assert series["data"][0]["name"] == "United States"
    assert series["data"][0]["id"] == "US"
    assert series["nameProperty"] == "region"


def test_client_export_help_and_live_script():
    assert "toDataURL" in data_url_help()
    chart = vz.bar({"region": ["A"], "sales": [1]}, x="region", y="sales")
    assert not hasattr(vz.BaseChart, "to_png")
    assert not hasattr(vz.BaseChart, "to_pdf")
    script = chart.live_update_script("vizly_demo")
    assert "setOption" in script
    assert "vizly_demo" in script


def test_editor_theme_applies():
    chart = vz.bar(
        {"region": ["A"], "sales": [1]},
        x="region",
        y="sales",
        theme="editor_tokyo_night",
    )
    opt = chart.to_option()
    assert opt["backgroundColor"] == "#1A1B26"


def test_prepare_frame_avoids_dataframe_copy():
    import pandas as pd

    from vizly.charts._helpers import prepare_frame

    df = pd.DataFrame({"region": ["A"], "sales": [1]})
    out = prepare_frame(df)
    assert out is df
