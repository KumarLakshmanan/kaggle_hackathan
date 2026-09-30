# Frozen native prefix proof — pasture guard/source leaf

This is an engineering proof only. It does not run any 720-turn outcome game.
The candidate, static pool, 208 public-feature rows and static-preflight
receipt are already frozen. This prefix plan is separately frozen with its
own generated `prefix_manifest.json` before the runner starts.

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
  pasture-bearing contexts and report the correct public pasture count.
  The runner independently recomputes public hands and pasture count from the
  live observation and compares both with the frozen feature row and bridge
  telemetry.
  Guard refusals, bridge failures, policy errors and procurement/guard errors
  must all be zero.
- At observation 72, `BRUNCH_SPOT|M8+|C>S|G+ -> 113332529` must activate on
  both THIRD seats only. The public leaf key is recomputed from the live
  observation and must match the candidate's recorded key. It must remain
  inactive on both ChrisTu seats and all five donor fixtures.

The fourteen proof jobs are each one fixture and seat. A job runs the
candidate and its fixed reference from the same cached initial frame and
opponent action tape through observation 72. Each process handles at most
four jobs; the runner requires exactly one worker. Inputs use the fixture
seed only in the native environment harness. The policy receives
`configuration.seed = None`, and no fixture identity is passed to it. Both
policies must remain `ACTIVE` at observation 72; the runner records 72
transitions and does not request a terminal outcome.

## Freeze and run

Generate the immutable bindings after reviewing the static freeze:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix.py freeze
```

Verify them without simulation:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix.py verify
```

After root review and scheduling, run only the 14 native prefix jobs with one
worker:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix.py run --workers 1
```

The runner writes prefix-specific progress and receipt files only inside
this study directory and holds an exclusive run lock while appending progress.
A prefix pass does not satisfy the separate 14-game full-outcome pilot gate.
