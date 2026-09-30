# Top-three single-tape controls (frozen before pilot)

## Purpose and source freeze

Build exactly three standalone diagnostic controls from the frozen
`diagnostics/fresh90_refresh_20260929/routes/development_latest/summary.json`
panel, choosing leaderboard ranks 1, 2 and 3. The summary SHA-256 is
`9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c`.
Leaderboard CSV snapshot: 2026-09-29 17:04:23 UTC; collection receipt:
17:04:25 UTC. Replay engine: 1.32.7.

Selection is solely ascending frozen rank among the 100 latest-development
rows. Candidate rank1 is DECEM (episode115321748, seat0); rank2 is DSM
(episode115323250, seat0); rank3 is Boey (episode115323250, seat1). No public
W/D/L, scores, reserved episode tiers, or game results enter selection.

## Candidate contract

Each candidate is exactly one complete 719-action tape from its selected
source route, with no switches, alternate tape, shop history, opponent lookup,
seed lookup, or identity-dependent logic. The wrapper uses the existing
observation-step behavior: read `observation.step` when available, otherwise
use the call counter; convert to integer with call-counter fallback; clamp to
0..718; return a deep copy of the indexed action. Export both `agent` and the
existing final callable `kaggle_fresh_opening_router_entrypoint` with the same
`(observation, configuration=None)` interface.

## Static comparison

Before any pilot, count action orders in offsets 0..23 only (day0). For market
orders report investment types `HIRE`, `BUY_LAND`, `BUY_ANIMAL`, `BUY_SEED`,
and `BUY_SEEDS`; report `BUY_PRODUCT`/`SELL` separately. Count crop-specific
seed purchases and `PLANT` commands in farmer/hand actions. Compare ranks 1–3
against each of the six tapes in the three rejected families (65/77, 16/83,
30/86), using only recorded actions. This is schedule description, not proof
that orders succeeded in the replay.

## Verification and limits

Check each source row, full route action hash, raw replay and archive hashes,
replay statuses/version/frame count, public-state/index hashes, source seat and
team mapping, and indexed action hash. Parse/compile/load each generated source
and verify the embedded action payload exactly matches the corresponding
source tape; confirm the two callables exist with the expected signatures.
Do not run an agent inside a game or simulator, execute policy actions, contact
Kaggle/network, inspect reserved episodes, alter any source artifact outside
this directory, or update `main.py`/`agent.md`. The parent task owns all game
pilots and their gates.
