"""BaseChart lifecycle: build, theme, update, live data, and export."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Union

from vizly.config import resolve_theme
from vizly.render import render_html
from vizly.theme.apply import apply_theme_to_option
from vizly.theme.merge import deep_merge

ThemeLike = Union[str, Mapping[str, Any]]


class BaseChart(ABC):
    """Shared chart lifecycle for all vizly chart types.

    Subclasses implement :meth:`_build` to return a structural ECharts option
    (series, axes, data). Theme chrome and user option merges are applied
    centrally here.
    """

    chart_type: str = "base"
    _needs_gl: bool = False
    _plugins: tuple = ()

    def __init__(
        self,
        data: Any = None,
        *,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Optional[ThemeLike] = None,
        option: Optional[Mapping[str, Any]] = None,
        events: bool = True,
        **kwargs: Any,
    ) -> None:
        self.data = data
        self.title = title
        self.width = width or "100%"
        self.height = height or "420px"
        self._theme_override = theme
        self._user_option: Dict[str, Any] = dict(option or {})
        self._updates: Dict[str, Any] = {}
        if "events" in kwargs:
            events = bool(kwargs.pop("events"))
        self._events = bool(events)
        self.kwargs = kwargs
        self._cached_option: Optional[Dict[str, Any]] = None
        self._cached_theme: Optional[Dict[str, Any]] = None
        self._register_maps: Dict[str, Dict[str, Any]] = {}
        self._option_patches: Dict[str, Any] = {}

    # --- subclass hook -------------------------------------------------

    @abstractmethod
    def _build(self) -> Dict[str, Any]:
        """Return the structural ECharts option (pre-theme)."""

    # --- theme / option assembly ---------------------------------------

    def _invalidate_cache(self) -> None:
        self._cached_option = None
        self._cached_theme = None

    @property
    def theme(self) -> Dict[str, Any]:
        """Resolved theme for this chart (does not mutate global config)."""
        if self._cached_theme is None:
            self._cached_theme = resolve_theme(self._theme_override)
        return self._cached_theme

    def _apply_theme(self, structural: Mapping[str, Any]) -> Dict[str, Any]:
        return apply_theme_to_option(
            structural,
            self.theme,
            user_option=self._user_option or None,
        )

    def _structural_with_title(self, structural: Dict[str, Any]) -> Dict[str, Any]:
        out = deepcopy(structural)
        if self.title is not None:
            title_opt = out.get("title")
            if isinstance(title_opt, Mapping):
                merged_title = dict(title_opt)
                merged_title["text"] = self.title
                out["title"] = merged_title
            else:
                out["title"] = {"text": self.title}
        if self._updates:
            out = deep_merge(out, self._updates)
        if self._option_patches:
            out = deep_merge(out, self._option_patches)
        return out

    def _option_for_html(self) -> Dict[str, Any]:
        """Resolved option including HTML-only keys (polygon overlays, etc.)."""
        structural = self._structural_with_title(self._build())
        return self._apply_theme(structural)

    def to_option(self) -> Dict[str, Any]:
        """Return the fully resolved, JSON-serializable ECharts option dict."""
        if self._cached_option is not None:
            return deepcopy(self._cached_option)
        option = self._option_for_html()
        # Internal HTML-only keys (SPA/JSON callers register maps themselves).
        option.pop("_vizly_layer_maps", None)
        option.pop("_vizly_geo_polygons", None)
        self._cached_option = option
        return deepcopy(option)

    def to_json(self, *, indent: Optional[int] = None) -> str:
        """Serialize :meth:`to_option` as JSON."""
        return json.dumps(
            self.to_option(),
            indent=indent,
            ensure_ascii=False,
            allow_nan=False,
        )

    def to_html(
        self,
        *,
        fragment: bool = False,
        width: Optional[str] = None,
        height: Optional[str] = None,
        include_assets: bool = True,
        message_origin: Optional[str] = None,
        chart_id: Optional[str] = None,
    ) -> str:
        """Return HTML for this chart.

        ``fragment=False``: complete document (Streamlit / standalone).
        ``fragment=True``: div+scripts only (Flask/Django templates, HTMX).
        ``include_assets=False``: omit ECharts library tags (parent page already
        loaded them — preferred for HTMX swaps).
        ``message_origin``: ``postMessage`` target (default same-origin;
        pass ``"*"`` only for cross-origin bridges such as Streamlit).
        """
        # Prefer structural option so HTML can apply polygon fill metadata.
        return render_html(
            self._option_for_html(),
            theme=self.theme,
            width=width or self.width,
            height=height or self.height,
            include_gl=self._needs_gl,
            plugins=list(self._plugins) if self._plugins else None,
            title=self.title,
            register_maps=self._register_maps or None,
            fragment=fragment,
            include_assets=include_assets,
            chart_type=self.chart_type,
            events=self._events,
            message_origin=message_origin,
            chart_id=chart_id,
        )

    def to_fragment(self, *, include_assets: bool = True) -> str:
        """Alias for :meth:`to_html` with ``fragment=True``."""
        return self.to_html(fragment=True, include_assets=include_assets)

    def render(self, path: Optional[Union[str, Path]] = None) -> str:
        """Render HTML; if ``path`` is given, write the file and return the path string."""
        html = self.to_html()
        if path is None:
            return html
        out = Path(path)
        out.write_text(html, encoding="utf-8")
        return str(out)

    def live_update_script(self, chart_id: str, *, not_merge: bool = False) -> str:
        """Return a ``<script>`` that pushes the current option to an existing embed.

        Does not re-load ECharts. The host must already have rendered this chart
        id (see ``window.__vizly``). Typical flow: ``set_data`` / ``set_option_patch``
        then inject this script (HTMX swap target, etc.).
        """
        from vizly.events import live_option_update_js

        return live_option_update_js(
            chart_id, self.to_option(), not_merge=not_merge
        )

    def _repr_html_(self) -> str:
        """Jupyter rich display."""
        return self.to_html()

    # --- mutation helpers ----------------------------------------------

    def set_data(self, data: Any) -> "BaseChart":
        """Replace chart data and invalidate the option cache (live refresh)."""
        self.data = data
        self._invalidate_cache()
        return self

    def set_option_patch(self, patch: Mapping[str, Any]) -> "BaseChart":
        """Deep-merge a partial option for live update without full rebuild."""
        self._option_patches = deep_merge(self._option_patches, dict(patch))
        self._invalidate_cache()
        return self

    def update(self, **kwargs: Any) -> "BaseChart":
        """Apply sparse high-level overrides (merged into structural option).

        Recognized convenience keys: ``title``, ``width``, ``height``, ``theme``.
        Remaining keys are deep-merged into the structural option before theme.
        """
        if "title" in kwargs:
            self.title = kwargs.pop("title")
        if "width" in kwargs:
            self.width = kwargs.pop("width")
        if "height" in kwargs:
            self.height = kwargs.pop("height")
        if "theme" in kwargs:
            self._theme_override = kwargs.pop("theme")
        if "events" in kwargs:
            self._events = bool(kwargs.pop("events"))
        if kwargs:
            self._updates = deep_merge(self._updates, kwargs)
        self._invalidate_cache()
        return self

    def merge_option(self, option: Mapping[str, Any]) -> "BaseChart":
        """Deep-merge a raw ECharts option fragment (wins over theme chrome)."""
        self._user_option = deep_merge(self._user_option, option)
        self._invalidate_cache()
        return self

    @property
    def options(self) -> Dict[str, Any]:
        """Alias for the resolved option dict (mutable copy for power users)."""
        return self.to_option()


class OptionChart(BaseChart):
    """Concrete chart that renders a caller-supplied ECharts option dict.

    Used for Layer 2 smoke tests and as the foundation for ``from_option``.
    """

    chart_type = "option"

    def __init__(
        self,
        option: Mapping[str, Any],
        *,
        title: Optional[str] = None,
        width: Optional[str] = None,
        height: Optional[str] = None,
        theme: Optional[ThemeLike] = None,
        needs_gl: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            data=None,
            title=title,
            width=width,
            height=height,
            theme=theme,
            option=None,
            **kwargs,
        )
        self._structural = deepcopy(dict(option))
        self._needs_gl = needs_gl

    def _build(self) -> Dict[str, Any]:
        return deepcopy(self._structural)

    def set_data(self, data: Any) -> "BaseChart":
        raise TypeError(
            "OptionChart has no tabular data=. Use set_option_patch or "
            "replace the option via merge_option / a new from_option()."
        )
