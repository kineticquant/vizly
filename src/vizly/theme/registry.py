"""Theme registry: register, resolve, list, load, and export themes."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, TextIO, Union

from vizly.theme.merge import deep_merge
from vizly.theme.presets import PRESETS, get_preset, list_presets
from vizly.theme.schema import ThemeValidationError, ensure_theme, validate_theme

PathLike = Union[str, Path]
ThemeSource = Union[PathLike, TextIO, Mapping[str, Any]]

_user_themes: Dict[str, Dict[str, Any]] = {}


def reset_registry() -> None:
    """Clear user-registered themes (builtins remain). Intended for tests."""
    _user_themes.clear()


def register_theme(name: str, theme: Mapping[str, Any]) -> Dict[str, Any]:
    """Register a named theme in the process-local user registry.

    Partial themes are deep-merged onto the ``default`` preset before storage
    so registered themes are always complete and exportable.
    """
    if not name or not isinstance(name, str):
        raise ThemeValidationError("Theme name must be a non-empty string.")
    if name in PRESETS:
        raise ThemeValidationError(
            f"Cannot overwrite builtin theme {name!r}. "
            "Choose a different name or use set_theme() for session overrides."
        )
    partial = validate_theme(theme, partial=True)
    resolved = deep_merge(get_preset("default"), partial)
    resolved["name"] = name
    stored = ensure_theme(resolved)
    _user_themes[name] = stored
    return deepcopy(stored)


def get_registered_theme(name: str) -> Dict[str, Any]:
    """Return a deep copy of a builtin or user-registered theme by name.

    Prefer :func:`vizly.config.get_theme` (no args) for the process-global
    current theme. This function looks up a theme by name only.
    """
    if name in _user_themes:
        return deepcopy(_user_themes[name])
    if name in PRESETS:
        return get_preset(name)
    available = ", ".join(list_themes())
    raise KeyError(f"Unknown theme {name!r}. Available themes: {available}.")


# Back-compat alias for internal callers; prefer get_registered_theme.
get_theme = get_registered_theme


def list_themes() -> list[str]:
    """Return builtin preset names followed by user-registered names."""
    return list_presets() + sorted(_user_themes.keys())


def load_theme(
    source: ThemeSource,
    *,
    activate: bool = False,
    name: Optional[str] = None,
    register: bool = False,
) -> Dict[str, Any]:
    """Load a theme from a path, file-like object, or dict.

    Parameters
    ----------
    source:
        JSON file path, open text file, or theme mapping.
    activate:
        If True, **replace** the process-global current theme with the loaded
        theme (does not deep-merge onto the previous session theme).
    name:
        Optional name to stamp onto the theme (and use when registering).
    register:
        If True, register the theme under ``name`` or the theme's own name.
    """
    raw = _read_theme_source(source)
    partial = validate_theme(raw, partial=True)
    base_name = name or partial.get("name") or "custom"
    resolved = deep_merge(get_preset("default"), partial)
    resolved["name"] = base_name
    theme = ensure_theme(resolved)

    if register:
        register_theme(base_name, theme)

    if activate:
        # Local import avoids circular dependency with config.
        from vizly import config as _config

        _config.replace_theme(theme)

    return deepcopy(theme)


def export_theme(
    name_or_theme: Union[str, Mapping[str, Any]],
    path: Optional[PathLike] = None,
    *,
    indent: int = 2,
) -> str:
    """Serialize a theme to JSON. Optionally write to ``path``.

    Returns the JSON string always.
    """
    if isinstance(name_or_theme, str):
        theme = get_registered_theme(name_or_theme)
    else:
        # Explicit fill from default for partial dicts (not a silent catch).
        partial = validate_theme(name_or_theme, partial=True)
        theme = ensure_theme(deep_merge(get_preset("default"), partial))

    text = json.dumps(theme, indent=indent, ensure_ascii=False) + "\n"
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text


def _read_theme_source(source: ThemeSource) -> Dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)

    if hasattr(source, "read"):
        text = source.read()  # type: ignore[union-attr]
        data = json.loads(text)
    else:
        path = Path(source)  # type: ignore[arg-type]
        data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ThemeValidationError(
            f"Theme JSON must be an object, got {type(data).__name__}."
        )
    return data
