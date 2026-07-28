"""ECharts GL 3D charts (Band B/C). GL assets load only when these are used."""

from __future__ import annotations

from typing import Any, Dict, Optional

from vizly.base import BaseChart
from vizly.charts._helpers import prepare_frame
from vizly.data import DataError, column_values, require_columns


class _GLChart(BaseChart):
    _needs_gl = True

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[str] = None,
        z: Optional[str] = None,
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
        self.x = x
        self.y = y
        self.z = z

    def _xyz(self):
        df = prepare_frame(self.data)
        x = self.x or ("x" if "x" in df.columns else None)
        y = self.y or ("y" if "y" in df.columns else None)
        z = self.z or ("z" if "z" in df.columns else None)
        if not x or not y or not z:
            raise DataError(
                f"{self.chart_type} requires x=, y=, and z= column names. "
                f"Available: {', '.join(map(str, df.columns))}."
            )
        require_columns(df, x, y, z)
        data = [
            [a, b, c]
            for a, b, c in zip(
                column_values(df, x),
                column_values(df, y),
                column_values(df, z),
            )
        ]
        return df, x, y, z, data


class Bar3DChart(_GLChart):
    chart_type = "bar3d"

    def _build(self) -> Dict[str, Any]:
        _, x, y, z, data = self._xyz()
        return {
            "tooltip": {},
            "visualMap": {"max": max((d[2] for d in data if d[2] is not None), default=1)},
            "xAxis3D": {"type": "category", "name": x},
            "yAxis3D": {"type": "category", "name": y},
            "zAxis3D": {"type": "value", "name": z},
            "grid3D": {},
            "series": [{"type": "bar3D", "data": data}],
        }


class Line3DChart(_GLChart):
    chart_type = "line3d"

    def _build(self) -> Dict[str, Any]:
        _, x, y, z, data = self._xyz()
        return {
            "tooltip": {},
            "xAxis3D": {"type": "value", "name": x},
            "yAxis3D": {"type": "value", "name": y},
            "zAxis3D": {"type": "value", "name": z},
            "grid3D": {},
            "series": [{"type": "line3D", "data": data}],
        }


class Scatter3DChart(_GLChart):
    chart_type = "scatter3d"

    def _build(self) -> Dict[str, Any]:
        _, x, y, z, data = self._xyz()
        return {
            "tooltip": {},
            "xAxis3D": {"type": "value", "name": x},
            "yAxis3D": {"type": "value", "name": y},
            "zAxis3D": {"type": "value", "name": z},
            "grid3D": {},
            "series": [{"type": "scatter3D", "data": data}],
        }


class Surface3DChart(_GLChart):
    chart_type = "surface3d"

    def _build(self) -> Dict[str, Any]:
        _, x, y, z, data = self._xyz()
        # surface needs a formula or grid; provide data as parametric points
        return {
            "tooltip": {},
            "xAxis3D": {"type": "value", "name": x},
            "yAxis3D": {"type": "value", "name": y},
            "zAxis3D": {"type": "value", "name": z},
            "grid3D": {},
            "series": [
                {
                    "type": "surface",
                    "data": data,
                    "wireframe": {"show": True},
                }
            ],
        }
