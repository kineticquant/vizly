"""Streamlit helpers for vizly charts.

Streamlit renders each ``components.html`` call in its **own iframe**. That
means N separate ``st_vizly(chart)`` calls load ECharts N times. For many
charts on one page, use :func:`st_dashboard` (or pass a list to
:func:`st_vizly`) so one iframe loads ECharts once.
"""

from __future__ import annotations

import re
from typing import Any, Optional, Sequence, Tuple, Union

from vizly.base import BaseChart
from vizly.integrations._embed import chart_html, dashboard_html

_PX_RE = re.compile(r"^(\d+(?:\.\d+)?)px$", re.IGNORECASE)

ChartOrCharts = Union[BaseChart, Sequence[BaseChart]]


def _resolve_height(
    height: Optional[int], chart_height: str
) -> Tuple[str, int]:
    """Return (css_height, iframe_px) without inventing a mismatched default."""
    if height is not None:
        px = int(height)
        return f"{px}px", px
    match = _PX_RE.match(str(chart_height).strip())
    if match:
        px = int(float(match.group(1)))
        return f"{px}px", px
    # Non-px chart heights (e.g. 100%) — iframe still needs a pixel box.
    return str(chart_height), 420


def _as_chart_list(chart_or_charts: ChartOrCharts) -> Sequence[BaseChart]:
    if isinstance(chart_or_charts, BaseChart):
        return (chart_or_charts,)
    charts = list(chart_or_charts)
    if not charts:
        raise ValueError("st_vizly / st_dashboard requires at least one chart.")
    for i, child in enumerate(charts):
        if not isinstance(child, BaseChart):
            raise TypeError(
                f"charts[{i}] must be a vizly BaseChart, got {type(child).__name__}."
            )
    return charts


def st_vizly(
    chart_or_charts: ChartOrCharts,
    *,
    width: Optional[str] = None,
    height: Optional[int] = None,
    scrolling: bool = False,
    title: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Render one chart, or many charts in **one** iframe (ECharts once).

    - Single ``BaseChart``: full HTML document with assets (required per iframe).
    - Sequence of charts: same as :func:`st_dashboard` — one ECharts load.

    Returns the Streamlit component value from ``components.html``.
    """
    try:
        import streamlit.components.v1 as components
    except ImportError as exc:  # pragma: no cover - exercised via importorskip
        raise ImportError(
            "st_vizly requires streamlit. Install with: pip install 'vizly[streamlit]'"
        ) from exc

    charts = _as_chart_list(chart_or_charts)
    if len(charts) == 1:
        chart = charts[0]
        css_height, px = _resolve_height(height, chart.height)
        html = chart_html(chart, fragment=False, width=width, height=css_height)
    else:
        # Stack child heights for a usable iframe box when height= omitted.
        if height is not None:
            px = int(height)
        else:
            total = 0
            for child in charts:
                _, child_px = _resolve_height(None, child.height)
                total += child_px + 48  # heading / padding budget
            px = max(total, 420)
        html = dashboard_html(
            charts,
            title=title,
            fragment=False,
            width=width,
            height=None,
        )
    return components.html(html, height=px, scrolling=scrolling, **kwargs)


def st_dashboard(
    charts: Sequence[BaseChart],
    *,
    width: Optional[str] = None,
    height: Optional[int] = None,
    scrolling: bool = False,
    title: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """Render many charts in one Streamlit iframe (ECharts loaded once).

    Prefer this over calling :func:`st_vizly` once per chart.
    """
    return st_vizly(
        charts,
        width=width,
        height=height,
        scrolling=scrolling,
        title=title,
        **kwargs,
    )
