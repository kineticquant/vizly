"""Canonicalize ECharts options for stable golden JSON comparison."""

from __future__ import annotations

import json
from typing import Any


def _json_default(obj: Any) -> Any:
    if hasattr(obj, "item"):
        try:
            return obj.item()
        except Exception:
            pass
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def canonicalize_option(option: Any) -> Any:
    """Round-trip through JSON with sorted keys for deterministic goldens."""
    text = json.dumps(
        option,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        default=_json_default,
    )
    return json.loads(text)


def option_golden_text(option: Any) -> str:
    """Pretty-printed golden file contents (trailing newline)."""
    return (
        json.dumps(
            canonicalize_option(option),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
