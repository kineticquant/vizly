# vizly vendored frontend assets

| File | Version | Source |
|------|---------|--------|
| `echarts.min.js` | 5.5.1 | https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js |
| `echarts-gl.min.js` | 2.0.9 | https://cdn.jsdelivr.net/npm/echarts-gl@2.0.9/dist/echarts-gl.min.js |
| `echarts-wordcloud.min.js` | 2.1.0 | https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js |
| `echarts-liquidfill.min.js` | 3.1.0 | https://cdn.jsdelivr.net/npm/echarts-liquidfill@3.1.0/dist/echarts-liquidfill.min.js |
| `maps/world.json` | echarts 4.9.0 map pack | https://cdn.jsdelivr.net/npm/echarts@4.9.0/map/json/world.json |
| `maps/usa.json` | apache/echarts-examples | https://cdn.jsdelivr.net/gh/apache/echarts-examples@gh-pages/public/data/asset/geo/USA.json |

Default render mode embeds local JS (no remote script). Optional CDN mode is
restricted to allowlisted hosts: `cdn.jsdelivr.net`, `unpkg.com`.

GL / wordcloud / liquidfill scripts load only when the chart type needs them.
China map packs are not bundled — register via `vizly.register_map_pack`.
Default `map=` / `geo` atlas is **world**; `usa` is an optional bundled regional pack.
