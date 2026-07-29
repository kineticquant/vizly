"""HTMX helpers — swap-ready chart fragments.

By default fragments **omit** the ECharts library tags so each ``hx-swap``
does not re-download ~1MB of JS. Put :func:`vizly.integrations._embed.assets_html`
in the parent page ``<head>`` once (see ``examples/htmx_demo``).
"""

from __future__ import annotations

import json
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


def htmx_event_listener_js(
    url: str,
    *,
    target: str = "#vizly-detail",
    swap: str = "innerHTML",
    include: Optional[str] = None,
) -> str:
    """Return a ``<script>`` that POSTs ``vizly:event`` payloads via HTMX.

    Put this once on the parent page (ECharts already loaded). Clicks do **not**
    reload ECharts assets. The server receives JSON with the click payload.

    Example parent page::

        {{ assets_html()|safe }}
        {{ htmx_event_listener_js('/chart/detail')|safe }}
    """
    url_json = json.dumps(url)
    target_json = json.dumps(target)
    swap_json = json.dumps(swap)
    include_js = (
        f"vals.include = {json.dumps(include)};"
        if include
        else ""
    )
    return f"""<script>
(function() {{
  if (window.__vizlyHtmxBound) return;
  window.__vizlyHtmxBound = true;
  window.addEventListener('vizly:event', function(ev) {{
    var detail = ev.detail || {{}};
    if (typeof htmx === 'undefined') {{
      console.warn('vizly HTMX bridge: htmx is not loaded');
      return;
    }}
    var vals = {{ vizly_event: JSON.stringify(detail) }};
    {include_js}
    htmx.ajax('POST', {url_json}, {{
      target: {target_json},
      swap: {swap_json},
      values: vals
    }});
  }});
}})();
</script>"""


def is_htmx_request(headers: Mapping[str, str]) -> bool:
    """True when the request carries the ``HX-Request`` header."""
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
