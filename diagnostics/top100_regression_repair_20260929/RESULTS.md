# Regression-repaired main.py — 29 September 2026

Exact candidate: `2c02f9f9898dc393f8798f1d51a3a4c26a4bf1ddf862770ef66be159d61d6e13`.
Standalone file: [main_candidate_regression_repair_20260929_2c02f9f9.py](H:/hackathan/main_candidate_regression_repair_20260929_2c02f9f9.py).

The candidate restores the original 4ee opening, removes the automatic donor switch based on rival worker count, and restores the original Brunch/Pizza route. Other source-route, planting, hiring and production repairs remain.

Frozen promotion gates passed: **False**. Root main.py promoted: **False**. No Kaggle access or upload occurred during this repair.

## Current saved top-100 panel

Leaderboard snapshot: 2026-09-29 11:03:38 UTC / 16:33:38 IST. This panel informed the repair and is development evidence. Every opponent is a fixed public replay action tape; it cannot react to changed markets or our moves. Each team is tested in both seats.

| Policy | Top 10 W/D/L | Top 20 W/D/L | Top 50 W/D/L | Top 100 W/D/L | Top 100 both-seat wins |
|---|---:|---:|---:|---:|---:|
| 4eeac9c3 | 11/0/9 | 27/0/13 | 71/0/29 | 141/0/59 | 70/100 |
| ae349d83 | 7/0/13 | 23/0/17 | 67/0/33 | 131/0/69 | 65/100 |
| new 2c02f9f9 | 11/0/9 | 27/0/13 | 73/0/27 | 147/0/53 | 73/100 |

All 200 repaired-policy games were DONE/DONE/720 with zero recorded candidate errors. All nine regressed team pairs were recovered and all 141 old-policy seat wins were preserved. The new policy adds six wins over 4ee. Relative to ae349 it recovers 18 seats and loses two seats against Attention Is All You Seed, for a net +16 wins.

## Fresh reacting comparisons

The policies played the same seeds, opponents and both seats, with original endogenous shops and hidden configuration seeds. Wins earn 1 point; draws earn 0.5. Seed blocks keep both seats and all four opponents together. The screen used native transitions; the independent confirmation used the full native framework.

### 8-seed screen

| Reacting opponent | New W/D/L | 4ee W/D/L | New minus 4ee points |
|---|---:|---:|---:|
| 4ee | 3/10/3 | 1/14/1 | +0 |
| ae349 | 1/14/1 | 3/10/3 | +0 |
| c95 | 16/0/0 | 12/0/4 | +4 |
| v35 | 16/0/0 | 14/0/2 | +2 |

Totals: new **36/24/4**, 4ee **30/24/10** (W/D/L). Paired win-point-rate change: **+9.38 percentage points**. Whole-seed bootstrap 95% interval: **[-6.25, +31.25] percentage points**. Gate passed: **True**.

### 16-seed native confirmation

| Reacting opponent | New W/D/L | 4ee W/D/L | New minus 4ee points |
|---|---:|---:|---:|
| 4ee | 2/22/8 | 2/28/2 | -3 |
| ae349 | 4/26/2 | 10/20/2 | -3 |
| c95 | 32/0/0 | 28/0/4 | +4 |
| v35 | 32/0/0 | 32/0/0 | +0 |

Totals: new **70/48/10**, 4ee **72/48/8** (W/D/L). Paired win-point-rate change: **-1.56 percentage points**. Whole-seed bootstrap 95% interval: **[-7.81, +4.69] percentage points**. Gate passed: **False**.

## Earlier saved 30-loss/top-20 archive

This supplementary 102-case diagnostic checks whether restoring the older opening undoes earlier targeted repairs. It is not fresh validation.

| Group | Previous ae349 both-seat wins | New both-seat wins | New W/D/L |
|---|---:|---:|---:|
| loss30 | 27/30 | 23/30 | 46/0/14 |
| pet_public_win_control | 1/1 | 1/1 | 2/0/0 |
| top20 | 19/20 | 19/20 | 38/0/2 |

Changed archived seat outcomes: 8. All archived cases clean: True. Full changes are recorded in `archive_v1_receipt.json`.

## Execution verification

All 14 completed native parity cases matched candidate/rival rewards, outcomes, statuses, frames and complete candidate telemetry. Four direct/file-loader runs covered both seats; every action and final reward matched. The intended callable was `kaggle_a44_pet_market_gate_entrypoint`. Minimum remaining overage was 59.824822 seconds.

The first native-verifier attempt had an `expected` metadata-key collision with the shared helper after gameplay; it produced no accepted result rows. The verifier was fixed and the entire 14-case check rerun. Original code and failure metadata are preserved under `revisions/native_expected_key_collision/`; no candidate change or gate waiver was involved.

A positive result against these local reacting policies would support an incremental improvement on this opponent set; it cannot determine a live Kaggle rating or guarantee top 10. The two prior uploaded ae349 copies are identical; new code here has not been uploaded.

## Files and reproduction

`build.py` created the exact candidate from the downloaded ae349 source. `run_saved.py v1 pilot` then `run_saved.py v1 full` produced the regression ledger. `run_reactive.py v1 screen`, `verify_native.py v1`, `verify_loader.py v1`, and `run_reactive.py v1 confirm` produced reacting and operational results. `run_archive.py v1` checks the earlier archive. Completed checkpoints are preserved; never change source bytes and reuse a prior ledger.

Evidence: `PLAN.md`, `ARCHIVE_CHECK_PLAN.md`, `manifest_v1.json`, all `*_receipt.json` files, `loader_v1.json`, and the detailed JSONL game ledgers. The old root file is backed up as `H:/hackathan/main_before_regression_repair_20260929_4eeac9c3.py`.
