# Repaired candidate V2 — 29 September 2026

File: [main_candidate_fixed_20260929_6cd6ff9e.py](H:/hackathan/main_candidate_fixed_20260929_6cd6ff9e.py). SHA-256: `6cd6ff9eed407f3c31c2b432c37da8b3ece8f703a2932d5293f9b93b7e060df3`.

Frozen promotion gates passed: **False**. Root main.py SHA-256: `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.

## What changed

Relative to uploaded ae349d83: restore the original source opening; remove the automatic donor switch based on rival worker count; restore original routes for Brunch/Pizza, Yarn/Farmers, and Farmers/Pizza. Retain the other source scheduling, planting, hiring, production, and market repairs. The second repair differs from V1 only in two mapping assignments. No opponent name or game seed is used as a strategy condition.

V1 recovered nine saved matchup regressions but failed independent native confirmation, so it was rejected. Its result and every case remain in [RESULTS.md](RESULTS.md). V2 was frozen before the new confirmation block.

## Current saved top-100 comparison

Snapshot: 2026-09-29 11:03:38 UTC / 16:33:38 IST, downloaded before this repair. Each team is tested in both seats. The 100 teams correspond to 91 distinct public episodes. Fixed replay actions cannot react to our policy changes. This panel informed the repair and is development evidence.

| Policy | Top 10 W/D/L | Top 20 W/D/L | Top 100 W/D/L | Seat win rate | Teams won in both seats |
|---|---:|---:|---:|---:|---:|
| September 27: 4eeac9c3 | 11/0/9 | 27/0/13 | 141/0/59 | 70.5% | 70/100 |
| September 29 upload: ae349d83 | 7/0/13 | 23/0/17 | 131/0/69 | 65.5% | 65/100 |
| Repair V1: 2c02f9f9 | 11/0/9 | 27/0/13 | 147/0/53 | 73.5% | 73/100 |
| Repair V2: 6cd6ff9e | 11/0/9 | 27/0/13 | 145/0/55 | 72.5% | 72/100 |

Recovered original regression teams: 9/9. Lost original 4ee seat wins: 0. All 200 candidate games clean: True.

## Reacting opponents

All opponents react to each move; shops evolve under the native game rules; configuration seeds are hidden. Both seats and four opponents stay together in each bootstrap seed block. Win = 1 point, draw = 0.5. Cash margin is diagnostic.

### Development: eight previously observed seed blocks

| Opponent | V2 W/D/L | 4ee W/D/L | Point change |
|---|---:|---:|---:|
| 4ee | 3/12/1 | 1/14/1 | +1 |
| ae349 | 9/6/1 | 9/4/3 | +1 |
| c95 | 16/0/0 | 8/0/8 | +8 |
| v35 | 16/0/0 | 14/0/2 | +2 |

Total W/D/L: V2 **44/18/2**; 4ee **32/18/14**. Win-point rate change +18.7500 percentage points. 95% whole-seed bootstrap interval [+6.2500, +37.5000] percentage points. Frozen stage gates passed: **True**.

The 64 exact 4ee baseline rows were reused from source-bound V1 ledgers with their original engine labels. All 64 V2 rows were newly run. These selected diagnostic seeds do not establish independent improvement.

### Independent confirmation: 16 untouched native seed blocks

| Opponent | V2 W/D/L | 4ee W/D/L | Point change |
|---|---:|---:|---:|
| 4ee | 1/30/1 | 1/30/1 | +0 |
| ae349 | 1/30/1 | 1/30/1 | +0 |
| c95 | 32/0/0 | 32/0/0 | +0 |
| v35 | 26/0/6 | 32/0/0 | -6 |

Total W/D/L: V2 **60/60/8**; 4ee **66/60/2**. Win-point rate change -4.6875 percentage points. 95% whole-seed bootstrap interval [-9.3750, +0.0000] percentage points. Frozen stage gates passed: **False**.

## Earlier saved public-loss and top-20 archive

| Group | Uploaded ae349 both-seat wins | V1 both-seat wins | V2 both-seat wins | V2 W/D/L |
|---|---:|---:|---:|---:|---:|
| loss30 | 27/30 | 23/30 | 22/30 | 44/0/16 |
| pet_public_win_control | 1/1 | 1/1 | 1/1 | 2/0/0 |
| top20 | 19/20 | 19/20 | 18/20 | 36/0/4 |

These older tapes are regression diagnostics, not a second independent leaderboard or a reason to conceal trades between opponent groups.

## Execution and decision

All 14 native parity checks passed: True. Four direct/file-loader games passed: True; complete action and reward equality: True. Kaggle loader selected `kaggle_a44_pet_market_gate_entrypoint`. Minimum remaining overage: 59.219831 seconds.

The candidate did not pass every frozen promotion gate. Keep it as an experimental standalone version and retain 4ee as root main.py; do not call it an independently proven replacement.

No Kaggle access or upload occurred during this repair. These local results cannot predict a Kaggle rating or top-10 probability. Backups preserve the exact previous root file and both repair candidates.

## Reproduction and complete cases

`build_v2.py`; `run_saved.py v2 full`; `run_reactive_v2.py v2 screen`; `verify_native.py v2`; `verify_loader.py v2`; `run_reactive_v2.py v2 confirm`; `run_archive.py v2`; `write_report_v2.py`.

Run these sequentially from this directory with the project Python runtime. The game coordinators share `diagnostics/.shared_game_run.lock`. Do not edit a candidate and reuse its completed checkpoints.

See [every top-100 matchup](TOP100_CASES_V2.md), [every fresh confirmation scenario](REACTIVE_CASES_V2.md), and [every archive case](ARCHIVE_CASES_V2.md). All original ledgers, SHA-bound receipts, and frozen PLAN_V2.md remain beside this report.

### Checkpoint recovery

The confirmation process stopped for an unconfirmed reason after 71 clean saved games. The coordinator and workers were verified absent, the stale lock was preserved, and every saved row was validated against the frozen job/source hashes before resuming only missing jobs. No candidate, seed, result, or criterion was changed. See `confirmation_interruption_20260929.json` and `interrupted_lock_20712.json`. Resume command: `finish_v2.py --resume-confirm`.
