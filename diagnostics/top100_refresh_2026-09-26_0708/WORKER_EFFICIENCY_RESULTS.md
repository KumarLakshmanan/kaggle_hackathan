# Worker-action efficiency result — 2026-09-26 19:29 UTC

`audit_worker_efficiency.py` replayed all 34 lost routes and ten deterministic
winning controls on their original seeds, candidate seat 0 and native shops.
Every game ended `DONE`/`DONE` and reproduced **both** terminal cash totals in
`main_100routes.json`. The candidate was unchanged `main.py` SHA-256
`489fe8e4...`. Source rows and per-operation/window counts are in
`worker_efficiency_44.json`; the predeclared gate is in
`WORKER_EFFICIENCY_PLAN.md`.

| Route set | Our non-`PASS` commands | Failed | Failure rate | Routes with ≥100 failures | Our `PASS` share |
| --- | ---: | ---: | ---: | ---: | ---: |
| 34 paired losses | 217,606 | 1,443 | **0.663%** | **0/34** (max 80) | 7.77% |
| 10 paired wins | 63,992 | 471 | **0.736%** | **0/10** (max 81) | 7.40% |

The most common failed commands in losses were `CARE` 403, `WATER` 324,
`HARVEST` 277 and `COLLECT_FERTILIZER` 218. These are spread over games and
time; the control failure rate is slightly higher. The fixed rival's failure
rate is not a fair policy comparison because its recorded actions execute in
our changed shared-market/game state. Our `PASS` rate similarly does not prove
that another productive task was reachable and funded on those turns.

**Decision: reject a generic invalid-command repair at the predeclared gate.**
Neither ten lost routes with ≥100 failures nor a 2% aggregate loss failure
rate occurred. No policy candidate, `main.py` change, or Kaggle upload from
this diagnostic. The larger tomato/wool production gaps remain a portfolio
and funded-schedule research problem; fixed tapes are diagnostic only.
