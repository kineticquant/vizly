"""Client-side chart image export (ECharts ``getDataURL``).

vizly does **not** ship headless Chromium. The page that already rendered the
chart can export a PNG/JPEG/SVG data URL::

    // after any vizly HTML embed
    const url = window.__vizly[chartId].toDataURL({ type: "png", pixelRatio: 2 });
    window.__vizly[chartId].downloadImage("chart.png");

Enable ECharts toolbox download without custom JS::

    chart.merge_option({
        "toolbox": {"feature": {"saveAsImage": {"type": "png"}}}
    })

For headless batch jobs, run Playwright (or similar) on ``chart.to_html()``
yourself — that stack is intentionally outside the vizly package.
"""

from __future__ import annotations

from typing import Any, Mapping

from vizly.events import live_option_update_js


class ExportError(RuntimeError):
    """Raised when an export helper cannot run."""


def live_patch_html(
    chart_id: str,
    option: Mapping[str, Any],
    *,
    not_merge: bool = False,
) -> str:
    """Return a ``<script>`` that ``setOption``s an already-embedded chart.

    Use after ``set_data`` / ``set_option_patch`` when the host kept ECharts
    loaded and the chart id is known (see ``window.__vizly``).
    """
    return live_option_update_js(chart_id, option, not_merge=not_merge)


def data_url_help() -> str:
    """Short English hint for hosts that expected server-side ``to_png``."""
    return (
        "Use window.__vizly[<id>].toDataURL() or downloadImage() in the browser. "
        "Server-side Chromium export is not part of vizly; run a headless browser "
        "on chart.to_html() if you need PNG bytes without a UI."
    )


def assert_no_server_raster() -> None:
    """Raise a clear error for removed Playwright-backed APIs."""
    raise ExportError(data_url_help())
