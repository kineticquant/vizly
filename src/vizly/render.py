"""HTML embed renderer with trusted local / allowlisted CDN assets."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.parse import urlparse

from vizly.theme.schema import ALLOWED_CDN_HOST_SUFFIXES

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
MAPS_DIR = ASSETS_DIR / "maps"

# In-memory cache for vendored JS (avoid re-reading ~1MB on every render).
_ASSET_CACHE: Dict[str, str] = {}
_MAP_CACHE: Dict[str, Dict[str, Any]] = {}

ECHARTS_FILENAME = "echarts.min.js"
ECHARTS_GL_FILENAME = "echarts-gl.min.js"
ECHARTS_WORDCLOUD_FILENAME = "echarts-wordcloud.min.js"
ECHARTS_LIQUID_FILENAME = "echarts-liquidfill.min.js"
ECHARTS_VERSION = "5.5.1"
ECHARTS_GL_VERSION = "2.0.9"
WORDCLOUD_VERSION = "2.1.0"
LIQUIDFILL_VERSION = "3.1.0"

# Markers embedded in HTML for provenance / regression tests.
LOCAL_ASSET_MARKER = f"vizly-asset:echarts@{ECHARTS_VERSION}"
LOCAL_GL_ASSET_MARKER = f"vizly-asset:echarts-gl@{ECHARTS_GL_VERSION}"
LOCAL_WORDCLOUD_MARKER = f"vizly-asset:echarts-wordcloud@{WORDCLOUD_VERSION}"
LOCAL_LIQUID_MARKER = f"vizly-asset:echarts-liquidfill@{LIQUIDFILL_VERSION}"

PLUGIN_ASSETS = {
    "wordcloud": (ECHARTS_WORDCLOUD_FILENAME, LOCAL_WORDCLOUD_MARKER),
    "liquidfill": (ECHARTS_LIQUID_FILENAME, LOCAL_LIQUID_MARKER),
}

_PLUGIN_CDN_PACKAGES = {
    "wordcloud": ("echarts-wordcloud", WORDCLOUD_VERSION, "echarts-wordcloud.min.js"),
    "liquidfill": ("echarts-liquidfill", LIQUIDFILL_VERSION, "echarts-liquidfill.min.js"),
}

_DEFAULT_CDN_PLUGINS = {
    name: f"https://cdn.jsdelivr.net/npm/{pkg}@{ver}/dist/{filename}"
    for name, (pkg, ver, filename) in _PLUGIN_CDN_PACKAGES.items()
}

# Host substrings banned in remote <script src> URLs (trust gate).
# Do not include bare "baidu" — vendored echarts.min.js contains Baidu Inc.
# copyright text. Baidu Map is blocked by having no map provider, not by
# substring scan of inlined JS.
BANNED_HOST_SUBSTRINGS = (
    "bootcdn",
    "baomitu",
    "staticfile.org",
    "staticfile.net",
    "cdnjs.cloudflare.com.cn",
    "assets.pyecharts.org",
    "npmmirror",
    "unpkg.zhimg.com",
    "map.baidu.com",
    "api.map.baidu.com",
    "map.qq.com",
    "amap.com",
)

_DEFAULT_CDN_ECHARTS = (
    f"https://cdn.jsdelivr.net/npm/echarts@{ECHARTS_VERSION}/dist/echarts.min.js"
)
_DEFAULT_CDN_ECHARTS_GL = (
    f"https://cdn.jsdelivr.net/npm/echarts-gl@{ECHARTS_GL_VERSION}/dist/echarts-gl.min.js"
)


class RenderError(ValueError):
    """Raised when HTML/assets cannot be rendered under the trust policy."""


_CSS_SIZE_RE = re.compile(
    r"^(?:"
    r"\d+(?:\.\d+)?(?:%|px|em|rem|vh|vw|cm|mm|in)?"
    r"|auto"
    r")$",
    re.IGNORECASE,
)


def sanitize_css_size(value: str, *, field: str = "size") -> str:
    """Allow only simple CSS length tokens for width/height injection."""
    cleaned = str(value).strip()
    if not _CSS_SIZE_RE.match(cleaned):
        raise RenderError(
            f"Invalid {field}={value!r}. Use a CSS length like '420px' or '100%'."
        )
    return cleaned


def assets_dir() -> Path:
    return ASSETS_DIR


def map_path(name: str) -> Path:
    """Return path to a bundled map GeoJSON (``world`` default atlas, or ``usa``)."""
    key = name.strip().lower()
    aliases = {"world": "world.json", "usa": "usa.json", "us": "usa.json"}
    filename = aliases.get(key, f"{key}.json")
    path = MAPS_DIR / filename
    if not path.is_file():
        available = ", ".join(p.stem for p in MAPS_DIR.glob("*.json")) or "(none)"
        raise RenderError(
            f"Unknown map {name!r}. Bundled maps: {available}."
        )
    return path


def load_map_geojson(name: str) -> Dict[str, Any]:
    """Load a bundled map GeoJSON as a dict (cached in-process)."""
    path = map_path(name)
    key = path.name
    cached = _MAP_CACHE.get(key)
    if cached is not None:
        return cached
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise RenderError(f"Map {name!r} GeoJSON must be a JSON object.")
    _MAP_CACHE[key] = data
    return data


def _read_asset(filename: str) -> str:
    path = ASSETS_DIR / filename
    if not path.is_file():
        raise RenderError(
            f"Missing vendored asset {filename!r} under {ASSETS_DIR}. "
            "Reinstall vizly or restore src/vizly/assets/."
        )
    cached = _ASSET_CACHE.get(filename)
    if cached is not None:
        return cached
    text = path.read_text(encoding="utf-8")
    _ASSET_CACHE[filename] = text
    return text


def _host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    return any(host == s or host.endswith("." + s) for s in ALLOWED_CDN_HOST_SUFFIXES)


def echarts_locale(theme: Mapping[str, Any]) -> str:
    """Map theme ``locale`` to an ECharts built-in locale id (``EN`` / ``ZH``)."""
    raw = str(theme.get("locale") or "en-US").strip().lower().replace("_", "-")
    if raw.startswith("zh"):
        return "ZH"
    return "EN"


def _script_src_urls(html: str) -> List[str]:
    return [
        match.group(1)
        for match in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I)
    ]


def _resolve_plugin_cdn_url(theme_assets: Mapping[str, Any], name: str) -> str:
    """Resolve plugin CDN URL on the same allowlisted host family as theme CDN."""
    if name not in _PLUGIN_CDN_PACKAGES:
        raise RenderError(f"Unknown plugin {name!r}.")
    pkg, ver, filename = _PLUGIN_CDN_PACKAGES[name]
    custom = theme_assets.get("cdn")
    if custom:
        host = (urlparse(str(custom).strip()).hostname or "").lower()
        if host == "unpkg.com" or host.endswith(".unpkg.com"):
            url = f"https://unpkg.com/{pkg}@{ver}/dist/{filename}"
            if not _host_allowed(url):
                raise RenderError(f"Plugin CDN URL not allowlisted: {url!r}.")
            return url
    url = _DEFAULT_CDN_PLUGINS[name]
    if not _host_allowed(url):
        raise RenderError(f"Plugin CDN URL not allowlisted: {url!r}.")
    return url


def resolve_cdn_url(
    theme_assets: Mapping[str, Any],
    *,
    kind: str = "echarts",
) -> str:
    """Resolve an allowlisted CDN URL for echarts or echarts-gl."""
    custom = theme_assets.get("cdn")
    if custom:
        url = str(custom).strip()
        if kind == "echarts-gl":
            # If user pointed at echarts.min.js, derive a sibling gl URL when possible.
            if url.endswith("echarts.min.js"):
                url = url.replace("echarts.min.js", "echarts-gl.min.js")
            elif "echarts@" in url and "echarts-gl" not in url:
                host = (urlparse(url).hostname or "").lower()
                if host == "unpkg.com" or host.endswith(".unpkg.com"):
                    url = (
                        f"https://unpkg.com/echarts-gl@{ECHARTS_GL_VERSION}"
                        "/dist/echarts-gl.min.js"
                    )
                else:
                    url = _DEFAULT_CDN_ECHARTS_GL
        if not _host_allowed(url):
            raise RenderError(
                f"CDN URL host is not allowlisted: {url!r}. "
                f"Allowed: {', '.join(ALLOWED_CDN_HOST_SUFFIXES)}."
            )
        return url
    return _DEFAULT_CDN_ECHARTS_GL if kind == "echarts-gl" else _DEFAULT_CDN_ECHARTS


def assert_html_trust_safe(html: str, *, asset_mode: str = "local") -> None:
    """Raise if remote script URLs reference banned or non-allowlisted hosts.

    Scans ``<script src>`` URLs only — not chart option JSON — so category
    labels that mention a banned substring do not block rendering.
    """
    for src in _script_src_urls(html):
        lowered = src.lower()
        for banned in BANNED_HOST_SUBSTRINGS:
            if banned in lowered:
                raise RenderError(
                    f"HTML references banned asset host substring {banned!r} "
                    f"in script src ({src!r})."
                )
        if asset_mode == "local":
            if lowered.startswith("http://") or lowered.startswith("https://"):
                raise RenderError(
                    f"Local asset mode HTML must not use remote script src ({src!r})."
                )
        elif not _host_allowed(src):
            raise RenderError(
                f"CDN mode script src is not allowlisted: {src!r}."
            )


def build_script_tags(
    theme: Mapping[str, Any],
    *,
    include_gl: bool = False,
    plugins: Optional[List[str]] = None,
) -> Tuple[str, str]:
    """Return (script_html, asset_mode) for the theme's asset policy.

    ``plugins`` may include ``wordcloud`` and/or ``liquidfill`` (loaded only
    when requested by chart types that need them).
    """
    assets = theme.get("assets") or {}
    mode = assets.get("mode") or "local"
    if mode not in ("local", "cdn"):
        raise RenderError(f"Unknown assets.mode {mode!r}; use 'local' or 'cdn'.")

    parts: List[str] = []
    plugin_list = list(plugins or [])
    if mode == "local":
        echarts_js = _read_asset(ECHARTS_FILENAME)
        parts.append(
            f"<!-- {LOCAL_ASSET_MARKER} -->\n"
            f"<script>\n{echarts_js}\n</script>"
        )
        if include_gl:
            gl_js = _read_asset(ECHARTS_GL_FILENAME)
            parts.append(
                f"<!-- {LOCAL_GL_ASSET_MARKER} -->\n"
                f"<script>\n{gl_js}\n</script>"
            )
        for name in plugin_list:
            if name not in PLUGIN_ASSETS:
                raise RenderError(f"Unknown plugin {name!r}.")
            filename, marker = PLUGIN_ASSETS[name]
            parts.append(
                f"<!-- {marker} -->\n<script>\n{_read_asset(filename)}\n</script>"
            )
    else:
        echarts_url = resolve_cdn_url(assets, kind="echarts")
        parts.append(f'<script src="{echarts_url}"></script>')
        if include_gl:
            gl_url = resolve_cdn_url(assets, kind="echarts-gl")
            parts.append(f'<script src="{gl_url}"></script>')
        for name in plugin_list:
            if name not in _PLUGIN_CDN_PACKAGES:
                raise RenderError(f"Unknown plugin {name!r}.")
            url = _resolve_plugin_cdn_url(assets, name)
            parts.append(f'<script src="{url}"></script>')

    return "\n".join(parts), mode


def render_html(
    option: Mapping[str, Any],
    *,
    theme: Mapping[str, Any],
    width: str = "100%",
    height: str = "400px",
    chart_id: Optional[str] = None,
    include_gl: bool = False,
    plugins: Optional[List[str]] = None,
    title: Optional[str] = None,
    register_maps: Optional[Mapping[str, Mapping[str, Any]]] = None,
    fragment: bool = False,
    include_assets: bool = True,
    chart_type: str = "chart",
    events: bool = True,
    message_origin: Optional[str] = None,
) -> str:
    """Build HTML for a chart option.

    ``fragment=False`` (default): complete HTML document.
    ``fragment=True``: chart root ``<div>`` + scripts only (templates / HTMX).
    ``include_assets=False``: omit ECharts library tags (parent already loaded them).
    ``message_origin``: ``postMessage`` targetOrigin (``None`` = same-origin).
    """
    from vizly.events import chart_bootstrap_script

    cid = chart_id or f"vizly_{uuid.uuid4().hex[:12]}"
    safe_width = sanitize_css_size(width, field="width")
    safe_height = sanitize_css_size(height, field="height")
    assets = theme.get("assets") or {}
    mode = assets.get("mode") or "local"
    if include_assets:
        scripts, mode = build_script_tags(
            theme, include_gl=include_gl, plugins=plugins
        )
    else:
        if mode not in ("local", "cdn"):
            raise RenderError(f"Unknown assets.mode {mode!r}; use 'local' or 'cdn'.")
        scripts = ""
    # Work on a mutable copy so polygon/layer keys can be stripped for setOption.
    option_data = dict(option)
    option_json = json.dumps(option_data, ensure_ascii=False, allow_nan=False)
    page_title = title or (theme.get("name") and f"vizly — {theme['name']}") or "vizly"

    # Escape </script> inside JSON just in case.
    option_json = option_json.replace("</", "<\\/")

    map_js_parts: List[str] = []
    if register_maps:
        for map_name, geojson in register_maps.items():
            geo_json = json.dumps(geojson, ensure_ascii=False, allow_nan=False).replace(
                "</", "<\\/"
            )
            safe_name = json.dumps(map_name)
            map_js_parts.append(
                f"echarts.registerMap({safe_name}, {geo_json});"
            )
    map_js = "\n      ".join(map_js_parts)
    locale_json = json.dumps(echarts_locale(theme))
    init_script = chart_bootstrap_script(
        cid,
        option_json,
        locale_json,
        chart_type,
        events=events,
        message_origin=message_origin,
        map_js=map_js,
    )

    chart_div = (
        f'<div id="{cid}" class="vizly-chart" data-vizly-asset-mode="{mode}" '
        f'style="width:{safe_width};height:{safe_height};"></div>'
    )

    if fragment:
        # Single primary root wrapper for HTMX swaps / template blocks.
        html = (
            f'<div class="vizly-embed" data-vizly-fragment="1">'
            f"{chart_div}{scripts}{init_script}</div>"
        )
        assert_html_trust_safe(html, asset_mode=mode)
        return html

    html = f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_escape_html(page_title)}</title>
  <style>
    html, body {{ margin: 0; padding: 0; background: {_escape_html(str(theme.get("background", "#fff")))}; }}
    #{cid} {{ width: {safe_width}; height: {safe_height}; }}
  </style>
</head>
<body>
  {chart_div}
  {scripts}
  {init_script}
</body>
</html>
"""
    assert_html_trust_safe(html, asset_mode=mode)
    return html


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
