# Retry a funded scheduled land purchase — 2026-09-27

Native DECEM diagnosis: the selected route requests southwest land on
turn 217, but cash is only 1,936 before a ten-coin seed purchase. The
2,000-coin land order fails and is never retried. Later wheat tasks target
LOCKED tiles; feed harvests fail and animals escape. This is an observed
execution failure, not an inference from final margin alone.

Start from frozen candidate `3cc0f69f...`, not the rejected wheat patch.
Use the currently selected route's past land orders to determine intended
land ownership, capped at four quadrants. When ownership is behind, retry
one BUY_LAND with enough current cash for its price, conservative existing
orders, and a 500-coin reserve. Respect ten market orders; stop retries at
turn 600. Keep unit actions and all existing orders unchanged. Record
retry count and exceptions. No opponent identity or seed conditions.

Development: DECEM in both seats, original endogenous shops. Require all
DONE, activation, and improved own cash and margin. If passed, compare all
50 fresh saved routes, both seats, against the frozen 42/50 source. Require
strictly more sweeps and at most one lost source sweep before confirmation.

Confirmation, frozen before any outcomes: native seeds 2633400–2633415,
both seats, old and new versus unchanged main and new versus reacting old.
Require all DONE, no aggregate win-point regression versus main, at least
10/16 paired win points against old, and at least four activated pairs.
Sparse activation requires a separately frozen conditional sample, not
promotion from the replay panel. Verify file-loader behavior in both seats
before promotion. Do not edit main or upload at the development stage.
