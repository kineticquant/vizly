#!/usr/bin/env python3
"""Rewrite ``goldens/options/*.json`` from current sample chart options.

Usage (from repo root)::

    python scripts/update_sample_goldens.py

Equivalent pytest entrypoint::

    python -m pytest -m samples --update-goldens -q
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vizly.charts import CHART_TYPES  # noqa: E402
from vizly.config import reset_config  # noqa: E402
from vizly.maps import reset_opt_in_maps  # noqa: E402
from vizly.theme.registry import reset_registry  # noqa: E402

from tests.samples.fixtures import SAMPLE_THEMES, make_chart  # noqa: E402
from tests.samples.normalize import option_golden_text  # noqa: E402
from tests.samples.paths import GOLDENS_OPTIONS_DIR, golden_path  # noqa: E402


def main() -> int:
    reset_registry()
    reset_config()
    reset_opt_in_maps()
    GOLDENS_OPTIONS_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    for chart_type in sorted(CHART_TYPES.keys()):
        for theme in SAMPLE_THEMES:
            option = make_chart(chart_type, theme=theme).to_option()
            path = golden_path(chart_type, theme)
            path.write_text(option_golden_text(option), encoding="utf-8")
            written += 1
            print(f"wrote {path.relative_to(ROOT)}")

    print(f"Updated {written} golden files under {GOLDENS_OPTIONS_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
