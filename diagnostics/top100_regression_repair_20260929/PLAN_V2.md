# Narrower route repair, frozen 2026-09-29

V1 recovered all nine September-29 replay regressions, but failed native
confirmation: 70/48/10 W/D/L versus 72/48/8 for 4ee. All worsened outcomes
were associated with the Yarn/Farmers and Farmers/Pizza overrides. Brunch/
Brunch and Brunch/Smoothie supplied the reacting-policy gains. Reject V1
for promotion; preserve its source, reports, and all outcomes.

## Candidate

Starting from exact V1 2c02f9f9, remove the global Yarn/Farmers replacement
and Farmers/Pizza loss-pool replacement. Restore the original 4ee route-map
entries, including their prefixed cases, for both pairs. No opponent names,
seed-specific conditions, or new production fingerprints. Retain all other
V1 code unchanged. The loss of the monsaraida replay rescue is an explicit
possible cost; do not hide it or change the rules after seeing results.

## Frozen checks

1. Full current top-100 regression panel: 200 games, both seats. Require
   clean DONE/DONE/720, no candidate errors, all nine regressed teams rescued,
   all 141 original 4ee seat wins retained, and more than 141 wins overall.
2. Development reacting panel: seeds 12929001, 12929005, 12929008,
   12929107, 12929108, 12929109, 12929115, 12929116; both seats against
   4ee, ae349, public V35, and C95. These seeds were used to design V2 and
   are NOT independent validation. Reuse exact hash-bound baseline rows
   with their original engine labels and provenance; run all 64 new-policy
   games. Require positive total points, no per-opponent point regression,
   at least six nonnegative seed blocks, and all games clean.
3. Verify native framework parity for both seats against saved Boey, Anton,
   and monsaraida, and both arms/seats against reacting 4ee and V35 on
   development seed 12929001 (14 games). Verify exact standalone file-loader
   actions and rewards in both seats (4 native games).
4. After checks 1-3 pass, run full native confirmation on untouched seeds
   12929201 through 12929216, the same four reacting policies, both seats,
   and candidate plus 4ee (256 games). Preserve the original strict
   promotion criterion: positive pooled point gain with positive 95%
   whole-seed bootstrap lower bound; no per-opponent point regression;
   clean execution. Do not enlarge or select the block after seeing it.
   Report an inconclusive gain as inconclusive, not as a passed gate.
5. Run all 102 earlier loss30/top20/control cases as a supplemental archive
   diagnostic. Report every changed outcome against ae349 and V1.

Wins/draws/losses are primary; margins diagnose changes. Preserve paired
seats in uncertainty estimates. Native shop generation is endogenous;
configuration seeds stay hidden from reacting agents. If the frozen gates
fail, leave main.py at 4ee and deliver a clearly labeled experimental file.
No Kaggle access or upload is part of this repair request.
