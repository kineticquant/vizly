"""vizly theme package — schema, merge, presets, registry, and ECharts apply."""

from vizly.theme.apply import (
    apply_theme_to_option,
    series_defaults_for,
    theme_to_echarts_option,
)
from vizly.theme.merge import deep_merge
from vizly.theme.registry import (
    export_theme,
    get_registered_theme,
    list_themes,
    load_theme,
    register_theme,
)
from vizly.theme.schema import (
    ALLOWED_CDN_HOST_SUFFIXES,
    THEME_SCHEMA_VERSION,
    ThemeValidationError,
)

__all__ = [
    "ALLOWED_CDN_HOST_SUFFIXES",
    "THEME_SCHEMA_VERSION",
    "ThemeValidationError",
    "apply_theme_to_option",
    "deep_merge",
    "export_theme",
    "get_registered_theme",
    "list_themes",
    "load_theme",
    "register_theme",
    "series_defaults_for",
    "theme_to_echarts_option",
]
