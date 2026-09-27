# Land retry — development results

Candidate SHA-256 `5002b442da0d97fb66c5eca761a15f66e8d9ff6a2b6e07feaad314352065edef`.

In the DECEM diagnosis the southwest purchase on turn 217 failed with
1,936 coins available for a 2,000-coin purchase (and a ten-coin seed order).
The candidate retries it once when funded. Both seats completed DONE/DONE:
146,374 versus 149,478 coins, margin -3,104 instead of -82,192. The later
missing-feed events disappear; only three initial plant and water commands
still target locked land before recovery.

The full fresh top-50 regression panel also completed DONE/DONE. It retains
84/100 seat wins and 42/50 two-seat sweeps, with no added wins or lost wins.
Decision: the strict sweep-improvement gate was not met. Do not advance
this artifact alone to promotion or claim independent validation. Preserve
the causal repair as a possible component of a separately frozen candidate.

The audit of the eight remaining matchups found no listed physical failures
in five; Majkel1337 has 13 unfunded fertilizer actions and one unfunded
feed, while ymg_aq has three plant-on-weed failures. Terminal orders already
sell nearly all available stock. Evidence: `top50.json`,
`remaining_execution_audit.json`, and `development_decem.json`.
