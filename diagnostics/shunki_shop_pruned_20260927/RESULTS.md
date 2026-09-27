# Pruned selector qualification

Candidate `db98141542b90eb84441a42070c0e9679e3733f46fb811dd85d6e2a5c9be439f`.
Parent for promotion is submitted 3cc. Construction removes the regressing
BAKERY/PET override from rejected 94f; three other replacements remain.

## Replay regression

44/50 both-seat wins and 89/100 seat wins, all referenced games DONE/DONE.
Four newly run Snorlax / We wanna be tomatos games exactly reproduce 3cc.
The other 96 measured games have identical policy paths to 94f. Captured
first-two-shop observations verify that these are the only four affected
games; see branch_isolation_proof.json. Do not call this 100 newly run games.

Added sweeps versus current main: DECEM and marwar22. No existing sweep
lost. Remaining non-sweeps: Majkel1337, seek inspiration, We wanna be
tomatos, Snorlax, Breaking1800, and the split ymg_aq matchup.

## Decision

Reject after all 240 fresh native games finished DONE/DONE. Both policies
win 46/48 against 489 and 48/48 against C95. The candidate then loses
**all 48 head-to-head games** against submitted 3cc, with every retained
branch active in both seats. This fails the frozen 16/24 paired-point gate.
The conditional best-active and loader stages are not run. Main and
uploads remain unchanged.
Root backup: main_candidate_shop_pruned_20260927_db981415.py.
