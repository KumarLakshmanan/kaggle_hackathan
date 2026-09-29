# Frozen native prefix proof, exact-a44 comparator (v4)

V4 preserves v1, v2, and v3 and does not edit the candidate policy. It fixes the
v3 reference mistake: the candidate's `source` fallback is its exact a44 base,
so all four affected jobs compare directly with
`diagnostics/upload_adaptive_donor_20260928_a44c8c2c/main.py`.

## Inputs and reused evidence

- Candidate SHA is bound to the frozen pool and must equal
  `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`.
- Active reference SHA is exact a44:
  `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`.
- The four fresh source-fallback jobs are THIRD and ChrisTu, both seats. Their
  fixtures, seeds, replay frames, opponent tapes, feature rows, native engine,
  helpers, and historical a44 dispatcher trace hashes are bound in the v4
  manifest.
- The reference policy is loaded from that exact-a44 file and calls its pinned
  `_BRIDGE_SOURCE_AGENT` function directly. The frozen feature rows show that
  the a44 outer dispatcher selected `shared151` in all four contexts, while
  the candidate's public pasture guard selects `source`. Comparing with the
  outer dispatcher would test a different branch and cannot establish source
  fallback compatibility. The saved a44 traces therefore remain provenance;
  they are not claimed as forced-source trace replays.
- V4 reuses the ten passing v3 donor result rows only after checking the
  candidate SHA, exact-a44 comparator SHA, byte-identical donor job
  definitions, all required passing checks, full observation/action equality,
  saved-trace reproduction, active status, and inactive source leaf. The v3
  manifest, runner, plan, progress ledger, and result receipt are hash-bound.
- The old exact32e comparator remains recorded as historical v3 provenance;
  no v4 job uses it.

## Frozen gates

- For all four affected jobs, candidate and exact-a44 full observations must
  match at every observation step 0 through 72.
- Candidate and exact-a44 actions must match at steps 0 through 71. On both
  THIRD seats, step 72 may differ only at that one action; the complete
  candidate and reference actions are recorded beside the candidate leaf
  telemetry. On both ChrisTu seats, actions must also match at step 72.
- The candidate must request and select the source branch at observation 1;
  runtime rival hands and pasture counts must match the bound public features.
- Shared source-policy telemetry at observation 1 must match exact a44. The
  candidate-only bridge selector fields must report the bound `source` branch,
  observed rival hands and pasture count, and zero errors. The three
  candidate-only `guard_leaf_*` fields must remain inactive at observation 1
  and match the intended step-72 leaf result.
- At observation 72, the candidate must record the actual public leaf key.
  Route `113332529` must activate exactly once on both THIRD seats, and remain
  inactive on both ChrisTu seats and the five donor fixtures.
- The ten reused donor rows must retain their v3 saved-trace reproduction
  checks. For affected rows, the direct exact-a44 source entrypoint is the
  reference; own physical/private state must match at observations 2 through
  72. Both policies must remain `ACTIVE`; policy, guard, collision,
  procurement, and engine error counters must be zero.
- V4 uses one worker. After review, its `run` phase executes only the four
  fresh affected prefixes and reuses the ten bound v3 donor rows. It does not
  run complete outcome games and does not itself authorize the 14-game pilot.

## Static freeze and verification

These commands create and verify the v4 manifest and a static freeze receipt;
they run zero simulator jobs:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix_v4.py freeze
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix_v4.py verify
```

The static receipt records the v4 manifest hash, input bindings, reuse checks,
four fresh job identities, and `simulator_jobs_run: 0`. The future result path
is separate and remains absent until an authorized run.

## Run command for root review

Only after the frozen manifest and static receipt are reviewed, run the four
affected prefixes sequentially with one worker:

```powershell
py -3 diagnostics/pasture_guard_source_leaf_20260928/prefix_v4.py run --workers 1
```

V4 writes its own `prefix_v4_progress.jsonl`, `prefix_v4_results.json`, and
`prefix_v4.lock`. It does not change any v1-v3 file or the candidate.
