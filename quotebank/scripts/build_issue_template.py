#!/usr/bin/env python3
"""Regenerate .github/ISSUE_TEMPLATE/submit-quote.yml from themes.txt and tags.txt.

Run this whenever you change the theme or tag lists, so the submission form's
dropdowns stay in sync. Field ids must match the parameters quotebank.py submits.
"""
import json, pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent
REPO = DATA.parent
lines = lambda n: [l.strip() for l in (DATA / n).read_text(encoding="utf-8").splitlines() if l.strip()]
themes, tags = lines("themes.txt"), lines("tags.txt")
q = json.dumps  # JSON strings are valid YAML scalars, so commas in theme names are safe


def dropdown(id_, label, options, required, desc=""):
    out = ["  - type: dropdown", f"    id: {id_}", "    attributes:", f"      label: {q(label)}"]
    if desc:
        out.append(f"      description: {q(desc)}")
    out.append("      options:")
    out += [f"        - {q(o)}" for o in options]
    out += ["    validations:", f"      required: {str(required).lower()}"]
    return out


def text(kind, id_, label, required, desc=""):
    out = [f"  - type: {kind}", f"    id: {id_}", "    attributes:", f"      label: {q(label)}"]
    if desc:
        out.append(f"      description: {q(desc)}")
    out += ["    validations:", f"      required: {str(required).lower()}"]
    return out


y = ['name: "Submit a quote"',
     'description: "Suggest a quote for the GAMSAT Section 2 quote bank."',
     'title: "Quote: "', 'labels: ["quote-submission"]', "body:"]
y += ["  - type: markdown", "    attributes:",
      '      value: "Thanks for contributing! Please include a real source: misattributed quotes will be rejected."']
y += text("textarea", "quote", "Quote", True, "Without surrounding quotation marks.")
y += text("input", "author", "Author", True)
y += text("input", "source", "Source / URL", True,
          "Book, speech, page number or link. Unsourced quotes are often misattributed.")
y += dropdown("theme", "Primary theme", themes, True)
y += dropdown("task", "Section suitability", ["Task A", "Task B", "Both"], True)
for i in (1, 2, 3):
    y += dropdown(f"tag_{i}", f"Secondary tag {i}", tags, False, "Optional.")
y += text("textarea", "interpretation", "Interpretation", False, "Optional.")
y += text("textarea", "opposing", "Opposing perspective", False, "Optional.")
y += text("textarea", "example", "Example / evidence", False, "Optional.")
y += text("textarea", "notes", "Notes", False, "Optional.")

y += ["  - type: checkboxes", "    id: agreement", "    attributes:", '      label: "Licence and source"',
      "      options:",
      '        - label: "I agree my contribution is released under CC BY-SA 4.0, and I have checked the source."',
      "          required: true"]

out = REPO / ".github" / "ISSUE_TEMPLATE" / "submit-quote.yml"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(y) + "\n", encoding="utf-8")
print("Wrote", out.relative_to(REPO))
