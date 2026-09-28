# Exact physical rollout prerequisite — 2026-09-28

**Accept engineering parity; no policy promotion or strength claim.** The
extracted pure native transition code reproduces all 575 consecutive
transitions from observation 144 to 719 in each of four saved replays:
chocolat, mhw, DECEM and Vadim. All **2,300** full physical comparisons pass,
including farms, shared market/town, both private states, day/hour/step,
DONE statuses and terminal rewards. The two top-20 replays are their original
public games, not the counterfactual 4ee games; this checks engine mechanics
independently of which policies generated the recorded actions.

The code is extracted from installed engine 1.32.7, source SHA-256
`bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`.
Extracted `native_core.py` SHA-256:
`5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795`.
Environment initialization, renderers, filesystem/network imports and sample
agents are excluded. A supplied initialized state is required.

Measured 575-step continuation time, including action copies and every-state
comparisons, is 0.139–0.181 seconds (0.241–0.314 ms per transition) on this
host while the other local regression was running. This is a feasibility
measurement, not a guaranteed Kaggle runtime. The local specification has
actTimeout=1 second, so a future multi-scenario chooser needs an explicit
timing/overage budget and graceful fallback.

**Critical scope:** this offline parity test uses the known episode seed,
both players' recorded private inventories and recorded future actions.
Those are test-only data. They must not enter a deployed chooser. No
alternative route was evaluated here. A future policy must initialize from
its own legal observation, represent unknown rival inventory/actions and
future shops as forecasts, then earn fresh reacting validation.

Main remains exact 4ee. Reproduce with `python -X utf8
diagnostics/physical_route_rollout_20260928/check.py`. Evidence: PLAN.md,
check.py, native_core.py and parity.json. No Kaggle request was made.

## Observable net-flow feature — 2026-09-28 02:33 UTC

The initial full-product accounting inversion failed: native price-1 sales
remove goods and credit cash without increasing shared market supply.
The original failed checker/model/result are retained under
`before_floor_censor_*`, and FLOW_CORRECTION.md records the revised
identifiability claim before its rerun.

The corrected function accepts only our two consecutive legal observations,
our own prior action and configuration. It reconstructs our post-worker
stock exactly, subtracts our net trade and adds back known town demand to
infer rival net sales. It returns unknown at midnight or for a product whose
market phase could reach price 1. No rival private stock/action enters this
function; the harness uses those solely as independent accounting truth.

**Accept the corrected past-flow feature.** Across both seats of four full
games, all 5,520 non-midnight transitions are visited. It infers **48,698 /
49,680 product-transitions (98.02%)** exactly, with zero mismatches and 982
explicitly censored values. All 29 midnight steps per seat are skipped.
No future supply forecast, candidate decision or strength claim follows
from this parity result. Gross buy/sell round trips remain unidentifiable.
Evidence: FLOW_PLAN.md, FLOW_CORRECTION.md, observable_flow.py,
check_flow.py and flow_parity.json.

## Full-policy fast harness parity — 2026-09-28

The complete selected Bakery/Pizza file (including actual queue optimizers)
was repeated in the memory-bounded pure-core harness on the three development
fixtures in both seats. All six games match the prior native result exactly:
both final rewards, DONE/DONE/720 and every telemetry field. No policy error
was recorded. Measured game time is 6.35–7.34 seconds, with maximum candidate
calls 0.267–0.326 seconds in this run. These are repeated known results, not
six additional independent games.

**Accept for faster development diagnostics only.** The harness deliberately
does not implement framework schema validation, timeout enforcement or the
Kaggle file loader; native qualification remains mandatory. Agents see their
own private inventory and normal public state, with configuration seed
hidden. Evidence: FAST_AGENT_PLAN.md, fast_game.py and fast_agent_parity.json.
# Reacting-policy helper parity — 2026-09-28 03:28 UTC

All eight repetitions of already-known native games, covering 4ee and
b6eb against both current 4ee and the market policy in both seats, exactly
match terminal cash, statuses, 720-frame counts and complete candidate
telemetry. The initial template matches a fresh native initialization.
Neither policy reports errors. **Accept for development and outcome-blind
prefix selection only; keep original-framework strength/runtime/loader
gates.** These repeats add no independent evidence about agent strength.
Evidence: `REACTIVE_PLAN.md`, `reactive_parity.json`, `fast_reactive.py`.
