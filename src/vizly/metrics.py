"""Normalize common ops metric payloads into tidy DataFrames for vizly.

Agents and ops tools often hand Prometheus / CloudWatch / Elasticsearch
JSON to a charting layer. These helpers turn those shapes into columns
ready for ``vz.line`` / ``vz.area`` / etc.

No live API clients — only payload shaping.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

import pandas as pd

from vizly.data import DataError

JsonLike = Union[Mapping[str, Any], Sequence[Any]]


def _note_skipped(df: pd.DataFrame, skipped: int, *, source: str) -> pd.DataFrame:
    """Attach skip metadata and warn when malformed rows were dropped."""
    if skipped <= 0:
        return df
    df.attrs["vizly_skipped"] = int(skipped)
    warnings.warn(
        f"{source} skipped {skipped} malformed row(s); "
        "see DataFrame.attrs['vizly_skipped'].",
        UserWarning,
        stacklevel=3,
    )
    return df


def _iso_from_epoch(ts: Any) -> str:
    """Prometheus uses unix seconds (float/int); CloudWatch may be ms."""
    try:
        value = float(ts)
    except (TypeError, ValueError) as exc:
        raise DataError(f"Invalid timestamp {ts!r}.") from exc
    # Heuristic: ≥ 1e12 → milliseconds
    if value >= 1_000_000_000_000:
        value = value / 1000.0
    dt = datetime.fromtimestamp(value, tz=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _metric_label(metric: Mapping[str, Any]) -> str:
    if not metric:
        return "value"
    name = metric.get("__name__")
    others = {k: v for k, v in metric.items() if k != "__name__"}
    if name and not others:
        return str(name)
    if name and others:
        tags = ",".join(f"{k}={v}" for k, v in sorted(others.items()))
        return f"{name}{{{tags}}}"
    if others:
        return ",".join(f"{k}={v}" for k, v in sorted(others.items()))
    return "value"


def from_prometheus(payload: JsonLike) -> pd.DataFrame:
    """Convert a Prometheus HTTP API query / query_range result to a frame.

    Accepts the full API envelope ``{"status","data":{...}}`` or the inner
    ``data`` object / ``result`` list.

    Returns columns: ``timestamp``, ``value``, ``series``.
    """
    data = payload
    if isinstance(payload, Mapping) and "data" in payload:
        data = payload["data"]
    if isinstance(data, Mapping) and "result" in data:
        results = data["result"]
        result_type = data.get("resultType")
    elif isinstance(data, list):
        results = data
        result_type = None
    else:
        raise DataError(
            "from_prometheus expected Prometheus API JSON with data.result "
            f"(or a result list). Got {type(payload).__name__}."
        )

    if not isinstance(results, list):
        raise DataError("Prometheus data.result must be a list.")

    rows: List[Dict[str, Any]] = []
    skipped = 0
    for item in results:
        if not isinstance(item, Mapping):
            skipped += 1
            continue
        series = _metric_label(item.get("metric") or {})
        if "values" in item:
            for pair in item["values"] or []:
                if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                    skipped += 1
                    continue
                rows.append(
                    {
                        "timestamp": _iso_from_epoch(pair[0]),
                        "value": _as_float(pair[1]),
                        "series": series,
                    }
                )
        elif "value" in item:
            pair = item["value"]
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                rows.append(
                    {
                        "timestamp": _iso_from_epoch(pair[0]),
                        "value": _as_float(pair[1]),
                        "series": series,
                    }
                )
            else:
                skipped += 1
        else:
            raise DataError(
                f"Prometheus result item missing values/value "
                f"(resultType={result_type!r})."
            )

    if not rows:
        return _note_skipped(
            pd.DataFrame(columns=["timestamp", "value", "series"]),
            skipped,
            source="from_prometheus",
        )
    return _note_skipped(pd.DataFrame(rows), skipped, source="from_prometheus")


def from_cloudwatch(payload: JsonLike, *, value: Optional[str] = None) -> pd.DataFrame:
    """Convert CloudWatch ``Datapoints`` (or a bare list) to a frame.

    Picks the first present statistic among Average / Sum / Maximum /
    Minimum / SampleCount unless ``value=`` names a field.

    Returns columns: ``timestamp``, ``value`` (and ``unit`` when present).
    """
    points: Sequence[Any]
    if isinstance(payload, Mapping):
        if "Datapoints" in payload:
            points = payload["Datapoints"]  # type: ignore[assignment]
        elif "MetricDataResults" in payload:
            return _from_cloudwatch_metric_data(payload["MetricDataResults"])
        else:
            raise DataError(
                "from_cloudwatch expected {'Datapoints': [...]} or "
                "{'MetricDataResults': [...]} or a datapoint list."
            )
    elif isinstance(payload, list):
        points = payload
    else:
        raise DataError(
            f"from_cloudwatch expected mapping or list, got {type(payload).__name__}."
        )

    stats = ("Average", "Sum", "Maximum", "Minimum", "SampleCount")
    rows: List[Dict[str, Any]] = []
    skipped = 0
    for pt in points:
        if not isinstance(pt, Mapping):
            skipped += 1
            continue
        ts = pt.get("Timestamp")
        if ts is None:
            skipped += 1
            continue
        if hasattr(ts, "isoformat"):
            ts_s = ts.isoformat().replace("+00:00", "Z")
        else:
            ts_s = str(ts)
            if ts_s.endswith("+00:00"):
                ts_s = ts_s[:-6] + "Z"
        field = value
        if field is None:
            for cand in stats:
                if cand in pt and pt[cand] is not None:
                    field = cand
                    break
        if field is None or field not in pt:
            skipped += 1
            continue
        row: Dict[str, Any] = {
            "timestamp": ts_s,
            "value": _as_float(pt[field]),
        }
        if "Unit" in pt:
            row["unit"] = pt["Unit"]
        rows.append(row)

    if not rows:
        return _note_skipped(
            pd.DataFrame(columns=["timestamp", "value"]),
            skipped,
            source="from_cloudwatch",
        )
    frame = pd.DataFrame(rows)
    return _note_skipped(
        frame.sort_values("timestamp").reset_index(drop=True),
        skipped,
        source="from_cloudwatch",
    )


def _from_cloudwatch_metric_data(results: Sequence[Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    skipped = 0
    for block in results:
        if not isinstance(block, Mapping):
            skipped += 1
            continue
        label = str(block.get("Label") or block.get("Id") or "value")
        timestamps = block.get("Timestamps") or []
        values = block.get("Values") or []
        for ts, val in zip(timestamps, values):
            if hasattr(ts, "isoformat"):
                ts_s = ts.isoformat().replace("+00:00", "Z")
            else:
                ts_s = str(ts)
            rows.append(
                {
                    "timestamp": ts_s,
                    "value": _as_float(val),
                    "series": label,
                }
            )
    if not rows:
        return _note_skipped(
            pd.DataFrame(columns=["timestamp", "value", "series"]),
            skipped,
            source="from_cloudwatch",
        )
    return _note_skipped(
        pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True),
        skipped,
        source="from_cloudwatch",
    )


def from_elasticsearch(
    payload: JsonLike,
    *,
    agg: Optional[str] = None,
    metric: Optional[str] = None,
) -> pd.DataFrame:
    """Convert Elasticsearch / OpenSearch date_histogram buckets to a frame.

    Accepts:
    - full search response with ``aggregations``
    - a single agg object ``{"buckets": [...]}``
    - a bare buckets list

    ``agg`` selects which aggregation when several exist.
    ``metric`` selects a sub-agg value field (default: ``doc_count``).

    Returns columns: ``timestamp``, ``value``.
    """
    buckets = _resolve_es_buckets(payload, agg=agg)
    rows: List[Dict[str, Any]] = []
    skipped = 0
    for b in buckets:
        if not isinstance(b, Mapping):
            skipped += 1
            continue
        ts = b.get("key_as_string")
        if ts is None and "key" in b:
            ts = _iso_from_epoch(b["key"])
        if ts is None:
            skipped += 1
            continue
        if metric is None:
            val = b.get("doc_count", 0)
        else:
            sub = b.get(metric)
            if isinstance(sub, Mapping) and "value" in sub:
                val = sub["value"]
            elif metric in b:
                val = b[metric]
            else:
                raise DataError(
                    f"Bucket missing metric {metric!r}. "
                    f"Keys: {', '.join(map(str, b.keys()))}."
                )
        rows.append({"timestamp": str(ts), "value": _as_float(val)})

    if not rows:
        return _note_skipped(
            pd.DataFrame(columns=["timestamp", "value"]),
            skipped,
            source="from_elasticsearch",
        )
    return _note_skipped(pd.DataFrame(rows), skipped, source="from_elasticsearch")


# Friendly alias for ELK / Elastic stack callers.
from_elk = from_elasticsearch


def _resolve_es_buckets(
    payload: JsonLike, *, agg: Optional[str]
) -> Sequence[Mapping[str, Any]]:
    if isinstance(payload, list):
        return payload  # type: ignore[return-value]
    if not isinstance(payload, Mapping):
        raise DataError(
            f"from_elasticsearch expected mapping or list, got {type(payload).__name__}."
        )
    if "buckets" in payload:
        buckets = payload["buckets"]
        if not isinstance(buckets, list):
            raise DataError("aggregations buckets must be a list.")
        return buckets
    aggs = payload.get("aggregations") or payload.get("aggs")
    if not isinstance(aggs, Mapping) or not aggs:
        raise DataError(
            "from_elasticsearch expected aggregations.<name>.buckets "
            "(or a buckets list)."
        )
    if agg is not None:
        node = aggs.get(agg)
        if not isinstance(node, Mapping) or "buckets" not in node:
            raise DataError(f"Aggregation {agg!r} not found or has no buckets.")
        return node["buckets"]
    # First agg with buckets
    for node in aggs.values():
        if isinstance(node, Mapping) and "buckets" in node:
            return node["buckets"]
    raise DataError("No aggregation with buckets found.")


def _as_float(value: Any) -> float:
    if value is None:
        raise DataError("Metric value is null.")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise DataError(f"Metric value is not numeric: {value!r}.") from exc
