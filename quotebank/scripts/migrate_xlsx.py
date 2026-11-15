#!/usr/bin/env python3
"""One-off migration: GAMSAT quote bank workbook -> quotes.csv, themes.txt, tags.txt.

Usage: python scripts/migrate_xlsx.py path/to/workbook.xlsx
Existing IDs are preserved. Outer quotation marks are stripped from quotes
(the CLI adds them back when displaying).
"""
import csv, sys, warnings, pathlib, datetime
from openpyxl import load_workbook

warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
FIELDS = ["id", "date_added", "quote", "author", "source", "primary_theme", "task",
          "secondary_tags", "interpretation", "opposing_perspective", "example", "notes"]
QUOTE_CHARS = "\"'\u201c\u201d\u2018\u2019 \t\n"


def clean_quote(text):
    text = str(text or "").strip()
    return text.strip(QUOTE_CHARS) if text[:1] in QUOTE_CHARS and text[-1:] in QUOTE_CHARS else text


def cell(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.date().isoformat() if isinstance(v, datetime.datetime) else v.isoformat()
    return "" if v is None else str(v).strip()


def column(ws, col):
    out = []
    for row in ws.iter_rows(min_row=2, min_col=col, max_col=col, values_only=True):
        v = row[0]
        if v is None or str(v).strip() == "":
            break
        out.append(str(v).strip())
    return out


def main(path):
    wb = load_workbook(path, data_only=True)
    bank, lists = wb["Quote Bank"], wb["Lists"]
    rows = []
    for r in bank.iter_rows(min_row=2, values_only=True):
        r = list(r) + [None] * (12 - len(r))
        if not str(r[2] or "").strip():
            continue
        rec = dict(zip(FIELDS, (cell(v) for v in r[:12])))
        rec["quote"] = clean_quote(r[2])
        rows.append(rec)
    rows.sort(key=lambda x: x["id"])
    with open(ROOT / "quotes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (ROOT / "themes.txt").write_text("\n".join(column(lists, 1)) + "\n", encoding="utf-8")
    (ROOT / "tags.txt").write_text("\n".join(column(lists, 3)) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} quotes, {len(column(lists, 1))} themes, {len(column(lists, 3))} tags.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
