# Static preflight audit — 29 September 2026

Status: **not ready for outcome games**. No simulation was run and no frozen
artifact was changed.

## Source and layer findings

- The named uploaded source exists and hashes to
  `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`.
  Root `main.py` is a different artifact and is not the source for this plan.
- `layer.py` captures the pre-bridge source callable, restores the route map
  at step 0, commits all BRUNCH route-map descendants before calling the
  source at step 72, and only wraps the source bridge. This wiring is
  structurally consistent with a source-only Brunch leaf.
- The pasture helper is currently unused. The layer resets
  `_BRIDGE_STATS['bridge_rival_pastures']` to zero, but never calculates or
  records the count. In the frozen source, bridge selection at step 1 still
  chooses `shared151` solely from `hands >= 5` (line 1104). A builder must
  patch that exact predicate to also require zero public rival PASTURE tiles
  and write the observed count to bridge telemetry; appending `layer.py`
  alone does not implement the guard.
- The cited component receipt and candidate are real and hash correctly:
  conditional receipt
  `63bc163b401ec5704f264b200d578aa24dd0bd5b93d8bd005081b4f0ab2a54f3`,
  candidate
  `0eb77448c82e08b114749076c7589755522fdb890537dc974e8f5c248505106d`.
  They were built against source `367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0`,
  not a44. Treat them as component provenance only; the plan's a44-bound
  feature, route, reset, and prefix checks are still required.

## Missing frozen bindings

The pasture study directory has only `PLAN.md`, `REVIEW.md`, and `layer.py`.
It has no builder/study script, candidate, fixture pool, 208-row a44 feature
receipt, control bindings, preflight receipt, or frozen helper/reader/cache
manifest. The component's 208 features are bound to its 367 source and do not
substitute for the required a44 traces. Consequently, the fixed 14-game
pilot is not yet reproducible from a frozen pool and should not start.

Before any pasture outcomes, build and hash-bind the exact a44 source, the
step-1 patch, `layer.py`, the candidate, all required target/public fixture
traces and source controls, the 208 a44 observation-72 feature rows, and the
native helper/cache. Then run the specified static preflight and prefix/state
checks and freeze their receipt. This audit did not inspect or modify root
`agent.md`, `main.py`, or any other study's frozen files.
