"""Builtin vizly theme presets (US-trust visual direction).

Avoid indigo/Inter AI-startup defaults and pyecharts gallery themes
(macarons, shine, etc.). Palettes lean colorblind-aware and restrained.

Ops presets ``ops_grafana`` / ``ops_cloudwatch`` / ``ops_kibana`` are visual
inspiration only (not affiliated with Grafana Labs, AWS, or Elastic).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from vizly.theme.merge import deep_merge
from vizly.theme.schema import THEME_SCHEMA_VERSION

# Shared structural defaults; presets override colors / chrome.
_BASE: Dict[str, Any] = {
    "version": THEME_SCHEMA_VERSION,
    "locale": "en-US",
    "font_family": '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
    "colorblind_safe": True,
    "grid": {"show": True, "color": "#E5E7EB", "type": "solid"},
    "axis": {
        "line_color": "#D1D5DB",
        "label_color": "#4B5563",
        "name_color": "#374151",
    },
    "tooltip": {
        "bg": "rgba(255,255,255,0.96)",
        "border": "#E5E7EB",
        "text": "#111827",
    },
    "legend": {"show": True, "top": "2%", "text_color": "#374151"},
    "title": {"color": "#111827", "font_weight": 600},
    "animation": {"enabled": True, "duration": 400},
    "series_defaults": {
        "line": {
            "smooth": True,
            "show_symbol": True,
            "symbol_size": 6,
            "label_show": False,
        },
        "bar": {"label_show": False, "bar_max_width": 48},
        "pie": {"label_show": True, "rose_type": None},
    },
    "assets": {"mode": "local", "cdn": None},
}


def _preset(name: str, **overrides: Any) -> Dict[str, Any]:
    return deep_merge(_BASE, {"name": name, **overrides})


# Clean US analytics light — primary product look.
DEFAULT: Dict[str, Any] = _preset(
    "default",
    background="#FFFFFF",
    text_color="#111827",
    muted_text="#6B7280",
    # Navy / steel / teal / amber / coral — not indigo-violet marketing.
    palette=[
        "#0B1F33",
        "#2F6FED",
        "#12A594",
        "#E2A03F",
        "#D64545",
        "#7C8C9E",
        "#5B4B8A",
        "#2D9CDB",
    ],
)

# Explicit light alias with slightly stronger axis contrast.
LIGHT: Dict[str, Any] = _preset(
    "light",
    background="#FFFFFF",
    text_color="#0F172A",
    muted_text="#64748B",
    palette=list(DEFAULT["palette"]),
    axis={
        "line_color": "#CBD5E1",
        "label_color": "#334155",
        "name_color": "#1E293B",
    },
)

# Dark dashboard — restrained, not neon.
DARK: Dict[str, Any] = _preset(
    "dark",
    background="#0F172A",
    text_color="#E2E8F0",
    muted_text="#94A3B8",
    palette=[
        "#93C5FD",
        "#5EEAD4",
        "#FCD34D",
        "#FCA5A5",
        "#C4B5FD",
        "#86EFAC",
        "#FDBA74",
        "#A5B4FC",
    ],
    grid={"show": True, "color": "#1E293B", "type": "solid"},
    axis={
        "line_color": "#334155",
        "label_color": "#94A3B8",
        "name_color": "#CBD5E1",
    },
    tooltip={
        "bg": "rgba(15,23,42,0.96)",
        "border": "#334155",
        "text": "#E2E8F0",
    },
    legend={"show": True, "top": "2%", "text_color": "#CBD5E1"},
    title={"color": "#F1F5F9", "font_weight": 600},
)

# Navy/steel finance-boardroom.
CORPORATE: Dict[str, Any] = _preset(
    "corporate",
    background="#FFFFFF",
    text_color="#0B1F33",
    muted_text="#5B6B7C",
    palette=[
        "#0B1F33",
        "#1F4E79",
        "#2F6FED",
        "#5B7C99",
        "#C5A46E",
        "#8B9AAB",
        "#3D5A80",
        "#98C1D9",
    ],
)

# Near-print, minimal chrome.
MINIMAL: Dict[str, Any] = _preset(
    "minimal",
    background="#FFFFFF",
    text_color="#111111",
    muted_text="#666666",
    palette=[
        "#111111",
        "#444444",
        "#777777",
        "#2F6FED",
        "#12A594",
        "#AAAAAA",
        "#D64545",
        "#E2A03F",
    ],
    grid={"show": False, "color": "#EEEEEE", "type": "solid"},
    legend={"show": False, "top": "2%", "text_color": "#444444"},
    animation={"enabled": False, "duration": 0},
    series_defaults={
        "line": {
            "smooth": False,
            "show_symbol": False,
            "symbol_size": 4,
            "label_show": False,
        },
        "bar": {"label_show": False, "bar_max_width": 36},
        "pie": {"label_show": True, "rose_type": None},
    },
)

# Higher-contrast / accessibility leaning.
CONTRAST: Dict[str, Any] = _preset(
    "contrast",
    background="#FFFFFF",
    text_color="#000000",
    muted_text="#333333",
    colorblind_safe=True,
    palette=[
        "#000000",
        "#0072B2",
        "#009E73",
        "#D55E00",
        "#CC79A7",
        "#F0E442",
        "#56B4E9",
        "#E69F00",
    ],
    grid={"show": True, "color": "#000000", "type": "solid"},
    axis={
        "line_color": "#000000",
        "label_color": "#000000",
        "name_color": "#000000",
    },
    tooltip={
        "bg": "#FFFFFF",
        "border": "#000000",
        "text": "#000000",
    },
    legend={"show": True, "top": "2%", "text_color": "#000000"},
    title={"color": "#000000", "font_weight": 700},
)

# --- Ops-inspired presets -------------------------------------------------
# Visual inspiration only. Not affiliated with Grafana Labs, Amazon Web
# Services, or Elastic. No logos, fonts, or proprietary design-system assets
# are copied. Public theme IDs use an ``ops_`` prefix (zero trademark surface).

_OPS_SERIES: Dict[str, Any] = {
    "line": {
        "smooth": False,
        "show_symbol": False,
        "symbol_size": 4,
        "label_show": False,
    },
    "bar": {"label_show": False, "bar_max_width": 28},
    "pie": {"label_show": True, "rose_type": None},
}

_OPS_FONT = '"Roboto Mono", "IBM Plex Mono", "Consolas", monospace'

# Dark panel aesthetic inspired by common Grafana-style dashboards.
OPS_GRAFANA: Dict[str, Any] = _preset(
    "ops_grafana",
    background="#111217",
    text_color="#D8D9DA",
    muted_text="#8E8E8E",
    font_family=_OPS_FONT,
    colorblind_safe=True,
    palette=[
        "#5794F2",
        "#B877D9",
        "#FF9830",
        "#73BF69",
        "#F2495C",
        "#FADE2A",
        "#8AB8FF",
        "#FF7383",
    ],
    grid={"show": True, "color": "#2C3235", "type": "solid"},
    axis={
        "line_color": "#3D3D3D",
        "label_color": "#9FA7B3",
        "name_color": "#CCCCDC",
    },
    tooltip={
        "bg": "rgba(24,27,31,0.96)",
        "border": "#3D3D3D",
        "text": "#D8D9DA",
    },
    legend={"show": True, "top": "2%", "text_color": "#CCCCDC"},
    title={"color": "#D8D9DA", "font_weight": 500},
    animation={"enabled": False, "duration": 0},
    series_defaults=_OPS_SERIES,
)

# Dark console aesthetic inspired by common CloudWatch-style metrics UIs.
OPS_CLOUDWATCH: Dict[str, Any] = _preset(
    "ops_cloudwatch",
    background="#232F3E",
    text_color="#FFFFFF",
    muted_text="#AAB7B8",
    font_family='"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
    colorblind_safe=True,
    palette=[
        "#FF9900",
        "#1B9AAA",
        "#2E7DFF",
        "#EC7211",
        "#7AA116",
        "#DD344C",
        "#EDFDFF",
        "#8C4FFF",
    ],
    grid={"show": True, "color": "#3B4A5A", "type": "solid"},
    axis={
        "line_color": "#545B64",
        "label_color": "#D5DBDB",
        "name_color": "#FFFFFF",
    },
    tooltip={
        "bg": "rgba(22,30,41,0.96)",
        "border": "#545B64",
        "text": "#FFFFFF",
    },
    legend={"show": True, "top": "2%", "text_color": "#D5DBDB"},
    title={"color": "#FFFFFF", "font_weight": 600},
    animation={"enabled": False, "duration": 0},
    series_defaults=_OPS_SERIES,
)

# Dark analytics aesthetic inspired by common Kibana-style analytics UIs.
OPS_KIBANA: Dict[str, Any] = _preset(
    "ops_kibana",
    background="#1D1E24",
    text_color="#DFE5EF",
    muted_text="#98A2B3",
    font_family='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
    colorblind_safe=True,
    palette=[
        "#00BFB3",
        "#F04E98",
        "#FEC514",
        "#00A69B",
        "#6092C0",
        "#E7664C",
        "#9170B8",
        "#6DCCB1",
    ],
    grid={"show": True, "color": "#343741", "type": "dashed"},
    axis={
        "line_color": "#343741",
        "label_color": "#98A2B3",
        "name_color": "#DFE5EF",
    },
    tooltip={
        "bg": "rgba(29,30,36,0.96)",
        "border": "#343741",
        "text": "#DFE5EF",
    },
    legend={"show": True, "top": "2%", "text_color": "#DFE5EF"},
    title={"color": "#DFE5EF", "font_weight": 600},
    animation={"enabled": True, "duration": 200},
    series_defaults=_OPS_SERIES,
)

PRESETS: Dict[str, Dict[str, Any]] = {
    "default": DEFAULT,
    "light": LIGHT,
    "dark": DARK,
    "corporate": CORPORATE,
    "minimal": MINIMAL,
    "contrast": CONTRAST,
    "ops_grafana": OPS_GRAFANA,
    "ops_cloudwatch": OPS_CLOUDWATCH,
    "ops_kibana": OPS_KIBANA,
}


def get_preset(name: str) -> Dict[str, Any]:
    """Return a deep copy of a builtin preset by name."""
    try:
        return deepcopy(PRESETS[name])
    except KeyError as exc:
        available = ", ".join(sorted(PRESETS))
        raise KeyError(
            f"Unknown builtin theme {name!r}. Available presets: {available}."
        ) from exc


def list_presets() -> list[str]:
    """Return builtin preset names in stable order."""
    return list(PRESETS.keys())
