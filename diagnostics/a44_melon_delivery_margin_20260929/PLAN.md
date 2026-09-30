# Frozen pre-outcome plan — a44 melon delivery margin

Date: 2026-09-29  
Status: **frozen outcome-blind plan; isolated candidate and action-transform checker only. No native games, simulations, outcomes, Kaggle, or edits to `main.py`/`agent.md`.**

## Objective

Use exact a44c8c2c as the incumbent. Test one late delivery path, seeking a strictly positive paired-margin change in both seats against offhand (`live-114271958`, baseline +670 each seat). Preserve every a44 saved-panel winning seat and therefore retain at least 19/20 top20 and 17/30 public both-seat sweeps. The same monotone selector also activates on Unknown Mother-Goose, a top20 win; keep that fixture and require no result regression and no negative paired-margin change in either seat. This explicitly protects the top20 score.

## Frozen selector v2 (supersedes the pre-outcome quote-ceiling draft)

Selector version: `a44-monotone-melon-delivery-v2`  
Selector file: `predicate.json`  
Semantic selector SHA-256: `33a813c56bc0c913a445508523288e6ebebbad5b1cf437e610074eb46507af52`  
Predicate file SHA-256: `cf67647b77a2b870d7a7841dc32c5709f2c51ccac8043054e882193d1a388593`

Activate at step 713 (day 29, hour 17) only if exactly one own farm hand meets all conditions:

- position `[1,4]`;
- incumbent action `WATER`;
- own private hand inventory contains at least 12 MELON;
- public MELON quote is **at least 100**, with **no upper quote bound**;
- Manhattan distance to a shed-access tile is at most 3.

The selector is monotone in the public melon quote. It activates on offhand at 133 and Unknown Mother-Goose at 158 in both seats (4 rows total). A higher quote is not an ex-ante reason to exclude UMG; step716 quotes are 91 for offhand and 158 for UMG, and market response remains unknown. Do not add a price ceiling or another outcome-informed split.

The inventory mapping is `private.inventories[0]` for the main farmer and `private.inventories[i+1]` for hand `i`. The candidate rule uses its own private inventory plus public market/farm data; it does not read opponent-private state or opponent policy actions.

## One isolated action-path change

The implementation uses a route latch keyed by `observation.player`. It is created only by the full step713 selector and valid startup config; step0 clears that player's prior episode entry, any out-of-order/state mismatch clears the entry, and step716 clears it on every terminal branch. This prevents one seat's route state from controlling the other seat and prevents leakage into the same player's next episode. Steps714–716 require the latched player, expected next step, `boardSize=10`, the exact stored hand index at the projected position, and exact MELON12 + FERTILIZER1 private inventory; they command the route action without checking the a44 action tape at those counterfactual states. The step716 DROP/SELL is allowed only after live shed/order guards. The exact continuation states are:

| Step | Day/hour | Required position before action | Replacement |
|---|---|---|---|
| 713 | 29/17 | `[1,4]` | `EAST` |
| 714 | 29/18 | `[2,4]` | `EAST` |
| 715 | 29/19 | `[3,4]` | `EAST` |
| 716 | 29/20 | `[4,4]` | `DROP`, and add one `SELL MELON 12` market order |

The target begins with MELON12 + FERTILIZER1. Three EAST actions place it at shed-access tile `[4,4]`. `DROP` deposits its entire inventory; player actions run before market processing, so the single same-turn MELON sale can use the deposit. On the exact saved rows, step716 has shed total26/MELON0, an empty own market queue, and 13 held items projected, so the nominal post-drop shed total is39. The traces do not serialize per-episode `shedCapacity` or `maxMarketOrdersPerTurn`; the candidate fails closed unless step713 receives valid config (`boardSize=10`, capacity enough for the step713 shed plus 13 items, and at least one order slot). At step716 it rechecks live config, projected full-drop capacity, one order slot, no duplicate MELON sale, and no competing same-turn own DROP. It uses no hardcoded config fallback.

This path replaces WATER at step713 and HARVEST at step714. The incumbent plant has yield5 at h17, becomes yield6 after watering, and the h18 harvest raises carried MELON from12 to18 by h19. The intervention gives up that observed six-unit harvest. No cash value or paired-market impact is inferred from static quotes.

On a failed step716 sell guard, use the following safe fallback: if the full drop fits and no other own actor has DROP or PLACE, issue DROP without a new market order (including missing/full order-capacity or an existing MELON sale); otherwise issue PASS to stay at `[4,4]`. In the PASS branch the saved a44 tape has EAST at step717, which would reach shed-access tile `[5,4]`, and DROP at step718. In the DROP-only branch step717 EAST likewise reaches `[5,4]`; step718's saved action is DROP. Those late actions are tape-based expectations only until native prefix validation. Count activation, successful early sale, DROP-only fallback, PASS fallback, and guard reasons in cumulative diagnostic telemetry; counters do not affect policy actions. On an unexpected continuation state, clear the latch and use PASS for its stored hand when possible; on step716 it is cleared after any safe action. This plan does not authorize outcome runs.

## Frozen evaluation gates for a later authorized run

1. Before any outcome evaluation, perform native step-by-step prefix validation for both seats of offhand and Unknown Mother-Goose. Feed the actual candidate state after each intervention action into the next a44 call; verify the candidate base action, positions, inventory, shed/capacity behavior, order slot, and the step716 sell/drop or guarded fallback. Saved action tapes cannot validate actions regenerated on counterfactual observations.
2. Then run all 100 frozen a44 target seat rows against exact a44 controls. Require clean completion, preserve every a44 winning seat, and retain at least 19/20 top20 plus 17/30 public both-seat sweeps. Report W/D/L and own/rival cash deltas separately.
3. Offhand `live-114271958`: both seats remain wins and each has strictly positive `delta_own - delta_rival` (candidate seat margin minus exact a44 seat margin).
4. Unknown Mother-Goose top20 control: both seats remain wins and each paired-margin change is nonnegative. This prevents losing or weakening the 19/20 top20 result through the shared market.
5. Every one of the 96 non-activation rows must retain **exact a44 action/output parity at every step and exact own reward, rival reward, seat margin, and W/D/L outcome**. This is a frozen equality gate, not merely a no-loss gate.
6. After the saved-panel gate, run one frozen original-shop paired check in both seats against one local reacting opponent. Freeze opponent hash, seed, and configuration before outcomes; compare candidate and a44 against the same opponent. Require no seat-result regression and nonnegative aggregate paired-margin change. This is a diagnostic check, not promotion evidence.

The planned observation-stream checker is action-transform-only: it applies the wrapper to the bound recorded a44 observation/action rows and minimal projected hand positions/inventory. It cannot establish candidate actions regenerated by the a44 policy on counterfactual observations, nor candidate rewards or margins. Native prefix validation in Gate 1 is mandatory before any outcome run. Fixed tapes remain regression controls, not independent validation.

Saved tapes are regression controls, not independent validation. Keep this as the sole intervention. Do not promote from the static receipt.

## Static binding

- Incumbent a44 candidate/source SHA-256: `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`
- Isolated candidate artifact SHA-256: `dbf54f4d89d0c56d89959e858bde7ffd02a160c1c4013c6cf7c80b25b522313e`
- Candidate builder SHA-256: `52fd610e8a6578369e7feaf81412dbbd944a045af04dbdaa257775ecfb914e83`
- Observation-stream checker SHA-256: `afb0effbb285e345175a070ddfc762fc096fa031738b108bf372c35286887d9b`
- Full results SHA-256: `ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732`
- Pool SHA-256: `4d0a74d3c897891d182d80948a1d8b79d761855147098ad4a6b7d763e068af5d`
- Predicate semantic SHA-256: `33a813c56bc0c913a445508523288e6ebebbad5b1cf437e610074eb46507af52`
- Predicate file SHA-256: `cf67647b77a2b870d7a7841dc32c5709f2c51ccac8043054e882193d1a388593`
- Exactly 4 selector activations in the 100 individually hash-verified target seat traces: offhand seats0/1 and Unknown Mother-Goose seats0/1. The isolated candidate imports the byte-exact a44 source prefix and adds only the local wrapper. No candidate outcomes were run.
