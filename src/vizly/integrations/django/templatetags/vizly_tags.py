"""Django template tags / filters for vizly charts."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

from django import template
from django.utils.safestring import mark_safe

from vizly.base import BaseChart
from vizly.integrations import _embed

register = template.Library()


def _parse_filter_mode(arg: str) -> Tuple[bool, bool]:
    """Parse ``vizly_html`` filter arg into ``(fragment, include_assets)``.

    Values:
    - ``""`` / ``fragment`` (default): fragment, **no** assets (use ``{% vizly_assets %}``)
    - ``assets``: fragment **with** assets (single-chart template without assets tag)
    - ``full`` / ``document``: full HTML document with assets
    - ``false`` / ``0`` / ``no``: full document (legacy fragment=False)
    """
    cleaned = str(arg or "").strip().lower()
    if cleaned in {"", "true", "1", "yes", "fragment"}:
        return True, False
    if cleaned in {"assets", "with_assets"}:
        return True, True
    if cleaned in {"full", "document", "false", "0", "no"}:
        return False, True
    raise template.TemplateSyntaxError(
        f"vizly_html filter arg {arg!r} not supported. "
        "Use fragment (default), assets, or full."
    )


@register.filter(name="vizly_html")
def vizly_html(chart: BaseChart, mode: str = "fragment") -> str:
    """Filter: ``{{ chart|vizly_html }}`` — fragment, assets omitted by default.

    Multi-chart pages: put ``{% vizly_assets charts=charts %}`` in ``<head>``,
    then ``{{ c|vizly_html }}`` per chart (ECharts once).

    Single chart without the assets tag: ``{{ chart|vizly_html:"assets" }}``.
    Full document: ``{{ chart|vizly_html:"full" }}``.
    """
    use_fragment, include_assets = _parse_filter_mode(mode)
    return mark_safe(
        _embed.chart_html(
            chart,
            fragment=use_fragment,
            include_assets=include_assets,
        )
    )


@register.simple_tag(name="vizly_assets")
def vizly_assets(
    include_gl: bool = False,
    charts: Optional[Sequence[BaseChart]] = None,
) -> str:
    """Tag: ``{% vizly_assets %}`` or ``{% vizly_assets charts=charts %}``.

    Put once in ``<head>`` for dashboards. Pass ``charts`` so GL/plugins load
    automatically when any chart needs them.
    """
    return mark_safe(
        _embed.assets_html(include_gl=include_gl, charts=charts)
    )


@register.simple_tag(name="vizly_chart")
def vizly_chart(
    chart: BaseChart,
    fragment: bool = True,
    width: str = "",
    height: str = "",
    include_assets: bool = False,
) -> str:
    """Tag: ``{% vizly_chart chart %}`` — fragment, assets off by default.

    Multi-chart: ``{% vizly_assets charts=charts %}`` once, then this tag per
    chart. Single-chart without assets tag: ``include_assets=True``.
    """
    return mark_safe(
        _embed.chart_html(
            chart,
            fragment=fragment,
            width=width or None,
            height=height or None,
            include_assets=include_assets,
        )
    )


@register.simple_tag(name="vizly_dashboard")
def vizly_dashboard(
    charts: Sequence[BaseChart],
    title: str = "",
    fragment: bool = True,
    width: str = "",
    height: str = "",
) -> str:
    """Tag: ``{% vizly_dashboard charts %}`` — many charts, ECharts once."""
    return mark_safe(
        _embed.dashboard_html(
            charts,
            title=title or None,
            fragment=fragment,
            width=width or None,
            height=height or None,
            include_assets=True,
        )
    )
