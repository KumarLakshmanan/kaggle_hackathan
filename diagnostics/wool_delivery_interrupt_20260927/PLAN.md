# Isolated wool-carrier delivery interrupt — 2026-09-26

## Hypothesis and fixed rule

The new 17-game cash audit reproduced every public terminal balance and
identified a seven-thousand-coin wool receipt gap in a near-mirror loss.
At two late sale races, the rival moved wool carriers to the shed two to
three turns earlier, then sold equal total units at better prices. A
market-only advance cannot move stock still carried on sheep tiles.

Freeze one observation-legal interrupt to the current submitted `main.py`.
Only on days 20–28, hours 10–18, at a visible WOOL quote at least 120,
consider a hand on a SHEEP tile carrying at least eight WOOL with at least
four ready units. Require at least 24 free shed spaces. Replace its current
command with `HARVEST`, then take the shortest axis-aligned route to the
central shed-access square `(5,5)`, `PLACE` the carried WOOL, and insert
one same-turn WOOL sale ahead of existing orders if a market slot is free.
Hold that hand at `(5,5)` until the parent next attempts `PLACE WOOL` for
it or the same day ends; then release it to the parent. Abort safely on
missing state or capacity. Do not alter other workers, products, route
selection, purchases, or the submitted file.

Implementation correction before fresh testing: the first draft required
an upcoming `PLACE WOOL` and sale in the raw route tape, but the raw route
contains only ten hands while a later controller schedules the two wool
carriers. That check never activated on the diagnosed replay. It provided
no outcome evidence. Replace the unavailable lookahead with the observed
parent command at runtime and hold until its next `PLACE WOOL` or day end.
This addendum freezes the executable rule before any fresh native seed is
examined.

This moves harvest/delivery ahead at the expense of some same-day
FEED/CARE/FERTILIZER tasks. Later production may suffer, so evaluate full
terminal cash, rival cash and paired margin, not just the target sale.

## Evidence gates

First verify the isolated candidate compiles and Kaggle's file-path loader
chooses its final callable in both seats. A single saved Takahiro route may
check that the branch is physically executable; its outcome is diagnostic
only and cannot promote the rule.

On fresh native seeds 2625000–2625015, compare current `main.py` and the
candidate against reacting unchanged `main.py`, both seats and original
shops. Require all 64 games DONE/DONE, zero branch errors, identical shops
within each control/candidate pair, at least four activated paired seeds,
positive aggregate own cash and paired-margin change on activated pairs,
at least two-thirds activated pairs with positive margin change, and no
activated pair worse than −5,000 margin coins. Failure rejects the rule.
Passing development would require an untouched second native block and
the saved top-100 paired panel before a `main.py` edit. No Kaggle upload
without a fresh explicit user request.
