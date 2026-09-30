# Optimize execution order within the current market turn

Frozen 2026-09-27 02:01 UTC. Parent is submitted 3cc. The q80 opening
experiment is rejected: 44/50 replay sweeps but 1/64 native head-to-head wins.
Keep the parent's quantities and physical schedule. Investigate order slots,
which quote both players simultaneously within a slot and settle it before
the following slot. A ready sale can precede a rival's same-turn sale, and
a wheat round trip can be completed before an unrelated seed purchase.

Build a separate single-file candidate. Embed the exact local 1.32.7 market
functions, not the environment runner. Project our current unit transfers.
Evaluate at most 24 permutations formed by moving a SELL order earlier in
the same queue. Keep the order count, every item and quantity, and all unit
commands unchanged. Use two forecasts: no rival market orders, and a rival
using our parent queue with our post-transfer shed as an explicit hypothetical
inventory and the rival's observed public cash. Do not access actual rival
private data, future shops, seed identity or a team lookup.

Accept a permutation only if it preserves our final seeds, shed, workers
and land in both forecasts; keeps the rival's resources unchanged in the
hypothetical mirror; never reduces our forecast cash in either scenario;
and increases own-minus-rival cash under the mirror forecast. Use the
highest predicted improvement, then own cash, then retain original order
on a tie. This is a model-based action, not a guarantee about rival orders.

Development: native seeds 2658000–2658007, both seats against reacting 3cc.
Require all DONE, zero wrapper errors, at least four active pairs, and at
least 6/8 paired win points. If it fails, reject the exact candidate.
If it passes, test the saved 50 in both seats: >42 sweeps, <=1 old sweep
lost, all DONE. Then freeze 32 fresh independent seeds 2660000–2660031:
old/new against reacting 489 and C95, new against 3cc and best-active 1f.
Require no external win-point regression versus either rival, a positive
pooled gain, >=20/32 paired points against 3cc and >=16/32 against 1f,
all DONE, no errors. Both-seat file-loader parity before promotion.
No upload is authorized by this experiment. Main and root backups remain.
