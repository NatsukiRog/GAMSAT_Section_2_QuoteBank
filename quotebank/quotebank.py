#!/usr/bin/env python3
"""GAMSAT Section 2 quote bank.

Commands:
  update     download the latest quotes from GitHub
  practice   random set of four quotes sharing one theme
  search     keyword / task / theme search
  stats      quote counts per theme and task
  submit     open a pre-filled GitHub issue to suggest a new quote
  validate   check quotes.csv for problems (used by maintainers and CI)

Standard library only (Python 3.8+).
"""
import argparse
import csv
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import date
from pathlib import Path

# ---- Set this to your repository -------------------------------------------
REPO = "NatsukiRog/GAMSAT_Section_2_QuoteBank"
BRANCH = "main"
# -----------------------------------------------------------------------------

RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
ISSUE_URL = f"https://github.com/{REPO}/issues/new"
DATA_FILES = ["quotes.csv", "themes.txt", "tags.txt"]
CACHE_DIR = Path.home() / ".quotebank"
SCRIPT_DIR = Path(__file__).resolve().parent
STALE_SECONDS = 24 * 60 * 60
MAX_URL_LENGTH = 7500
MAX_TAGS = 3

FIELDS = ["id", "date_added", "quote", "author", "source", "primary_theme", "task",
          "secondary_tags", "interpretation", "opposing_perspective", "example", "notes"]
TASKS = ["Task A", "Task B", "Both"]


# ---------------------------------------------------------------- data access

def data_dir(override=None):
    """--data-dir wins; then a repo checkout next to this script; then the cache."""
    if override:
        return Path(override)
    if (SCRIPT_DIR / "quotes.csv").exists():
        return SCRIPT_DIR
    return CACHE_DIR


def update(quiet=False):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for name in DATA_FILES:
        tmp = CACHE_DIR / (name + ".tmp")
        urllib.request.urlretrieve(RAW_BASE + name, tmp)
        tmp.replace(CACHE_DIR / name)
    if not quiet:
        print(f"Updated quote bank from github.com/{REPO}")


def ensure_data(directory):
    """Download on first run; refresh the cache quietly when it is over a day old."""
    if directory != CACHE_DIR:
        return
    quotes = CACHE_DIR / "quotes.csv"
    try:
        if not quotes.exists():
            print("Downloading the quote bank...")
            update()
        elif time.time() - quotes.stat().st_mtime > STALE_SECONDS:
            update(quiet=True)
    except Exception as exc:  # offline is fine if we already have a copy
        if not quotes.exists():
            sys.exit(f"Could not download the quote bank ({exc}). "
                     f"Check your connection and the REPO setting in quotebank.py.")


def read_list(path):
    if not path.exists():
        return []
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def load(directory):
    with open(directory / "quotes.csv", newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("quote") or "").strip()]
    return rows, read_list(directory / "themes.txt"), read_list(directory / "tags.txt")


# ------------------------------------------------------------------- helpers

def norm_task(value):
    """'a', 'Task A', 'TASK B', 'both' -> canonical task name, else None."""
    v = (value or "").strip().lower().replace("task", "").strip()
    return {"a": "Task A", "b": "Task B", "both": "Both"}.get(v)


def fits_task(row_task, task):
    """Quotes marked Both (or blank) can be used in either task."""
    t = (row_task or "").strip()
    return t in ("", "Both") or t == task


def resolve_theme(text, themes):
    """Exact match first, then a unique case-insensitive substring ('justice')."""
    if not text or text.lower() in ("all", "random"):
        return None
    for t in themes:
        if t.lower() == text.lower():
            return t
    hits = [t for t in themes if text.lower() in t.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f'No theme matches "{text}". Run "quotebank stats" to see the theme list.')
    sys.exit(f'"{text}" matches several themes: ' + "; ".join(hits))


def show(text):
    return "\u201c" + text.strip() + "\u201d"


def norm_quote(text):
    return re.sub(r"[\W_]+", "", text.lower())


def tag_list(value):
    return [t.strip() for t in (value or "").split(",") if t.strip()]


# ------------------------------------------------------------------ practice

def build_set(rows, task, theme):
    """Port of GenerateRandomQuote: pick a (task, theme) group with 4+ quotes, then 4 distinct quotes."""
    tasks = [task] if task else ["Task A", "Task B"]
    themes = sorted({r["primary_theme"] for r in rows if r["primary_theme"]})
    if theme:
        themes = [t for t in themes if t == theme]
    if not themes:
        sys.exit(f'No saved quotes found for "{theme}".')
    groups = []
    for tk in tasks:
        for th in themes:
            pool = [r for r in rows if r["primary_theme"] == th and fits_task(r["task"], tk)]
            if len(pool) >= 4:
                groups.append((tk, th, pool))
    if not groups:
        t_txt = task or "Task A or Task B"
        th_txt = f'"{theme}"' if theme else "any one theme"
        sys.exit(f"No four-quote set is available yet. Need at least four quotes from {th_txt} "
                 f"suitable for {t_txt}. Quotes marked Both count for either task.")
    tk, th, pool = random.choice(groups)
    return tk, th, pool, random.sample(pool, 4)


def cmd_practice(args):
    d = data_dir(args.data_dir)
    ensure_data(d)
    rows, themes, _ = load(d)
    task = norm_task(args.task) if args.task else None
    if args.task and task in (None, "Both"):
        sys.exit("--task must be A or B.")
    theme = resolve_theme(args.theme, themes)
    interactive = sys.stdin.isatty() and not args.once
    while True:
        tk, th, pool, picks = build_set(rows, task, theme)
        print(f"\n{tk} practice set | Theme: {th} | 4 of {len(pool)} matching quotes\n")
        for i, r in enumerate(picks, 1):
            print(f"{i}. {show(r['quote'])}")
            print(f"   \u2014 {r['author'] or 'Unknown'}  [{r['task'] or 'Both'}]")
            if r["source"]:
                print(f"   {r['source']}")
            print()
        print("Use the shared theme as your starting point. You can respond to one or more quotes; "
              "you do not need to address all four.")
        if not interactive:
            return
        if input("\nEnter for a new set, q to quit: ").strip().lower().startswith("q"):
            return


# -------------------------------------------------------------------- search

def cmd_search(args):
    d = data_dir(args.data_dir)
    ensure_data(d)
    rows, themes, _ = load(d)
    keyword = " ".join(args.keyword).lower()
    task = norm_task(args.task) if args.task else None
    if args.task and not task:
        sys.exit("--task must be A, B or Both.")
    theme = resolve_theme(args.theme, themes)
    matches = []
    for r in rows:
        # like the Excel search: every column from the quote onward, minus id and date
        blob = " ".join(str(r.get(k, "")) for k in FIELDS[2:]).lower()
        if keyword and keyword not in blob:
            continue
        if task == "Both" and r["task"] != "Both":
            continue
        if task in ("Task A", "Task B") and not fits_task(r["task"], task):
            continue
        if theme and r["primary_theme"] != theme:
            continue
        matches.append(r)
    print(f"{len(matches)} matching quote(s).\n")
    for r in matches:
        print(f"{show(r['quote'])}\n   \u2014 {r['author']}  [{r['task']}]  {r['primary_theme']}")
        if r["secondary_tags"]:
            print(f"   Tags: {r['secondary_tags']}")
        if r["source"]:
            print(f"   {r['source']}")
        for label, key in (("Interpretation", "interpretation"),
                           ("Opposing perspective", "opposing_perspective"),
                           ("Example", "example"), ("Notes", "notes")):
            if r[key]:
                print(f"   {label}: {r[key]}")
        print()


# --------------------------------------------------------------------- stats

def cmd_stats(args):
    d = data_dir(args.data_dir)
    ensure_data(d)
    rows, themes, _ = load(d)
    a = sum(fits_task(r["task"], "Task A") for r in rows)
    b = sum(fits_task(r["task"], "Task B") for r in rows)
    both = sum(r["task"] == "Both" for r in rows)
    print(f"Total quotes: {len(rows)}   Task A (incl. Both): {a}   "
          f"Task B (incl. Both): {b}   Both: {both}\n")
    width = max([len(t) for t in themes] + [12])
    print(f"{'Theme'.ljust(width)}  Total  Task A  Task B  Both")
    for t in themes:
        sub = [r for r in rows if r["primary_theme"] == t]
        print(f"{t.ljust(width)}  {len(sub):>5}  "
              f"{sum(r['task'] == 'Task A' for r in sub):>6}  "
              f"{sum(r['task'] == 'Task B' for r in sub):>6}  "
              f"{sum(r['task'] == 'Both' for r in sub):>4}")


# ------------------------------------------------------------------- submit

def choose(prompt, options, optional=False):
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        raw = input(f"{prompt}{' (Enter to skip)' if optional else ''}: ").strip()
        if not raw and optional:
            return ""
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("  Enter one of the numbers above.")


def cmd_submit(args):
    d = data_dir(args.data_dir)
    ensure_data(d)
    _, themes, tags = load(d)
    print("Suggest a quote. You will review it on GitHub before anything is sent.\n")
    quote = input("Quote: ").strip().strip("\"\u201c\u201d")
    author = input("Author: ").strip()
    source = input("Source / URL (book, speech, page; helps verify the quote): ").strip()
    print("\nPrimary theme:")
    theme = choose("Number", themes)
    print("\nSuitable for:")
    task = choose("Number", TASKS)
    chosen = []
    for n in range(1, MAX_TAGS + 1):
        print(f"\nSecondary tag {n}:")
        t = choose("Number", [x for x in tags if x not in chosen], optional=True)
        if not t:
            break
        chosen.append(t)
    interpretation = input("\nInterpretation (optional): ").strip()
    opposing = input("Opposing perspective (optional): ").strip()
    example = input("Example / evidence (optional): ").strip()
    notes = input("Notes (optional): ").strip()
    if not quote or not author or not source:
        sys.exit("Quote, author and source are required.")

    params = {"template": "submit-quote.yml", "title": f"Quote: {author}", "quote": quote,
              "author": author, "source": source, "theme": theme, "task": task,
              "interpretation": interpretation, "opposing": opposing,
              "example": example, "notes": notes}
    for i in range(MAX_TAGS):
        params[f"tag_{i + 1}"] = chosen[i] if i < len(chosen) else ""
    params = {k: v for k, v in params.items() if v}

    def url_for(p):
        return ISSUE_URL + "?" + urllib.parse.urlencode(p)

    url = url_for(params)
    if len(url) > MAX_URL_LENGTH:
        dropped = {k: params.pop(k) for k in ("interpretation", "opposing", "example", "notes")
                   if k in params}
        url = url_for(params)
        if dropped:
            print("\nThose extra fields were too long to pre-fill. Paste them into the form yourself:")
            for k, v in dropped.items():
                print(f"  [{k}] {v}")
    if args.print_url:
        print(url)
        return
    webbrowser.open(url)
    print("\nOpened GitHub. Review the form and click 'Submit new issue'. (A free GitHub account is needed.)")
    print("If your browser did not open, copy this link:\n" + url)


# ----------------------------------------------------------------- validate

def validate(directory):
    """Return (errors, warnings) as lists of strings."""
    errors, warnings = [], []
    path = directory / "quotes.csv"
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            return [f"Header must be exactly: {','.join(FIELDS)}"], []
        rows = list(reader)
    themes = set(read_list(directory / "themes.txt"))
    tags = set(read_list(directory / "tags.txt"))
    seen_ids, seen_quotes = {}, {}
    for n, r in enumerate(rows, start=2):
        where = f"line {n} ({r['id'] or 'no id'})"
        if not r["id"]:
            errors.append(f"{where}: missing id")
        elif r["id"] in seen_ids:
            errors.append(f"{where}: duplicate id (also line {seen_ids[r['id']]})")
        seen_ids[r["id"]] = n
        if not r["quote"].strip():
            errors.append(f"{where}: empty quote")
        else:
            key = norm_quote(r["quote"])
            if key in seen_quotes:
                errors.append(f"{where}: duplicate quote (also line {seen_quotes[key]})")
            seen_quotes[key] = n
        for k in FIELDS[2:]:
            if r[k].lstrip()[:1] in ("=", "+", "@"):
                errors.append(f"{where}: {k} must not start with =, + or @ (spreadsheet formula risk)")
        if not r["author"].strip():
            errors.append(f"{where}: author is required")
        if not r["source"].strip():
            errors.append(f"{where}: source is required")
        if r["primary_theme"] not in themes:
            errors.append(f"{where}: theme \"{r['primary_theme']}\" is not in themes.txt")
        if r["task"] not in TASKS:
            errors.append(f"{where}: task must be one of {', '.join(TASKS)}")
        tl = tag_list(r["secondary_tags"])
        bad = [t for t in tl if t not in tags]
        if bad:
            errors.append(f"{where}: unknown tag(s): {', '.join(bad)}")
        if len(tl) > MAX_TAGS:
            errors.append(f"{where}: at most {MAX_TAGS} secondary tags")
        if len(set(tl)) != len(tl):
            errors.append(f"{where}: repeated tag")
        try:
            date.fromisoformat(r["date_added"])
        except ValueError:
            errors.append(f"{where}: date_added must be YYYY-MM-DD")
        if r["quote"].strip()[:1] in "\"\u201c" and r["quote"].strip()[-1:] in "\"\u201d":
            warnings.append(f"{where}: quote has surrounding quotation marks (they are added on display)")
    return errors, warnings


def cmd_validate(args):
    d = data_dir(args.data_dir)
    errors, warnings = validate(d)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:  ", e)
    if errors:
        sys.exit(f"\n{len(errors)} error(s).")
    print(f"quotes.csv OK ({len(warnings)} warning(s)).")


# --------------------------------------------------------------------- main

def main(argv=None):
    p = argparse.ArgumentParser(prog="quotebank", description="GAMSAT Section 2 quote bank")
    p.add_argument("--data-dir", help="use quotes.csv/themes.txt/tags.txt from this folder")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("update", help="download the latest quotes")

    pr = sub.add_parser("practice", help="random set of 4 quotes sharing one theme")
    pr.add_argument("--task", help="A or B (default: random)")
    pr.add_argument("--theme", help='theme name or unique part of it, e.g. "justice" (default: random)')
    pr.add_argument("--once", action="store_true", help="print one set and exit")

    se = sub.add_parser("search", help="search the bank")
    se.add_argument("keyword", nargs="*", help="optional keyword")
    se.add_argument("--task", help="A, B or Both")
    se.add_argument("--theme", help="theme name or unique part of it")

    sub.add_parser("stats", help="counts per theme and task")

    su = sub.add_parser("submit", help="suggest a new quote via GitHub")
    su.add_argument("--print-url", action="store_true", help="print the link instead of opening a browser")

    sub.add_parser("validate", help="check quotes.csv")

    args = p.parse_args(argv)
    if args.cmd == "update":
        try:
            update()
        except Exception as exc:
            sys.exit(f"Update failed: {exc}")
        return
    {"practice": cmd_practice, "search": cmd_search, "stats": cmd_stats,
     "submit": cmd_submit, "validate": cmd_validate}[args.cmd](args)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
    except BrokenPipeError:  # e.g. output piped into `head`
        sys.stderr.close()
