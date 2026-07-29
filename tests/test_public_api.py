"""Public API surface audit — ``__all__`` must match exported names."""

from __future__ import annotations

import vizly as vz

# Stable public names expected on the package surface.
EXPECTED_PUBLIC = {
    "BaseChart",
    "DataError",
    "GeoLayer",
    "OptionChart",
    "TabularView",
    "__version__",
    "area",
    "as_tabular",
    "bar",
    "bar3d",
    "boxplot",
    "build_click_payload",
    "candlestick",
    "chart",
    "combo",
    "diagram",
    "donut",
    "effect_scatter",
    "export_theme",
    "filter_by_click",
    "filter_tabular",
    "flowchart",
    "from_cloudwatch",
    "from_columnar",
    "from_csv",
    "from_elasticsearch",
    "from_elk",
    "from_excel",
    "from_json",
    "from_option",
    "from_prometheus",
    "from_records",
    "from_sql",
    "from_tsv",
    "funnel",
    "gauge",
    "geo",
    "get_theme",
    "graph",
    "grid",
    "heatmap",
    "infer_roles",
    "kline",
    "line",
    "line3d",
    "liquid",
    "list_bundled_maps",
    "list_chart_types",
    "list_opt_in_maps",
    "list_themes",
    "list_unavailable_chart_types",
    "load_map_geojson",
    "load_theme",
    "map",
    "map_chart",
    "map_path",
    "mix",
    "overlay_geojson",
    "page",
    "parallel",
    "pictorial_bar",
    "pie",
    "polar",
    "radar",
    "register_map_pack",
    "register_theme",
    "resolve_theme",
    "sankey",
    "scatter",
    "scatter3d",
    "set_theme",
    "standardize",
    "sunburst",
    "surface3d",
    "tab",
    "theme_river",
    "timeline",
    "tree",
    "treemap",
    "waterfall",
    "wordcloud",
}


def test_all_matches_expected():
    assert set(vz.__all__) == EXPECTED_PUBLIC


def test_all_names_are_importable():
    for name in vz.__all__:
        assert hasattr(vz, name), f"missing export {name!r}"
        assert getattr(vz, name) is not None or name == "__version__"


def test_version_string():
    assert isinstance(vz.__version__, str)
    assert vz.__version__.count(".") >= 1
