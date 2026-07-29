"""Data ingest demo — CSV / JSON / SQL → charts without building a DataFrame."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text

import vizly as vz

ROOT = Path(__file__).resolve().parents[1] / "artifacts" / "html"
ROOT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    csv_path = ROOT / "_demo.csv"
    csv_path.write_text("region,sales\nEast,40\nWest,55\nNorth,33\n", encoding="utf-8")
    table = vz.from_csv(csv_path)
    bar = vz.bar(table, x="region", y="sales", title="From CSV", theme="editor_nord")

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE metrics (day TEXT, value INTEGER)"))
        conn.execute(
            text(
                "INSERT INTO metrics VALUES "
                "('2026-01-01', 10), ('2026-01-02', 14), ('2026-01-03', 12)"
            )
        )
    sql_table = vz.from_sql("SELECT day, value FROM metrics ORDER BY day", bind=engine)
    line = vz.line(sql_table, x="day", y="value", title="From SQL", theme="editor_nord")

    edges = [
        {"source": "CSV", "target": "TabularView"},
        {"source": "SQL", "target": "TabularView"},
        {"source": "TabularView", "target": "Chart"},
    ]
    flow = vz.flowchart(edges, title="Ingest path", theme="editor_nord")
    page = vz.page(charts=[bar, line, flow], title="Data in")
    out = ROOT / "ingest_demo.html"
    page.render(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
