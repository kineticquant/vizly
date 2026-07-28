"""Band B/C gallery seed snippets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import vizly as vz

OUT = Path(__file__).resolve().parent / "_gallery_out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    vz.set_theme("dark")
    scatter_df = pd.DataFrame({"x": [1, 2, 3, 4], "y": [3, 1, 4, 2]})
    vz.effect_scatter(scatter_df, x="x", y="y", title="Effect").render(
        OUT / "effect_scatter.html"
    )
    vz.waterfall(
        {"step": ["Open", "In", "Out", "Close"], "delta": [100, 30, -20, 0]},
        x="step",
        y="delta",
        title="Waterfall",
    ).render(OUT / "waterfall.html")
    vz.wordcloud(
        {"name": ["vizly", "echarts", "theme", "trust"], "value": [40, 30, 20, 15]},
        title="Words",
    ).render(OUT / "wordcloud.html")
    vz.liquid(value=0.62, title="Fill").render(OUT / "liquid.html")
    xyz = pd.DataFrame({"x": [0, 1, 2], "y": [0, 1, 0], "z": [1, 3, 2]})
    vz.bar3d(xyz, x="x", y="y", z="z", title="Bar3D").render(OUT / "bar3d.html")
    print(f"Wrote B/C gallery HTML under {OUT}")


if __name__ == "__main__":
    main()
