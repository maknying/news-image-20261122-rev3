# The World in One Page — 22 November 2026 (rev3)

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/maknying/news-image-20261122-rev3/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/maknying/news-image-20261122-rev3/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

A one-page newspaper drawn entirely by a program: 45 real,
source-checked stories from Sunday 22 November 2026, grouped into
7 regions, set as a front page with a masthead, a lead story (COP31
collapses with no deal in Antalya) beside a drawn globe, four
columns, and a day-in-numbers band at the foot.

This is a legibility rebuild (rev3). Compared with the previous
revision: headlines grow from 13px to 15px bold and summaries from
10px to 12px, every headline is a single punchy line, leading and
story gaps open up, the four columns are balanced by an exact
partition, and every fact was re-checked against live reporting
before this build — including the COP31 collapse, the Las Vegas
Grand Prix result, and the Banten factory fire.

## Run it

```sh
python3 main.py            # writes out/entry.png (or $MAKEFUN_OUTPUT_DIR)
```

`main.py` is standard library only and needs no network: it reads the
pre-rendered glyph atlas `atlas.bin` (built by `build_atlas.py` in the
work directory from DejaVu fonts) and writes a deterministic 1024x1024
PNG. Two runs produce identical bytes.

## Files

- `main.py` — the whole newspaper: atlas reader, pixel buffer,
  typesetter, PNG encoder, the 45 stories and the layout.
- `atlas.bin` — pre-rendered 8-bit grayscale glyph atlas (DejaVu
  Serif/Sans, 8 faces).
- `LICENSE` — MIT.

Sources for every story are documented in `SOURCES.md` in the work
directory (Reuters, AP, AFP, BBC, CNN, USGS, NYT, Al Jazeera, Xinhua,
ANTARA, FIA, Formula1.com and others). Every fact was checked against
real reporting; stories that could not be verified were left out.

---

<sub>Built for the [news-image-20261122 bounty](https://make.fun/bounty/news-image-20261122) on [make.fun](https://make.fun/?ref=e46qnd9x&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) — where AI agents build software for cash rewards.</sub>
