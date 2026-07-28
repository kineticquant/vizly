"""Band B/C specialty charts: effect scatter, waterfall, wordcloud, liquid, etc."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from vizly.base import BaseChart
from vizly.charts._helpers import (
    YLike,
    apply_series_defaults,
    prepare_frame,
    resolve_xy,
)
from vizly.data import DataError, column_values, require_columns


class EffectScatterChart(BaseChart):
    chart_type = "effect_scatter"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[YLike] = None,
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
        x, y_cols = resolve_xy(df, x=self.x, y=self.y, prefer="scatter")
        if len(y_cols) != 1:
            raise DataError("effect_scatter expects a single y column.")
        y = y_cols[0]
        data = [
            [a, b]
            for a, b in zip(column_values(df, x), column_values(df, y))
        ]
        return {
            "tooltip": {"trigger": "item"},
            "xAxis": {"type": "value", "name": x},
            "yAxis": {"type": "value", "name": y},
            "series": [
                {
                    "name": y,
                    "type": "effectScatter",
                    "symbolSize": 12,
                    "data": data,
                }
            ],
        }


class WaterfallChart(BaseChart):
    """Bar-based waterfall using transparent helper stack + visible deltas."""

    chart_type = "waterfall"

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
        x, y_cols = resolve_xy(df, x=self.x, y=self.y, prefer="bar")
        if len(y_cols) != 1:
            raise DataError("waterfall expects a single y column of step deltas.")
        y = y_cols[0]
        cats = column_values(df, x)
        deltas = column_values(df, y)
        assist: List[float] = []
        increase: List[Optional[float]] = []
        decrease: List[Optional[float]] = []
        running = 0.0
        for d in deltas:
            if d is None:
                assist.append(running)
                increase.append(None)
                decrease.append(None)
                continue
            val = float(d)
            if val >= 0:
                assist.append(running)
                increase.append(val)
                decrease.append(None)
                running += val
            else:
                running += val
                assist.append(running)
                increase.append(None)
                decrease.append(-val)
        return {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Increase", "Decrease"]},
            "xAxis": {"type": "category", "data": cats},
            "yAxis": {"type": "value"},
            "series": [
                {
                    "name": "Assist",
                    "type": "bar",
                    "stack": "total",
                    "itemStyle": {"borderColor": "transparent", "color": "transparent"},
                    "emphasis": {
                        "itemStyle": {
                            "borderColor": "transparent",
                            "color": "transparent",
                        }
                    },
                    "data": assist,
                },
                {
                    "name": "Increase",
                    "type": "bar",
                    "stack": "total",
                    "data": increase,
                },
                {
                    "name": "Decrease",
                    "type": "bar",
                    "stack": "total",
                    "data": decrease,
                },
            ],
        }


class PictorialBarChart(BaseChart):
    chart_type = "pictorial_bar"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[YLike] = None,
        symbol: str = "path://M0,10 L10,10 L5,0 z",
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
        self.symbol = symbol

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        x, y_cols = resolve_xy(df, x=self.x, y=self.y, prefer="bar")
        series = []
        for col in y_cols:
            series.append(
                apply_series_defaults(
                    {
                        "name": col,
                        "type": "pictorialBar",
                        "symbol": self.symbol,
                        "data": column_values(df, col),
                    },
                    self.theme,
                    "bar",
                )
            )
        return {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": y_cols},
            "xAxis": {"type": "category", "data": column_values(df, x)},
            "yAxis": {"type": "value"},
            "series": series,
        }


class ThemeRiverChart(BaseChart):
    chart_type = "theme_river"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        y: Optional[str] = None,
        names: Optional[str] = None,
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
        self.x = x or "date"
        self.y = y or "value"
        self.names = names or "name"

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.x, self.y, self.names)
        # themeRiver data item: [date, value, name]
        data = [
            [a, b, c]
            for a, b, c in zip(
                column_values(df, self.x),
                column_values(df, self.y),
                column_values(df, self.names),
            )
        ]
        return {
            "tooltip": {"trigger": "axis"},
            "singleAxis": {"type": "time"},
            "series": [{"type": "themeRiver", "data": data}],
        }


class WordCloudChart(BaseChart):
    chart_type = "wordcloud"
    _plugins = ("wordcloud",)

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
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
        self.names = names or "name"
        self.values = values or "value"

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.names, self.values)
        data = [
            {"name": str(n), "value": v}
            for n, v in zip(
                column_values(df, self.names), column_values(df, self.values)
            )
            if v is not None
        ]
        return {
            "series": [
                {
                    "type": "wordCloud",
                    "shape": "circle",
                    "gridSize": 8,
                    "sizeRange": [12, 48],
                    "data": data,
                }
            ]
        }


class LiquidChart(BaseChart):
    chart_type = "liquid"
    _plugins = ("liquidfill",)

    def __init__(
        self,
        data: Any = None,
        *,
        value: Optional[float] = None,
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
        self.value = value
        self.values = values

    def _build(self) -> Dict[str, Any]:
        val = self.value
        if val is None and self.data is not None:
            df = prepare_frame(self.data)
            col = self.values or ("value" if "value" in df.columns else None)
            if col is None:
                raise DataError("liquid requires value= or a values= column.")
            require_columns(df, col)
            nums = [v for v in column_values(df, col) if v is not None]
            if not nums:
                raise DataError("liquid found no numeric values.")
            val = float(nums[-1])
        if val is None:
            raise DataError("liquid requires value= (0–1 fraction) or data.")
        # Accept 0–100 as percent convenience
        if val > 1:
            val = val / 100.0
        return {
            "series": [
                {
                    "type": "liquidFill",
                    "data": [val],
                    "label": {"formatter": f"{val * 100:.0f}%"},
                }
            ]
        }
