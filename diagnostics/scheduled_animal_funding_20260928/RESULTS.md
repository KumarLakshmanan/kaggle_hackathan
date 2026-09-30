# Scheduled animal funding — rejected, 2026-09-28

Exact candidate `7fad3c8074c774cb5278078820aecc7074b699b090007d94a3da58ea58e14f86`
finishes all four fast diagnostic games DONE/DONE/720 with no recorded
policy errors. The layer changes one turn in each Boey game and never
activates in Kaggledew. It recovers the scheduled sheep, but **Boey remains
a loss in both seats**, worsening from the route-only -1,577 to -5,419.
Kaggledew stays exactly +4,877. **Reject at the frozen rescue gate; do not
run native strength or promote.**

The new sheep costs the expected 500: observation 196 changes from 527
coins/no sheep to 27 coins/one sheep. The next scheduled wheat purchases
then fail; observation 197 has zero shed wheat instead of four. Both
policies still buy their planned land, but atomically blocked PLANT
commands increase from nine to eleven, and later shops diverge at step
288. Own final cash falls 18,442 and rival cash falls 14,600, a -3,842
paired-margin change. Recovering the animal does not recover a fully
funded production schedule. Fewer empty-pasture actions do not establish
a competitive gain.

Evidence: `PLAN.md`, `candidate.json`, `fast_screen.json/jsonl`, four
hash-receipted trace paths in the results. Main stays exact 4ee. No Kaggle
activity occurred.
