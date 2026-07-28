"""Composition helpers: grid, mix/combo, page, tab, timeline."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional, Sequence, Tuple

from vizly.base import BaseChart
from vizly.charts._helpers import (
    YLike,
    apply_series_defaults,
    prepare_frame,
)
from vizly.config import resolve_theme
from vizly.data import DataError, column_values
from vizly.theme.apply import apply_theme_to_option


def _require_child_charts(
    charts: Optional[Sequence[BaseChart]], kind: str
) -> List[BaseChart]:
    children = list(charts or [])
    if not children:
        raise DataError(f"{kind} requires charts=[...] with at least one BaseChart.")
    for i, child in enumerate(children):
        if not isinstance(child, BaseChart):
            raise DataError(
                f"{kind} charts[{i}] must be a vizly BaseChart, "
                f"got {type(child).__name__}."
            )
    return children


def _aggregate_child_render_deps(
    children: Sequence[BaseChart],
    *,
    load_maps: bool = True,
) -> Tuple[bool, List[str], Dict[str, Dict[str, Any]]]:
    """Union GL / plugins / map packs needed to render ``children``."""
    need_gl = False
    plugins: List[str] = []
    maps: Dict[str, Dict[str, Any]] = {}
    for child in children:
        if child._needs_gl:
            need_gl = True
        for p in child._plugins or ():
            if p not in plugins:
                plugins.append(p)
        if load_maps:
            if hasattr(child, "_ensure_maps"):
                child._ensure_maps()
            for name, geo in (child._register_maps or {}).items():
                maps.setdefault(name, geo)
    return need_gl, plugins, maps


def _child_option_with_parent_theme(
    child: BaseChart, parent_theme_override: Any
) -> Dict[str, Any]:
    """Resolve child option using parent theme when child has none (no mutation)."""
    if parent_theme_override is None or child._theme_override is not None:
        return child.to_option()
    structural = child._structural_with_title(child._build())
    theme = resolve_theme(parent_theme_override)
    return apply_theme_to_option(
        structural, theme, user_option=child._user_option or None
    )


def _has_cartesian_axes(opt: Dict[str, Any]) -> bool:
    return "xAxis" in opt and "yAxis" in opt


class GridChart(BaseChart):
    """Arrange multiple **cartesian** vizly charts in an ECharts multi-grid layout.

    Children must produce ``xAxis`` + ``yAxis`` (line, bar, scatter, etc.).
    Non-cartesian types (pie, map, gauge, sankey, …) are rejected — use
    :class:`PageChart` or :class:`TabChart` for mixed layouts.
    """

    chart_type = "grid"

    def __init__(
        self,
        charts: Optional[Sequence[BaseChart]] = None,
        *,
        cols: int = 2,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=None,
            title=title,
            width=width,
            height=height or "720px",
            theme=theme,
            option=option,
            **kwargs,
        )
        self.charts = _require_child_charts(charts, "grid")
        self.cols = max(1, int(cols))
        need_gl, plugins, _maps = _aggregate_child_render_deps(
            self.charts, load_maps=False
        )
        self._needs_gl = need_gl
        self._plugins = tuple(plugins)

    def _build(self) -> Dict[str, Any]:
        n = len(self.charts)
        cols = self.cols
        rows = (n + cols - 1) // cols
        grids: List[Dict[str, Any]] = []
        x_axes: List[Dict[str, Any]] = []
        y_axes: List[Dict[str, Any]] = []
        series: List[Dict[str, Any]] = []
        cell_w = 100 / cols
        cell_h = 100 / rows

        for idx, child in enumerate(self.charts):
            # Use child's structural option without its own full theme pass;
            # parent theme applies once.
            child_opt = child._structural_with_title(child._build())
            if not _has_cartesian_axes(child_opt):
                raise DataError(
                    f"grid charts[{idx}] ({child.chart_type!r}) is not cartesian "
                    "(needs xAxis + yAxis). Use page/tab for mixed chart types."
                )
            r, c = divmod(idx, cols)
            left = c * cell_w + 4
            top = r * cell_h + 6
            width = cell_w - 8
            height = cell_h - 10
            grids.append(
                {
                    "left": f"{left}%",
                    "top": f"{top}%",
                    "width": f"{width}%",
                    "height": f"{height}%",
                }
            )
            cx = child_opt.get("xAxis")
            cy = child_opt.get("yAxis")
            if isinstance(cx, dict):
                xa = deepcopy(cx)
                xa["gridIndex"] = idx
                x_axes.append(xa)
            elif isinstance(cx, list) and cx:
                xa = deepcopy(cx[0])
                xa["gridIndex"] = idx
                x_axes.append(xa)
            else:
                raise DataError(
                    f"grid charts[{idx}] has unsupported xAxis shape."
                )

            if isinstance(cy, dict):
                ya = deepcopy(cy)
                ya["gridIndex"] = idx
                y_axes.append(ya)
            elif isinstance(cy, list) and cy:
                ya = deepcopy(cy[0])
                ya["gridIndex"] = idx
                y_axes.append(ya)
            else:
                raise DataError(
                    f"grid charts[{idx}] has unsupported yAxis shape."
                )

            for s in child_opt.get("series") or []:
                if not isinstance(s, dict):
                    continue
                sc = deepcopy(s)
                sc["xAxisIndex"] = idx
                sc["yAxisIndex"] = idx
                series.append(sc)

        return {
            "tooltip": {"trigger": "axis"},
            "grid": grids,
            "xAxis": x_axes,
            "yAxis": y_axes,
            "series": series,
        }


class MixChart(BaseChart):
    """Overlay bar + line (combo) on shared axes."""

    chart_type = "mix"

    def __init__(
        self,
        data: Any = None,
        *,
        x: Optional[str] = None,
        bar: Optional[YLike] = None,
        line: Optional[YLike] = None,
        y: Optional[YLike] = None,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data,
            title=title,
            width=width,
            height=height,
            theme=theme,
            option=option,
            **kwargs,
        )
        self.x = x
        self.bar = bar
        self.line = line
        # y= as all bar series if bar/line not split
        self.y = y

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        from vizly.data import resolve_y_columns, require_columns

        bar_cols = resolve_y_columns(self.bar) if self.bar is not None else []
        line_cols = resolve_y_columns(self.line) if self.line is not None else []
        if not bar_cols and not line_cols:
            if self.y is None:
                raise DataError(
                    "mix/combo requires bar=, line=, or y= column roles."
                )
            cols = resolve_y_columns(self.y)
            if len(cols) == 1:
                bar_cols, line_cols = cols, []
            else:
                mid = max(1, len(cols) // 2)
                bar_cols, line_cols = cols[:mid], cols[mid:]

        measure_cols = bar_cols + line_cols
        if self.x is not None:
            x = self.x
        else:
            candidates = [c for c in df.columns if c not in measure_cols]
            if not candidates:
                raise DataError(
                    "mix/combo could not infer x=. Pass x= explicitly "
                    f"(columns: {', '.join(map(str, df.columns))})."
                )
            x = str(candidates[0])

        require_columns(df, x, *measure_cols)
        categories = column_values(df, x)
        series: List[Dict[str, Any]] = []
        for col in bar_cols:
            s = apply_series_defaults(
                {"name": col, "type": "bar", "data": column_values(df, col)},
                self.theme,
                "bar",
            )
            series.append(s)
        for col in line_cols:
            s = apply_series_defaults(
                {"name": col, "type": "line", "data": column_values(df, col)},
                self.theme,
                "line",
            )
            series.append(s)
        return {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": bar_cols + line_cols},
            "xAxis": {"type": "category", "data": categories},
            "yAxis": {"type": "value"},
            "series": series,
        }


ComboChart = MixChart


class PageChart(BaseChart):
    """Stack multiple vizly charts vertically in one HTML page.

    ECharts (+ GL/plugins) and map GeoJSON are embedded **once** for all
    children. Parent ``theme=`` styles children that have no theme of their
    own without mutating those child instances.
    """

    chart_type = "page"

    def __init__(
        self,
        charts: Optional[Sequence[BaseChart]] = None,
        *,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=None,
            title=title,
            width=width,
            height=height or "100%",
            theme=theme,
            option=option,
            **kwargs,
        )
        self.charts = _require_child_charts(charts, "page")
        need_gl, plugins, _maps = _aggregate_child_render_deps(
            self.charts, load_maps=False
        )
        self._needs_gl = need_gl
        self._plugins = tuple(plugins)

    def _build(self) -> Dict[str, Any]:
        child_opts = [
            _child_option_with_parent_theme(c, self._theme_override)
            for c in self.charts
        ]
        # Compose descriptor for JSON/API consumers (not a single ECharts option).
        return {
            "title": {"text": self.title or "page"},
            "_vizly_compose": {"type": "page", "options": child_opts},
        }

    def to_html(
        self,
        *,
        fragment: bool = False,
        width: Optional[str] = None,
        height: Optional[str] = None,
        include_assets: bool = True,
    ) -> str:
        import json
        import uuid

        from vizly.render import (
            assert_html_trust_safe,
            build_script_tags,
            echarts_locale,
            sanitize_css_size,
            _escape_html,
        )

        need_gl, plugins, maps = _aggregate_child_render_deps(self.charts)
        page_theme = self.theme
        locale_json = json.dumps(echarts_locale(page_theme))
        if include_assets:
            scripts, mode = build_script_tags(
                page_theme, include_gl=need_gl, plugins=plugins or None
            )
        else:
            assets = page_theme.get("assets") or {}
            mode = assets.get("mode") or "local"
            scripts = ""

        # registerMap once (world.json alone is ~1MB).
        map_js = ""
        for map_name, geojson in maps.items():
            geo = json.dumps(
                geojson, ensure_ascii=False, allow_nan=False
            ).replace("</", "<\\/")
            map_js += f"echarts.registerMap({json.dumps(map_name)}, {geo});"

        bodies: List[str] = []
        for child in self.charts:
            cid = f"vizly_{uuid.uuid4().hex[:10]}"
            opt = json.dumps(
                _child_option_with_parent_theme(child, self._theme_override),
                ensure_ascii=False,
                allow_nan=False,
            ).replace("</", "<\\/")
            h = sanitize_css_size(
                height or child.height or "360px", field="height"
            )
            w = sanitize_css_size(
                width or child.width or "100%", field="width"
            )
            bodies.append(
                f"<h2>{_escape_html(child.title or child.chart_type)}</h2>"
                f"<div id='{cid}' class='vizly-chart' style='width:{w};height:{h}' "
                f"data-vizly-asset-mode='{mode}'></div>"
                f"<script>(function(){{var el=document.getElementById('{cid}');"
                f"var chart=echarts.init(el,null,{{locale:{locale_json}}});"
                f"chart.setOption({opt});"
                f"window.addEventListener('resize',function(){{chart.resize();}});}})();"
                f"</script>"
            )

        # Shared map registration before first init when maps are present.
        if map_js:
            bodies.insert(0, f"<script>{map_js}</script>")

        body_html = "".join(bodies)
        if fragment:
            html = (
                f"<div class='vizly-embed' data-vizly-fragment='1'>"
                f"{scripts}{body_html}</div>"
            )
            assert_html_trust_safe(html, asset_mode=mode)
            return html

        page = (
            "<!DOCTYPE html><html lang='en-US'><head><meta charset='utf-8'/>"
            f"<title>{_escape_html(self.title or 'vizly page')}</title>"
            f"{scripts}</head><body>{body_html}</body></html>"
        )
        assert_html_trust_safe(page, asset_mode=mode)
        return page


class TabChart(BaseChart):
    """Tabbed composition of vizly child charts (HTML tab controls)."""

    chart_type = "tab"

    def __init__(
        self,
        charts: Optional[Sequence[BaseChart]] = None,
        *,
        labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=None,
            title=title,
            width=width,
            height=height or "480px",
            theme=theme,
            option=option,
            **kwargs,
        )
        self.charts = _require_child_charts(charts, "tab")
        self.labels = list(labels) if labels else [
            c.title or c.chart_type for c in self.charts
        ]
        need_gl, plugins, _maps = _aggregate_child_render_deps(
            self.charts, load_maps=False
        )
        self._needs_gl = need_gl
        self._plugins = tuple(plugins)

    def _build(self) -> Dict[str, Any]:
        return {
            "title": {"text": self.title or "tab"},
            "_vizly_compose": {
                "type": "tab",
                "labels": self.labels,
                "options": [
                    _child_option_with_parent_theme(c, self._theme_override)
                    for c in self.charts
                ],
            },
        }

    def to_html(
        self,
        *,
        fragment: bool = False,
        width: Optional[str] = None,
        height: Optional[str] = None,
        include_assets: bool = True,
    ) -> str:
        import json
        import uuid

        from vizly.render import (
            assert_html_trust_safe,
            build_script_tags,
            echarts_locale,
            sanitize_css_size,
            _escape_html,
        )

        need_gl, plugins, maps = _aggregate_child_render_deps(self.charts)
        page_theme = self.theme
        locale_json = json.dumps(echarts_locale(page_theme))
        if include_assets:
            scripts, mode = build_script_tags(
                page_theme, include_gl=need_gl, plugins=plugins or None
            )
        else:
            assets = page_theme.get("assets") or {}
            mode = assets.get("mode") or "local"
            scripts = ""

        map_js = ""
        for map_name, geojson in maps.items():
            geo = json.dumps(
                geojson, ensure_ascii=False, allow_nan=False
            ).replace("</", "<\\/")
            map_js += f"echarts.registerMap({json.dumps(map_name)}, {geo});"

        root_id = f"vizly_tabs_{uuid.uuid4().hex[:10]}"
        h = sanitize_css_size(height or self.height or "480px", field="height")
        w = sanitize_css_size(width or self.width or "100%", field="width")

        buttons: List[str] = []
        panels: List[str] = []
        inits: List[str] = []
        for i, child in enumerate(self.charts):
            label = self.labels[i] if i < len(self.labels) else child.chart_type
            panel_id = f"{root_id}_p{i}"
            btn_id = f"{root_id}_b{i}"
            display = "block" if i == 0 else "none"
            aria = "true" if i == 0 else "false"
            buttons.append(
                f"<button type='button' id='{btn_id}' role='tab' "
                f"aria-selected='{aria}' aria-controls='{panel_id}' "
                f"data-vizly-tab='{i}' "
                f"style='margin-right:0.5rem;cursor:pointer'>"
                f"{_escape_html(str(label))}</button>"
            )
            panels.append(
                f"<div id='{panel_id}' role='tabpanel' "
                f"style='display:{display};width:{w};height:{h}' "
                f"class='vizly-chart' data-vizly-asset-mode='{mode}'></div>"
            )
            opt = json.dumps(
                _child_option_with_parent_theme(child, self._theme_override),
                ensure_ascii=False,
                allow_nan=False,
            ).replace("</", "<\\/")
            inits.append(
                f"var el{i}=document.getElementById('{panel_id}');"
                f"var c{i}=echarts.init(el{i},null,{{locale:{locale_json}}});"
                f"c{i}.setOption({opt});"
                f"charts.push(c{i});"
            )

        n = len(self.charts)
        switch_js = (
            f"function showTab(idx){{"
            f"for(var i=0;i<{n};i++){{"
            f"var p=document.getElementById('{root_id}_p'+i);"
            f"var b=document.getElementById('{root_id}_b'+i);"
            f"if(p)p.style.display=(i===idx)?'block':'none';"
            f"if(b)b.setAttribute('aria-selected',i===idx?'true':'false');"
            f"}}"
            f"if(charts[idx])charts[idx].resize();"
            f"}}"
            f"document.getElementById('{root_id}').addEventListener('click',"
            f"function(e){{var t=e.target.closest('[data-vizly-tab]');"
            f"if(!t)return;showTab(parseInt(t.getAttribute('data-vizly-tab'),10));}});"
        )

        body_html = (
            f"<div id='{root_id}' class='vizly-tabs'>"
            f"<div role='tablist'>{''.join(buttons)}</div>"
            f"{''.join(panels)}"
            f"<script>(function(){{var charts=[];{map_js}"
            f"{''.join(inits)}{switch_js}"
            f"window.addEventListener('resize',function(){{"
            f"charts.forEach(function(c){{c.resize();}});}});}})();</script>"
            f"</div>"
        )

        if fragment:
            html = (
                f"<div class='vizly-embed' data-vizly-fragment='1'>"
                f"{scripts}{body_html}</div>"
            )
            assert_html_trust_safe(html, asset_mode=mode)
            return html

        page = (
            "<!DOCTYPE html><html lang='en-US'><head><meta charset='utf-8'/>"
            f"<title>{_escape_html(self.title or 'vizly tabs')}</title>"
            f"{scripts}</head><body>{body_html}</body></html>"
        )
        assert_html_trust_safe(page, asset_mode=mode)
        return page


class TimelineChart(BaseChart):
    """ECharts timeline over child vizly chart options."""

    chart_type = "timeline"

    def __init__(
        self,
        charts: Optional[Sequence[BaseChart]] = None,
        *,
        labels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Any = None,
        option: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=None,
            title=title,
            width=width,
            height=height or "480px",
            theme=theme,
            option=option,
            **kwargs,
        )
        self.charts = _require_child_charts(charts, "timeline")
        self.labels = list(labels) if labels else [
            c.title or f"t{i}" for i, c in enumerate(self.charts)
        ]
        need_gl, plugins, _maps = _aggregate_child_render_deps(
            self.charts, load_maps=False
        )
        self._needs_gl = need_gl
        self._plugins = tuple(plugins)

    def _build(self) -> Dict[str, Any]:
        options = [
            _child_option_with_parent_theme(c, self._theme_override)
            for c in self.charts
        ]
        base = deepcopy(options[0]) if options else {"series": []}
        for opt in options:
            opt.pop("_vizly_compose", None)
        return {
            "baseOption": {
                "timeline": {
                    "axisType": "category",
                    "autoPlay": False,
                    "data": self.labels,
                },
                "tooltip": base.get("tooltip", {}),
                "legend": base.get("legend", {}),
            },
            "options": options,
            "series": base.get("series", [{"type": "line", "data": []}]),
        }

    def to_html(
        self,
        *,
        fragment: bool = False,
        width: Optional[str] = None,
        height: Optional[str] = None,
        include_assets: bool = True,
    ) -> str:
        _need_gl, _plugins, maps = _aggregate_child_render_deps(self.charts)
        self._register_maps = maps
        return super().to_html(
            fragment=fragment,
            width=width,
            height=height,
            include_assets=include_assets,
        )
