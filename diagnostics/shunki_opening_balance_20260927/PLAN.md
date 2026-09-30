# Opening wheat quantity screen — frozen 2026-09-27

Parent: submitted 3cc. No changes to worker commands or the season selector.
Its first market turn starts BUY WHEAT 28 / SELL WHEAT 24 / BUY WHEAT 2.
The first two orders are a four-unit net purchase whose gross quantity affects
shared-market execution. Public notebook tetsutani/market-smart-farming-kaggriculture
describes this interaction, but its different opening cannot be transplanted
as a complete set of orders. Downloaded archive main hash f6a756cf is research
material only; no notebook code or embedded runtime has been executed.

Development selection: using only the first two turns of the 50 downloaded
opponent tapes, test gross buys 4, 8, 12, 20, 28, 40, 55, 70 and 80. The matching
SELL is buy minus four, leaving the third BUY 2 intact and the order slots
unchanged (a zero sale is a harmless ignored order). Preserve all other orders.
Run both seats in the installed original engine, with one fixed initialization
seed (shops have not opened yet). A quantity is eligible only if every game
retains the parent's own workers, farm tiles, seeds, carried items and shed
quantities after both turns. Select the eligible quantity with greatest mean
improvement in own-minus-rival liquid assets: bank cash plus seed costs,
animal purchase costs and base-price product stock in shed/worker inventories.
This is an opening development proxy, not a full-game strength claim. Ties
prefer quantity nearest 28; do not select on later outcomes.

If an eligible different quantity improves this proxy, freeze it and run
all 50 full replay matchups in both seats. Require >42 sweeps, at most one
previous sweep lost, all DONE and correct executed opening resource counts.
If no eligible quantity improves, stop without a full season test.

Only after that full-panel gate passes: original-shop independent games on
32 paired seeds 2656000–2656031, old/new versus reacting 489 and public C95,
plus new versus 3cc and actual leading active 1f. Require no fewer external
win points versus either rival, positive pooled improvement, at least 20/32
paired win points versus both 3cc and 1f, all DONE, and both-seat file-loader
parity before promotion. This plan does not authorize another upload.

Source: https://www.kaggle.com/code/tetsutani/market-smart-farming-kaggriculture
