# GAMSAT Section 2 Quote Bank

A community quote bank for GAMSAT Section 2 essay practice. Quotes are tagged by
theme and by suitability for Task A, Task B or both.

## Use it on the web

**https://NatsukiRog.github.io/GAMSAT_Section_2_QuoteBank/** : practice sets, search and
quote submission in your browser, on any device. Nothing to install.

## Or use it in the terminal (Python 3.8+, nothing to install)

```
python quotebank.py practice                      # 4 random quotes sharing one theme
python quotebank.py practice --task A --theme justice
python quotebank.py search peace --task A
python quotebank.py stats                         # how many quotes per theme
python quotebank.py submit                        # suggest a new quote
python quotebank.py update                        # get the latest quotes
```

Press Enter in `practice` for a new set, `q` to quit. Quotes marked **Both** count
for either task.

## Contribute a quote

Run `python quotebank.py submit`, answer the prompts, and your browser opens a
pre-filled GitHub issue. Check it and press **Submit new issue** (a free GitHub
account is required). Please include a real source: misattributed quotes are
common and will be rejected.

## Data

| File | Purpose |
|---|---|
| `quotes.csv` | the quote bank |
| `themes.txt` | allowed primary themes |
| `tags.txt` | allowed secondary tags (max 3 per quote) |

Columns: `id, date_added, quote, author, source, primary_theme, task,
secondary_tags, interpretation, opposing_perspective, example, notes`.
`id` and `date_added` are assigned automatically when a quote is accepted.
Maintainers: run `python quotebank.py validate` before merging.

## Maintainers

How a submission flows:

1. A student runs `quotebank submit` and files a pre-filled issue (label `quote-submission`).
2. **Check submission** runs automatically. Problems (duplicate, missing source, bad theme)
   get a comment and the `needs-fix` label; a valid one gets `ready-for-review`.
3. You read the issue, check the attribution, and add the **`approved`** label.
4. **Accept submission** runs: it assigns the id and date, appends the row to `quotes.csv`,
   commits, and closes the issue with a thank-you. To decline, just close the issue with a comment.

One-time setup: in **Settings → Actions → General → Workflow permissions**, allow
**Read and write permissions** so the approval workflow can commit the CSV. The
workflows create the `quote-submission`, `needs-fix` and `ready-for-review` labels
when the first quote is submitted. Create an `approved` label (for example, grey)
for maintainers to use after reviewing a submission. Only the repository owner
can trigger the CSV import by adding that label.

The issue form and workflows must live at the repository root in `.github/`.
After editing `quotebank/themes.txt` or `quotebank/tags.txt`, run
`python quotebank/scripts/build_issue_template.py` from the repository root and
commit the regenerated `.github/ISSUE_TEMPLATE/submit-quote.yml` form. Run
`python quotebank/quotebank.py validate` before merging changes to the data files.
`scripts/migrate_xlsx.py` was used once to import the original Excel workbook.

## Licence

Code: MIT (`LICENSE`). Data: CC BY-SA 4.0 (`LICENSE-DATA`). Quotes remain the property of
their authors. This is an independent community resource, not affiliated with ACER.
