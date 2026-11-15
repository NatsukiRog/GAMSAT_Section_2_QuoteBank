#!/usr/bin/env python3
"""Turn a GitHub issue-form submission into a quotes.csv row.

  python scripts/import_issue.py check   validate only, change nothing
  python scripts/import_issue.py add     validate, then append the row to quotes.csv

Reads ISSUE_BODY (and optionally ISSUE_AUTHOR) from the environment, writes
status=... to $GITHUB_OUTPUT, and writes a message for the submitter to comment.md.
The issue body is untrusted input: it is only parsed here, never executed.
"""
import csv
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import quotebank as qb  # noqa: E402

TIMEZONE = "Australia/Melbourne"      # date_added uses this zone
COMMENT_FILE = Path(os.environ.get("COMMENT_FILE", "comment.md"))
MAX_QUOTE_LENGTH = 1500

# issue-form field label -> column / temporary key
LABELS = {
    "Quote": "quote", "Author": "author", "Source / URL": "source",
    "Primary theme": "primary_theme", "Section suitability": "task",
    "Secondary tag 1": "tag_1", "Secondary tag 2": "tag_2", "Secondary tag 3": "tag_3",
    "Interpretation": "interpretation", "Opposing perspective": "opposing_perspective",
    "Example / evidence": "example", "Notes": "notes",
}
EMPTY = {"", "_no response_", "none"}     # what GitHub writes for blank fields
QUOTE_CHARS = "\"'\u201c\u201d\u2018\u2019"


def today():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(TIMEZONE)).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()


def parse(body):
    """Split an issue-form body on its '### Label' headings."""
    parts = re.split(r"(?m)^###[ \t]+(.+?)[ \t]*$", body.replace("\r\n", "\n"))
    fields = {}
    for label, text in zip(parts[1::2], parts[2::2]):
        key = LABELS.get(label.strip())
        if key:
            value = " ".join(text.split())
            fields[key] = "" if value.lower() in EMPTY else value
    return fields


def strip_outer_quotes(text):
    if text and text[0] in QUOTE_CHARS and text[-1] in QUOTE_CHARS:
        return text.strip(QUOTE_CHARS + " ")
    return text


def build(fields, rows, themes, tags):
    """Return (row, friendly_errors). id and date_added are filled in later."""
    g = lambda k: fields.get(k, "")
    errors = []
    quote = strip_outer_quotes(g("quote"))
    for key, label in (("author", "Author"), ("source", "Source / URL")):
        if not g(key):
            errors.append(f"**{label}** is required (a real source helps us rule out misattributed quotes).")
    if not quote:
        errors.append("**Quote** is required.")
    elif len(quote) > MAX_QUOTE_LENGTH:
        errors.append(f"**Quote** is too long ({len(quote)} characters; the limit is {MAX_QUOTE_LENGTH}).")
    if g("primary_theme") not in themes:
        errors.append("**Primary theme** must be chosen from the dropdown list.")
    if g("task") not in qb.TASKS:
        errors.append("**Section suitability** must be Task A, Task B or Both.")
    chosen = []
    for k in ("tag_1", "tag_2", "tag_3"):
        t = g(k)
        if t and t not in chosen:
            chosen.append(t)
    unknown = [t for t in chosen if t not in tags]
    if unknown:
        errors.append("Unknown secondary tag(s): " + ", ".join(unknown))
    if quote:
        key = qb.norm_quote(quote)
        for r in rows:
            if qb.norm_quote(r["quote"]) == key:
                errors.append(f"This quote is already in the bank ({r['id']}, {r['author']}).")
                break
    row = {"id": "", "date_added": "", "quote": quote, "author": g("author"),
           "source": g("source"), "primary_theme": g("primary_theme"), "task": g("task"),
           "secondary_tags": ", ".join(chosen), "interpretation": g("interpretation"),
           "opposing_perspective": g("opposing_perspective"), "example": g("example"),
           "notes": g("notes")}
    for k, v in row.items():
        if v[:1] in ("=", "+", "@"):
            errors.append(f"**{k}** must not start with =, + or @ (it can be read as a spreadsheet formula).")
    return row, errors


def output(**kv):
    text = "".join(f"{k}={v}\n" for k, v in kv.items())
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(text)
    print(text, end="")


def fail(errors):
    COMMENT_FILE.write_text(
        "Thanks for the submission! A few things need fixing before it can be added:\n\n"
        + "\n".join(f"- {e}" for e in errors)
        + "\n\nEdit the issue to fix them and the check will run again.\n", encoding="utf-8")
    output(status="invalid")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in ("check", "add"):
        sys.exit(__doc__)
    author = os.environ.get("ISSUE_AUTHOR", "").strip()
    thanks = f" @{author}" if re.fullmatch(r"[A-Za-z0-9-]+", author) else ""
    rows, themes, tags = qb.load(ROOT)
    rows = [{k: r.get(k, "") for k in qb.FIELDS} for r in rows]
    row, errors = build(parse(os.environ.get("ISSUE_BODY", "")), rows, themes, tags)
    if errors:
        return fail(errors)
    if mode == "check":
        COMMENT_FILE.write_text(f"Thanks{thanks}! This submission looks valid and is waiting "
                                f"for a maintainer to review it.\n", encoding="utf-8")
        return output(status="valid")

    ids = {r["id"] for r in rows}
    n = int(time.time() * 1000)
    while f"Q{n}" in ids:
        n += 1
    row["id"], row["date_added"] = f"Q{n}", today()
    path = ROOT / "quotes.csv"
    original = path.read_text(encoding="utf-8")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=qb.FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows + [row], key=lambda r: r["id"]))
    problems, _ = qb.validate(ROOT)
    if problems:                      # safety net: never leave a bad file behind
        path.write_text(original, encoding="utf-8")
        return fail(problems)
    COMMENT_FILE.write_text(f"Thanks{thanks}! Your quote has been added to the bank as `{row['id']}`. "
                            f"It will appear for everyone after their next `quotebank update`.\n",
                            encoding="utf-8")
    output(status="added", quote_id=row["id"])


if __name__ == "__main__":
    main()
