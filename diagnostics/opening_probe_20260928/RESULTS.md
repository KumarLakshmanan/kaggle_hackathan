# Common-opening arm screen — 2026-09-28 IST

All 200 full games completed DONE/DONE/720, with both arms seeing identical
step-1 captures on every fixture/seat. The earlier 20 physical prefix checks
also passed. Current main.py and both frozen candidate hashes stayed intact.

| Complete arm | Saved loss pairs won | Top-20 pairs won | Former winning top-20 pairs lost |
| --- | ---: | ---: | ---: |
| Common opening + 4ee | 3/30 | 16/20 | 2 |
| Common opening + V43 | 13/30 | 12/20 | 5 |

The 4ee arm newly wins Kucing Garong (+43,653 per seat), Junliang Ye
(+5,888), fasith 007 (+23,607), and top-20 Vadim (+3,655 versus incumbent
−400). It loses former controls M & M & P & Q (−10,250) and Unknown
Mother-Goose (−29,912). Both V43 seats also lose those two controls, so even
an outcome-informed chooser cannot preserve all 17 existing top-20 wins.

The frozen search over small public-state threshold rules has a best
development result of 28/50 both-seat sweeps and 58/100 seat wins, but loses
six incumbent winning seats. No allowed rule preserves incumbent wins.
An outcome-informed per-fixture chooser could attain only 32/50 sweeps;
that ceiling is diagnostic and is not an executable validated policy.

**Decision: reject these exact arms for promotion. Retain the common-opening
architecture and fix its market-state preservation before another screen.**
Matching own physical resources at step 3 was insufficient: changing gross
initial WHEAT orders changed shared-market prices, early cash and later
shops. A separately frozen revision will preserve the incumbent's order
indices and exact market/cash state through step 3 while still deferring
private animal purchases to permit an observable farming choice.

Evidence: `arms.json`, resumable `arms.jsonl`, `selection.json`,
`physical.json`, and `candidates.json`. No main.py edit, upload or Kaggle access.
