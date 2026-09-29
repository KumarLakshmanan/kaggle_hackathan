# a44 kwa wheat-zero route splice

## Frozen scope

This is an isolated static candidate built by appending one source-only
observation-72 selector to the exact integrated 6d candidate
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.
It does not derive from or modify root `main.py`.

The selector requires all four conditions at observation 72:

1. The a44 bridge selected the `source` branch.
2. The public key is `BRUNCH_SPOT|M8+|C<S|G0`.
3. Public rival tiles contain zero WHEAT crop plots.
4. The observation step is exactly 72.

On a match, the candidate commits route `113535489` before making the same
single parent call that the integrated 6d agent uses. It reads no fixture ID.
Outside that predicate this wrapper does not change the route map or mutate the
integrated parent's returned action.

## Frozen static corpus and gates

The bound corpus is the integrated 6d package's 208 trace-backed feature rows:
60 loss30 seats, 40 top20 seats, and 108 public-win seats. The preflight
rehashes every trace, reads only its step-72 observation, recomputes the public
leaf and rival wheat-plot count, and joins outcomes from the bound a44 control
receipt. Required results:

- Exactly two trigger rows: `live-114227779`, seats 0 and 1, loss30.
- Zero triggers in top20 and public-win.
- Every same-leaf a44-winning control has wheat plots and stays inactive.
- The public predicate and route are identical in both seats; no fixture ID is
  present in the candidate selector.
- The integrated parent is called exactly once on every wrapper invocation.
- The existing Goose4 reset restores the saved source route map and FARMICE
  tape at step 0. The new wrapper resets only its own state. The reused source
  commit changes BRUNCH descendants and its fallback; it leaves other shop
  namespaces and FARMICE unchanged for this BRUNCH route.

## Proposed outcome check after static review

If this package passes static preflight, a six-game fixed replay is the next
diagnostic: `live-114227779` and the same-leaf winning controls
`live-114236633` and `live-114257327`, both seats each. The wheat-positive
controls must not activate. For the target, record route activation, final
outcome, terminal status, frame count, candidate errors, and the exact a44
suffix behavior (including the animal-cash wrapper). The existing route result
is not an outcome receipt for this exact composition.

## Frozen one-shot runner gates

`run_six.py` fixes the job order to the three fixtures above, seats 0 then 1,
with one sequential worker. It reserves the workspace-wide exclusive lock
`diagnostics/.shared_game_run.lock` and writes under the fixed directory
`runs/six_game_run_001/`. A run directory that already exists is a hard error:
there is no resume mode or ambiguous checkpoint recovery. Started/finished
attempts and completed game rows go to separate append-only `attempts.jsonl`
and `outcomes.jsonl` files; the one-time run manifest and final receipt use
exclusive-create semantics.

Before any result is observed, the manifest freezes these gates:

- All six games finish DONE/DONE at 720 frames with no candidate errors.
- Kwa wins both seats, has positive margin in both, and improves both paired
  margins over the exact integrated-6d `combined_results.json` rows.
- Kwa reports the source branch, exact public key, zero rival wheat plots,
  route 113535489, 647 active turns, and zero wrapper errors in both seats.
- The four wheat-positive control seats do not activate and match the bound
  exact-6d combined result fields exactly: result, margin, both rewards, both
  statuses, and frame count.

The run is explicitly fixed-tape diagnostic evidence. The baseline is the
hash-bound integrated-6d combined receipt; its reused rows remain rows of that
receipt with their decision-equivalence metadata intact. Static preflight
checks the six-job coverage, baseline bindings, exclusive lock path, append
semantics, no-resume rule, and these exact outcome gates without invoking the
runner.

No game or simulator was run to create this package. The static report is not
promotion evidence. Keep root `main.py` and `agent.md` unchanged; any future
replay needs its own explicit run plan and result receipt.

## Reproduction

From the workspace root:

```powershell
python -X utf8 diagnostics/a44_kwa_wheat_zero_20260929/build_candidate.py
python -X utf8 diagnostics/a44_kwa_wheat_zero_20260929/static_preflight.py
```

Both commands are deterministic file/hash/feature checks. Neither starts the
Kaggle environment or invokes a policy action.

The actual six-game runner is staged at
`diagnostics/a44_kwa_wheat_zero_20260929/run_six.py`; it was not invoked while
freezing this package.
