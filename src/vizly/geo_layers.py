"""GeoJSON overlay layers — segregated from basemap pack registration.

Basemap packs (``register_map_pack``, bundled ``world`` / ``usa``, choropleth
``vz.map``) use ``echarts.registerMap``. This module is for FeatureCollection
overlays (polygons, lines, points) composed on a **geo** coordinate system.

China administrative packs remain opt-in only via ``register_map_pack``.
No Baidu Map / blocked CDN defaults.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from vizly.data import DataError

PathLike = Union[str, Path]
GeoJSONLike = Union[Mapping[str, Any], PathLike]


def _load_geojson(source: GeoJSONLike) -> Dict[str, Any]:
    if isinstance(source, Mapping):
        return dict(source)
    path = Path(source)
    return json.loads(path.read_text(encoding="utf-8"))


def _feature_kind(geom_type: str) -> str:
    t = (geom_type or "").lower()
    if t in {"point", "multipoint"}:
        return "point"
    if t in {"linestring", "multilinestring"}:
        return "line"
    return "polygon"


def _as_ring(coords: Any) -> Optional[List[List[float]]]:
    if not isinstance(coords, list) or not coords:
        return None
    ring: List[List[float]] = []
    for c in coords:
        if isinstance(c, (list, tuple)) and len(c) >= 2:
            ring.append([float(c[0]), float(c[1])])
    return ring or None


def _polygon_rings(gtype: str, coords: Any) -> List[List[List[float]]]:
    """Return exterior (+ hole) rings as lon/lat polylines."""
    t = gtype.lower()
    rings: List[List[List[float]]] = []
    if t == "polygon" and isinstance(coords, list):
        for part in coords:
            ring = _as_ring(part)
            if ring:
                rings.append(ring)
    elif t == "multipolygon" and isinstance(coords, list):
        for poly in coords:
            if not isinstance(poly, list):
                continue
            for part in poly:
                ring = _as_ring(part)
                if ring:
                    rings.append(ring)
    return rings


class GeoLayer:
    """One GeoJSON overlay layer for multi-layer map dashboards."""

    def __init__(
        self,
        geojson: GeoJSONLike,
        *,
        name: str = "overlay",
        kind: Optional[str] = None,
        name_property: str = "name",
        id_property: Optional[str] = None,
        style: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.name = name
        self.geojson = _load_geojson(geojson)
        self.name_property = name_property
        self.id_property = id_property
        self.style = dict(style or {})
        self.kind = kind  # point | line | polygon | None=auto

    def features(self) -> List[Mapping[str, Any]]:
        gj = self.geojson
        if gj.get("type") == "FeatureCollection":
            return list(gj.get("features") or [])
        if gj.get("type") == "Feature":
            return [gj]
        raise DataError(
            "GeoLayer expects a GeoJSON Feature or FeatureCollection."
        )

    def series_fragments(self, *, coordinate_system: str = "geo") -> List[Dict[str, Any]]:
        """Build ECharts series fragments for this overlay.

        Polygons attach ``_vizly_polygon_metas`` for HTML fill via custom
        series (``renderItem`` cannot travel through JSON alone).
        """
        points: List[Dict[str, Any]] = []
        lines: List[Dict[str, Any]] = []
        poly_metas: List[Dict[str, Any]] = []
        outline_lines: List[Dict[str, Any]] = []

        for feat in self.features():
            props = feat.get("properties") or {}
            geom = feat.get("geometry") or {}
            gtype = str(geom.get("type") or "")
            kind = self.kind or _feature_kind(gtype)
            label = props.get(self.name_property) or props.get("name") or self.name
            fid = None
            if self.id_property:
                fid = props.get(self.id_property)
            coords = geom.get("coordinates")
            if kind == "point":
                if (
                    gtype.lower() == "point"
                    and isinstance(coords, (list, tuple))
                    and len(coords) >= 2
                ):
                    item = {"name": str(label), "value": [coords[0], coords[1]]}
                    if fid is not None:
                        item["id"] = fid
                    points.append(item)
                elif gtype.lower() == "multipoint":
                    for c in coords or []:
                        if isinstance(c, (list, tuple)) and len(c) >= 2:
                            points.append(
                                {"name": str(label), "value": [c[0], c[1]]}
                            )
            elif kind == "line":
                line_coords = _line_coords(gtype, coords)
                if line_coords:
                    lines.append({"name": str(label), "coords": line_coords})
            else:
                rings = _polygon_rings(gtype, coords)
                if not rings:
                    continue
                fill = self.style.get("fill") or self.style.get("areaColor")
                stroke = self.style.get("stroke") or (
                    (self.style.get("lineStyle") or {}).get("color")
                )
                meta: Dict[str, Any] = {
                    "name": str(label),
                    "rings": rings,
                    "fill": fill or "rgba(47, 111, 237, 0.28)",
                    "stroke": stroke or "#2F6FED",
                    "lineWidth": self.style.get("lineWidth", 1.5),
                    "zlevel": self.style.get("zlevel", 2),
                }
                if fid is not None:
                    meta["id"] = fid
                poly_metas.append(meta)
                for ring in rings:
                    outline_lines.append({"name": str(label), "coords": ring})

        series: List[Dict[str, Any]] = []
        if points:
            series.append(
                {
                    "type": "scatter",
                    "name": self.name,
                    "coordinateSystem": coordinate_system,
                    "data": points,
                    "symbolSize": self.style.get("symbolSize", 10),
                    "zlevel": self.style.get("zlevel", 3),
                }
            )
        if lines:
            series.append(
                {
                    "type": "lines",
                    "name": self.name,
                    "coordinateSystem": coordinate_system,
                    "data": [
                        {"coords": c["coords"], "name": c["name"]}
                        for c in lines
                        if c.get("coords")
                    ],
                    "polyline": True,
                    "lineStyle": self.style.get(
                        "lineStyle", {"width": 2, "opacity": 0.8}
                    ),
                    "zlevel": self.style.get("zlevel", 2),
                }
            )
        if outline_lines:
            series.append(
                {
                    "type": "lines",
                    "name": f"{self.name}_outline",
                    "coordinateSystem": coordinate_system,
                    "data": outline_lines,
                    "polyline": True,
                    "lineStyle": self.style.get(
                        "lineStyle",
                        {"width": 1.5, "color": "#2F6FED", "opacity": 0.9},
                    ),
                    "zlevel": self.style.get("zlevel", 2),
                    "_vizly_polygon_metas": poly_metas,
                }
            )
        elif poly_metas:
            series.append(
                {
                    "type": "lines",
                    "name": f"{self.name}_outline",
                    "coordinateSystem": coordinate_system,
                    "data": [],
                    "polyline": True,
                    "_vizly_polygon_metas": poly_metas,
                }
            )
        return series


def _line_coords(gtype: str, coords: Any) -> Optional[List[List[float]]]:
    t = gtype.lower()
    if t == "linestring" and isinstance(coords, list):
        return _as_ring(coords)
    if t == "multilinestring" and isinstance(coords, list) and coords:
        return _as_ring(coords[0])
    return None


def overlay_geojson(
    geojson: GeoJSONLike,
    *,
    name: str = "overlay",
    kind: Optional[str] = None,
    name_property: str = "name",
    id_property: Optional[str] = None,
    style: Optional[Mapping[str, Any]] = None,
) -> GeoLayer:
    """Create a GeoLayer from a FeatureCollection (path or dict)."""
    return GeoLayer(
        geojson,
        name=name,
        kind=kind,
        name_property=name_property,
        id_property=id_property,
        style=style,
    )


def merge_geo_layers(
    base_option: Mapping[str, Any],
    layers: Sequence[GeoLayer],
    *,
    map_name: str = "world",
) -> Dict[str, Any]:
    """Merge overlay series into a geo/map option (does not mutate input).

    Ensures a single ``geo`` component (shared roam) for overlays. Callers with
    a choropleth ``map`` series should set ``geoIndex: 0`` on that series when
    layers are present.
    """
    out = deepcopy(dict(base_option))
    geo = out.get("geo")
    if not isinstance(geo, Mapping):
        out["geo"] = {
            "map": map_name,
            "roam": True,
            "emphasis": {"label": {"show": True}},
        }
    else:
        geo_out = dict(geo)
        geo_out.setdefault("map", map_name)
        geo_out.setdefault("roam", True)
        out["geo"] = geo_out

    series = list(out.get("series") or [])
    for i, s in enumerate(series):
        if isinstance(s, Mapping) and s.get("type") == "map" and "geoIndex" not in s:
            linked = dict(s)
            linked["geoIndex"] = 0
            linked.pop("roam", None)
            series[i] = linked

    register: Dict[str, Any] = {}
    polygons: List[Dict[str, Any]] = []
    for layer in layers:
        register[f"vizly_layer_{layer.name}"] = layer.geojson
        for frag in layer.series_fragments():
            metas = frag.pop("_vizly_polygon_metas", None) or []
            if metas:
                polygons.extend(metas)
            frag.pop("_vizly_geojson", None)
            frag.pop("_vizly_polygon_overlay", None)
            if frag.get("data") == []:
                continue
            series.append(frag)
    out["series"] = series
    if register:
        out["_vizly_layer_maps"] = register
    if polygons:
        out["_vizly_geo_polygons"] = polygons
    return out


def collect_layer_map_registrations(
    option: Mapping[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Extract overlay GeoJSON packs embedded by :func:`merge_geo_layers`."""
    raw = option.get("_vizly_layer_maps") or {}
    return {str(k): dict(v) for k, v in raw.items()}
