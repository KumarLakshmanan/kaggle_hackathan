# Exact shed projection audit — 2026-09-29

## Decision

Reject an exact-worker replacement for `_queue_stock` as a game candidate on
this evidence. The helper and the embedded native worker transition predicted
the same shed contents on every observed turn in the completed 40-job panel.
An exact-stock patch therefore has no demonstrated market prediction or
action change to test. Keep the current helper; do not spend a fresh game block
on this change unless new traces contain a concrete counterexample.

This is a mechanics audit of fixed diagnostic traces, not policy validation.
The panel receipt itself marks these games `fixed_replay_diagnostic_only`.

## Evidence and method

- Candidate source: `main_candidate_minimal_repair_20260929_cb76fbc4.py`,
  SHA-256 `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`.
- Inputs: all 40 rows with both players `DONE` in
  `diagnostics/fresh90_improvement_20260929/cb76_top20_jobs_results.jsonl`.
  Each corresponding gzip was exhausted (including CRC/trailer validation),
  and contained 719 newline-terminated decisions for steps 0–718. No trace was
  rejected. That is 28,760 recorded decisions across 20 team fixtures and
  both seats; those fixtures reuse 15 distinct public episodes, so fixture
  traces are correlated.
- `_queue_stock` is at candidate lines 62–80. Native worker semantics are
  `_apply_unit_action` in `diagnostics/physical_route_rollout_20260928/native_core.py:230`
  (the same function embedded in the candidate at line 534).
- On every decision, worker actions that could change shed stock were
  identified from the four native shed-access tiles. For the 4,406 decisions
  containing `PICKUP`, `DROP`, or `PLACE` there, I cloned the observed farm and
  private state and applied all final worker actions in order with the source's
  exact `_PLANT_CORE["_apply_unit_action"]`, using board size 10, day
  `step // 24`, 24 turns per day, and shed capacity 100. The remaining 24,354
  decisions contained no shed-changing worker action; the native transition
  leaves shed contents unchanged on those turns.
- The normalized shed maps from `_queue_stock` at line 62 and the native
  transition matched on all 4,406 relevant decisions: **0 mismatch turns, 0
  item deltas**. The main helper handles pickup quantity/availability and
  capacity-limited drops as the native transition does.
- There is a source-level animal `PLACE` edge worth watching: `_queue_stock`
  skips all animals, while native `PLACE` falls through to a shed drop if the
  standing tile is not a matching empty structure. The traces contained 84
  animal `PLACE` actions at shed-access tiles, all with inventory; all 84 were
  on matching empty structures and placed into them. No realized fallback
  shed drop occurred.
- Since the stock forecast is unchanged on every final action, replacing it
  with the exact native transition cannot change the market simulator inputs
  for these turns. The actual candidate telemetry confirms the ordering layers
  were active across the 40 seats (3,710 base queue reorder turns, 2,213
  purchase queue reorder turns, and 1,887 iterated queue reorder turns), but
  an exact-stock replacement would still feed them the same shed forecast.
  No extra market simulations were needed after observing zero stock deltas.

## Reproduction

Run the read-only audit from the workspace root:

```powershell
python diagnostics/fresh90_policy_design_20260929/audit_queue_stock_traces.py `
  > diagnostics/fresh90_policy_design_20260929/audit_queue_stock_traces_results.json
```

The output JSON includes the per-job trace manifest and SHA-256 hashes,
completion/validity counts, action categories, mismatch counts, and any market
scenario effects. The script checks the source hash before running.

## Promotion record

- **Candidate:** replace `_queue_stock` with the exact native worker
  transition.
- **Outcome:** rejected as a game candidate for this panel; no executable
  stock mismatch or changed market forecast was observed.
- **Promotion:** none. No shared agent source, harness, or research memory was
  changed.
