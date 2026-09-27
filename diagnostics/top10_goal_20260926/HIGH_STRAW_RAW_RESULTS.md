# High-strawberry raw-route screen — 2026-09-26

The current saved top-100 loss panel includes opponents with nine to ten
strawberry tiles at day six. To test whether one of their complete recorded
action schedules is a robust replacement, `high_straw_raw_screen.py` replayed
five such schedules against reacting current `main.py` on the same four fresh
native seeds (2610960–2610963), both seats. All 40 games ended `DONE`.

| Saved schedule | Day-six strawberries | Wins / 8 seat games | Aggregate margin |
| --- | ---: | ---: | ---: |
| mtmr_s1 | 9 | 0 | −451,901 |
| YumeNeko | 10 | 2 | −213,484 |
| Lucas Boesen | 10 | 2 | −47,382 |
| Matt Motoki | 10 | 4 | −60,055 |
| marwar22 | 10 | 0 | −241,500 |

The recorded schedules are fixed actions, while `main.py` reacts to each
game. Their day-six farm compositions transfer, but later purchases, shops,
sales and cash differ from the source episode. **Reject all five raw
schedules as general replacements.** The result does not establish that a
state-aware policy built around those farms would lose. No `main.py` edit or
Kaggle upload resulted. Exact routes, hashes and game rows are in
`high_straw_raw_screen.json`.
