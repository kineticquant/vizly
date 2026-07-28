"""FastAPI helpers for vizly charts."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from vizly.base import BaseChart
from vizly.integrations._embed import (
    assets_html,
    chart_html,
    chart_json,
    chart_option,
    dashboard_html,
)

__all__ = [
    "assets_html",
    "chart_html",
    "chart_json",
    "chart_option",
    "dashboard_html",
    "dashboard_response",
    "html_response",
    "json_response",
    "option_json",
]


def html_response(
    chart: BaseChart,
    *,
    fragment: bool = False,
    status_code: int = 200,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: bool = True,
    **kwargs: Any,
) -> Any:
    """Return a FastAPI/Starlette ``HTMLResponse`` for a vizly chart.

    Multi-chart pages: serve ``assets_html()`` once in the shell, then
    ``html_response(..., fragment=True, include_assets=False)``, or use
    :func:`dashboard_response`.
    """
    try:
        from fastapi.responses import HTMLResponse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "html_response requires fastapi. Install with: pip install 'vizly[fastapi]'"
        ) from exc

    html = chart_html(
        chart,
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
    )
    return HTMLResponse(content=html, status_code=status_code, **kwargs)


def dashboard_response(
    charts: Sequence[BaseChart],
    *,
    title: Optional[str] = None,
    fragment: bool = False,
    status_code: int = 200,
    **kwargs: Any,
) -> Any:
    """Multi-chart HTML with ECharts loaded once."""
    try:
        from fastapi.responses import HTMLResponse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "dashboard_response requires fastapi. Install with: pip install 'vizly[fastapi]'"
        ) from exc

    html = dashboard_html(charts, title=title, fragment=fragment)
    return HTMLResponse(content=html, status_code=status_code, **kwargs)


def json_response(
    chart: BaseChart,
    *,
    status_code: int = 200,
    **kwargs: Any,
) -> Any:
    """Return a FastAPI/Starlette ``JSONResponse`` of the chart option dict."""
    try:
        from fastapi.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "json_response requires fastapi. Install with: pip install 'vizly[fastapi]'"
        ) from exc

    return JSONResponse(content=chart_option(chart), status_code=status_code, **kwargs)


def option_json(chart: BaseChart) -> str:
    """Plain JSON string helper (also useful outside FastAPI)."""
    return chart_json(chart)
