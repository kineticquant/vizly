"""Shared embed contract for framework integrations.

Modes
-----
- full document (``fragment=False``): Streamlit, standalone pages, FastAPI HTML
- fragment (``fragment=True``): Flask/Django templates, HTMX swaps
- dashboard: many charts, ECharts (+ GL/plugins/maps) loaded **once**
- JSON: SPA / client re-init via ``to_option`` / ``to_json``

``include_assets``
------------------
When ``False``, the fragment/page omits vendored ECharts ``<script>`` tags.
Use that for HTMX swaps and multi-chart template pages where the parent
document already loaded ECharts once via :func:`assets_html`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from vizly.base import BaseChart
from vizly.config import get_theme, resolve_theme
from vizly.render import build_script_tags

ThemeLike = Union[str, Mapping[str, Any]]


def _aggregate_asset_flags(
    charts: Sequence[BaseChart],
) -> tuple:
    """Return ``(include_gl, plugins)`` needed for ``charts``."""
    from vizly.charts.compose import _aggregate_child_render_deps

    need_gl, plugins, _maps = _aggregate_child_render_deps(
        list(charts), load_maps=False
    )
    return need_gl, plugins


def assets_html(
    theme: Optional[ThemeLike] = None,
    *,
    include_gl: bool = False,
    plugins: Optional[List[str]] = None,
    charts: Optional[Sequence[BaseChart]] = None,
) -> str:
    """Return ECharts ``<script>`` tags for a page ``<head>`` (load once).

    Pass ``charts=`` to include GL / wordcloud / liquidfill automatically when
    any child needs them. Manual ``include_gl`` / ``plugins`` still union in.
    """
    if theme is None:
        resolved = get_theme()
    elif isinstance(theme, str):
        resolved = resolve_theme(theme)
    elif isinstance(theme, Mapping):
        resolved = resolve_theme(theme)
    else:
        raise TypeError(
            f"theme expected str, dict, or None, got {type(theme).__name__}."
        )
    plugin_list = list(plugins or [])
    need_gl = include_gl
    if charts is not None:
        auto_gl, auto_plugins = _aggregate_asset_flags(charts)
        need_gl = need_gl or auto_gl
        for name in auto_plugins:
            if name not in plugin_list:
                plugin_list.append(name)
    scripts, _mode = build_script_tags(
        resolved, include_gl=need_gl, plugins=plugin_list or None
    )
    return scripts


def chart_html(
    chart: BaseChart,
    *,
    fragment: bool = False,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: bool = True,
    message_origin: Optional[str] = None,
    chart_id: Optional[str] = None,
) -> str:
    """Render a vizly chart to HTML (full document or fragment).

    Does **not** mutate ``chart`` when ``width`` / ``height`` are passed —
    overrides apply only to this render call.

    For **multiple charts on one page**, load ECharts once::

        from vizly.integrations import assets_html, chart_html
        head = assets_html(charts=[c1, c2])
        a = chart_html(c1, fragment=True, include_assets=False)
        b = chart_html(c2, fragment=True, include_assets=False)

    Or use :func:`dashboard_html` / ``vz.page(...)``.

    ``message_origin``: ``postMessage`` targetOrigin. Default is same-origin.
    Pass ``"*"`` only for cross-origin embed bridges (e.g. Streamlit).
    """
    # Ensure map packs are loaded when HTML needs registerMap.
    if hasattr(chart, "_ensure_maps"):
        chart._ensure_maps()
    return chart.to_html(
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
        message_origin=message_origin,
        chart_id=chart_id,
    )


def dashboard_html(
    charts: Sequence[BaseChart],
    *,
    title: Optional[str] = None,
    fragment: bool = False,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: bool = True,
    theme: Optional[ThemeLike] = None,
    connect: bool = True,
    message_origin: Optional[str] = None,
) -> str:
    """Render multiple charts with ECharts (+ maps/plugins) loaded once.

    Preferred helper for Flask/Django/FastAPI/Streamlit multi-chart pages.
    ``connect=True`` links charts for shared tooltip / brush.
    ``message_origin``: forwarded to each child click bridge (``None`` =
    same-origin; pass ``"*"`` only for cross-origin bridges).
    """
    from vizly.charts.compose import PageChart

    page = PageChart(charts=list(charts), title=title, theme=theme, connect=connect)
    return page.to_html(
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
        message_origin=message_origin,
    )


def chart_json(chart: BaseChart, *, indent: Optional[int] = None) -> str:
    """Serialize chart option JSON."""
    return chart.to_json(indent=indent)


def chart_option(chart: BaseChart) -> Dict[str, Any]:
    """Return the resolved ECharts option dict."""
    return chart.to_option()
