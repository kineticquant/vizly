# Option goldens

Checked-in `to_option()` snapshots for Level 2 sample charts (`<chart>__<theme>.json`).

These are **JSON**, not browser pages. HTML for visual review is generated under gitignored `artifacts/html/`.

Full validation runbook: [TESTING.md](../TESTING.md).

```bash
python scripts/update_sample_goldens.py
# or
python -m pytest -m samples --update-goldens
```

Do not hand-edit unless you know why the option shape changed.
