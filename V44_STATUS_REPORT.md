# V44 guarded strategy review

## Decision

Keep the current `main.py` / V43 policy as the control. Keep V44 as an isolated candidate until the external strategy review decides how to handle the remaining public-state ambiguity. Do not promote V44 by overwriting the control yet.

## Architecture implemented

`main_v44_guarded.py` wraps the existing V43 policy instead of replacing it wholesale:

- The route choice is made once at the exact step-88 boundary from public observations only: unlocked shop, visible opponent farm composition, public money, and public hand count.
- The wrapper temporarily installs the selected route into the shared V43 router only for the base-policy call, then restores the previous selector in `finally`. This prevents cross-agent and cross-benchmark global-state contamination.
- The optional stateful residual policy is warmed from turn 0, but it can replace V43 only after a strict step-88 public gate: the configured shop is `PIZZA_SHOP`, opponent hand count is at least 8, public money is at least 400, melons are at least 10, and wheat is at least 6.
- Actions are deep-copied and validated for farmer shape, hand count, market order count, positive quantities, and supported order shapes.
- If the policy raises, recovery uses the last validated unit plan and strips capital orders; it does not use a broad silent PASS fallback as the primary path.
- The terminal collision overlay is optional through `V44_MODE`; the benchmarked candidate used `terminal_collision`.

## Validation evidence

All benchmark runs used engine `1.32.7` and completed every game.

| Panel | Result |
|---|---|
| Current top-10 control | 66/108 wins, 33/54 paired wins, mean margin +12,270 |
| V44 strict warm current top-10 | 74/108 wins, 37/54 paired wins, mean margin +15,572.84; mean call 2.25 ms; max 475 ms |
| Kaito adaptive league | 16/16 wins, 8/8 paired wins |
| main_v16 adaptive league | 16/16 wins, 8/8 paired wins |
| Arun market adaptive league | 16/16 wins, 8/8 paired wins |
| Dani relay adaptive league | 14/16 wins, 7/8 paired wins; only pair loss was seed 129679470 at -12,801 |
| Recent exact top-20 holdout | 56/58 wins, 19/29 paired wins; one paired loss of -1,606 |
| Older exact top-20 holdout | 15/58 wins, mean margin about -4,683; this matches fresh control and shows no regression |
| V44 self-play | 4/4 paired seed outcomes exactly net to zero; all games completed |

The strict gate removed the broad residual policy's severe Dani regression at seed 246802468. The isolated selector also removed the earlier benchmark state leak caused by mutating the shared V43 route selector across candidate modules.

## Remaining limitation

Seeds `681236343` and `129679470` are indistinguishable at the step-88 public snapshot used by the route gate: both expose the same first shop and the same relevant visible portfolio/count features. The refined branch changes the paired result for 681236343 from a large loss to a small win, but changes 129679470 to a small loss. The agent cannot deterministically choose opposite actions from identical public information without another observable signal or a robust randomized policy.

## Files and result artifacts

- Candidate: `main_v44_guarded.py`
- Control: `main.py`
- Top-10 strict result: `benchmark_v44_refined_strict_residual_warm_top10_2026-09-21.json`
- Adaptive league result: `benchmark_v44_adaptive_strict_final_2026-09-21.json`
- Recent holdout: `benchmark_v44_strict_recent_top20_final_2026-09-21.json`
- Older holdout: `benchmark_v44_strict_exact_top20_final_2026-09-21.json`
- Self-play: `benchmark_v44_selfplay_strict_final_2026-09-21.json`

## Questions for the external ChatGPT review

1. Is the V44 wrapper architecture safe for Kaggle's repeated per-turn invocation model, especially the temporary shared-router selector and restoration in `finally`?
2. Given the 681/129 indistinguishable public snapshot, what is the best winning strategy: a randomized mixture, a deterministic tie-break from a legal public signal, a later re-branch point, or preserving V43 for that equivalence class?
3. Should `terminal_collision` remain enabled, or should the candidate use the plain guarded policy for lower complexity and latency?
4. What additional holdout, leakage, exception, and state-contamination tests should be run before promotion?
5. Please provide a concrete next patch and promotion criteria, not just general advice.
