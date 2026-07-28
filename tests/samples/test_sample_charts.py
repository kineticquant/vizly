"""Level 2 — sample / golden chart suite.

Builds every registered chart type for ``default`` and ``dark`` themes,
writes self-contained HTML under ``artifacts/html/`` (gitignored), and
compares ``to_option()`` against checked-in ``goldens/options/``.

Refresh goldens after intentional option/theme changes::

    python -m pytest -m samples --update-goldens -q
    # or
    python scripts/update_sample_goldens.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import pytest

from vizly.charts import CHART_TYPES
from vizly.config import reset_config
from vizly.maps import reset_opt_in_maps
from vizly.render import LOCAL_ASSET_MARKER, assert_html_trust_safe
from vizly.theme.registry import reset_registry

from tests.samples.fixtures import SAMPLE_THEMES, make_chart
from tests.samples.normalize import canonicalize_option, option_golden_text
from tests.samples.paths import golden_path, html_artifact_path

ALL_TYPES = sorted(CHART_TYPES.keys())
MIN_HTML_BYTES = 50_000  # local mode embeds echarts.min.js


@pytest.fixture(scope="module")
def sample_builds(
    artifacts_html_dir: Path,
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Build all chart×theme samples once per module; write HTML artifacts."""
    reset_registry()
    reset_config()
    reset_opt_in_maps()
    artifacts_html_dir.mkdir(parents=True, exist_ok=True)

    built: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for chart_type in ALL_TYPES:
        for theme in SAMPLE_THEMES:
            chart = make_chart(chart_type, theme=theme)
            option = chart.to_option()
            html = chart.to_html()
            out = html_artifact_path(chart_type, theme)
            out.write_text(html, encoding="utf-8")
            built[(chart_type, theme)] = {
                "chart": chart,
                "option": option,
                "html": html,
                "html_path": out,
            }
    return built


@pytest.mark.samples
@pytest.mark.parametrize("theme", SAMPLE_THEMES)
@pytest.mark.parametrize("chart_type", ALL_TYPES)
def test_sample_chart_option_golden(
    chart_type: str,
    theme: str,
    sample_builds: Dict[Tuple[str, str], Dict[str, Any]],
    update_goldens: bool,
    goldens_options_dir: Path,
) -> None:
    payload = sample_builds[(chart_type, theme)]
    option = payload["option"]
    assert isinstance(option, dict)
    if chart_type in ("page", "tab"):
        compose = option.get("_vizly_compose")
        assert isinstance(compose, dict)
        assert compose.get("type") == chart_type
        assert isinstance(compose.get("options"), list)
        assert len(compose["options"]) >= 1
    else:
        assert "series" in option
        assert isinstance(option["series"], list)
        assert len(option["series"]) >= 1
    json.dumps(option, allow_nan=False, default=str)

    path = golden_path(chart_type, theme)
    text = option_golden_text(option)
    if update_goldens:
        goldens_options_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return

    if not path.is_file():
        pytest.fail(
            f"Missing golden {path}. "
            "Generate with: python -m pytest -m samples --update-goldens "
            "or python scripts/update_sample_goldens.py"
        )

    expected = json.loads(path.read_text(encoding="utf-8"))
    actual = canonicalize_option(option)
    assert actual == expected, (
        f"Option golden mismatch for {chart_type!r} theme={theme!r}.\n"
        f"Update deliberately with: pytest -m samples --update-goldens\n"
        f"Golden: {path}"
    )


@pytest.mark.samples
@pytest.mark.parametrize("theme", SAMPLE_THEMES)
@pytest.mark.parametrize("chart_type", ALL_TYPES)
def test_sample_chart_html_artifact(
    chart_type: str,
    theme: str,
    sample_builds: Dict[Tuple[str, str], Dict[str, Any]],
) -> None:
    payload = sample_builds[(chart_type, theme)]
    html = payload["html"]
    path: Path = payload["html_path"]

    assert path.is_file()
    assert path.stat().st_size >= MIN_HTML_BYTES
    assert LOCAL_ASSET_MARKER in html
    assert "echarts.init" in html
    # Trust gate: script src URLs only (inlined echarts may mention Baidu Inc.).
    assert_html_trust_safe(html, asset_mode="local")
    assert "<script src=" not in html.lower()

    # Standard single-chart HTML includes the asset-mode marker; page/tab
    # compose paths build a custom document but still embed local ECharts.
    if chart_type not in ("page", "tab"):
        assert 'data-vizly-asset-mode="local"' in html

    # Theme chrome should surface in the embedded option JSON.
    assert '"backgroundColor"' in html or "backgroundColor" in html

    if chart_type in ("map", "geo"):
        assert "registerMap" in html

    chart = payload["chart"]
    if getattr(chart, "_needs_gl", False):
        assert "vizly-asset:echarts-gl@" in html
    plugins = getattr(chart, "_plugins", ()) or ()
    if "wordcloud" in plugins:
        assert "vizly-asset:echarts-wordcloud@" in html
    if "liquidfill" in plugins:
        assert "vizly-asset:echarts-liquidfill@" in html
