# Premium-sale gap by per-turn quantities — 2026-09-26

`price_gap_all.py` reran all 29 frozen live public losses with current
`main.py` SHA-256 `489fe8e4...` against each saved rival action history on
its original seed and seat. All 29 replays reproduced both Kaggle terminal
cash amounts and ended `DONE`/`DONE`. The installed engine's transaction hook
recorded each successful sale price and unit from day 20 onward.

I separated product sale turns into (a) turns where both agents executed the
same positive number of sale units and (b) turns where their executed unit
counts differed. The second group includes one-sided sale turns and turns
where both sold unequal batches; it measures **pacing/batch differences**
without assuming which policy change would improve the outcome.

| Product | Our total late receipt gap | Same-unit turns: count / receipt gap | Different-unit turns: count / receipt gap | Our vs rival total units |
| --- | ---: | ---: | ---: | ---: |
| Strawberry | −9,640 | 388 / **+155** | 658 / **−9,795** | 4,999 / 5,003 |
| Wool | −9,268 | 291 / −1,963 | 371 / −7,305 | 2,179 / 2,185 |

For strawberry, equal-sized same-turn sales slightly favored us in aggregate;
the observed deficit sits in how units were distributed across turns. Wool
has both a same-unit price gap and a larger pacing gap. In the four largest
equal-volume strawberry-loss cases, only −60 of −3,549 aggregate strawberry
receipts arose on equal-unit turns; the rest arose on different-unit turns.

**Decision: diagnose only.** Broad sale advance and a simple half-base quote
guard have failed their predeclared rescue gates. A future candidate would
need to choose batch sizes from visible inventory, recovery, shed capacity,
remaining time and uncertain rival sales, then pass fresh native reactive
games. These saved rival actions cannot validate that candidate by themselves.
No `main.py` edit or Kaggle upload was made. Per-case numbers are in
`price_gap_cases_29.json` (and the original four-case pilot in
`price_gap_cases_4.json`).
