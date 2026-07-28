"""Map resolution: worldwide atlas by default, regional packs as needed.

Bundled starters: ``world`` (default) and ``usa`` (regional).
China administrative packs are never shipped or auto-selected — register
explicitly via :func:`register_map_pack`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

from vizly.data import DataError

PathLike = Union[str, Path]

# Process-local opt-in packs (name -> geojson). Never auto-loaded.
_OPT_IN_MAPS: Dict[str, Dict[str, Any]] = {}

CHINA_MAP_NAMES = frozenset({"china", "china-cities", "china-contour"})
BUNDLED_MAPS = ("world", "usa")


def list_opt_in_maps() -> list[str]:
    return sorted(_OPT_IN_MAPS)


def list_bundled_maps() -> list[str]:
    return list(BUNDLED_MAPS)


def register_map_pack(
    name: str,
    geojson: Union[Mapping[str, Any], PathLike],
) -> str:
    """Explicitly register a non-bundled map pack (e.g. China provinces).

    China administrative packs are **opt-in only** — they are not shipped in
    the default vizly wheel and are never used unless you call this.
    """
    key = name.strip().lower()
    if not key:
        raise DataError("Map pack name must be a non-empty string.")
    if isinstance(geojson, (str, Path)):
        path = Path(geojson)
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = dict(geojson)
    if not isinstance(data, dict):
        raise DataError("Map pack GeoJSON must be a JSON object.")
    _OPT_IN_MAPS[key] = data
    return key


def get_opt_in_map(name: str) -> Optional[Dict[str, Any]]:
    return _OPT_IN_MAPS.get(name.strip().lower())


def reset_opt_in_maps() -> None:
    """Clear opt-in packs (tests)."""
    _OPT_IN_MAPS.clear()


def resolve_map_geojson(name: str) -> Dict[str, Any]:
    """Resolve bundled world/usa or an explicitly registered opt-in pack."""
    from vizly.render import RenderError, load_map_geojson

    key = name.strip().lower()
    if key in {"us", "usa", "united states"}:
        key = "usa"
    elif key in {"world", "earth"}:
        key = "world"

    if key in CHINA_MAP_NAMES and key not in _OPT_IN_MAPS:
        raise DataError(
            f"Map {name!r} is a China administrative pack and is opt-in only. "
            "Call vizly.register_map_pack('china', geojson_or_path) after "
            "supplying your own GeoJSON. Defaults ship the world atlas "
            "(plus a bundled USA regional pack); China is never auto-selected."
        )
    if key in _OPT_IN_MAPS:
        return _OPT_IN_MAPS[key]
    try:
        return load_map_geojson(key)
    except RenderError as exc:
        available = ", ".join([*BUNDLED_MAPS, *list_opt_in_maps()])
        raise DataError(
            f"Unknown map {name!r}. Available: {available}."
        ) from exc
