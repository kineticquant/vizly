#!/usr/bin/env python3
"""Open a real browser and validate sample chart HTML (local review suite).

Option goldens under ``goldens/options/`` are JSON - pytest diffs those.
This script validates the matching **HTML** under ``artifacts/html/`` by
loading each page in Chromium and checking that ECharts actually draws.

**Two different windows (easy to confuse):**

- ``--gallery`` / ``--gallery-only`` -> your **system** browser opens
  ``artifacts/html/index.html`` for click-through review.
- Default / ``--headed`` -> Playwright launches a **visible Chromium** window
  that flips through each chart and asserts it rendered.

Examples::

    # Best for watching charts: visible Chromium + pause between pages
    python scripts/validate_samples_browser.py --hero --pause-ms 1000

    # Auto-validate in Chromium AND open the click-through gallery
    python scripts/validate_samples_browser.py --gallery --pause-ms 1000

    # Just browse samples (no Playwright auto-flip) - usually what you want
    python scripts/validate_samples_browser.py --gallery-only

    # Full matrix, both themes, visible
    python scripts/validate_samples_browser.py --all-themes --pause-ms 800

    # CI-style (no window)
    python scripts/validate_samples_browser.py --headless --hero

Requires (except ``--gallery-only``)::

    pip install -e ".[dev,browser]"
    python -m playwright install chromium
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vizly.charts import CHART_TYPES  # noqa: E402
from vizly.config import reset_config  # noqa: E402
from vizly.maps import reset_opt_in_maps  # noqa: E402
from vizly.theme.registry import reset_registry  # noqa: E402

from tests.browser.checks import write_gallery_index  # noqa: E402
from tests.samples.fixtures import (  # noqa: E402
    HERO_CHART_TYPES,
    SAMPLE_THEMES,
    make_chart,
)
from tests.samples.paths import ARTIFACTS_HTML_DIR, html_artifact_path  # noqa: E402

# When Chromium is visible and the user did not set --pause-ms, keep each
# chart on screen long enough to actually see it.
DEFAULT_HEADED_PAUSE_MS = 800


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--hero",
        action="store_true",
        help="Only hero charts: line, bar, pie, map, mix",
    )
    p.add_argument(
        "--all-themes",
        action="store_true",
        help="Validate default and dark (default is theme=default only)",
    )
    p.add_argument(
        "--theme",
        default="default",
        help="Theme id when not using --all-themes (default: default)",
    )
    headed = p.add_mutually_exclusive_group()
    headed.add_argument(
        "--headed",
        dest="headless",
        action="store_false",
        help="Show a real Chromium window (default)",
    )
    headed.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Do not show the Chromium window (CI / quiet)",
    )
    p.set_defaults(headless=False)
    p.add_argument(
        "--gallery",
        action="store_true",
        help=(
            "Write artifacts/html/index.html and open it in your *system* browser "
            "(separate from Playwright Chromium). Still runs Chromium validation "
            "unless combined with --gallery-only."
        ),
    )
    p.add_argument(
        "--gallery-only",
        action="store_true",
        help=(
            "Only write/open the click-through gallery in your system browser; "
            "skip Playwright. Best for casual visual review."
        ),
    )
    p.add_argument(
        "--pause-ms",
        type=int,
        default=None,
        help=(
            "Pause between charts in Playwright Chromium so you can watch "
            f"(default: {DEFAULT_HEADED_PAUSE_MS} when headed, 0 when headless)"
        ),
    )
    p.add_argument(
        "--rebuild",
        action="store_true",
        help="Always regenerate HTML before validating (default: rebuild missing only)",
    )
    return p.parse_args(argv)


def _chart_types(hero: bool) -> list[str]:
    if hero:
        return list(HERO_CHART_TYPES)
    return sorted(CHART_TYPES.keys())


def _themes(all_themes: bool, theme: str) -> list[str]:
    if all_themes:
        return list(SAMPLE_THEMES)
    return [theme]


def _ensure_html(chart_type: str, theme: str, *, rebuild: bool) -> Path:
    path = html_artifact_path(chart_type, theme)
    if rebuild or not path.is_file():
        chart = make_chart(chart_type, theme=theme)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(chart.to_html(), encoding="utf-8")
    return path


def _resolve_pause_ms(args: argparse.Namespace, *, headless: bool) -> int:
    if args.pause_ms is not None:
        return max(0, int(args.pause_ms))
    return 0 if headless else DEFAULT_HEADED_PAUSE_MS


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    gallery_only = bool(args.gallery_only)
    want_gallery = bool(args.gallery) or gallery_only
    headless = bool(args.headless)
    pause_ms = _resolve_pause_ms(args, headless=headless)

    reset_registry()
    reset_config()
    reset_opt_in_maps()
    ARTIFACTS_HTML_DIR.mkdir(parents=True, exist_ok=True)

    types = _chart_types(args.hero)
    themes = _themes(args.all_themes, args.theme)
    entries: list[tuple[str, str, Path]] = []
    for chart_type in types:
        for theme in themes:
            path = _ensure_html(chart_type, theme, rebuild=args.rebuild)
            entries.append((chart_type, theme, path))

    if want_gallery:
        index = write_gallery_index(ARTIFACTS_HTML_DIR, entries)
        webbrowser.open(index.resolve().as_uri())
        print(f"Opened system-browser gallery: {index}")
        print("  (Click a chart name in the left sidebar to preview it.)")
        if gallery_only:
            print(
                "\nGallery-only mode: skipped Playwright. "
                "Browse the system browser window to review charts."
            )
            return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Playwright is not installed. Run:\n"
            '  pip install -e ".[dev,browser]"\n'
            "  python -m playwright install chromium\n"
            "Or use --gallery-only to browse without Playwright.",
            file=sys.stderr,
        )
        return 2

    from tests.browser.checks import validate_sample_html

    if headless:
        print(
            f"Validating {len(entries)} sample HTML file(s) in headless Chromium "
            f"(pause={pause_ms}ms)..."
        )
    else:
        print(
            f"Opening visible Chromium window for {len(entries)} chart(s) "
            f"(pause={pause_ms}ms between pages)..."
        )
        print(
            "  Watch for a Chromium window (may open behind other windows). "
            "This is separate from any system-browser gallery tab."
        )

    failed: list[str] = []
    # slow_mo makes headed navigation visibly paced; keep it modest vs pause_ms.
    slow_mo = min(250, pause_ms // 3) if (not headless and pause_ms > 0) else 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=[] if headless else ["--start-maximized"],
        )
        context = browser.new_context(
            viewport={"width": 1100, "height": 720} if headless else None,
            no_viewport=not headless,
        )
        page = context.new_page()
        try:
            if not headless:
                # Nudge focus so the window is less likely to stay behind terminals.
                page.bring_to_front()
            for chart_type, theme, path in entries:
                label = f"{chart_type}__{theme}"
                try:
                    validate_sample_html(page, path, label=label)
                    print(f"  OK  {label}")
                except Exception as exc:  # noqa: BLE001 - report and continue
                    failed.append(f"{label}: {exc}")
                    print(f"  FAIL {label}: {exc}", file=sys.stderr)
                if pause_ms > 0:
                    page.wait_for_timeout(pause_ms)
            if not headless and pause_ms > 0:
                # Brief hold on the last chart before closing.
                page.wait_for_timeout(min(1500, pause_ms))
        finally:
            browser.close()

    if failed:
        print(f"\n{len(failed)} failure(s):", file=sys.stderr)
        for item in failed:
            print(f"  - {item}", file=sys.stderr)
        return 1

    print(f"\nAll {len(entries)} sample pages rendered successfully.")
    if want_gallery:
        print("System-browser gallery stays open for manual click-through review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
