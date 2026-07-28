"""Data ingestion, cleaning, and column-role inference for vizly charts.

Accepted input shapes
--------------------
- ``pandas.DataFrame``
- ``list[dict]`` (records)
- ``dict[str, list]`` (columnar)

Missing values
--------------
pandas/NumPy NA and NaN values are converted to ``None`` in extracted
column lists so ECharts JSON stays valid (``null``).

Datetime policy
---------------
Datetime-like values are serialized as **ISO 8601 strings** in chart data
payloads (e.g. ``2026-01-02T00:00:00``). Display formatting for axis/tooltip
labels is left to theme/locale formatters in HTML embeds (``echarts.init``
locale from theme) — data stays
machine-sortable and unambiguous.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import numpy as np
import pandas as pd

DataLike = Union[pd.DataFrame, Sequence[Mapping[str, Any]], Mapping[str, Sequence[Any]]]

# Soft cardinality threshold for preferring bar over line on categoricals.
_LOW_CARDINALITY_MAX = 30

_NAME_HINTS = frozenset({"name", "names", "label", "labels", "category", "segment"})
_VALUE_HINTS = frozenset({"value", "values", "amount", "share", "count", "total"})


class DataError(ValueError):
    """Raised when chart data cannot be standardized or roles inferred."""


def standardize(data: DataLike) -> pd.DataFrame:
    """Normalize supported inputs into a DataFrame (copy).

    Does not mutate the caller's object. Column order is preserved.
    """
    if isinstance(data, pd.DataFrame):
        if data.columns.duplicated().any():
            dupes = list(data.columns[data.columns.duplicated()])
            raise DataError(
                f"DataFrame has duplicate column names: {dupes}. "
                "Rename columns so each name is unique."
            )
        return data.copy()

    if isinstance(data, Mapping):
        try:
            lengths = {k: len(v) for k, v in data.items()}
        except TypeError as exc:
            raise DataError(
                "dict[list] input requires each value to be a sequence "
                f"(list/tuple). Detail: {exc}"
            ) from exc
        if lengths and len(set(lengths.values())) > 1:
            detail = ", ".join(f"{k}={n}" for k, n in lengths.items())
            raise DataError(
                f"Columnar dict has unequal lengths: {detail}. "
                "All columns must have the same number of rows."
            )
        return pd.DataFrame(dict(data))

    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        if len(data) == 0:
            return pd.DataFrame()
        if not all(isinstance(row, Mapping) for row in data):
            raise DataError(
                "list[dict] input requires every row to be a mapping "
                f"(dict-like). Got types: "
                f"{sorted({type(r).__name__ for r in data})}."
            )
        return pd.DataFrame(list(data))

    raise DataError(
        f"Unsupported data type {type(data).__name__}. "
        "Pass a DataFrame, list[dict], or dict[list]."
    )


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _serialize_value(value: Any) -> Any:
    if _is_missing(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, np.datetime64):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, np.generic):
        return value.item()
    # datetime.date / datetime.datetime
    if hasattr(value, "isoformat") and not isinstance(value, str):
        try:
            return value.isoformat()
        except (TypeError, ValueError, AttributeError):
            # Not a real date-like; leave as-is for JSON (may fail later with
            # allow_nan=False if still non-serializable — fail clearly there).
            return value
    return value


def column_values(df: pd.DataFrame, column: str) -> List[Any]:
    """Return a column as a JSON-friendly list (NaN→None, datetimes→ISO)."""
    if column not in df.columns:
        available = ", ".join(map(str, df.columns)) or "(none)"
        raise DataError(
            f"Column {column!r} not found. Available columns: {available}."
        )
    series = df[column]
    # Fast path: datetime64 → ISO without per-cell Timestamp wrapping where possible.
    if pd.api.types.is_datetime64_any_dtype(series):
        iso = series.dt.strftime("%Y-%m-%dT%H:%M:%S")
        return [None if pd.isna(v) else str(v) for v in iso.tolist()]
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        out: List[Any] = []
        for v in series.tolist():
            if _is_missing(v):
                out.append(None)
            elif isinstance(v, np.generic):
                out.append(v.item())
            else:
                out.append(v)
        return out
    return [_serialize_value(v) for v in series.tolist()]


def records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return row dicts with NaN→None and datetimes→ISO."""
    cols = list(df.columns)
    out: List[Dict[str, Any]] = []
    for row in df.itertuples(index=False, name=None):
        out.append({c: _serialize_value(v) for c, v in zip(cols, row)})
    return out


def _is_datetime_series(s: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(s):
        return True
    if s.dtype == object:
        sample = s.dropna().head(20)
        if sample.empty:
            return False
        try:
            converted = pd.to_datetime(sample, errors="raise", utc=False)
            return bool(len(converted))
        except (TypeError, ValueError, OverflowError):
            return False
    return False


def _is_numeric_series(s: pd.Series) -> bool:
    return bool(pd.api.types.is_numeric_dtype(s))


def _is_categorical_like(s: pd.Series) -> bool:
    if isinstance(s.dtype, pd.CategoricalDtype) or pd.api.types.is_string_dtype(s):
        return True
    if s.dtype == object and not _is_datetime_series(s):
        return True
    return False


def infer_roles(
    df: pd.DataFrame,
    *,
    prefer: Optional[str] = None,
) -> Dict[str, Any]:
    """Infer chart type and column roles from a standardized DataFrame.

    Returns a dict with keys:
    ``chart_type``, ``x``, ``y``, ``names``, ``values``, ``confidence``,
    ``reason``.

    Inference rules (token reduction):
    1. One datetime-like + one numeric → line (x=datetime, y=numeric)
    2. One low-cardinality categorical + one numeric → bar
    3. Two numerics → scatter
    4. Columns named like name/label + value/amount → pie
    5. If ambiguous, ``confidence`` is ``"low"`` and ``chart_type`` may be None
    """
    if df.empty or len(df.columns) == 0:
        raise DataError(
            "Cannot infer column roles from empty data. "
            "Provide a non-empty DataFrame/list/dict with named columns."
        )

    columns = [str(c) for c in df.columns]
    lower_map = {c.lower(): c for c in columns}

    # Named pie hints
    name_col = next((lower_map[h] for h in _NAME_HINTS if h in lower_map), None)
    value_col = next((lower_map[h] for h in _VALUE_HINTS if h in lower_map), None)
    if name_col and value_col and (prefer in (None, "pie", "donut")):
        return {
            "chart_type": "pie" if prefer != "donut" else "donut",
            "x": None,
            "y": None,
            "names": name_col,
            "values": value_col,
            "confidence": "high",
            "reason": f"Matched name/value columns ({name_col!r}, {value_col!r}).",
        }

    datetime_cols = [c for c in columns if _is_datetime_series(df[c])]
    numeric_cols = [c for c in columns if _is_numeric_series(df[c])]
    categorical_cols = [
        c
        for c in columns
        if c not in datetime_cols
        and c not in numeric_cols
        and _is_categorical_like(df[c])
    ]

    if prefer == "scatter" and len(numeric_cols) >= 2:
        return {
            "chart_type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1],
            "names": None,
            "values": None,
            "confidence": "high",
            "reason": "prefer=scatter with two numeric columns.",
        }

    if len(datetime_cols) == 1 and len(numeric_cols) >= 1 and prefer in (None, "line", "area"):
        y = numeric_cols if len(numeric_cols) > 1 else numeric_cols[0]
        return {
            "chart_type": "area" if prefer == "area" else "line",
            "x": datetime_cols[0],
            "y": y,
            "names": None,
            "values": None,
            "confidence": "high",
            "reason": "One datetime column and numeric measure(s).",
        }

    low_card_cats = [
        c
        for c in categorical_cols
        if df[c].nunique(dropna=True) <= _LOW_CARDINALITY_MAX
    ]
    if len(low_card_cats) == 1 and len(numeric_cols) >= 1 and prefer in (None, "bar"):
        y = numeric_cols if len(numeric_cols) > 1 else numeric_cols[0]
        return {
            "chart_type": "bar",
            "x": low_card_cats[0],
            "y": y,
            "names": None,
            "values": None,
            "confidence": "high",
            "reason": "One low-cardinality categorical and numeric measure(s).",
        }

    if len(numeric_cols) >= 2 and prefer in (None, "scatter"):
        return {
            "chart_type": "scatter",
            "x": numeric_cols[0],
            "y": numeric_cols[1],
            "names": None,
            "values": None,
            "confidence": "medium",
            "reason": "Two or more numeric columns; defaulting to scatter.",
        }

    if len(categorical_cols) == 1 and len(numeric_cols) == 1:
        return {
            "chart_type": "bar",
            "x": categorical_cols[0],
            "y": numeric_cols[0],
            "names": None,
            "values": None,
            "confidence": "medium",
            "reason": "One categorical and one numeric column.",
        }

    available = ", ".join(columns)
    return {
        "chart_type": None,
        "x": None,
        "y": None,
        "names": None,
        "values": None,
        "confidence": "low",
        "reason": (
            "Could not unambiguously infer roles from columns "
            f"[{available}]. Pass explicit role fields (e.g. x=, y=)."
        ),
    }


def require_columns(df: pd.DataFrame, *columns: str) -> None:
    """Raise :class:`DataError` listing missing columns."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        available = ", ".join(map(str, df.columns)) or "(none)"
        raise DataError(
            f"Missing required column(s): {', '.join(repr(c) for c in missing)}. "
            f"Available columns: {available}."
        )


def resolve_y_columns(y: Union[str, Sequence[str]]) -> List[str]:
    """Normalize ``y`` as ``str | list[str]`` into a list of column names."""
    if isinstance(y, str):
        return [y]
    if isinstance(y, Sequence) and not isinstance(y, (str, bytes)):
        cols = list(y)
        if not cols:
            raise DataError("y= must be a non-empty column name or list of names.")
        if not all(isinstance(c, str) for c in cols):
            raise DataError("y= list entries must be column name strings.")
        return cols
    raise DataError(f"y= must be str or list[str], got {type(y).__name__}.")
