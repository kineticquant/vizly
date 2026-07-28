"""Partitional / relational Band A charts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from vizly.base import BaseChart
from vizly.charts._helpers import apply_series_defaults, prepare_frame
from vizly.data import DataError, column_values, infer_roles, require_columns


class PieChart(BaseChart):
    chart_type = "pie"
    _donut: bool = False

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        values: Optional[str] = None,
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
        self.names = names
        self.values = values

    def _resolve_roles(self):
        df = prepare_frame(self.data)
        names, values = self.names, self.values
        if names is None or values is None:
            roles = infer_roles(df, prefer="donut" if self._donut else "pie")
            names = names or roles.get("names")
            values = values or roles.get("values")
        if names is None or values is None:
            available = ", ".join(map(str, df.columns)) or "(none)"
            raise DataError(
                "pie/donut requires names= and values= (or columns named "
                f"name/value). Available columns: {available}."
            )
        require_columns(df, names, values)
        return df, names, values

    def _build(self) -> Dict[str, Any]:
        df, names, values = self._resolve_roles()
        data = [
            {"name": n, "value": v}
            for n, v in zip(column_values(df, names), column_values(df, values))
        ]
        series: Dict[str, Any] = {
            "type": "pie",
            "radius": ["45%", "70%"] if self._donut else "65%",
            "data": data,
        }
        series = apply_series_defaults(series, self.theme, "pie")
        return {
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [series],
        }


class DonutChart(PieChart):
    chart_type = "donut"
    _donut = True


class FunnelChart(BaseChart):
    chart_type = "funnel"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        values: Optional[str] = None,
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
        self.names = names or "name"
        self.values = values or "value"

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.names, self.values)
        data = [
            {"name": n, "value": v}
            for n, v in zip(
                column_values(df, self.names), column_values(df, self.values)
            )
        ]
        return {
            "tooltip": {"trigger": "item"},
            "series": [
                {
                    "type": "funnel",
                    "data": data,
                    "label": {"show": True},
                }
            ],
        }


class GaugeChart(BaseChart):
    chart_type = "gauge"

    def __init__(
        self,
        data: Any = None,
        *,
        value: Optional[float] = None,
        values: Optional[str] = None,
        name: str = "value",
        min: float = 0,  # noqa: A002
        max: float = 100,  # noqa: A002
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
        self.value = value
        self.values = values
        self.name = name
        self.min = min
        self.max = max

    def _build(self) -> Dict[str, Any]:
        val = self.value
        if val is None and self.data is not None:
            df = prepare_frame(self.data)
            col = self.values
            if col is None:
                numeric = [
                    c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])
                ]
                if len(numeric) == 1:
                    col = numeric[0]
                elif "value" in df.columns:
                    col = "value"
                else:
                    raise DataError(
                        "gauge needs value= or a single numeric column / values=."
                    )
            require_columns(df, col)
            series_vals = [v for v in column_values(df, col) if v is not None]
            if not series_vals:
                raise DataError("gauge found no numeric values.")
            val = series_vals[-1]
        if val is None:
            raise DataError("gauge requires value= or data with a numeric column.")
        return {
            "series": [
                {
                    "type": "gauge",
                    "min": self.min,
                    "max": self.max,
                    "data": [{"value": val, "name": self.name}],
                }
            ]
        }


class SankeyChart(BaseChart):
    chart_type = "sankey"

    def __init__(
        self,
        data: Any = None,
        *,
        source: Optional[str] = None,
        target: Optional[str] = None,
        values: Optional[str] = None,
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
        self.source = source or "source"
        self.target = target or "target"
        self.values = values or "value"

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.source, self.target, self.values)
        sources = column_values(df, self.source)
        targets = column_values(df, self.target)
        values = column_values(df, self.values)
        node_names = list(dict.fromkeys([*sources, *targets]))
        nodes = [{"name": str(n)} for n in node_names]
        links = [
            {"source": str(s), "target": str(t), "value": v}
            for s, t, v in zip(sources, targets, values)
            if v is not None
        ]
        return {
            "tooltip": {"trigger": "item"},
            "series": [{"type": "sankey", "data": nodes, "links": links}],
        }


class TreemapChart(BaseChart):
    chart_type = "treemap"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        values: Optional[str] = None,
        parent: Optional[str] = None,
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
        self.names = names or "name"
        self.values = values or "value"
        self.parent = parent

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.names, self.values)
        if self.parent and self.parent in df.columns:
            # Build shallow parent→children tree
            children_map: Dict[Any, List[Dict[str, Any]]] = {}
            roots: List[Dict[str, Any]] = []
            names = column_values(df, self.names)
            values = column_values(df, self.values)
            parents = column_values(df, self.parent)
            for n, v, p in zip(names, values, parents):
                node = {"name": str(n), "value": v}
                if p is None or p == "" or p == n:
                    roots.append(node)
                else:
                    children_map.setdefault(p, []).append(node)
            for root in roots:
                kids = children_map.get(root["name"])
                if kids:
                    root["children"] = kids
            data = roots or [
                {"name": str(n), "value": v} for n, v in zip(names, values)
            ]
        else:
            data = [
                {"name": str(n), "value": v}
                for n, v in zip(
                    column_values(df, self.names), column_values(df, self.values)
                )
            ]
        return {
            "tooltip": {"trigger": "item"},
            "series": [{"type": "treemap", "data": data}],
        }


class SunburstChart(BaseChart):
    chart_type = "sunburst"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        values: Optional[str] = None,
        parent: Optional[str] = None,
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
        self.names = names or "name"
        self.values = values or "value"
        self.parent = parent

    def _build(self) -> Dict[str, Any]:
        # Reuse treemap-style hierarchy builder
        tree = TreemapChart(
            self.data,
            names=self.names,
            values=self.values,
            parent=self.parent,
        )._build()
        data = tree["series"][0]["data"]
        return {
            "tooltip": {"trigger": "item"},
            "series": [{"type": "sunburst", "data": data, "radius": [0, "90%"]}],
        }


class TreeChart(BaseChart):
    chart_type = "tree"

    def __init__(
        self,
        data: Any = None,
        *,
        names: Optional[str] = None,
        parent: Optional[str] = None,
        values: Optional[str] = None,
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
        self.names = names or "name"
        self.parent = parent or "parent"
        self.values = values

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.names, self.parent)
        names = column_values(df, self.names)
        parents = column_values(df, self.parent)
        values = (
            column_values(df, self.values)
            if self.values and self.values in df.columns
            else [None] * len(names)
        )
        nodes = {
            str(n): {"name": str(n), "children": []}
            for n in names
        }
        roots = []
        for n, p, v in zip(names, parents, values):
            node = nodes[str(n)]
            if v is not None:
                node["value"] = v
            if p is None or p == "" or str(p) not in nodes or str(p) == str(n):
                roots.append(node)
            else:
                nodes[str(p)]["children"].append(node)
        if not roots:
            roots = list(nodes.values())[:1]
        return {
            "tooltip": {"trigger": "item"},
            "series": [
                {
                    "type": "tree",
                    "data": roots,
                    "orient": "LR",
                    "label": {"position": "left", "verticalAlign": "middle"},
                }
            ],
        }


class GraphChart(BaseChart):
    chart_type = "graph"

    def __init__(
        self,
        data: Any = None,
        *,
        source: Optional[str] = None,
        target: Optional[str] = None,
        values: Optional[str] = None,
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
        self.source = source or "source"
        self.target = target or "target"
        self.values = values

    def _build(self) -> Dict[str, Any]:
        df = prepare_frame(self.data)
        require_columns(df, self.source, self.target)
        sources = column_values(df, self.source)
        targets = column_values(df, self.target)
        vals = (
            column_values(df, self.values)
            if self.values and self.values in df.columns
            else [1] * len(sources)
        )
        node_names = list(dict.fromkeys([*sources, *targets]))
        nodes = [{"name": str(n), "symbolSize": 20} for n in node_names]
        links = [
            {"source": str(s), "target": str(t), "value": v}
            for s, t, v in zip(sources, targets, vals)
        ]
        return {
            "tooltip": {},
            "series": [
                {
                    "type": "graph",
                    "layout": "force",
                    "roam": True,
                    "data": nodes,
                    "links": links,
                    "label": {"show": True},
                    "force": {"repulsion": 120},
                }
            ],
        }
