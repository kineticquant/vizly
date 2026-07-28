"""HTMX helpers — swap-ready chart fragments.

By default fragments **omit** the ECharts library tags so each ``hx-swap``
does not re-download ~1MB of JS. Put :func:`vizly.integrations._embed.assets_html`
in the parent page ``<head>`` once (see ``examples/htmx_demo``).
"""

from __future__ import annotations

from typing import Mapping, Optional

from vizly.base import BaseChart
from vizly.integrations import _embed


def htmx_chart_fragment(
    chart: BaseChart,
    *,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: bool = False,
) -> str:
    """Return a single-root HTML fragment suitable for ``hx-swap``.

    The root node is ``div.vizly-embed[data-vizly-fragment=1]``.

    ``include_assets`` defaults to ``False`` — the parent page should load
    ECharts once via :func:`vizly.integrations._embed.assets_html`.
    """
    return _embed.chart_html(
        chart,
        fragment=True,
        width=width,
        height=height,
        include_assets=include_assets,
    )


def is_htmx_request(headers: Mapping[str, str]) -> bool:
    """True when the request carries the ``HX-Request`` header."""
    # Support both WSGI environ style and normalized header maps.
    for key, value in headers.items():
        if key.lower().replace("_", "-") in {"hx-request", "http-hx-request"}:
            return str(value).lower() in {"true", "1", "yes"}
    return False


def htmx_or_full(
    chart: BaseChart,
    headers: Mapping[str, str],
    *,
    width: Optional[str] = None,
    height: Optional[str] = None,
    include_assets: Optional[bool] = None,
) -> str:
    """Fragment for HTMX requests; full document otherwise.

    When ``include_assets`` is omitted: ``False`` for HTMX fragments (parent
    already has ECharts), ``True`` for full documents.
    """
    fragment = is_htmx_request(headers)
    if include_assets is None:
        include_assets = not fragment
    return _embed.chart_html(
        chart,
        fragment=fragment,
        width=width,
        height=height,
        include_assets=include_assets,
    )
