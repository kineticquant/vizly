"""Geo / map charts — worldwide by default; no Baidu Map provider.

Trust posture (vendored/allowlisted assets, English-first ``en-US`` chrome) is
separate from geography: the default map is the world atlas. USA is a bundled
regional pack; China administrative packs remain explicit opt-in only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from vizly.base import BaseChart
from vizly.charts._helpers import prepare_frame
from vizly.data import DataError, column_values, require_columns
from vizly.maps import resolve_map_geojson


def _normalize_map_name(name: str) -> str:
    key = name.strip().lower()
    if key in {"us", "usa", "united states"}:
        return "usa"
    if key in {"world", "earth"}:
        return "world"
    return key


class MapChart(BaseChart):
    chart_type = "map"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        values: Optional[str] = None,
        map: str = "world",  # noqa: A002 — chart API; worldwide default
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data,
            title=title,
            width=width,
            height=height,
            theme=theme,
            option=option,
            **kwargs,
        )
        self.names = names or "name"
        self.values = values or "value"
        self.map_name = _normalize_map_name(map)
        self._maps_loaded = False

    def _ensure_maps(self) -> None:
        """Lazy-load GeoJSON only when HTML needs registerMap."""
        if self._maps_loaded:
            return
        geo = resolve_map_geojson(self.map_name)
        self._register_maps = {self.map_name: geo}
        self._maps_loaded = True

    def to_html(
        self,
        *,
        fragment: bool = False,
        width: Optional[str] = None,
        height: Optional[str] = None,
        include_assets: bool = True,
    ) -> str:
        self._ensure_maps()
        return super().to_html(
            fragment=fragment,
            width=width,
            height=height,
            include_assets=include_assets,
        )

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.names, self.values)
        names = column_values(df, self.names)
        values = column_values(df, self.values)
        data = [{"name": str(n), "value": v} for n, v in zip(names, values)]
        nums = [v for v in values if isinstance(v, (int, float))]
        vmin = min(nums) if nums else 0
        vmax = max(nums) if nums else 1
        return {
            "tooltip": {"trigger": "item"},
            "visualMap": {
                "min": vmin,
                "max": vmax,
                "left": "left",
                "top": "bottom",
                "calculable": True,
            },
            "series": [
                {
                    "type": "map",
                    "map": self.map_name,
                    "roam": True,
                    "data": data,
                    "emphasis": {"label": {"show": True}},
                }
            ],
        }


class GeoChart(BaseChart):
    """Scatter points on a geo coordinate system (world default; no Baidu Map).

    Expects longitude/latitude columns (not choropleth name/value — use
    :class:`MapChart` for region fills).
    """

    chart_type = "geo"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        lng: Optional[str] = None,
        lat: Optional[str] = None,
        values: Optional[str] = None,
        map: str = "world",  # noqa: A002
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data,
            title=title,
            width=width,
            height=height,
            theme=theme,
            option=option,
            **kwargs,
        )
        self.names = names
        self.lng = lng
        self.lat = lat
        self.values = values
        self.map_name = _normalize_map_name(map)
        self._maps_loaded = False

    def _ensure_maps(self) -> None:
        if self._maps_loaded:
            return
        geo = resolve_map_geojson(self.map_name)
        self._register_maps = {self.map_name: geo}
        self._maps_loaded = True

    def to_html(
        self,
        *,
        fragment: bool = False,
        width: Optional[str] = None,
        height: Optional[str] = None,
        include_assets: bool = True,
    ) -> str:
        self._ensure_maps()
        return super().to_html(
            fragment=fragment,
            width=width,
            height=height,
            include_assets=include_assets,
        )

    def _resolve_lng_lat(self, df) -> tuple[str, str]:
        lng = self.lng
        lat = self.lat
        if lng is None:
            for cand in ("lng", "lon", "longitude", "long"):
                if cand in df.columns:
                    lng = cand
                    break
        if lat is None:
            for cand in ("lat", "latitude"):
                if cand in df.columns:
                    lat = cand
                    break
        if lng is None or lat is None:
            available = ", ".join(map(str, df.columns)) or "(none)"
            raise DataError(
                "geo requires lng= and lat= columns (or columns named "
                f"lng/lon + lat). Available columns: {available}."
            )
        require_columns(df, lng, lat)
        return lng, lat

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        lng_col, lat_col = self._resolve_lng_lat(df)
        lngs = column_values(df, lng_col)
        lats = column_values(df, lat_col)
        if self.names:
            require_columns(df, self.names)
            names: List[Any] = column_values(df, self.names)
        else:
            names = [f"p{i}" for i in range(len(df))]
        sizes: Optional[List[Any]] = None
        if self.values:
            require_columns(df, self.values)
            sizes = column_values(df, self.values)

        data: List[Dict[str, Any]] = []
        for i, (name, lng, lat) in enumerate(zip(names, lngs, lats)):
            if lng is None or lat is None:
                continue
            try:
                point: List[Any] = [float(lng), float(lat)]
            except (TypeError, ValueError) as exc:
                raise DataError(
                    f"geo row {i}: lng/lat must be numeric, got "
                    f"{lng!r}, {lat!r}."
                ) from exc
            item: Dict[str, Any] = {"name": str(name), "value": point}
            if sizes is not None and sizes[i] is not None:
                try:
                    item["symbolSize"] = max(4.0, min(abs(float(sizes[i])), 64.0))
                except (TypeError, ValueError) as exc:
                    raise DataError(
                        f"geo row {i}: values/symbolSize must be numeric, "
                        f"got {sizes[i]!r}."
                    ) from exc
            data.append(item)

        return {
            "tooltip": {"trigger": "item"},
            "geo": {
                "map": self.map_name,
                "roam": True,
                "emphasis": {"label": {"show": True}},
            },
            "series": [
                {
                    "type": "scatter",
                    "coordinateSystem": "geo",
                    "data": data,
                    "symbolSize": 8,
                }
            ],
        }
