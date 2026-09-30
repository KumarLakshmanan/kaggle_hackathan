# Day-18 shop retarget experiment (2026-09-27)

## Hypothesis

Seven embedded EXP240 routes (105, 108, 120, 121, 122, 124, 125) have
**identical full action tapes through step 431**, including all work and
market orders. They diverge from day 18 through day 26 in complete worker,
input and sale schedules, before converging at day 27. At day 18 the latest
unlocked shops may provide better demand information than the first two
shops used by the incumbent day-6 router. Switch once, only inside this
state-compatible route family, to the existing route assigned by the EXP240
router to the two latest shops when that route also belongs to the family.
No future or rival-private information is used.

## Frozen test

Build an isolated exact `main.py` snapshot plus the day-18 router wrapper.
Verify same action on step 0 and that the final Kaggle path entrypoint remains
last. Native reacting comparison against the unchanged snapshot uses fresh
seeds 2617300–2617315, both seats, original shops. If fewer than four paired
seeds actually change route, conclude this pilot is too narrow and do not
promote. Otherwise require all games `DONE`, positive aggregate own cash and
paired margin over activated seeds, at least two-thirds activated paired
seeds with positive margin, and no activated paired loss below −5,000. A
passing development result would require an untouched second native block
before any `main.py` promotion. Fixed action replays are diagnostic only.

No Kaggle upload is authorized here.
