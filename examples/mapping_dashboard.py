"""Mapping dashboard example — choropleth + overlay + linked charts.

Run::

    python examples/mapping_dashboard.py
    # opens artifacts or prints HTML path
"""

from __future__ import annotations

from pathlib import Path

import vizly as vz
from vizly.geo_layers import overlay_geojson

OUT = Path(__file__).resolve().parents[1] / "artifacts" / "html" / "mapping_dashboard.html"


def main() -> None:
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
    layer = overlay_geojson(sites, name="ops_sites", kind="point")
    world = vz.map(
        demand,
        layers=[layer],
        title="Global demand + ops sites",
        height="480px",
        theme="ops_grafana",
    )
    by_region = vz.bar(
        [{"region": r["name"], "sales": r["value"]} for r in demand],
        x="region",
        y="sales",
        title="Demand by region (click map to filter in host apps)",
        theme="ops_grafana",
    )
    trend = vz.line(
        {
            "date": [f"2026-0{i}-01" for i in range(1, 7)],
            "requests": [120, 140, 135, 160, 175, 190],
        },
        x="date",
        y="requests",
        title="Request volume",
        theme="ops_grafana",
    )
    page = vz.page(charts=[world, by_region, trend], title="Mapping ops dashboard", connect=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    page.render(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
