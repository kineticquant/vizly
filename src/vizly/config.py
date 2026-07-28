"""Process-global session configuration (current theme).

The current theme is process-local state. Use :func:`set_theme` once per app
or session; pass ``theme=`` on individual charts for overrides that do not
mutate this global.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, Optional, Union

from vizly.theme.merge import deep_merge
from vizly.theme.presets import get_preset
from vizly.theme.registry import get_registered_theme
from vizly.theme.schema import ensure_theme, validate_theme

ThemeLike = Union[str, Mapping[str, Any]]

_current_theme: Dict[str, Any] = get_preset("default")


def reset_config() -> None:
    """Reset the global theme to ``default``. Intended for tests."""
    global _current_theme
    _current_theme = get_preset("default")


def get_theme() -> Dict[str, Any]:
    """Return a deep copy of the process-global current theme."""
    return deepcopy(_current_theme)


def replace_theme(theme: Mapping[str, Any]) -> Dict[str, Any]:
    """Replace the process-global theme with a fully resolved theme dict.

    Used by :func:`vizly.theme.registry.load_theme` when ``activate=True``.
    Unlike :func:`set_theme` with a dict, this does not merge onto the prior
    session theme.
    """
    global _current_theme
    _current_theme = ensure_theme(theme)
    return get_theme()


def set_theme(theme: ThemeLike) -> Dict[str, Any]:
    """Set the process-global current theme.

    - If ``theme`` is a string, load that builtin/registered theme by name
      (full replace).
    - If ``theme`` is a dict, deep-merge it over the current theme (partial
      overrides allowed). The result becomes the new current theme.
    """
    global _current_theme
    if isinstance(theme, str):
        _current_theme = ensure_theme(get_registered_theme(theme))
    elif isinstance(theme, Mapping):
        partial = validate_theme(theme, partial=True)
        merged = deep_merge(_current_theme, partial)
        if "name" not in partial:
            # Keep prior name unless caller renamed.
            merged["name"] = _current_theme.get("name", "custom")
        _current_theme = ensure_theme(merged)
    else:
        raise TypeError(
            f"set_theme expected str or dict, got {type(theme).__name__}."
        )
    return get_theme()


def resolve_theme(theme: Optional[ThemeLike] = None) -> Dict[str, Any]:
    """Resolve a chart-level theme override without mutating global state.

    Precedence for callers that stack overrides themselves:
    preset / registered base < ``set_theme`` dict < chart ``theme=`` override.

    - ``None`` → copy of current global theme
    - ``str`` → named builtin/registered theme
    - ``dict`` → deep-merge over current global theme
    """
    if theme is None:
        return get_theme()
    if isinstance(theme, str):
        return ensure_theme(get_registered_theme(theme))
    if isinstance(theme, Mapping):
        partial = validate_theme(theme, partial=True)
        return ensure_theme(deep_merge(_current_theme, partial))
    raise TypeError(
        f"theme override expected str, dict, or None, got {type(theme).__name__}."
    )
