"""Radar (Band A) and related polar-ish charts."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

import pandas as pd

from vizly.base import BaseChart
from vizly.charts._helpers import prepare_frame
from vizly.data import DataError, column_values, require_columns


class RadarChart(BaseChart):
    chart_type = "radar"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        values: Optional[Sequence[str]] = None,
        indicators: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        """Radar chart.

        ``data`` should be wide: one row per series, indicator columns numeric.
        ``names`` column labels each series; ``values``/``indicators`` lists
        the metric columns (defaults to all numeric columns except ``names``).
        """
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
        self.values = list(values) if values is not None else None
        self.indicators = list(indicators) if indicators is not None else None

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        name_col = self.names
        metric_cols = self.values or self.indicators
        if metric_cols is None:
            metric_cols = [
                c
                for c in df.columns
                if c != name_col and pd.api.types.is_numeric_dtype(df[c])
            ]
        if not metric_cols:
            raise DataError(
                "radar needs numeric indicator columns via values=/indicators= "
                f"or numeric fields. Available: {', '.join(map(str, df.columns))}."
            )
        require_columns(df, *metric_cols)
        if name_col:
            require_columns(df, name_col)
            series_names = [str(n) for n in column_values(df, name_col)]
        else:
            series_names = [f"series-{i + 1}" for i in range(len(df))]

        # Serialize each metric column once (avoid O(rows*cols) re-walks).
        metric_matrix = {col: column_values(df, col) for col in metric_cols}

        indicator = []
        for col in metric_cols:
            vals = [v for v in metric_matrix[col] if v is not None]
            vmax = max(vals) if vals else 1
            indicator.append({"name": str(col), "max": vmax * 1.1 if vmax else 1})

        series_data = []
        n_rows = len(series_names)
        for i, row_name in enumerate(series_names):
            if i >= n_rows:
                break
            row_vals = [metric_matrix[col][i] for col in metric_cols]
            series_data.append({"name": row_name, "value": row_vals})

        return {
            "tooltip": {},
            "legend": {"data": series_names},
            "radar": {"indicator": indicator},
            "series": [{"type": "radar", "data": series_data}],
        }


class PolarChart(BaseChart):
    """Bar/line on a polar coordinate system."""

    chart_type = "polar"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[str] = None,
        series_type: str = "bar",
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
        self.series_type = series_type if series_type in {"bar", "line", "scatter"} else "bar"

    def _build(self) -> Dict[str, Any]:
        from vizly.charts._helpers import resolve_xy

        df = prepare_frame(self.data)
        x, y_cols = resolve_xy(df, x=self.x, y=self.y, prefer="bar")
        y = y_cols[0]
        return {
            "tooltip": {},
            "polar": {},
            "angleAxis": {
                "type": "category",
                "data": column_values(df, x),
            },
            "radiusAxis": {},
            "series": [
                {
                    "type": self.series_type,
                    "coordinateSystem": "polar",
                    "data": column_values(df, y),
                    "name": y,
                }
            ],
        }


class ParallelChart(BaseChart):
    chart_type = "parallel"

    def __init__(
        self,
        data: Any = None,
        *,
        dimensions: Optional[Sequence[str]] = None,
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
        self.dimensions = list(dimensions) if dimensions is not None else None

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        dims = self.dimensions or [
            c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
        ]
        if len(dims) < 2:
            raise DataError(
                "parallel needs at least two numeric dimensions= columns."
            )
        require_columns(df, *dims)
        parallel_axis = [
            {"dim": i, "name": str(col)} for i, col in enumerate(dims)
        ]
        matrix = [column_values(df, col) for col in dims]
        data = [list(row) for row in zip(*matrix)]
        return {
            "tooltip": {},
            "parallelAxis": parallel_axis,
            "series": [{"type": "parallel", "data": data}],
        }
