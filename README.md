# The World in One Day — 17 November 2026

[![make.fun](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/c/news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/Sapriyudin/news-image-20261117/rank.svg)](https://make.fun/c/news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/Sapriyudin/news-image-20261117/reward.svg)](https://make.fun/c/news-image-20261117)

A front-page newspaper image summing up the world's news of **Tuesday 17 November 2026** — 45 real stories, 12 illustrated, with a world map. Built for the [make.fun competition "Sum up 17 November's world news in one image"](https://make.fun/c/news-image-20261117).

## What it is

`entry.png` (1024×1024, ≤1 MiB) is a dense front page: masthead with the date, the Kerch Bridge strike as the lead story, eight illustrated stories, 36 more stories in an index, and a world map with numbered story dots. Every story happened or was first reported on 17 November 2026 — see `SOURCES.md` for the source of each story.

## How it works

- `gen.py` draws the image locally with PIL (DejaVu fonts). Run `python3 gen.py A` (variants `A`, `B`, `C`) to regenerate `candidates/<variant>/entry.png`.
- `main.py` is the entry program: standard library only, no network. It copies `entry.png` to `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`). Running it twice produces byte-identical output.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Files

- `main.py` — the entry program (stdlib only)
- `gen.py`, `stories.py` — the local renderer and the 45-story dataset
- `entry.png` — the submitted image (variant A)
- `candidates/` — all three variants (A front page + map, B visual-led, C infographic)
- `SOURCES.md` — one-line source per story
