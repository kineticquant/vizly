"""Level 3 — browser / visual smoke for hero charts.

Not a per-commit gate. Run via::

    pip install -e ".[dev,browser]"
    python -m playwright install chromium
    python -m pytest -m browser -v

For a local visible walkthrough of sample HTML (all charts or hero)::

    python scripts/validate_samples_browser.py
    python scripts/validate_samples_browser.py --gallery --pause-ms 600
"""

from __future__ import annotations

from typing import Dict

import pytest
from tests.browser.checks import validate_sample_html
from tests.samples.fixtures import HERO_CHART_TYPES, make_chart
from tests.samples.paths import ARTIFACTS_HTML_DIR, html_artifact_path

from vizly.config import reset_config
from vizly.maps import reset_opt_in_maps
from vizly.theme.registry import reset_registry

pytestmark = pytest.mark.browser

HERO_THEME = "default"


@pytest.fixture(autouse=True)
def _clean():
    reset_registry()
    reset_config()
    reset_opt_in_maps()
    yield
    reset_registry()
    reset_config()
    reset_opt_in_maps()


@pytest.fixture(scope="module")
def hero_html_files() -> Dict[str, object]:
    """Ensure hero sample HTML exists under artifacts/html/."""
    reset_registry()
    reset_config()
    reset_opt_in_maps()
    ARTIFACTS_HTML_DIR.mkdir(parents=True, exist_ok=True)
    paths = {}
    for chart_type in HERO_CHART_TYPES:
        chart = make_chart(chart_type, theme=HERO_THEME, title=f"hero-{chart_type}")
        path = html_artifact_path(chart_type, HERO_THEME)
        path.write_text(chart.to_html(), encoding="utf-8")
        paths[chart_type] = path
    return paths


@pytest.fixture(scope="module")
def chromium_browser():
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.mark.parametrize("chart_type", HERO_CHART_TYPES)
def test_hero_chart_loads_in_chromium(
    chart_type: str,
    hero_html_files,
    chromium_browser,
) -> None:
    path = hero_html_files[chart_type]
    assert path.is_file()
    page = chromium_browser.new_page()
    try:
        validate_sample_html(page, path, label=chart_type)
    finally:
        page.close()
