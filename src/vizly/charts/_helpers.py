"""Shared helpers for chart builders."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import pandas as pd

from vizly.data import (
    DataError,
    DataLike,
    as_tabular,
    column_values,
    infer_roles,
    require_columns,
    resolve_y_columns,
)
from vizly.theme.apply import series_defaults_for

YLike = Union[str, Sequence[str]]


def prepare_frame(data: Optional[DataLike]) -> pd.DataFrame:
    """Materialize chart input as a DataFrame via the TabularView spine.

    Callers may pass DataFrame, list[dict], dict[list], TabularView, or
    loader output. A DataFrame is not required at the call site.

    When the input is already a pandas DataFrame, returns that frame without
    an extra copy (builders treat it as read-only).
    """
    if data is None:
        raise DataError(
            "This chart requires data=. Pass a DataFrame, list[dict], "
            "dict[list], TabularView, or loader output."
        )
    table = as_tabular(data)
    # Avoid a defensive copy when the spine already wraps a DataFrame.
    to_pandas = getattr(table, "to_pandas", None)
    if callable(to_pandas):
        try:
            return to_pandas(copy=False)
        except TypeError:
            return to_pandas()
    return table.to_pandas()


def prepare_table(data: Optional[DataLike]):
    """Adapt chart input to TabularView without forcing a DataFrame."""
    if data is None:
        raise DataError(
            "This chart requires data=. Pass a DataFrame, list[dict], "
            "dict[list], TabularView, or loader output."
        )
    return as_tabular(data)


def resolve_xy(
    df: pd.DataFrame,
    *,
    x: Optional[str],
    y: Optional[YLike],
    prefer: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """Resolve x and y column roles, inferring when omitted."""
    if x is not None and y is not None:
        y_cols = resolve_y_columns(y)
        require_columns(df, x, *y_cols)
        return x, y_cols

    roles = infer_roles(df, prefer=prefer)
    if roles["confidence"] == "low" or roles["chart_type"] is None:
        available = ", ".join(map(str, df.columns)) or "(none)"
        raise DataError(
            f"Could not infer x/y roles. {roles['reason']} "
            f"Available columns: {available}. Pass explicit x= and y=."
        )

    inferred_x = x or roles.get("x")
    inferred_y = y if y is not None else roles.get("y")
    if inferred_x is None or inferred_y is None:
        available = ", ".join(map(str, df.columns)) or "(none)"
        raise DataError(
            f"Could not resolve x/y for this data. Available columns: {available}. "
            "Pass explicit x= and y=."
        )
    y_cols = resolve_y_columns(inferred_y)
    require_columns(df, inferred_x, *y_cols)
    return str(inferred_x), y_cols


def apply_series_defaults(
    series: Dict[str, Any],
    theme: Mapping[str, Any],
    chart_type: str,
) -> Dict[str, Any]:
    """Merge theme series_defaults into an ECharts series dict."""
    defaults = series_defaults_for(theme, chart_type)
    out = dict(series)
    if "smooth" in defaults:
        out["smooth"] = defaults["smooth"]
    if "show_symbol" in defaults:
        out["showSymbol"] = defaults["show_symbol"]
    if "symbol_size" in defaults:
        out["symbolSize"] = defaults["symbol_size"]
    if "label_show" in defaults:
        out.setdefault("label", {})
        if isinstance(out["label"], dict):
            out["label"] = {**out["label"], "show": defaults["label_show"]}
    if "bar_max_width" in defaults:
        out["barMaxWidth"] = defaults["bar_max_width"]
    if "rose_type" in defaults and defaults["rose_type"] is not None:
        out["roseType"] = defaults["rose_type"]
    return out


def cartesian_option(
    *,
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    series_type: str,
    theme: Mapping[str, Any],
    stacked: bool = False,
    area: bool = False,
    smooth: Optional[bool] = None,
) -> Dict[str, Any]:
    categories = column_values(df, x)
    series_list: List[Dict[str, Any]] = []
    for col in y_cols:
        series: Dict[str, Any] = {
            "name": col,
            "type": series_type,
            "data": column_values(df, col),
        }
        if stacked:
            series["stack"] = "total"
        if area or series_type == "line" and area:
            series["areaStyle"] = {}
        series = apply_series_defaults(series, theme, "area" if area else series_type)
        if smooth is not None and series_type == "line":
            series["smooth"] = smooth
        series_list.append(series)

    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"data": y_cols},
        "xAxis": {"type": "category", "data": categories},
        "yAxis": {"type": "value"},
        "series": series_list,
    }
