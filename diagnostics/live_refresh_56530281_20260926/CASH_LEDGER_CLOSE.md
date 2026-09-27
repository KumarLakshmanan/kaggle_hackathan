# Executed cash in selected close live games — 2026-09-26

`cash_ledger_close.py` passively instrumented the installed 1.32.7 engine
while replaying the exact submitted artifact against the downloaded opponent
actions on the original seed and seat. The panel was declared as the eight
smallest near-mirror live losses and three close near-mirror wins from the
fresh 40-episode slice. All 11 reruns reproduced both players' final cash
exactly and finished `DONE`.

For every game, final cash minus the initial 3,000 equaled the sum of the
observed successful per-unit market cash changes plus atomic hire/land cash
changes. The unexplained remainder was **zero for both players in all 11**.
This is an executed net-cash ledger, rather than a count of requested orders.

All eight selected losses had lower net strawberry cash, totaling **2,151
coins** of deficit. Seven sold the **same number of strawberry units** as the
rival; the eighth sold one fewer. Three losses also sold 13–20 fewer carrots.
The three winning controls show that a strawberry deficit is not a complete
win predictor: one won by 64 despite 312 fewer strawberry coins. Atomic
hire/land spending was equal in all 11 selected games. Other item sales and
purchases offset much of the strawberry difference; no single gross sale
category explains terminal margin by itself.

The exact-unit `sale_timing_probe.py` on 113363691 (-13 final margin)
isolated a -332 strawberry receipt difference across nine nonmatching sale
turns. In two major bursts the rival sold 20 units two turns before our
corresponding 20-unit sale, and sold 21 while ours sold 2 before our later
19-unit sale. Both sides sold 249 strawberry units overall. This motivated
a narrow same-item sale-protection experiment, but this trace by itself does
not establish that advancing those sales helps in a reactive game.

Evidence: `cash_ledger_close.json`, `sale_probe_113363691_strawberry.json`,
and the source scripts. The opponent action tapes remain fixed during these
reruns; causal policy testing must use matched candidate and reactive games.

**Decision:** retain this as diagnosis. No direct `main.py` edit or Kaggle
upload follows from the accounting result alone.
