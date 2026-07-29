"""Map vizly theme dicts to ECharts option fragments."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Union

from vizly.theme.merge import deep_merge

AxisOption = Union[Dict[str, Any], List[Any]]

# Default cartesian plot padding — keeps title/legend clear of the series area.
# Callers override via chart grid= / merge_option / theme plot keys in user option.
_DEFAULT_CARTESIAN_GRID: Dict[str, Any] = {
    "top": 64,
    "left": 12,
    "right": 16,
    "bottom": 28,
    "containLabel": True,
}


def theme_to_echarts_option(theme: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert a resolved vizly theme into ECharts option fragments.

    Does not include series data — only visual / chrome defaults that charts
    deep-merge into their built options.

    Important: this fragment does **not** set ``xAxis`` / ``yAxis``. Axis
    chrome is applied by :func:`apply_theme_to_option` onto whatever axis
    shape the chart already built (object or list), so category/data axes
    are never replaced by a bare style dict.

    Title / legend layout keys from the theme (``left``, ``right``, ``top``,
    ``orient``) are defaults only — structural builders and ``user_option``
    still win for keys they set (via deep-merge order in
    :func:`apply_theme_to_option`).
    """
    tooltip = theme.get("tooltip") or {}
    legend = theme.get("legend") or {}
    title = theme.get("title") or {}
    animation = theme.get("animation") or {}

    title_opt: Dict[str, Any] = {
        "left": title.get("left", "left"),
        "top": title.get("top", 10),
        "textStyle": {
            "color": title.get("color"),
            "fontWeight": title.get("font_weight"),
            "fontFamily": theme.get("font_family"),
        },
    }
    if "right" in title:
        title_opt["right"] = title["right"]

    legend_opt: Dict[str, Any] = {
        "show": legend.get("show", True),
        "top": legend.get("top", 10),
        "textStyle": {"color": legend.get("text_color")},
    }
    if "right" in legend:
        legend_opt["right"] = legend["right"]
    elif "left" not in legend:
        legend_opt["right"] = 12
    if "left" in legend:
        legend_opt["left"] = legend["left"]
    if "orient" in legend:
        legend_opt["orient"] = legend["orient"]

    option: Dict[str, Any] = {
        "color": list(theme.get("palette") or []),
        "backgroundColor": theme.get("background"),
        "textStyle": {
            "color": theme.get("text_color"),
            "fontFamily": theme.get("font_family"),
        },
        "title": title_opt,
        "legend": legend_opt,
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


def _ensure_cartesian_plot_grid(option: Dict[str, Any]) -> None:
    """Inject default plot ``grid`` under existing chart/user grid (dict only)."""
    if "xAxis" not in option or "yAxis" not in option:
        return
    existing = option.get("grid")
    if isinstance(existing, list):
        # Multi-grid compose layouts own their geometry.
        return
    if existing is None:
        option["grid"] = dict(_DEFAULT_CARTESIAN_GRID)
        return
    if isinstance(existing, Mapping):
        # Chart-set keys win over defaults.
        option["grid"] = deep_merge(_DEFAULT_CARTESIAN_GRID, existing)


def apply_theme_to_option(
    option: Mapping[str, Any],
    theme: Mapping[str, Any],
    user_option: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Merge theme fragments under ``option``, then apply ``user_option`` last.

    Precedence: theme chrome defaults < structural option < user option.

    Theme layout keys only fill gaps; chart builders and ``merge_option`` keep
    control of positions they set (e.g. pie legend ``top: "middle"``).

    Axis styling is merged into existing ``xAxis`` / ``yAxis`` values whether
    they are a single object or a list, preserving chart-built data/type.
    Axes are **not** injected when the structural option omitted them (pie,
    sankey, gauge, radar, etc.).

    Cartesian charts (both ``xAxis`` and ``yAxis`` present) receive default
    plot ``grid`` padding so title/legend do not cover the series. Chart and
    user ``grid`` keys win over those defaults.
    """
    # Defaults first; structural option wins on keys it sets.
    themed: Dict[str, Any] = deep_merge(theme_to_echarts_option(theme), option)
    style = _axis_style_fragment(theme)
    # Only style axes the chart already declared — do not invent empty axes.
    if "xAxis" in themed:
        themed["xAxis"] = _merge_axis_style(themed.get("xAxis"), style)
    if "yAxis" in themed:
        themed["yAxis"] = _merge_axis_style(themed.get("yAxis"), style)
    # Drop conflicting theme ``right`` when the chart pinned legend to the left.
    legend = themed.get("legend")
    if isinstance(legend, Mapping) and "left" in legend and "right" in legend:
        # Chart chose a side; keep left, drop default right from theme.
        cleaned = dict(legend)
        # Only drop right when it looks like the theme default alongside left.
        if cleaned.get("left") is not None:
            cleaned.pop("right", None)
            themed["legend"] = cleaned
    _ensure_cartesian_plot_grid(themed)
    if user_option:
        # User may replace axes / chrome entirely; honor that after theme chrome.
        themed = deep_merge(themed, user_option)
    return themed


def series_defaults_for(theme: Mapping[str, Any], chart_type: str) -> Dict[str, Any]:
    """Return series default overrides for a chart type from the theme."""
    defaults = theme.get("series_defaults") or {}
    entry = defaults.get(chart_type) or {}
    return dict(entry)
