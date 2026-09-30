# Funded strawberry opening pilot — 2026-09-26

The refreshed top-100 saved-route losses include opponents with nine or ten
strawberry tiles at day six, versus four in current `main.py`. A separate
candidate (`exp_strawberry6_opening_20260926.py`, SHA-256 `4b839dec...`)
attempted to convert the first six melon seed purchases and matching planting
actions into strawberries. It kept the rest of the current policy, including
its final Kaggle callable. The candidate was built from current `main.py`
SHA-256 `08aa268a...` using `build_strawberry6.py`.

On fresh native seeds 2610920–2610921 against reacting current `main.py`, both
seats per seed, all four games ended `DONE`. The candidate lost all four:
41,250 versus 54,471 coins on seed 2610920 and 80,020 versus 95,033 on
seed 2610921 (same respective results in both seats). At day six it had eight
strawberries and four melons, with the expected animals and wheat, but one of
the six targeted turn actions was skipped by its exact-action guard. Its
existing later route was not redesigned for the changed crop life cycle.

**Reject this candidate.** The attempted swap substantially reduced cash in
both seeds and did not achieve the intended ten-strawberry portfolio. This
pilot does not establish that a fully redesigned strawberry strategy would
lose. No `main.py` change or Kaggle upload resulted. Raw result and day-six
captures: `strawberry6_pilot.json`.
