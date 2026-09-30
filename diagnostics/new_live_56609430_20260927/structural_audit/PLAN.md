# Day-6/day-10 live structure audit — 2026-09-27

Use the entire frozen 16:53 UTC submission-56609430 public cohort: 61 games,
42 wins and 19 losses, no outcome filtering. Verify each decompressed raw
replay SHA-256 against `cohort_165306.json`. Extract state at steps 144 and
240 (start of days 7 and 11, after days 6 and 10 complete). These are the
first states at which all day-6/day-10 work and the next shop unlock are
visible. Record both players' public money, land and tile commitments, current
shops, and shared prices/inventory. Own private stock is observable; rival
private stock is diagnostic only and cannot enter a deployable trigger.

Audit four mechanisms: crop/animal commitments, cash/funding, worker-task
execution, and shared-market response. Historical own action counts may
diagnose execution, but a candidate day-6/day-10 trigger must use only the
current observation. Compare losses with wins overall and within rank <=200
to reduce the obvious opponent-strength confound. Report all thresholds and
denominators; repeat-opponent games remain separate episodes but identify
them. Candidate trigger search is exploratory and cannot promote a policy.

Only flag a *narrow* trigger if it catches at least four of 19 losses, fires
on at most four of 42 wins, and catches at least two losses among the rank
<=200 opponents. Report false positives by opponent and shop pair, and avoid
restating rejected generic melon or full-route switches. If no feature meets
these conditions with a coherent executable intervention, reject a trigger
from this audit and state the residual mechanism uncertainty. No agent edit
or Kaggle upload is in scope.
