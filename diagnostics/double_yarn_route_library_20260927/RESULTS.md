# Complete double-Yarn route-library screen — 2026-09-26 21:19 UTC

`screen_routes.py` tested all **40** complete route tapes whose first 144
actions match incumbent route 9. It overrode only the day-six
`YARN_STORE,YARN_STORE` mapping in an isolated runtime copy of unchanged
`main.py` SHA-256 `489fe8e4...`. Each route faced the three frozen major
losses (mhw, ShunkiKyoya, AI是我的豆包) and the dodsters same-shop control on
their original seeds in seat 0 with native shops: **160 games, all
DONE/DONE**. The four route-9 cash pairs exactly matched the previously
saved `main_100routes.json` results. Exact per-route own/rival cash and
paired margins are in `fixed_screen.json`.

No route improved paired margin on **all three** major losses. Exactly
one route, **126**, increased our own terminal cash on all three, but it
worsened ShunkiKyoya's paired margin and rescued none:

| Fixed rival | Own cash change | Rival cash change | Paired-margin change |
| --- | ---: | ---: | ---: |
| AI是我的豆包 | +6,142 | +830 | +5,312 |
| ShunkiKyoya | +1,679 | +4,191 | −2,512 |
| mhw | +4,956 | +2,380 | +2,576 |
| dodsters control | +47 | +223 | −176 |

Route 126 had the highest minimum target margin change among alternatives
(−2,512), while incumbent route 9 had zero change by definition. It failed
the predeclared positive-own **and** positive-margin requirement on every
target. The control stayed within its guard, but that does not rescue the
target failure. The target losses remain large even where route 126 helps.

**Decision: reject every library remapping for double-Yarn promotion.**
These are fixed saved action histories; they do not adapt to the policy
change. Because no route passed the frozen development gate, no both-seat
fixed escalation, fresh reactive seed block, `main.py` edit, or Kaggle
upload follows. The existing route library lacks a schedule that solves
this loss cluster; a new funded production and worker-delivery schedule is
the next meaningful unit of work.

Evidence: `PLAN.md`, `fixed_screen.json` and `screen_partial.json`.
Reproduce with:

```powershell
python -X utf8 diagnostics\double_yarn_route_library_20260927\screen_routes.py
```
