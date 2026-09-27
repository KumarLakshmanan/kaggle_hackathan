# Refreshed current top-20 saved routes — 2026-09-26 19:51 UTC

A read-only Kaggle leaderboard snapshot at 19:46 UTC listed twenty current
leading teams. The collector saved each selected submission's newest completed
public action route. `routes/summary.json` contains **20 teams, 20 distinct
action SHA-256 hashes and 18 source episodes**. None of the action hashes or
episodes overlaps the 07:08 top-100 panel; none of the hashes overlaps the
older top-20 panel. See `leaderboard.json` and `routes/summary.json`.

Unchanged uploaded `main.py` SHA-256 `489fe8e4...` played all twenty saved
routes on original replay seeds, both seats and native shops under engine
1.32.7. All forty games ended `DONE`/`DONE`, with **18/20 positive paired
routes and 36/40 seat wins**. Full identities, results and completion state
are in `main_20routes.json`.

| Lost rank / team | Seat-0 and seat-1 cash | Margin per seat | First two shops |
| --- | --- | ---: | --- |
| 1 / Boey | 96,194 versus 112,256 | −16,062 | Ice Cream Shop, Bakery |
| 6 / DECEM | 73,769 versus 83,645 | −9,876 | Bakery, Pizza Shop |

`diagnose_two_losses.py` reproduced both losses exactly with native event
traces in seat 0 and reconciled every coin of the cash gap in
`two_loss_ledgers.json`. Boey's largest net item gaps were wheat −8,990,
egg −7,635 and milk −4,830; it sold 2,826 fewer wheat units, 166 fewer eggs
and 44 fewer milk units. DECEM's largest gaps were egg −11,037, carrot
−9,864 and wheat −8,866; our agent sold 243 fewer eggs and 210 fewer
carrots, while earning 15,917 more net tomato cash. These are net executed
cash differences, not standalone marginal returns from changing production.
The public shop paths and shared prices are endogenous.

**Decision: diagnosis/regression panel only.** The refreshed fixed-action
routes show the all-100 goal remains unmet and indicate a diversified wheat,
egg, carrot and dairy production gap against two leading teams. They do not
prove a direct crop/animal swap would improve live games. Test any complete
funded route change with matched controls and fresh reactive opponents before
promoting `main.py`. No main edit or Kaggle upload from this panel.
