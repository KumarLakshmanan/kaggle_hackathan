# Purchase and iterated queue candidate 4eeac9c3

Updated 2026-09-27T13:10:38.194297+00:00.

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
Status: SubmissionStatus.PENDING.
Submitted source SHA-256: `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Remote all-action and both-cash parity: False.
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
loader_parity.json and, after upload, promotion_receipt.json and validation_parity.json.
