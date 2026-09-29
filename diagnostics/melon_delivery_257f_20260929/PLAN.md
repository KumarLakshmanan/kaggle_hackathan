# 257f melon-delivery paired-margin experiment

Status: **frozen before outcomes. Candidate rebase is isolated. No outcomes are authorized until the four native prefixes pass.**

## Frozen identities and baseline

- Incumbent: exact last-uploaded experimental candidate `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`, at `main_candidate_pet_source_guard_20260929_257f941d.py`.
- Isolated proposal: `candidate_257f_melon_delivery.py`, SHA-256 `a8174509cd2679578869b3090a9137d136e22a4e752c2bc9dc822b86a1aade25`.
- Proposal builder: `build_candidate.py`; it checks the exact incumbent hash, appends the reviewed a44 wrapper in a private namespace, and preserves the incumbent's original source bytes as an exact file prefix.
- Root research `main.py` is the separate 4ee baseline and must not change.
- Exact 257f saved goal panel: 27/30 both-seat prior-loss wins and 19/20 both-seat top20 wins; 92 wins / 0 draws / 8 losses over 100 goal-panel seats. Two public-win control seats are also part of the 102-row preservation cohort.
- Exact-257f baseline receipts: `diagnostics/margin_target_257f_20260929/baseline_receipt.json` (offhand and Unknown Mother-Goose) and `narrow_win_baseline_receipt.json` (two other closest wins). Both receipts are SHA-bound in `frozen_manifest.json`.
- Initial four native baseline captures show both seats on both planned fixtures match the selector at step 713. Their configs use board size 10, shed capacity 100, and 10 market order slots; offhand MELON quote is 133 and Unknown Mother-Goose quote is 158. The all-panel incidence is not assumed: `capture_incumbent_census.py` must find exactly these four selector rows before treatment outcomes.

## Objective and predeclared target

Improve paired cash margin while preserving wins. The a44 idea is rebased only to two hash-bound observations on exact 257f:

- `live-114271958` / offhand: +670 margin in each seat; must remain two wins and gain strictly positive margin in each seat.
- `top20-08-Unknown Mother-Goose-114272024`: +4,471 margin in each seat; protected top20 control must remain two wins and have nonnegative margin change in each seat.

Other notable 257f narrow wins are +313 in both seats for `live-114223338` and +244/+6,475 for `live-114267572`. Their step-713 states do not match this selector; this route is not being generalized to them.

These are saved-action tapes used as regression controls, not independent validation and not evidence of rating gain.

## Intervention

At step 713/day 29/hour 17, activate only if exactly one own hand is at `[1,4]`, its incumbent command is WATER, its private inventory contains at least 12 MELON, and public MELON quote is at least 100. Require actual supplied board size 10, a valid shed capacity that fits the existing shed plus full hand inventory, and a one-player route latch. Move EAST at steps 713–715. At step 716, only if the live state is `[4,4]` with exactly MELON 12 + FERTILIZER 1, DROP and submit SELL MELON 12 under the wrapper's order/capacity guards; otherwise use its guarded fallback. A player-keyed route latch scopes the continuation and clears at step 0 or by step 716.

The intervention gives up the incumbent's observed six-unit harvest at step 714. No cash or margin gain is assumed. No quote ceiling or opponent fingerprint may be added after seeing outcomes.

## Frozen gates

1. Before treatment outcomes, run native step-by-step prefixes on exact 257f for both seats of offhand and Unknown Mother-Goose, feeding every counterfactual state into a fresh parent-policy call. Check supplied configuration; step-713 trigger/action; per-player latch; actual position and inventory through steps 714–716; returned action shape; exact hand route; live competing deposits, shed capacity, market order slot and duplicate-sale guards; and post-step-716 DROP/order effects. Stop the outcome-free prefix after applying step 716 and recording the native state for step 717; do not read terminal rewards or margins. Interleave the two player seats in a prefix test to verify latch isolation/reset. Require no policy/native errors and exactly the planned hand/action/order differences from the parent on each modified step. Stop on any mismatch.
2. Before treatment outcomes, use the frozen incumbent-only `capture_incumbent_census.py` across all 102 saved rows. It must identify exactly four selector activations: offhand and Unknown Mother-Goose, both seats. This census stops at the step-713 observation before applying an intervention or measuring results. If any other row activates, stop and revise plan plus prefix coverage before treatment outcomes.
3. If prefixes and incidence pass, run all 102 frozen preservation rows with exact 257f controls and the same opponent tapes. Require exact returned-action parity at every step for every non-trigger row, including exact own/replay rewards and margin there; unchanged incumbent telemetry except the new melon diagnostic counters, checked against the exact 257f parent on each same observation and against saved baseline telemetry on non-trigger rows; preserve every existing W/D/L result; retain at least 27/30 loss sweeps and 19/20 top20 sweeps; zero native errors; DONE/DONE at frame 720. On all four target runs, record policy actions at steps 713–718, allow only the planned step-713–716 route/order differences, require the route latch cleared after step 716, and verify steps 717–718 return the exact 257f parent action on the same counterfactual state; step 719 is the terminal frame and receives no policy call.
4. Offhand must remain a win in both seats with strictly positive `candidate_margin - 257f_margin` in both seats.
5. Unknown Mother-Goose must remain a win in both seats with nonnegative margin change in both seats.
6. Report own/replay rewards, seat margins, paired margin deltas, W/D/L, and activation/guard telemetry separately. Saved tapes do not establish independent gain.
7. Only after all saved-panel gates pass, run a fresh, predeclared original-shop paired diagnostic against two distinct local reacting opponents: `diagnostics/public_ahmed_v35_20260927/public_v35_main.py` (SHA-256 `294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d`) and `diagnostics/public_rayk_top_meta/public_c95_main.py` (SHA-256 `489f5d197527f107027626cce79d850fd2ca90edd43d94384b849b6511e27bdb`). Use the fixed seed block `2026093001`–`2026093004`. The repository-wide scan `rg -l "2026093001|2026093002|2026093003|2026093004" -g '!diagnostics/melon_delivery_257f_20260929/**' .` returned no hits in pre-existing files. Do not screen or replace seeds based on shops, triggers, or outcomes. Compare the treatment candidate with exact 257f, using the same opponent, seed and candidate seat for each pair; run each arm in both seats under `kaggle_environments` 1.32.7 with `episodeSteps=720` and the engine's other defaults. This is 2 arms × 2 opponents × 4 seeds × 2 seats = 32 full games. Require all games DONE/DONE at frame 720, no policy errors, tested-candidate calls below 1,000 ms, no pairwise W/D/L regression, and nonnegative aggregate paired-margin change. Record selector activation and all W/D/L and margin results separately. If the selector never activates, the treatment effect remains unvalidated. This small fixed-seed block is a diagnostic, not promotion or leaderboard evidence.

A failure rejects this isolated candidate. Keep `main.py` and Kaggle untouched.
