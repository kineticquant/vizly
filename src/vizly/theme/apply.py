"""Map vizly theme dicts to ECharts option fragments."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Union

from vizly.theme.merge import deep_merge

AxisOption = Union[Dict[str, Any], List[Any]]


def theme_to_echarts_option(theme: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert a resolved vizly theme into ECharts option fragments.

    Does not include series data — only visual / chrome defaults that charts
    deep-merge into their built options.

    Important: this fragment does **not** set ``xAxis`` / ``yAxis``. Axis
    chrome is applied by :func:`apply_theme_to_option` onto whatever axis
    shape the chart already built (object or list), so category/data axes
    are never replaced by a bare style dict.
    """
    tooltip = theme.get("tooltip") or {}
    legend = theme.get("legend") or {}
    title = theme.get("title") or {}
    animation = theme.get("animation") or {}

    option: Dict[str, Any] = {
        "color": list(theme.get("palette") or []),
        "backgroundColor": theme.get("background"),
        "textStyle": {
            "color": theme.get("text_color"),
            "fontFamily": theme.get("font_family"),
        },
        "title": {
            "textStyle": {
                "color": title.get("color"),
                "fontWeight": title.get("font_weight"),
                "fontFamily": theme.get("font_family"),
            },
        },
        "legend": {
            "show": legend.get("show", True),
            "top": legend.get("top", "2%"),
            "textStyle": {"color": legend.get("text_color")},
        },
        "tooltip": {
            "backgroundColor": tooltip.get("bg"),
            "borderColor": tooltip.get("border"),
            "borderWidth": 1,
            "textStyle": {"color": tooltip.get("text")},
        },
        "animation": bool(animation.get("enabled", True)),
        "animationDuration": animation.get("duration", 400),
    }
    return option


def _axis_style_fragment(theme: Mapping[str, Any]) -> Dict[str, Any]:
    axis = theme.get("axis") or {}
    grid = theme.get("grid") or {}
    return {
        "axisLine": {"lineStyle": {"color": axis.get("line_color")}},
        "axisLabel": {"color": axis.get("label_color")},
        "nameTextStyle": {"color": axis.get("name_color")},
        "splitLine": {
            "show": bool(grid.get("show", True)),
            "lineStyle": {
                "color": grid.get("color"),
                "type": grid.get("type", "solid"),
            },
        },
    }


def _merge_axis_style(
    existing: Optional[AxisOption],
    style: Mapping[str, Any],
) -> AxisOption:
    """Deep-merge axis style into an existing axis option (dict or list)."""
    if existing is None:
        return deep_merge(style, {})
    if isinstance(existing, list):
        if not existing:
            return [deep_merge(style, {})]
        return [
            deep_merge(item, style) if isinstance(item, Mapping) else item
            for item in existing
        ]
    if isinstance(existing, Mapping):
        return deep_merge(existing, style)
    return deep_merge(style, {})


def apply_theme_to_option(
    option: Mapping[str, Any],
    theme: Mapping[str, Any],
    user_option: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge theme fragments under ``option``, then apply ``user_option`` last.

    Precedence: structural option < theme fragments < user option.

    Axis styling is merged into existing ``xAxis`` / ``yAxis`` values whether
    they are a single object or a list, preserving chart-built data/type.
    Axes are **not** injected when the structural option omitted them (pie,
    sankey, gauge, radar, etc.).
    """
    themed: Dict[str, Any] = deep_merge(option, theme_to_echarts_option(theme))
    style = _axis_style_fragment(theme)
    # Only style axes the chart already declared — do not invent empty axes.
    if "xAxis" in themed:
        themed["xAxis"] = _merge_axis_style(themed.get("xAxis"), style)
    if "yAxis" in themed:
        themed["yAxis"] = _merge_axis_style(themed.get("yAxis"), style)
    if user_option:
        # User may replace axes entirely; honor that after theme chrome.
        themed = deep_merge(themed, user_option)
    return themed


def series_defaults_for(theme: Mapping[str, Any], chart_type: str) -> Dict[str, Any]:
    """Return series default overrides for a chart type from the theme."""
    defaults = theme.get("series_defaults") or {}
    entry = defaults.get(chart_type) or {}
    return dict(entry)
