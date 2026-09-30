# Final minimal route repair — 29 September 2026

Standalone candidate: [main_candidate_minimal_repair_20260929_cb76fbc4.py](H:/hackathan/main_candidate_minimal_repair_20260929_cb76fbc4.py).

SHA-256: `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`. Frozen promotion gates passed: **False**. Root main.py promoted: **False**.

## Changes

Start from exact 4eeac9c3 (September 27). Preserve its opening and core queue, quantity, purchase and market logic. Add complete schedule choices for Brunch/Brunch, Brunch/Smoothie, and IceCream/Pet after both shops have appeared. Their earlier schedule prefixes match the original. Carry forward the existing repair that retains executable planting requests when there are too few seeds for all requested plantings.

This avoids the later automatic donor opening and production-fingerprint controllers. It does not select routes using opponent identities or game seeds. A final explicit entrypoint ensures the file loader selects the intended agent.

## Current saved top100

Same frozen snapshot for every file: September 29, 11:03:38 UTC / 16:33:38 IST. The 100 teams correspond to 91 distinct episodes. Each tape is tested in both seats. Fixed actions cannot react to changed markets; this is development and regression evidence, not independent validation.

| Version | Top10 W/D/L | Top20 W/D/L | Top100 W/D/L | Seat win rate | Both-seat team wins |
|---|---:|---:|---:|---:|---:|
| 4eeac9c3 | 11/0/9 | 27/0/13 | 141/0/59 | 70.5% | 70/100 |
| ae349d83 | 7/0/13 | 23/0/17 | 131/0/69 | 65.5% | 65/100 |
| repair v1 | 11/0/9 | 27/0/13 | 147/0/53 | 73.5% | 73/100 |
| repair v2 | 11/0/9 | 27/0/13 | 145/0/55 | 72.5% | 72/100 |
| repair v3 | 11/0/9 | 27/0/13 | 145/0/55 | 72.5% | 72/100 |

V3 recovered **9/9** regression teams; lost 4ee seat wins: **0**. Every V3 game clean: True.

The complete table includes every changed and unchanged team: [TOP100_CASES_V3.md](TOP100_CASES_V3.md).

## Reacting-policy tests

Original native shop generation, hidden configuration seed, both seats, and four reacting opponents. Win = 1 point; draw = 0.5. The bootstrap keeps both seats and all four opponents in each complete seed block.

### Selected development cases

| Opponent | V3 W/D/L | 4ee W/D/L | Point difference |
|---|---:|---:|---:|
| 4ee | 2/14/0 | 0/16/0 | +1 |
| ae349 | 6/10/0 | 6/8/2 | +1 |
| c95 | 16/0/0 | 12/0/4 | +4 |
| v35 | 16/0/0 | 14/0/2 | +2 |

Totals: V3 **40/24/0**; 4ee **32/24/8**. Win-point-rate change **+12.5000 percentage points**; 95% whole-seed bootstrap interval **[+0.0000, +31.2500]**. Stage passed: **True**.

Development seeds were chosen from earlier experiments. Only the 64 source-bound 4ee baseline rows were reused, with original engine labels and provenance. Every V3 game was newly run.

### Independent 32-seed native confirmation

| Opponent | V3 W/D/L | 4ee W/D/L | Point difference |
|---|---:|---:|---:|
| 4ee | 8/48/8 | 6/52/6 | +0 |
| ae349 | 17/42/5 | 19/38/7 | +0 |
| c95 | 62/0/2 | 60/0/4 | +2 |
| v35 | 62/0/2 | 62/0/2 | +0 |

Totals: V3 **149/90/17**; 4ee **147/90/19**. Win-point-rate change **+0.7812 percentage points**; 95% whole-seed bootstrap interval **[-1.5625, +3.1250]**. Stage passed: **False**.

New route activations in confirmation: **8/256 candidate games** across **2/32 seed blocks**. Partial planting activated in 4 games.

| New route pair | Activated games | W/D/L |
|---|---:|---:|
| BRUNCH_SPOT / BRUNCH_SPOT | 8 | 4/2/2 |
| BRUNCH_SPOT / SMOOTHIE_SHOP | 0 | 0/0/0 |
| ICE_CREAM_SHOP / PET_CAFE | 0 | 0/0/0 |

The three nonzero fresh seed blocks show different mechanisms: 12929312 improved by two points with the planting repair active and no new route active; 12929315 lost two points under Brunch/Brunch against the two source-style opponents; 12929324 gained two points under Brunch/Brunch against C95. Thus the same complete route helped one opponent setting and harmed another. The other two new shop-pair routes did not activate in this fresh block. See `v3_fresh_outcome_changes.json` for every flipped outcome and telemetry.

Complete native outcomes: [REACTIVE_CASES_V3.md](REACTIVE_CASES_V3.md).

## Earlier loss30 and top20 archive

These are older saved tapes, distinct from today’s top20. They measure retained and lost earlier fixes. They are not fresh validation. Each fraction below counts matchups won in both seats; W/D/L counts individual games.

| Group | Uploaded ae349 | V1 | V2 | V3 | V3 W/D/L |
|---|---:|---:|---:|---:|---:|
| loss30 | 27/30 | 23/30 | 22/30 | 3/30 | 6/0/54 |
| pet_public_win_control | 1/1 | 1/1 | 1/1 | 1/1 | 2/0/0 |
| top20 | 19/20 | 19/20 | 18/20 | 17/20 | 34/0/6 |

Every archive comparison: [ARCHIVE_CASES_V3.md](ARCHIVE_CASES_V3.md).

## Execution and recommendation

Native parity: 14 cases, passed=True. Four direct/file-loader games passed=True, with exact actions and rewards in both seats. Loader callable: `kaggle_minimal_route_repair_entrypoint`. Minimum remaining overage: 60.000000 seconds.

V3 did not pass every prospectively frozen promotion gate. Keep root main.py at 4ee and retain this standalone candidate as experimental. Do not claim independently established overall superiority.

V1 and V2 were both rejected because their untouched native blocks were worse than 4ee. Their reports and exact files remain preserved. No Kaggle access or upload occurred during these repairs. No local test can provide a reliable rating forecast or top10 probability.

## Reproduce

`build_v3.py`; `finish_v3.py` (sequential saved, development, native parity, loader, native confirmation, archive); `write_report_v3.py`.

Use the project Python runtime from this directory. The shared game lock prevents concurrent coordinators. All plans, source manifests, jobs, JSONL results and SHA-bound receipts are preserved. The prior main.py backup is `H:/hackathan/main_before_regression_repair_20260929_4eeac9c3.py`.
