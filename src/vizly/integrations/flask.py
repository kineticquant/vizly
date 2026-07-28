"""Flask helpers for vizly charts."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from vizly.base import BaseChart
from vizly.integrations import _embed

assets_html = _embed.assets_html
dashboard_html = _embed.dashboard_html


def chart_html(
    chart: BaseChart,
    *,
    fragment: bool = True,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: bool = True,
) -> str:
    """HTML string for Jinja templates (fragment by default).

    Multi-chart pages: put ``assets_html()`` in ``<head>`` once, then
    ``chart_html(..., include_assets=False)`` per chart — or use
    :func:`dashboard_html`.
    """
    return _embed.chart_html(
        chart,
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
    )


def chart_response(
    chart: BaseChart,
    *,
    fragment: bool = False,
    status: int = 200,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: bool = True,
    **kwargs: Any,
) -> Any:
    """Return a ``flask.Response`` with chart HTML."""
    try:
        from flask import Response
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "chart_response requires flask. Install with: pip install 'vizly[flask]'"
        ) from exc

    html = chart_html(
        chart,
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
    )
    return Response(html, status=status, mimetype="text/html; charset=utf-8", **kwargs)


def dashboard_response(
    charts: Sequence[BaseChart],
    *,
    title: Optional[str] = None,
    fragment: bool = False,
    status: int = 200,
    **kwargs: Any,
) -> Any:
    """Return a Flask response for a multi-chart dashboard (assets once)."""
    try:
        from flask import Response
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "dashboard_response requires flask. Install with: pip install 'vizly[flask]'"
        ) from exc

    html = dashboard_html(charts, title=title, fragment=fragment)
    return Response(html, status=status, mimetype="text/html; charset=utf-8", **kwargs)


def chart_json_response(
    chart: BaseChart,
    *,
    status: int = 200,
) -> Any:
    """Return a Flask JSON response of the chart option."""
    try:
        from flask import jsonify
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "chart_json_response requires flask. Install with: pip install 'vizly[flask]'"
        ) from exc

    resp = jsonify(_embed.chart_option(chart))
    resp.status_code = status
    return resp
