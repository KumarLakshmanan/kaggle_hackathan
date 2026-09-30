# Mirror pure-sale protection pilot — frozen 2026-09-26 17:14 UTC

The current agent protects the first planned sale in its 12-turn physical-mirror
advance window, because that sale might fund a later market purchase. This
isolated candidate keeps the protection when the planned sale turn contains
any other market-order type. When that turn contains only `SELL` orders and
the farms visibly mirror, it permits the existing advance routine to sell
the stock earlier. All production, routing, non-mirror sale rules, and the
24-turn strawberry window remain unchanged. The candidate uses only current
observation and its own built-in public action tape; no opponent identity,
episode ID, seed, or future shop is a deployment input.

Development panel: all 29 losses and the ten smallest-margin wins in the
latest 100 public games of submission 56572390, frozen by
`extract_recent_mirror_dev.py`. Replay the current source and the candidate
against each rival's public fixed actions on the original seed in both seats.
Require exact baseline reproduction of the live terminal cash in the original
seat; all games `DONE`; at least five original-seat loss rescues; no more than
one original-seat control win reversal; and positive aggregate candidate own
cash delta across the 39 original seats. A fixed-route margin gain driven
only by suppressing rival cash is insufficient. Any failed requirement rejects
the pilot before broader testing.

If the development gate passes, test fresh native reacting-agent seeds
2612400–2612415 in both seats against the current uploaded source, requiring
positive paired-seed majority, positive aggregate margin, no execution errors,
and a bounded call time. Check both seats on the previously sensitive len8487
route and the full physical-mirror-eligible subsets of the older and refreshed
top-100 panels, with no control-win reversal. Verify Kaggle file-path loading
before any local promotion, and back up the exact current `main.py` bytes.
The saved replays are development/regression data, not independent validation.
No new Kaggle upload is authorized.
