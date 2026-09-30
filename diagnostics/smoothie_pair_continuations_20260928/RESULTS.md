# Smoothie compatible-continuation screen — results

Completed 2026-09-28 18:47 UTC (2026-09-29 00:17 Asia/Kolkata) from the frozen study inputs.

## Execution and integrity

- Resumed with `python -X utf8 diagnostics\smoothie_pair_continuations_20260928\study.py run --workers 1` after inspecting the runner. It validates checkpoint rows, requires unique keys, and schedules only keys absent from `screen.jsonl`.
- The initial checkpoint had 55/132 valid unique keys. The resumed run appended the remaining 77 keys; final ledger has exactly 132/132 unique, valid rows. The command exited 0.
- All 11 routes were evaluated against the same six frozen fixtures in both seats. Every row is DONE/DONE at 720 frames, with zero candidate errors, 647 production-leaf turns, and 575 production-pair turns.
- Verified the 14 bound input/helper/source hashes, all 11 candidate hashes, the four passing preflight prefix checks, and the pool hash before resuming. Rechecked the final screen and selection against those frozen bindings.
- Pool SHA-256: `b117609154d03f727fa683703a290a6ac1cec360ff34621d37bb6124fdd520f7`.
- Preflight SHA-256: `8af7db353a299ae94a634b22fd69c8827b24367ab6b4dd697bdbcda09ee7f7d7`.
- Final JSONL SHA-256: `4f6ab4a6124406e9d9023e5cc964b4e4792ea8549ac569bcdaa1c92a8af06693`.
- Final screen JSON SHA-256: `221fcab550707148908fa8678c93b62da9b31fd28751266dff30282c687f8519`.
- Selection JSON SHA-256: `3e8ac95239b1842f5ec8ad3657fa535d6964013eed84991e155b658d5803cada`.

The stale lock named PID 25168. Both process lookups were empty before archive, and a second Win32 process lookup was empty immediately before the move. The exact lock was preserved as `screen.lock.stale-20260928T183531294Z.json`; its SHA-256 is `e32887af4df269d7060af1db0b0826873a8e0eee1ae8d00649f2528a76e7b40e`. Its timestamped PID-absence receipt is `stale_lock_receipt_20260928T183531294Z.json` (SHA-256 `13f5b06e4b6e1058b7fde4156e2f56ea5218e2a7aa3120a99c643053f2d13d0d`). The archived lock bytes were hash-verified; no stale lock was deleted. The runner removed its new lock on clean exit.

## Frozen selection gate

Family 0 (`SMOOTHIE_SHOP|M8+|C>S`) passes the predeclared screen gate: every observed shop pair has an eligible continuation that retains all source-winning seats, and the target `live-114223338` is rescued in both seats. The selected map preserves 10/10 source-winning seats across the six fixtures and produces 12/12 wins, versus 10/12 source wins. Across all 12 seat comparisons, selected margins improve by 51,530 coins in total.

| Fixture | Observed shop pair | Route | Source margin/seat | Selected margin/seat | Margin delta, both seats |
|---|---|---:|---:|---:|---:|
| chocolat | SMOOTHIE_SHOP / BAKERY | 113639519 | 6,019 | 11,582 | +11,126 |
| forever young (target) | SMOOTHIE_SHOP / SMOOTHIE_SHOP | 113639519 | -10,466 | 313 | +21,558 |
| yfy | SMOOTHIE_SHOP / BRUNCH_SPOT | 113340658 | 10,562 | 1,245 | -18,634 |
| c_fxy | SMOOTHIE_SHOP / FARMERS_MARKET | 113639519 | 872 | 14,384 | +27,024 |
| Rio | SMOOTHIE_SHOP / ICE_CREAM_SHOP | 113340658 | 1,472 | 330 | -2,284 |
| Argyris Anastopoulos | SMOOTHIE_SHOP / PIZZA_SHOP | 113618016 | 9,814 | 16,184 | +12,740 |

The generated screen candidate is `candidate_selected_family0.py`, SHA-256 `b4af93f784800d309cf64475ec91eed0c4ad5e009f3140f6d3894dec6ff6f768`. Its six selected rules are recorded in `selection.json`. Target margin changes from -10,466 to +313 per seat, a +10,779 change per seat.

## Decision

**Pass this finite continuation-selection gate; advance only to the exact full affected-panel check. Do not promote the candidate.** These are saved-replay outcomes, so they are development evidence rather than independent validation. The frozen plan still requires full affected-panel composition checking, followed by reacting/native gates. Generalization to unobserved shop pairs remains unproven; the generated candidate retains the medoid for those pairs.
