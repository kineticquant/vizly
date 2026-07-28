"""Shared Playwright checks for sample HTML (hero + full matrix)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

READY_JS = """() => {
  const nodes = document.querySelectorAll('canvas, svg');
  if (!nodes.length) return false;
  if (typeof echarts === 'undefined') return false;
  return true;
}"""

DRAWING_JS = """() => {
  const canvas = document.querySelector('canvas');
  if (canvas) return canvas.width > 0 && canvas.height > 0;
  return !!document.querySelector('svg');
}"""

INSTANCE_JS = """() => {
  const els = document.querySelectorAll('.vizly-chart, [id^="vizly_"]');
  if (!els.length || typeof echarts === 'undefined') return false;
  for (const el of els) {
    const inst = echarts.getInstanceByDom(el);
    if (inst && typeof inst.getOption === 'function') return true;
  }
  return false;
}"""


def validate_sample_html(page, path: Path, *, label: str, timeout_ms: int = 60_000) -> None:
    """Load ``path`` in ``page`` and assert ECharts initialized without errors."""
    console_errors: List[str] = []
    page_errors: List[str] = []

    def _on_console(msg) -> None:
        if msg.type == "error":
            console_errors.append(msg.text)

    def _on_page_error(exc) -> None:
        page_errors.append(str(exc))

    page.on("console", _on_console)
    page.on("pageerror", _on_page_error)

    page.goto(path.resolve().as_uri(), wait_until="load", timeout=timeout_ms)
    page.wait_for_function(READY_JS, timeout=min(timeout_ms, 30_000))

    assert page.evaluate(DRAWING_JS), f"{label}: expected canvas/svg after echarts.init"
    assert page.evaluate(INSTANCE_JS), f"{label}: echarts instance missing on chart root"
    assert not page_errors, f"{label}: page errors: {page_errors}"
    real_errors = [e for e in console_errors if "favicon" not in e.lower()]
    assert not real_errors, f"{label}: console errors: {real_errors}"


def write_gallery_index(
    html_dir: Path,
    entries: Sequence[tuple[str, str, Path]],
) -> Path:
    """Write a simple click-through gallery index for sample HTML files."""
    links = []
    for chart_type, theme, path in entries:
        rel = path.name
        links.append(
            f'<li><a href="{rel}" target="preview">{chart_type} · {theme}</a></li>'
        )
    body = "\n".join(links)
    index = html_dir / "index.html"
    index.write_text(
        f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8"/>
  <title>vizly sample gallery</title>
  <style>
    :root {{ color-scheme: light; }}
    body {{ margin: 0; font-family: Georgia, serif; display: grid;
           grid-template-columns: 240px 1fr; height: 100vh; }}
    aside {{ overflow: auto; border-right: 1px solid #ccc; padding: 1rem; background: #f6f4ef; }}
    h1 {{ font-size: 1.1rem; margin: 0 0 0.75rem; }}
    ul {{ list-style: none; padding: 0; margin: 0; font-size: 0.9rem; }}
    li {{ margin: 0.25rem 0; }}
    a {{ color: #0d6e6e; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    iframe {{ border: 0; width: 100%; height: 100%; background: #fff; }}
  </style>
</head>
<body>
  <aside>
    <h1>vizly samples</h1>
    <p style="font-size:0.8rem;color:#555;margin:0 0 1rem">
      Click a chart to preview. Generated under <code>artifacts/html/</code>.
    </p>
    <ul>
{body}
    </ul>
  </aside>
  <iframe name="preview" title="Chart preview"></iframe>
</body>
</html>
""",
        encoding="utf-8",
    )
    return index
