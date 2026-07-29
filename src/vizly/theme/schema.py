"""Versioned vizly theme schema and validation.

Themes are plain JSON-serializable dicts. Nested sections use TypedDicts
for documentation and static checking; runtime validation is light and
rejects unknown top-level keys that would break round-trip expectations.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Literal, Mapping, Optional, TypedDict, Union

THEME_SCHEMA_VERSION = 1

AssetMode = Literal["local", "cdn"]

# US-trust allowlist for theme assets.cdn when mode == "cdn".
# Host must match these suffixes (see validate_theme).
ALLOWED_CDN_HOST_SUFFIXES = (
    "cdn.jsdelivr.net",
    "unpkg.com",
)


class GridTheme(TypedDict, total=False):
    show: bool
    color: str
    type: str


class AxisTheme(TypedDict, total=False):
    line_color: str
    label_color: str
    name_color: str


class TooltipTheme(TypedDict, total=False):
    bg: str
    border: str
    text: str


class LegendTheme(TypedDict, total=False):
    show: bool
    top: Union[str, int]
    left: Union[str, int]
    right: Union[str, int]
    orient: str
    text_color: str


class TitleTheme(TypedDict, total=False):
    color: str
    font_weight: Union[int, str]
    left: Union[str, int]
    right: Union[str, int]
    top: Union[str, int]


class AnimationTheme(TypedDict, total=False):
    enabled: bool
    duration: int


class LineSeriesDefaults(TypedDict, total=False):
    smooth: bool
    show_symbol: bool
    symbol_size: int
    label_show: bool


class BarSeriesDefaults(TypedDict, total=False):
    label_show: bool
    bar_max_width: int


class PieSeriesDefaults(TypedDict, total=False):
    label_show: bool
    rose_type: Optional[str]


class SeriesDefaults(TypedDict, total=False):
    line: LineSeriesDefaults
    bar: BarSeriesDefaults
    pie: PieSeriesDefaults


class AssetsTheme(TypedDict, total=False):
    mode: AssetMode
    cdn: Optional[str]


class ThemeDict(TypedDict, total=False):
    version: int
    name: str
    locale: str
    font_family: str
    background: str
    text_color: str
    muted_text: str
    palette: List[str]
    colorblind_safe: bool
    grid: GridTheme
    axis: AxisTheme
    tooltip: TooltipTheme
    legend: LegendTheme
    title: TitleTheme
    animation: AnimationTheme
    series_defaults: SeriesDefaults
    assets: AssetsTheme


KNOWN_THEME_KEYS = frozenset(ThemeDict.__annotations__.keys())

REQUIRED_THEME_KEYS = frozenset(
    {
        "version",
        "name",
        "locale",
        "font_family",
        "background",
        "text_color",
        "muted_text",
        "palette",
        "colorblind_safe",
        "grid",
        "axis",
        "tooltip",
        "legend",
        "title",
        "animation",
        "series_defaults",
        "assets",
    }
)


class ThemeValidationError(ValueError):
    """Raised when a theme dict fails schema validation."""


def validate_theme(theme: Mapping[str, Any], *, partial: bool = False) -> Dict[str, Any]:
    """Validate a theme mapping and return a shallow-copied dict.

    Parameters
    ----------
    theme:
        Candidate theme object.
    partial:
        If True, allow incomplete themes (for deep-merge overrides).
        Unknown top-level keys are always rejected.
    """
    if not isinstance(theme, Mapping):
        raise ThemeValidationError(
            f"Theme must be a mapping, got {type(theme).__name__}."
        )

    unknown = set(theme.keys()) - KNOWN_THEME_KEYS
    if unknown:
        keys = ", ".join(sorted(repr(k) for k in unknown))
        raise ThemeValidationError(
            f"Unknown theme key(s): {keys}. "
            f"Known keys: {', '.join(sorted(KNOWN_THEME_KEYS))}."
        )

    if not partial:
        missing = REQUIRED_THEME_KEYS - set(theme.keys())
        if missing:
            keys = ", ".join(sorted(missing))
            raise ThemeValidationError(f"Theme is missing required key(s): {keys}.")

    if "version" in theme and theme["version"] != THEME_SCHEMA_VERSION:
        raise ThemeValidationError(
            f"Unsupported theme schema version {theme['version']!r}; "
            f"expected {THEME_SCHEMA_VERSION}."
        )

    if "palette" in theme:
        palette = theme["palette"]
        if not isinstance(palette, list) or not all(
            isinstance(c, str) for c in palette
        ):
            raise ThemeValidationError(
                "Theme 'palette' must be a list of color strings."
            )

    if "assets" in theme:
        assets = theme["assets"]
        if not isinstance(assets, Mapping):
            raise ThemeValidationError("Theme 'assets' must be a mapping.")
        mode = assets.get("mode")
        if mode is not None and mode not in ("local", "cdn"):
            raise ThemeValidationError(
                f"Theme assets.mode must be 'local' or 'cdn', got {mode!r}."
            )
        cdn = assets.get("cdn")
        if mode == "cdn":
            _validate_cdn_url(cdn)
        elif cdn is not None and cdn != "":
            # Even in local mode, reject disallowed hosts if a CDN URL is set.
            _validate_cdn_url(cdn)

    return dict(theme)


def _validate_cdn_url(cdn: Any) -> None:
    if not isinstance(cdn, str) or not cdn.strip():
        raise ThemeValidationError(
            "Theme assets.cdn must be a non-empty URL string when using CDN assets."
        )
    lowered = cdn.strip().lower()
    if not (lowered.startswith("https://") or lowered.startswith("http://")):
        raise ThemeValidationError(
            f"Theme assets.cdn must be an http(s) URL, got {cdn!r}."
        )
    # Extract host: scheme://host[:port]/path
    without_scheme = lowered.split("://", 1)[1]
    host = without_scheme.split("/", 1)[0].split(":", 1)[0]
    if not any(
        host == suffix or host.endswith("." + suffix)
        for suffix in ALLOWED_CDN_HOST_SUFFIXES
    ):
        allowed = ", ".join(ALLOWED_CDN_HOST_SUFFIXES)
        raise ThemeValidationError(
            f"Theme assets.cdn host {host!r} is not allowlisted. "
            f"Allowed hosts: {allowed}."
        )


def ensure_theme(theme: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate a complete theme and return a deep copy."""
    validated = validate_theme(theme, partial=False)
    return deepcopy(validated)
