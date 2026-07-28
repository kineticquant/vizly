"""Cartesian / statistical Band A charts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from vizly.base import BaseChart
from vizly.charts._helpers import (
    YLike,
    apply_series_defaults,
    cartesian_option,
    prepare_frame,
    resolve_xy,
)
from vizly.data import DataError, column_values, require_columns


class _CartesianChart(BaseChart):
    _series_type: str = "line"
    _prefer: Optional[str] = "line"
    _force_area: bool = False

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[YLike] = None,
        stacked: bool = False,
        smooth: Optional[bool] = None,
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
        self.stacked = stacked
        self.smooth = smooth

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        x, y_cols = resolve_xy(df, x=self.x, y=self.y, prefer=self._prefer)
        return cartesian_option(
            df=df,
            x=x,
            y_cols=y_cols,
            series_type=self._series_type,
            theme=self.theme,
            stacked=self.stacked,
            area=self._force_area,
            smooth=self.smooth,
        )


class LineChart(_CartesianChart):
    chart_type = "line"
    _series_type = "line"
    _prefer = "line"


class BarChart(_CartesianChart):
    chart_type = "bar"
    _series_type = "bar"
    _prefer = "bar"


class AreaChart(_CartesianChart):
    chart_type = "area"
    _series_type = "line"
    _prefer = "area"
    _force_area = True


class ScatterChart(BaseChart):
    chart_type = "scatter"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[YLike] = None,
        size: Optional[str] = None,
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
        self.size = size

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        x, y_cols = resolve_xy(df, x=self.x, y=self.y, prefer="scatter")
        if len(y_cols) != 1:
            raise DataError(
                "scatter expects a single y column (got "
                f"{y_cols}). Pass y='col' or reduce to one series."
            )
        y = y_cols[0]
        xs = column_values(df, x)
        ys = column_values(df, y)
        x_numeric = all(isinstance(v, (int, float)) for v in xs if v is not None)
        x_axis: Dict[str, Any] = (
            {"type": "value", "name": x}
            if x_numeric
            else {
                "type": "category",
                "data": list(dict.fromkeys(str(v) for v in xs)),
                "name": x,
            }
        )

        def _point(a: Any, b: Any) -> List[Any]:
            return [a, b] if x_numeric else [str(a), b]

        if self.size:
            require_columns(df, self.size)
            sizes = column_values(df, self.size)
            # JSON options cannot carry JS callbacks — encode size per datum.
            data = [
                {"value": _point(a, b), "symbolSize": _symbol_size(c)}
                for a, b, c in zip(xs, ys, sizes)
            ]
            series: Dict[str, Any] = {"name": y, "type": "scatter", "data": data}
        else:
            data = [_point(a, b) for a, b in zip(xs, ys)]
            series = {"name": y, "type": "scatter", "data": data}
        series = apply_series_defaults(series, self.theme, "scatter")
        return {
            "tooltip": {"trigger": "item"},
            "xAxis": x_axis,
            "yAxis": {"type": "value", "name": y},
            "series": [series],
        }


def _symbol_size(raw: Any) -> float:
    """Map a numeric size channel to a sensible pixel radius."""
    if raw is None:
        return 8.0
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return 8.0
    return max(4.0, min(abs(val), 64.0))


class BoxplotChart(BaseChart):
    chart_type = "boxplot"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[str] = None,
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

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        if self.x is None or self.y is None:
            raise DataError(
                "boxplot requires x= (category) and y= (numeric values). "
                f"Available columns: {', '.join(map(str, df.columns))}."
            )
        require_columns(df, self.x, self.y)
        categories: List[str] = []
        box_data: List[List[float]] = []
        for key, group in df.groupby(self.x, sort=False):
            vals = pd.to_numeric(group[self.y], errors="coerce").dropna()
            if vals.empty:
                continue
            q1 = float(vals.quantile(0.25))
            med = float(vals.quantile(0.5))
            q3 = float(vals.quantile(0.75))
            mn = float(vals.min())
            mx = float(vals.max())
            categories.append(str(key))
            # ECharts boxplot: [min, Q1, median, Q3, max]
            box_data.append([mn, q1, med, q3, mx])
        if not categories:
            raise DataError("boxplot found no numeric values after grouping.")
        return {
            "tooltip": {"trigger": "item"},
            "xAxis": {"type": "category", "data": categories},
            "yAxis": {"type": "value"},
            "series": [{"name": self.y, "type": "boxplot", "data": box_data}],
        }


class HeatmapChart(BaseChart):
    chart_type = "heatmap"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[str] = None,
        values: Optional[str] = None,
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
        self.values = values

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        if not self.x or not self.y or not self.values:
            raise DataError(
                "heatmap requires x=, y=, and values= column names. "
                f"Available columns: {', '.join(map(str, df.columns))}."
            )
        require_columns(df, self.x, self.y, self.values)
        xs = column_values(df, self.x)
        ys = column_values(df, self.y)
        zs = column_values(df, self.values)
        x_cats = list(dict.fromkeys(xs))
        y_cats = list(dict.fromkeys(ys))
        x_index = {v: i for i, v in enumerate(x_cats)}
        y_index = {v: i for i, v in enumerate(y_cats)}
        points = []
        nums: List[float] = []
        for xv, yv, zv in zip(xs, ys, zs):
            if zv is None:
                continue
            points.append([x_index[xv], y_index[yv], float(zv)])
            nums.append(float(zv))
        vmin = min(nums) if nums else 0
        vmax = max(nums) if nums else 1
        return {
            "tooltip": {"position": "top"},
            "grid": {"height": "70%", "top": "10%"},
            "xAxis": {"type": "category", "data": [str(c) for c in x_cats]},
            "yAxis": {"type": "category", "data": [str(c) for c in y_cats]},
            "visualMap": {
                "min": vmin,
                "max": vmax,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "bottom": "0%",
            },
            "series": [
                {
                    "type": "heatmap",
                    "data": points,
                    "label": {"show": False},
                }
            ],
        }


class CandlestickChart(BaseChart):
    chart_type = "candlestick"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        open: Optional[str] = None,  # noqa: A002 — chart role name
        close: Optional[str] = None,
        low: Optional[str] = None,
        high: Optional[str] = None,
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
        self.open = open or "open"
        self.close = close or "close"
        self.low = low or "low"
        self.high = high or "high"

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        x = self.x
        if x is None:
            # Prefer a datetime-like / first column named date/time
            for cand in ("date", "time", "datetime", "timestamp"):
                if cand in df.columns:
                    x = cand
                    break
            if x is None:
                x = str(df.columns[0])
        require_columns(df, x, self.open, self.close, self.low, self.high)
        categories = column_values(df, x)
        # ECharts candlestick item: [open, close, low, high]
        o = column_values(df, self.open)
        c = column_values(df, self.close)
        lo = column_values(df, self.low)
        hi = column_values(df, self.high)
        data = [[a, b, c_, d] for a, b, c_, d in zip(o, c, lo, hi)]
        return {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": categories},
            "yAxis": {"type": "value", "scale": True},
            "series": [{"type": "candlestick", "data": data}],
        }


# Alias with distinct chart_type for registry / list_chart_types.
class KlineChart(CandlestickChart):
    chart_type = "kline"
