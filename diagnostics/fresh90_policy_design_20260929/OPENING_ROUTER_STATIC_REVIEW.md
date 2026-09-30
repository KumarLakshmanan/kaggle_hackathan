# Fresh opening routers: static review

Date: 2026-09-29/30
Scope: source and policy-loader review only; no games run and no candidate/root files changed.

## Frozen pilot sources

The three source hashes agree with the current validation receipt:

- `candidate_01_family01_rank65.py`: `d37c271ae00c4c773cc44fff45a210512df69643f348245281b6ff4708b0ebb2`
- `candidate_02_family02_rank16.py`: `1e98e564c0a221ce988416dba5a4d97848c07a8094757158321eacfb926080ce`
- `candidate_03_family03_rank30.py`: `7bbcdea8747a61a867b8934059c6e277c1319e1b04b645559bb7bea97258df26`

The standalone sources expose `agent` and `kaggle_fresh_opening_router_entrypoint`; their decoded tapes contain only `rank`, `shop_history`, and `actions`. Selection reads `step` and currently visible `town.unlocked_shops`, with no seed, rival identity/actions, score, outcome, or future shop query. Step 0 resets `_ACTIVE_RANK` to the family base. `_CALLS` is not reset, but real observations provide `step`, so that counter is only fallback behavior when step is absent. The frozen validation receipt records AST/compile/import and first-action checks, source replay/sidecar provenance, and zero games.

All eligible switches occur after exact complete-action compatibility through the switch boundary:

- Family ranks 65/77: the first physical and raw market-list divergence is step 148. The route can switch at step 144 based on the second visible shop; actions through step 147 are identical.
- Ranks 16/83 diverge at step 83; ranks 30/86 at step 77. Their only possible switch is step 72, after identical actions/market lists through step 71.

This makes the physical projection's exclusion of `SELL` and `BUY_PRODUCT` benign at the actual eligible switch boundaries in these three frozen families. After each family's first physical divergence, the router cannot switch to its sibling. Candidate selection among ranks is therefore a one-time visible-shop fork at step 72 or 144, not a stale later override.

## Reproducibility defect

`build_candidates.py:273-296` strips each `packed_data` tape down to `rank`, `shop_history`, and `actions`, then line 293 requests provenance keys such as `tape_id`, `team`, and `episode_id` from those stripped objects. Calling `build_candidates.main()` as currently written will raise `KeyError` at that manifest comprehension. `regenerate_minimal_candidate_sources.py` is the successful final source builder: it checks the frozen plan and development summary hashes, looks up selected source rows, and verifies route action hashes before rebuilding the same minimal payload. The validation script separately checks replay/sidecar provenance. This is a regeneration/reproducibility defect, not a blocker for the already frozen and hash-verified pilot sources; document the working builder or repair it after the pilot.

## Market-helper transplant assessment

A future separate candidate can use the raw family router as the base schedule, then add the queue engine/stock forecast, sell-order queue, quantity adjustment, purchase-order queue, iterated queue, and partial-plant wrapper. Safe wiring must set the base agent once and explicitly keep it as the raw forecast parent. Mechanical copying is unsafe: V2 reassigns `_QUEUE_PARENT` to `_farmice_schedule` at line 334, and `_ITERATED_QUEUE_RAW` captures that pointer at line 437. The route `DATA`, `_FARMICE_TAPE`/schedule, route-pair selectors, and their telemetry wrappers must stay out.

The helper scope is limited: queue layers reorder or retune existing market orders; partial planting only removes over-requested plant actions when seed stock is positive but less than the simultaneous demand. They do not repair worker/crop schedule commitments, add missing seed orders, or address zero-seed planting. The queue forecasts use idle/mirror/raw schedule scenarios and cannot model every reacting rival. With raw family pilots at 15/46, 8W/2D/46, and 23/46 versus the incumbent's 32/46, and no trace evidence tying the losses to market-queue failures, there is not a falsifiable basis to expect this transplant to close the gap. Recommendation: stop this architecture rather than spend a second pilot on a broad helper transplant.

## Reproducibility patch and command

The minimal repair is to change the provenance manifest comprehension in `build_candidates.py` to iterate over `members`, the original loaded tape records, instead of `packed_data`, which has already been reduced to the three executable fields:

```diff
-                for tape in packed_data],
+                for tape in members],
```

This preserves minimal executable payloads while reading provenance from the full source records. It is a one-line source fix only; it does not alter route selection or embedded candidate bytes.

The already-used minimal regeneration command, from the workspace root, is:

```powershell
python diagnostics/fresh90_current_opening_20260929/regenerate_minimal_candidate_sources.py
```

That command rebuilds candidate sources and updates `family_analysis.json`; it was documented here but not run during this review. The candidate/validation files were left unchanged.
