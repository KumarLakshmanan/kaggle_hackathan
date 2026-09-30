# 6d pasture guard and source Brunch leaf — prefix preflight

## Frozen parent and candidate scope

The parent is the exact 6d Goose4 + Smoothie candidate at
`diagnostics/a44_goose4_smoothie_source_20260929/candidate.py`, SHA-256
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.
Build an isolated derivative from those bytes. The only selector change is
observation 1: retain `shared151` iff public rival hands are at least five and
the public rival pasture count is zero; otherwise select `source`. Append only
the frozen source-only Brunch goose leaf
`BRUNCH_SPOT|M8+|C>S|G+ -> 113332529` at observation 72. The source selector
and route leaf use public observations. No identity, seed, cash, seed stock,
or private data enters either predicate. Donor schedules and the existing
Goose4 and Smoothie rules remain intact.

## Static trigger census

Bind and reconcile all 208 seat rows from the exact 6d `pair_rows.json` and
the pasture study's public step-1 feature rows. Count the original and guarded
branches on every row; identity labels only explain the resulting panel rows.
The source row at observation 72 is recorded as parent-branch provenance only.
The prefix jobs below must generate their own keys while executing the 6d
source branch. They must not infer a source-branch key from a saved
`shared151` trajectory or from the earlier cb5/a44 prefix result.

## Four-job source-prefix proof

Run exactly four jobs: `live-114274897` (THIRD) and `public-win-114193811`
(ChrisTu), each in seats 0 and 1. For each job, compare the derivative against
the exact 6d source branch, using the same frozen initial state, seed,
configuration, and opponent action tape on both sides. The reference is the
original 6d bytes with only the step-1 dispatcher expression replaced
in-memory by `branch = 'source'`; this makes the comparator the same 6d policy
on its existing source path. It is not a separately tuned or saved policy.

The runner advances only observations 0 through 72. It requires:

- Exact complete observations and actions on steps 0 through 71 between the
  derivative and forced-source 6d reference. Both policies must agree on the
  common step-0 action and source-restoration step-1 action.
- The derivative's step-1 runtime public values must match the frozen feature
  row: hands and pasture count. Its request and selected branch must both be
  `source` for all four jobs; the bridge common, guard-refusal, source-guard,
  and policy error counters must remain zero.
- The candidate's route map must equal the 6d base route map after step-0
  reset. At observation 72 the runner computes the key from that actual
  source-branch observation, records all public inputs, and verifies the
  route-map delta separately.
- Both THIRD seats must produce the exact Brunch key, activate route
  `113332529` once, and change only the Brunch route-map descendants plus the
  Brunch base key. Actions may differ only at step 72; record both actions
  and allow no route other than `113332529` to be committed.
- Both ChrisTu seats must compute a nonmatching Brunch key, leave the route
  inactive, make no route-map change, and match the forced-source reference
  action at step 72 as well as all earlier steps.
- Both policies remain active at observation 72. There are no policy,
  collision, procurement, bridge, leaf, or native-engine errors. The existing
  procurement counters are recorded and must remain zero.
- The exact replay, opponent action tape, trace provenance, cached input and
  initial-state bindings, engine source, native state helpers, run-lock helper,
  parent candidate, derivative, build script, layer, runner, and this plan
  match their frozen hashes.

These are prefix engineering gates only. No full-game outcome rows run in
this study. The single-worker prefix command is staged but requires root
review of the frozen candidate and manifest first:

```powershell
python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/prefix_runner.py run --workers 1
```

Static-only build, freeze, and verification commands:

```powershell
python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/build_preflight.py build
python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/prefix_runner.py freeze
python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/prefix_runner.py verify
```
