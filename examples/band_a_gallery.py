"""Band A gallery seed snippets.

Run individually, e.g.::

    python examples/band_a_gallery.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import vizly as vz

OUT = Path(__file__).resolve().parent / "_gallery_out"
OUT.mkdir(exist_ok=True)


def main() -> None:
    vz.set_theme("corporate")

    line_df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]),
            "revenue": [12, 18, 15, 22],
            "cost": [5, 7, 6, 9],
        }
    )
    vz.line(line_df, x="date", y="revenue", title="Revenue").render(OUT / "line.html")
    vz.bar(line_df, x="date", y=["revenue", "cost"], stacked=True, title="Stacked").render(
        OUT / "bar_stacked.html"
    )
    vz.area(line_df, x="date", y="revenue", title="Area").render(OUT / "area.html")
    vz.pie(
        {"name": ["East", "West", "Central"], "value": [40, 35, 25]},
        title="Share",
    ).render(OUT / "pie.html")
    vz.mix(
        line_df, x="date", bar="cost", line="revenue", title="Combo"
    ).render(OUT / "mix.html")

    map_df = pd.DataFrame(
        {"name": ["United States", "Canada", "Brazil", "Germany"], "value": [40, 20, 25, 15]}
    )
    vz.map(map_df, title="World sample").render(OUT / "map_world.html")
    vz.map(
        pd.DataFrame({"name": ["California", "Texas", "Florida"], "value": [30, 22, 18]}),
        map="usa",
        title="USA regional sample",
    ).render(OUT / "map_usa.html")

    print(f"Wrote gallery HTML under {OUT}")


if __name__ == "__main__":
    main()
