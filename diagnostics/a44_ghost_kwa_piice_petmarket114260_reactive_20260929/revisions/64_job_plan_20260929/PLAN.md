# Fresh reactive qualification pilot: exact 6a + Pet Cafe

## Candidate and prior evidence

Test the exact Pet Cafe candidate
`ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe`
against exact 6a parent
`6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`.
The candidate bytes are the 6a agent followed by the frozen step-72 Pet Cafe
gate for route `113517834`. Root `main.py` is an opponent only; it is not
edited.

The completed saved fixed-tape panel had 100 seats, no W/D/L regressions
against 6a, both `live-114260122` target seats changing from losses to wins,
27/30 loss-fixture sweeps, and 19/20 top20 sweeps. It finished all 104 games
DONE/DONE at 720. Its receipt still says `passed: false` because the static
expected WHEAT value at step 72 was stale on both `live-114274897` seats:
the trace census recorded 9,975, while the exact 6a native state had 9,980.
The Pet gate stayed inactive and those two outcomes matched 6a. Keep that
completed receipt unchanged; the fresh run below records the actual step-72
features from each new game.

Bound prior evidence: receipt
`ec2f45acfa6a7988868bb13e657a639e546ced46d148c15456e78679b0d7dcb5`,
outcomes `bb1ae8bd2f3a9b892508ce77f101397596fd4d73868791425e6d667fb0bff97a`,
and exact 6a baseline receipt
`f5b962c853b8812f231c85af41a608e6df1b1ede99dd14c22a2bcaebb10bc8b2`.

## Fresh original-shop panel

Use seeds `2026092911`–`2026092914`, selected as a fixed block with no
matching seed literals found in existing diagnostics. Do not screen or replace
seeds based on shops, triggers, or outcomes. The installed Kaggle
Environment 1.32.7 creates each full episode and its endogenous shop sequence
from the seed; no saved opponent tapes or replay states are used.

For each seed, test both candidate versions in both seats against each of
these four reacting opponents:

| Opponent | Exact local file | SHA-256 |
| --- | --- | --- |
| Current root agent | `main.py` | `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed` |
| 6a pasture parent | `diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py` | `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc` |
| Public Ahmed V35 | `diagnostics/public_ahmed_v35_20260927/public_v35_main.py` | `294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d` |
| Public C95 | `diagnostics/public_rayk_top_meta/public_c95_main.py` | `489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb` |

Each parent/candidate comparison uses the same opponent, seed, and candidate
seat. Reload all policy modules for each game. There are 64 full native games:
4 seeds × 4 opponents × 2 versions × 2 seats. The game engine seed is hidden
from both policies by the bound qualification helper. Record step-1 shop
context and the candidate's step-72 gate telemetry, but never filter or
resample games by either.

## Frozen pass rule

Score outcomes as 1 point for a win, 0.5 for a draw, and 0 for a loss. The
primary comparison is candidate points versus exact 6a points, paired within
the same seed, opponent, and seat. Require:

1. Exactly 64 distinct jobs complete DONE/DONE at 720 frames, with no
   candidate or opponent errors.
2. Candidate calls stay below the existing 1,000 ms screening ceiling.
3. The Pet telemetry is internally consistent: zero gate errors; when active,
   route `113517834` and 647 active calls; when inactive, empty route and zero
   active calls. Record the observed WHEAT stock without imposing 9,975.
4. Candidate win points are no lower than 6a against each individual
   opponent, and pooled candidate points exceed pooled 6a points.
5. At least three of the four whole-seed paired point deltas are nonnegative.

Report W/D/L, per-opponent and pooled points, per-seed deltas, own/rival cash,
cash margins, max call time, shops, and activation count. Cash margins and
Pet activation are diagnostics, not substitute outcomes or separate pass
gates. A pass earns only a separately frozen larger confirmation; four seeds
are too few for promotion or a leaderboard claim.

## Runner and boundary

Use the already exercised `diagnostics/opening_probe_v2_20260928/qualify.py`
`play` helper, which loads each policy afresh, masks the seed in policy
configuration, calls the installed `make('kaggriculture')` and `env.run`,
and records both policies' errors and candidate telemetry. The engine source,
helper, local run lock, policies, candidate, parent, route source, and prior
receipts are hash-bound in `frozen_manifest.json`. The staged runner is
one-shot, serial, and requires `--root-release`; a partial run is incomplete
and is not resumable or countable.

This is a local original-framework reacting-policy pilot. It is not a Kaggle
upload, a submission file-loader check, or promotion evidence. No games or
transitions were run while staging this plan.
