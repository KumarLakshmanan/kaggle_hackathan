# Isolated generative planner scope — 2026-09-30

`kaggriculture_engine/planner.py` is a separate offline experiment. It does not
modify the frozen v1 candidate, native transition copy, builder or CLI. The
planner proposes new joint worker and market programs, then evaluates them by
calling the existing `engine.make_world` and `engine.advance`, which invoke the
copied native Kaggriculture transition.

## Search and output contract

`search_plan(observation, configuration, continuation, horizon=12, width=4,
max_nodes=400, seconds=10.0, limits=DEFAULT_LIMITS)` returns a dictionary that
includes:

- `actions`: the selected common open-loop sequence.
- `nodes` / `evaluated_programs`, `requested_horizon`, `completed_depth`,
  `complete_horizon`, `elapsed_seconds` and `budget_exhausted`.
- `scenario_results`: exact simulated own coins, rival coins and cash margin,
  plus `inventory_only_leaf_value` for the reached state.
- `final_season_forecast`: true only when the native simulator actually marked
  every selected scenario `DONE`.
- explicit scenario assumptions, generator limits, hidden-state/episode-seed
  flags and limitations.

The incumbent continuation is evaluated at each depth and kept in the beam.
Beam width is at least four even if a smaller width is requested, so the
incumbent plus first-deviation physical, investment and combined branches can
survive together. If the search reaches the requested horizon, it selects only
among complete-horizon leaves. If time or node limits stop it early, it returns
a best leaf at the deepest evaluated depth and reports that depth as partial.
Natural native `DONE` states count as complete.

The sequence is open-loop and shared by all scenarios; it cannot choose a
different action for a hypothetical rival response. The supplied continuation
is rerun from scenario zero's simulated observation at each step. Consumers
should replan when a real observation arrives.

## Generated action families and hard bounds

The generator reads the current public board/market and own private inventories
only. Movement actions are a one-step Manhattan-shortest-path step toward an
owned tile task or shed access tile; it may choose either axis when both reduce
distance. The native rules allow movement across locked tiles and units do not
block one another, so no hidden obstacle map or route assumption is needed.
Actions at a destination are generated from current prerequisites: empty-tile
planting with available seeds; harvest only for mature, positive-yield crops or
animals; watering/fertilizing; weed clearing; empty coop/pasture building;
animal placement; feed/care/fertilizer collection; and shed drop/pickup.
Generated joint actions are replayed through the native unit-action function
to reject clipped, conflicting or ineffective changed work. Same-crop planting
requests are checked against the core's atomic seed rule and use distinct plots.

Market candidates append to the continuation queue. They include up to two
investment orders selected from seeds, animals, wheat/fertilizer, hiring and
land, optionally preceded by one sale to fund the bundle. A new order is kept
only if a paired native control rollout with identical worker commands proves
that every appended order committed in every scenario. The total queue also
respects `maxMarketOrdersPerTurn`. If a worker is already on an empty owned
tile, the planner can combine a new animal purchase with a direct coop/pasture
build; native market orders resolve after worker work, so the purchased animal
stays in the shed and is placed on a later turn. When a worker must travel to an
empty plot, that turn contains only the first movement step.

Default per-parent generation limits are:

| Limit | Default |
| --- | ---: |
| Candidate programs, including continuation | 72 |
| Single-worker changes considered | 20 |
| Joint action candidates | 28 |
| Joint option pool / combinations examined | 18 / 180 |
| Workers changed in one generated program | 3 |
| Per-worker options retained for joint synthesis | 3 |
| Direct or movement options per worker | 12 |
| Coordinated planting groups | 12 |
| Empty-plot build templates / compound programs | 12 / 12 |
| Market programs synthesized per parent | 24 |
| Investment order options / sale candidates | 16 / 6 |
| Added sale orders per program | 1 |
| Added investment orders per program | 2 |
| Maximum seed quantity in a generated order | 3 |
| Maximum wheat quantity in a generated order | 2 |
| Rollout hypotheses | 3 |

Worker options per individual are further clipped to at most 12 direct actions
or movement directions. Joint tuple enumeration stops after 180 combinations,
before copying worker programs. The investment menu keeps at most 16 order
types and reserves available animal purchases and land purchase for
consideration. Market programs are capped before compound work-plus-investment
variants are generated. These are deliberate synthesis bounds, not
claims that omitted actions are infeasible or unprofitable. Candidate count,
node count and elapsed time are reported separately; a node is one candidate
program evaluated, while a market-funding proof adds exact control transitions.

## Valuation and uncertainty

Every step through the requested horizon is simulated exactly under the chosen
action sequence and the fixed scenario assumptions. At a nonterminal leaf, the
ranking adds only discounted current inventory salvage to exact cash margin,
using the existing `engine.terminal_value` policy. It assigns **no** credit to
unexecuted crop harvest, animal output, planned future sales or other portfolio
production. A horizon ending before maturity can therefore undervalue a funded
production plan; this limitation is explicit rather than hidden in a forecast.

The scenarios are unweighted hypotheses: idle rival market, a mirrored
continuation queue, and a front-loaded mirrored queue with synthetic rival
stock set to twice our visible shed stock. Rival worker actions are PASS.
Future randomness uses fixed synthetic scenario seeds; the actual episode seed
is cleared before simulation and before calling the continuation. These
scenarios are not opponent probabilities, win-rate estimates or predictions of
real rival private stock. Coin outcomes are conditional exact simulator results
and need native reacting-policy games before making competitive claims.

## Focused verification

Run `python diagnostics/executable_engine_20260930/verify_planner.py` from the
workspace root. The probes use small synthetic observations and native single-
step transitions to check movement bounds, coordinated seed-funded planting,
shed transfers, animal placement/feed/care/fertilizer collection, sale-funded
multi-order completion, and full-versus-partial search reporting. They are not
full games, performance benchmarks or independent policy validation.
