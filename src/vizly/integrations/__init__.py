"""Framework integrations for vizly (Streamlit, FastAPI, Flask, Django, HTMX)."""

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
]
