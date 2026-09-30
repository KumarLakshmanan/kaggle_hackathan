# Purchase and iterated queue candidate 4eeac9c3

Updated 2026-09-27T18:09:54.503813+00:00.

The candidate adds purchase ordering and two passes of queue reordering to
the uploaded c68 agent. It keeps the physical schedules and market quantities.
It excludes the planned-funding component that failed its coverage test.

## Development pilot

| Reacting opponent | Candidate W/D/L |
|---|---:|
| c68 | 16/0/0 |
| 43d | 15/0/1 |
| 3bd | 12/0/4 |

All 48 complete: True. Recorded errors: 0.
Frozen pilot gate passed: True.

## Recorded regression panels

The recent panel is the 27 September 11:37 UTC leaderboard snapshot.
It contains 99 external teams and one separate self-control. These are
recorded moves, not the opponents' private reacting policies.

| Panel | Prior both-seat wins | New both-seat wins | New seat W/D/L |
|---|---:|---:|---:|
| Recent top 50 | 36/50 | 36/50 | 72/0/28 |
| Recent top 100, external | 73/99 | 73/99 | 146/0/52 |
| Original saved top 50 | 44/50 | 44/50 | 88/0/12 |

All 300 complete: True. Recorded error rows: 0.
Previously winning seats lost: 0.
Frozen regression gate passed: True.

No external recorded win/loss outcome changed. Cash margins can still differ.

## Independent reacting-policy confirmation

Untouched seeds 2713000–2713015, both seats and original native shops.
Agents cannot see the configured seed. All 256 comparisons were retained.

| Reacting opponent | Old c68 W/D/L | New candidate W/D/L |
|---|---:|---:|
| c68 | 0/32/0 | 32/0/0 |
| 43d | 0/0/32 | 32/0/0 |
| 3bd | 0/0/32 | 28/0/4 |
| 1f | 32/0/0 | 32/0/0 |

Paired-seed 95% bootstrap interval for pooled win-point gain: [0.546875, 0.625].
Both seats and all references stay together in each sampled seed.
All complete: True; recorded errors: 0.
Frozen confirmation gate passed: True.

## File-loader verification

Passed: True. Selected callable: `kaggle_purchase_iterated_entrypoint`.
Direct execution and Kaggle file loading match every action and both cash
totals in both seats. Native runtime budgets remain nonnegative.

## Promotion and upload

Submission: **56609430**.
Status: SubmissionStatus.COMPLETE at the 2026-09-27 18:09:54 UTC official snapshot.
Submitted source SHA-256: `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Remote validation all-action and both-cash parity: **PASS**. In validation episode
114183268, the exact uploaded file reproduces all 719 actions for both seats and
both 104,134 coin final rewards with native seed 0.
The latest live snapshot contains 84 completed public episodes, all downloaded
without an outcome filter: **54 wins, 30 losses, 0 draws**. All 85 replay hashes
(including validation) verify; no replay paths or episode IDs failed. The live
leaderboard row is rank 136, team Score 2572.1, LastSubmissionDate
2026-09-27 13:10:15 UTC. Submission publicScore is 2551.5. The top-10
objective remains unmet. The team score equals the older c68 submission
56602057's current publicScore 2572.1, so the team rank is not a score gain
from 4ee.
Previous main backup: `H:\hackathan\main_before_purchase_iterated_20260927_c68fa46f.py`.
Uploaded backup: `H:\hackathan\main_uploaded_purchase_iterated_20260927_4eeac9c3.py`.
The current user request authorized this single upload; authorization is consumed.

## Decision

Accept qualification for promotion; upload status is recorded separately.

## Interpretation

Passing these stages does not establish a top-10 leaderboard rank or victory
against every top-50 or top-100 team. Live ratings must be observed on Kaggle.
The previous standalone-candidate rejections remain part of the research record.

Evidence: PLAN.md, build_manifest.json, pilot.json, panels.json, confirmation.json,
loader_parity.json, promotion_receipt.json, and
`diagnostics/new_live_56609430_20260927/RESULTS.md`, `cohort_171158.json`,
`snapshot_174722/summary.json`, `delta_174722.json`, and
`validation_parity.json` there.
