"""Click / drill / live-update event contract for vizly embeds.

HTML embeds emit a structured ``vizly:event`` CustomEvent and optionally a
``postMessage`` payload. SPA/JSON callers attach ``chart.on('click', …)``
themselves — ``to_option()`` / ``to_json()`` do not auto-wire drilldowns.

Image export is client-side via ``window.__vizly[id].toDataURL()`` /
``downloadImage()`` (ECharts ``getDataURL``).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional, Sequence

from vizly.data import DataLike, TabularView, as_tabular, filter_tabular

MessageOrigin = Optional[str]  # None → window.location.origin; "*" opt-in


def build_click_payload(
    *,
    chart_id: str,
    chart_type: str,
    params: Mapping[str, Any],
) -> Dict[str, Any]:
    """Normalize an ECharts click ``params`` object into a vizly event dict."""
    name = params.get("name")
    value = params.get("value")
    data_index = params.get("dataIndex")
    series_name = params.get("seriesName")
    series_type = params.get("seriesType") or chart_type
    data = params.get("data")
    breadcrumb: List[Any] = []
    tree_path = params.get("treePathInfo") or params.get("treeAncestors")
    if isinstance(tree_path, Sequence):
        for node in tree_path:
            if isinstance(node, Mapping):
                breadcrumb.append(node.get("name") or node.get("title"))
            else:
                breadcrumb.append(node)
    region = None
    if series_type == "map" or chart_type == "map":
        region = name
    return {
        "source": "vizly",
        "event": "click",
        "chart_id": chart_id,
        "chart_type": chart_type,
        "name": name,
        "value": value,
        "dataIndex": data_index,
        "seriesName": series_name,
        "seriesType": series_type,
        "region": region,
        "breadcrumb": [b for b in breadcrumb if b is not None],
        "data": data,
    }


def filter_by_click(
    data: DataLike,
    payload: Mapping[str, Any],
    *,
    column: Optional[str] = None,
) -> TabularView:
    """Filter tabular data using a click payload (categorical / map drill).

    Uses ``column`` if given; otherwise prefers ``region`` then ``name``.
    """
    table = as_tabular(data)
    key = column
    value = payload.get("region") if payload.get("region") is not None else payload.get("name")
    if key is None:
        cols = list(table.columns)
        for cand in ("region", "name", "category", "x", "label"):
            if cand in cols:
                key = cand
                break
        if key is None and cols:
            key = cols[0]
    if key is None or value is None:
        return table
    return filter_tabular(table, key, value)


def _message_origin_js(message_origin: MessageOrigin) -> str:
    """JS expression for ``postMessage`` targetOrigin."""
    if message_origin is None:
        return "window.location.origin"
    return json.dumps(message_origin)


def embed_event_js(
    chart_id: str,
    chart_type: str,
    *,
    enabled: bool = True,
    message_origin: MessageOrigin = None,
) -> str:
    """Return JS that wires click → CustomEvent + postMessage for one chart.

    ``message_origin``:
    - ``None`` (default): ``window.location.origin`` (same-origin parents)
    - ``"*"``: explicit cross-origin opt-in (e.g. Streamlit component bridge)
    - other str: exact target origin
    """
    if not enabled:
        return ""
    cid = json.dumps(chart_id)
    ctype = json.dumps(chart_type)
    origin_expr = _message_origin_js(message_origin)
    return f"""
      chart.on('click', function(params) {{
        var payload = {{
          source: 'vizly',
          event: 'click',
          chart_id: {cid},
          chart_type: {ctype},
          name: params.name,
          value: params.value,
          dataIndex: params.dataIndex,
          seriesName: params.seriesName,
          seriesType: params.seriesType || {ctype},
          region: (params.seriesType === 'map' || {ctype} === 'map') ? params.name : null,
          breadcrumb: (params.treePathInfo || params.treeAncestors || []).map(function(n) {{
            return (n && (n.name || n.title)) || n;
          }}).filter(function(x) {{ return x != null; }}),
          data: params.data
        }};
        try {{
          var el = document.getElementById({cid});
          if (el) {{
            el.dispatchEvent(new CustomEvent('vizly:event', {{detail: payload, bubbles: true}}));
          }}
          window.dispatchEvent(new CustomEvent('vizly:event', {{detail: payload}}));
          if (window.parent && window.parent !== window) {{
            window.parent.postMessage(payload, {origin_expr});
          }}
        }} catch (err) {{
          console.warn('vizly event bridge failed', err);
        }}
      }});
"""


def live_update_js(chart_id: str) -> str:
    """Expose ``window.__vizly[id]`` for setOption + client image export."""
    cid = json.dumps(chart_id)
    return f"""
      window.__vizly = window.__vizly || {{}};
      window.__vizly[{cid}] = {{
        chart: chart,
        setOption: function(opt, notMerge) {{
          chart.setOption(opt, notMerge === true);
        }},
        resize: function() {{ chart.resize(); }},
        toDataURL: function(opts) {{
          return chart.getDataURL(opts || {{ type: 'png', pixelRatio: 2 }});
        }},
        downloadImage: function(filename, opts) {{
          var url = this.toDataURL(opts);
          var a = document.createElement('a');
          a.href = url;
          a.download = filename || 'vizly-chart.png';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return url;
        }}
      }};
"""


def live_option_update_js(
    chart_id: str,
    option: Mapping[str, Any],
    *,
    not_merge: bool = False,
) -> str:
    """Return a ``<script>`` that patches an existing embed without re-loading ECharts."""
    cid = json.dumps(chart_id)
    opt = json.dumps(dict(option), ensure_ascii=False, allow_nan=False).replace(
        "</", "<\\/"
    )
    merge_js = "true" if not_merge else "false"
    return f"""<script>
(function() {{
  var entry = (window.__vizly || {{}})[{cid}];
  if (!entry || !entry.setOption) {{
    console.warn('vizly live update: chart not found', {cid});
    return;
  }}
  entry.setOption({opt}, {merge_js});
}})();
</script>"""


def connect_charts_js(chart_ids: Sequence[str], group: str = "vizly") -> str:
    """Return JS that connects multiple ECharts instances for linked brush/tooltip."""
    if len(chart_ids) < 2:
        return ""
    ids_json = json.dumps(list(chart_ids))
    group_json = json.dumps(group)
    return f"""
      (function() {{
        var ids = {ids_json};
        var charts = [];
        for (var i = 0; i < ids.length; i++) {{
          var entry = (window.__vizly || {{}})[ids[i]];
          if (entry && entry.chart) {{ charts.push(entry.chart); }}
        }}
        if (charts.length >= 2 && echarts.connect) {{
          echarts.connect(charts);
          for (var j = 0; j < charts.length; j++) {{
            charts[j].group = {group_json};
          }}
        }}
      }})();
"""


def apply_geo_polygons_js() -> str:
    """JS snippet: turn ``option._vizly_geo_polygons`` into filled custom series."""
    return """
      (function() {
        var polys = option._vizly_geo_polygons;
        if (option._vizly_geo_polygons) { delete option._vizly_geo_polygons; }
        if (option._vizly_layer_maps) { delete option._vizly_layer_maps; }
        if (!polys || !polys.length) { return; }
        var series = (option.series || []).slice();
        for (var i = 0; i < polys.length; i++) {
          (function(poly) {
            series.push({
              type: 'custom',
              name: poly.name || 'overlay',
              coordinateSystem: 'geo',
              zlevel: poly.zlevel != null ? poly.zlevel : 2,
              data: [{ name: poly.name || 'overlay', value: 0 }],
              renderItem: function(params, api) {
                var rings = poly.rings || [];
                if (!rings.length || !rings[0] || !rings[0].length) {
                  return null;
                }
                var children = [];
                for (var r = 0; r < rings.length; r++) {
                  var pts = [];
                  var ring = rings[r];
                  for (var p = 0; p < ring.length; p++) {
                    pts.push(api.coord(ring[p]));
                  }
                  children.push({
                    type: 'polygon',
                    shape: { points: pts },
                    style: {
                      fill: poly.fill || 'rgba(47, 111, 237, 0.28)',
                      stroke: poly.stroke || '#2F6FED',
                      lineWidth: poly.lineWidth != null ? poly.lineWidth : 1.5
                    }
                  });
                }
                return { type: 'group', children: children };
              }
            });
          })(polys[i]);
        }
        option.series = series;
      })();
"""


def chart_bootstrap_js(
    chart_id: str,
    option_json: str,
    locale_json: str,
    chart_type: str,
    *,
    events: bool = True,
    message_origin: MessageOrigin = None,
    map_js: str = "",
    bind_resize: bool = True,
    after_init: str = "",
) -> str:
    """Shared ECharts init body used by single-chart, page, and tab embeds.

    ``option_json`` / ``locale_json`` must already be JSON text safe for
    embedding in a ``<script>`` (callers escape ``</``). Sets locals ``chart``
    and ``option``. Does not wrap in ``<script>`` or an IIFE.
    """
    poly_js = apply_geo_polygons_js()
    live_js = live_update_js(chart_id)
    event_js = embed_event_js(
        chart_id,
        chart_type,
        enabled=events,
        message_origin=message_origin,
    )
    resize_js = (
        'window.addEventListener("resize", function() { chart.resize(); });'
        if bind_resize
        else ""
    )
    # chart_id is generated by vizly (uuid prefix); keep getElementById quoted.
    return f"""
      var el = document.getElementById({json.dumps(chart_id)});
      var chart = echarts.init(el, null, {{locale: {locale_json}}});
      {map_js}
      var option = {option_json};
      {poly_js}
      chart.setOption(option);
      {live_js}
      {event_js}
      {after_init}
      {resize_js}
"""


def chart_bootstrap_script(
    chart_id: str,
    option_json: str,
    locale_json: str,
    chart_type: str,
    *,
    events: bool = True,
    message_origin: MessageOrigin = None,
    map_js: str = "",
) -> str:
    """IIFE ``<script>`` wrapper around :func:`chart_bootstrap_js`."""
    body = chart_bootstrap_js(
        chart_id,
        option_json,
        locale_json,
        chart_type,
        events=events,
        message_origin=message_origin,
        map_js=map_js,
        bind_resize=True,
    )
    return f"<script>\n    (function() {{{body}\n    }})();\n  </script>"
