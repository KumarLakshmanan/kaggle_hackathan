# Three-arm reactive qualification pilot: exact 6a + Pet Cafe

## Purpose and evidence boundary

This is a fresh, diagnostic-only comparison of the new exact 6a + Pet Cafe
candidate against the exact last uploaded policy and its exact 6a parent. The
primary question is whether the new candidate earns more win/draw/loss points
than uploaded `a44c8c2c`. The separate incremental comparison asks whether
the Pet layer improves on 6a. Four fresh seeds are a screening block: even a
pass earns a larger independent confirmation, not promotion or a top-10
claim.

The completed saved fixed-tape panel for the candidate had 100 seats, no W/D/L
regressions against 6a, both `live-114260122` target seats changing from losses
to wins, 27/30 loss-fixture sweeps, and 19/20 top20 sweeps. All 104 games
finished DONE/DONE at 720. Its receipt remains unchanged and says
`passed: false` because the expected step-72 WHEAT value on both
`live-114274897` seats was stale: the trace census recorded 9,975, while the
exact 6a native state had 9,980. The Pet gate stayed inactive and those two
outcomes matched 6a. The saved panel compared against 6a; it contains no
evidence that the candidate beats the last uploaded policy.

Prior evidence is bound by the frozen manifest: candidate receipt
`ec2f45acfa6a7988868bb13e657a639e546ced46d148c15456e78679b0d7dcb5`, outcomes
`bb1ae8bd2f3a9b892508ce77f101397596fd4d73868791425e6d667fb0bff97a`, and exact
6a baseline receipt
`f5b962c853b8812f231c85af41a608e6df1b1ede99dd14c22a2bcaebb10bc8b2`.

The earlier, pre-outcome 64-job two-arm plan is preserved byte-for-byte under
`revisions/64_job_plan_20260929/`. Its snapshot manifest records its file
hashes and confirms no games or transitions were run for that version.

## Exact policy arms

| Arm | Exact local file | SHA-256 |
| --- | --- | --- |
| Last uploaded policy | `diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py` | `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f` |
| Incremental baseline | `diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py` | `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc` |
| New candidate | `diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/candidate.py` | `ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe` |

The new candidate is byte-for-byte the 6a parent followed by the frozen Pet
layer. Its route source is
`diagnostics/public_90_research_20260928/candidates/PET_CAFE_113517834.py`,
SHA-256 `cd6b3ba4526599e93d1125e2143fffb639ce7eebed1d0bf41171be18173f57f8`.
The Pet gate uses public step-72 observations. The exact 6a source, Pet layer,
route source, and candidate hash are all bound by the manifest.

## Fresh original-shop reacting panel

Use the fixed seed block `2026092911`–`2026092914`, retained from the earlier
staged plan after its static scan found no matching seed literals in existing
diagnostics. Do not screen or replace seeds based on shops, triggers, or
outcomes. Run each arm against each of four exact local reacting opponents in
both seats:

| Opponent | Exact local file | SHA-256 |
| --- | --- | --- |
| Current root policy | `main.py` | `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed` |
| 6a pasture policy | `diagnostics/a44_ghost_kwa_piice_pasture_isolation_20260929/candidate.py` | `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc` |
| Public Ahmed V35 | `diagnostics/public_ahmed_v35_20260927/public_v35_main.py` | `294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d` |
| Public C95 | `diagnostics/public_rayk_top_meta/public_c95_main.py` | `489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb` |

Every policy arm is played against every opponent, seed, and candidate seat:
3 arms × 4 opponents × 4 seeds × 2 seats = 96 full games. Pair comparisons
are grouped by seed, opponent, and candidate seat. For the seed-level screen,
both seats and all four opponents are grouped together, so the four seed
blocks—not the 32 seats—are the uncertainty units. These are fresh native
original-shop episodes, not fixed-tape replays. Same-seed games share the
initial seed but are not identical tapes: actions and market response can
change the episode.

## Frozen W/D/L criteria

Score win = 1, draw = 0.5, loss = 0. Primary is new candidate versus exact
uploaded `a44c8c2c`; incremental is new candidate versus exact 6a. Apply each
comparison separately, with paired rows matched on seed, opponent, and
candidate seat:

1. All 96 unique jobs finish DONE/DONE at 720 frames, with zero candidate or
   opponent policy errors and every tested policy call below 1,000 ms.
2. For each opponent, candidate points are no lower than comparator points.
3. Pooled candidate points exceed comparator points.
4. At least three of the four whole-seed point deltas are nonnegative.

The primary result passes only if its four W/D/L criteria and all technical
checks pass. The Pet-vs-6a result is reported separately. If no candidate game
activates the public Pet gate, label that incremental comparison
`inconclusive_no_activation`; do not let it change the primary comparison.
If it activates at least once, report whether its same four W/D/L criteria
pass, but treat that as a screening result only. A candidate pass earns only a
larger independent confirmation; no leaderboard rank or promotion claim is
authorized by this pilot.

The frozen runner records W/D/L, per-opponent and pooled points, seed deltas,
both rewards, cash margin, shops captured at step 1, and maximum tested-policy
call time across all 96 games. Margins and activation are diagnostics, not
pass criteria.

## Pet telemetry and execution

The bound `diagnostics/opening_probe_v2_20260928/qualify.py` helper runs the
installed Kaggle Environment 1.32.7 `make('kaggriculture')` and `env.run`,
reloads modules for each game, masks the episode seed from both policies, and
returns the actual candidate module telemetry after each game. The runner's
bound telemetry adapter serializes those observed candidate values for all 32
new-candidate jobs. It checks zero gate errors and consistency between the
observed active flag, route `113517834`, and active-step count: 647 when active,
zero when inactive. It records observed WHEAT without expecting 9,975 or
9,980. The adapter does not infer activation from a helper or source rule.

Builder, runner, actual telemetry adapter, helper, engine source, run lock,
three arms, four opponents, route source, prior receipts, and preserved 64-job
snapshot are hash-bound in `frozen_manifest.json`. The runner is serial,
one-shot, and writes only to the four explicit paths listed there. Its default
invocation performs static verification only; running games requires
`--root-release` after the root task coordinates simulator use. No games or
transitions were run while staging this plan.
