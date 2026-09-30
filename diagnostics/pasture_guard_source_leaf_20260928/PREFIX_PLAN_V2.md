# Frozen native prefix proof — pasture guard/source leaf, harness v2

This separately bound harness version corrects the original runner's
observation-1 instrumentation. The initial town state has no unlocked shop;
v2 records `first_unlocked_shop: null` and `leaf_key72: null` there. It checks
the Brunch leaf key only at observation 72, when the frozen affected fixtures
have a revealed shop. The candidate policy and original plan, runner,
manifest, original plan, and empty progress file remain unchanged and
hash-bound as lineage.

## Fixed proof jobs

- Five successful donor controls, both seats: candidate versus exact a44.
  Require identical actions and complete observations at observations 0–72;
  compare original telemetry after excluding only the new public
  `bridge_rival_pastures` field. The saved a44 full-control trace is bound for
  each fixture/seat. The source-only leaf must stay inactive.
- THIRD and ChrisTu, both seats: candidate versus exact32e source. Require
  exact turn-0 common action and exact turn-1 source-restoration action,
  plus matching own physical/private state after each opening turn. Require
  exact own physical/private state at observations 2–72. Cash, shared-market
  and action differences after the opening are recorded in separate ledgers.
- At observation 1, the candidate must select `source` in all four
  pasture-bearing contexts. The runner independently recomputes public rival
  hands and pasture count from the live observation and compares them with
  the frozen feature row and bridge telemetry. An empty shop list is recorded
  as a pre-shop state and is valid at this observation.
- At observation 72, `BRUNCH_SPOT|M8+|C>S|G+ -> 113332529` must activate on
  both THIRD seats only. The runner recomputes the public shop and leaf
  features from the live observation, compares them with the frozen feature
  row and candidate telemetry, and requires the exact key. It must remain
  inactive on both ChrisTu seats and all five donor fixtures.
- Policy, bridge guard, source guard, collision, procurement and engine errors
  must be zero. The policies must remain `ACTIVE` at observation 72; the
  runner records 72 transitions and does not request a terminal outcome.

The fourteen jobs each use one fixture and seat, the same cached initial frame,
and the bound opponent action tape. Each worker process handles at most four
jobs; exactly one worker is required. The fixture seed is used only in the
native environment harness; policy configuration receives `seed = None`, and
fixture identity is not passed to the policy.

## Freeze and verify

Create the v2 manifest without running a simulation:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix_v2.py freeze
```

Verify the v2 manifest and its original-freeze lineage without simulation:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix_v2.py verify
```

After review and scheduling, run the fourteen native prefix jobs with one
worker:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix_v2.py run --workers 1
```

The v2 runner writes only `prefix_v2_progress.jsonl` and
`prefix_v2_results.json` inside this study directory, with its own
`prefix_v2.lock`. It does not consume or overwrite the original prefix
checkpoint. A prefix pass does not satisfy the separate 14-game full-outcome
pilot gate.
