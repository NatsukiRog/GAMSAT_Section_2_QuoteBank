# GAMSAT Section 2 Quote Bank (How To Use It)

A community quote bank for GAMSAT Section 2 essay practice. Quotes are tagged by
theme and by suitability for Task A, Task B or both.

The Aim of the Game here is to have a BUNCH of high quality quotes we can use for endless essay practicing fun :)

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



## Licence

Code: MIT (`LICENSE`). Data: CC BY-SA 4.0 (`LICENSE-DATA`). Quotes remain the property of
their authors. This is an independent community resource, not affiliated with ACER.
