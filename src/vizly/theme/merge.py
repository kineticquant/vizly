"""Deep-merge utilities for vizly themes and ECharts option fragments.

List policy
-----------
When merging mappings, nested dicts are merged recursively. **Lists are
replaced wholesale** by the overlay value (they are not concatenated or
zipped). This keeps categorical palettes and series lists predictable:
the last writer wins for the entire list.

Scalars and other non-mapping values are overwritten by the overlay.
``None`` in an overlay still overwrites (explicit clear).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, MutableMapping


def deep_merge(
    base: Mapping[str, Any],
    overlay: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Return a new dict: ``base`` deep-merged with ``overlay``.

    Neither input is mutated. If ``overlay`` is ``None`` or empty, a deep
    copy of ``base`` is returned.
    """
    result: Dict[str, Any] = deepcopy(dict(base))
    if not overlay:
        return result
    _merge_into(result, overlay)
    return result


def _merge_into(
    target: MutableMapping[str, Any],
    overlay: Mapping[str, Any],
) -> None:
    for key, value in overlay.items():
        if (
            key in target
            and isinstance(target[key], MutableMapping)
            and isinstance(value, Mapping)
            and not isinstance(value, (str, bytes))
        ):
            _merge_into(target[key], value)
        else:
            # Lists and scalars: replace (do not concatenate lists).
            target[key] = deepcopy(value)
