"""Django helpers and app config for vizly template tags.

Add to Django settings::

    INSTALLED_APPS = [
        ...,
        "vizly.integrations.django",
    ]

Then in templates (multi-chart / dashboard — ECharts once)::

    {% load vizly_tags %}
    <head>{% vizly_assets charts=charts %}</head>
    {% vizly_chart c1 %}
    {% vizly_chart c2 %}
    {{ c3|vizly_html }}

Or one HTML blob::

    {% vizly_dashboard charts %}

Single chart without ``{% vizly_assets %}``::

    {% vizly_chart chart include_assets=True %}
    {{ chart|vizly_html:"assets" }}
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from vizly.base import BaseChart
from vizly.integrations import _embed

assets_html = _embed.assets_html
dashboard_html = _embed.dashboard_html


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
    """Return a Django ``HttpResponse`` with chart HTML."""
    try:
        from django.http import HttpResponse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "chart_response requires django. Install with: pip install 'vizly[django]'"
        ) from exc

    html = _embed.chart_html(
        chart,
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
    )
    return HttpResponse(
        html, status=status, content_type="text/html; charset=utf-8", **kwargs
    )


def dashboard_response(
    charts: Sequence[BaseChart],
    *,
    title: Optional[str] = None,
    fragment: bool = False,
    status: int = 200,
    **kwargs: Any,
) -> Any:
    """Multi-chart Django response (ECharts loaded once)."""
    try:
        from django.http import HttpResponse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "dashboard_response requires django. Install with: pip install 'vizly[django]'"
        ) from exc

    html = dashboard_html(charts, title=title, fragment=fragment)
    return HttpResponse(
        html, status=status, content_type="text/html; charset=utf-8", **kwargs
    )


def chart_json_response(
    chart: BaseChart,
    *,
    status: int = 200,
) -> Any:
    """Return a Django ``JsonResponse`` of the chart option."""
    try:
        from django.http import JsonResponse
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "chart_json_response requires django. Install with: pip install 'vizly[django]'"
        ) from exc

    return JsonResponse(_embed.chart_option(chart), status=status, safe=False)
