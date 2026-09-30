# Funded land queue audit — 2026-09-29

## Finding

The completed top-20 traces contain one distinct missed-land event: Majkel1337 episode `115317514`, mirrored in both candidate seats. The exact-cb76 `candidate_funded_land_v1.py` helper recognizes both saved copies of that event and moves the **already-requested** `BUY_LAND` from queue index 2 to the tail. In recorded-action/native-market static controls, this adds the intended SW quadrant while preserving worker positions, seeds, shed stock, hires, and the modeled rival's physical state. This is a strong, executable test case for the current pilot, not evidence of a win-rate gain; the saved trace is fixed and correlated across seats.

## Exact chronology

Trace `rank10_ep115317514_s0.jsonl.gz` is rank 10, Majkel1337, episode `115317514`, seed `1747201981`; cb76 reward `64,930`, opponent reward `75,645`, margin `-10,715`. Seat 1 has the same saved action tape and outcome.

- At step 169 / day 7, the farm has `$4,321`, only NW unlocked, and eight hands. The existing queue ends with `BUY_LAND`, after its current sell/buy/sell sequence. The native land price at this point is `$1,000`; next observation has `$4,179`, eight hands, and NW+NE. This NE investment succeeds. No earlier land purchase failed.
- At step 241 / day 10, the farm has `$1,882`, NW+NE, and eight hands. Its queue has four `HIRE` orders (indices 3, 5, 6, 7) and purchases one GOOSE and one SHEEP (indices 8, 9). At step 242, the trace confirms all four hires succeeded (12 hands) and both animals are in the shed. This is the preceding worker/animal commitment, not a failed land action.
- At step 242, cash is `$1,928`, quadrants remain NW+NE, and the current prices are fertilizer `$69` and wheat `$37`. The queue is `SELL FERTILIZER 2`, `BUY_PRODUCT WHEAT 2`, `BUY_LAND`, then three existing wheat sells (`9`, `1`, `2`). Because NE is already owned, the requested SW land costs `$2,000`. The saved opponent tape's step-242 action is `SELL WHEAT 4`, `HIRE`; this shared-market action can change later wheat quotes, which is why the `$8` amount below is reported only for idle/mirror forecasts.
- The actual trace's next observation, step 243, still has only NW+NE and `$2,432`; therefore the queued land order failed, while the later sales left the farm funded. The saved candidate trace does not include the rival action; the separate public action tape shows `SELL WHEAT 4`, `HIRE`, which can alter shared wheat quotes. I did not reconstruct the exact live cash at queue index 2. Replaying our recorded prefix through the first two orders in the candidate's native market engine under idle and mirror forecasts yields `$1,992` before land—an `$8` forecast shortfall. This is not an assertion about the exact live shortfall.
- Moving that same `BUY_LAND` behind the three existing sells preserves the six-order queue and unlocks SW in both controls. No new purchase or duplicate land order is added. The next-turn step-243 queue independently has four of ten market slots and starts with actual `$2,432`, but the proposed intervention need not wait for it.
- Physical consequence begins immediately: at step 243, hand 5 at `[4,5]` attempts `PLANT WHEAT` on a `LOCKED` SW tile; step 244 it attempts `WATER` at the same locked tile. Similar locked-tile planting recurs in the trace. This links the missed investment to the worker's planned tasks, without establishing how much terminal reward the newly unlocked quadrant would recover.

## Activation census over recorded top-20 rows

Ran `_funded_land_apply(obs, deepcopy(recorded_action), cfg)` on all 40 completed cb76 seat traces, using each stored observation/action and configuration `{boardSize:10, maxMarketOrdersPerTurn:10, shedCapacity:100, farmHandCostMult:1}`. The helper's idle and mirror comparisons call its embedded native `_process_market`; no game was run.

- 80 recorded `BUY_LAND` occurrences across the 40 seat traces.
- 34 are structurally eligible for this one-order tail deferral (exactly one non-tail `BUY_LAND`, queue length 2–10, and another quadrant remains).
- Of those, 32 already unlock land in the baseline next observation; the remaining two are the same Majkel fixture in both seats, where baseline land fails.
- Helper activation: exactly those two trace rows; proposed queue in both is `SELL FERTILIZER 2`, `BUY_PRODUCT WHEAT 2`, `SELL WHEAT 9`, `SELL WHEAT 1`, `SELL WHEAT 2`, `BUY_LAND`.

The all-row census is descriptive of this fixed panel; it is not an activation-rate estimate for other opponents.

## Native controls on Majkel step 242

The helper's full queue simulations report:

| Forecast | Own cash before → after | Own delta | Rival cash before → after | Rival delta | Own non-land signature | Rival physical signature |
|---|---:|---:|---:|---:|---|---|
| Idle rival | `$2,436 → $436` | `−$2,000` | `$1,970 → $1,970` | `$0` | unchanged | unchanged |
| Mirrored original queue | `$2,431 → $434` | `−$1,997` | `$473 → $470` | `−$3` | unchanged | unchanged |

In both cases own quadrants change exactly from `NW, NE` to `NW, NE, SW`. The differences in simulated before-cash versus the trace's `$2,432` next observation reflect the absent real rival action; the guard's limits pass within its explicit modeled controls. Root should keep the native reacting paired pilot as the causal test.

## Why the existing queue optimizer cannot accept it

In `candidate_funded_land_v1.py`, `_queue_signature()` at line 93 includes `tuple(farm['unlocked_quadrants'])`. `_queue_optimize()` rejects any proposal whose idle signature differs from the original at line 148, and in mirror mode requires `mirror[2:] == original_mirror[2:]` at line 151. A queue reorder that makes the already-committed land purchase succeed necessarily changes that quadrant element, so the general optimizer rejects it even if all other state and cash checks pass. The funded-land helper is a narrowly scoped exception: it explicitly permits only `quadrants + next LAND_ORDER quadrant`, checks unchanged shed/seeds/hands/hire count, requires rival physical signature equality and no rival cash increase, and caps own cash loss at the native land cost.

## Small recorded-trace controls

Root owns candidate tests. The useful compact controls for the frozen pilot are:

1. **Positive case:** replay both recorded Majkel step-242 observations through the helper and assert the exact existing order multiset is preserved, only `BUY_LAND` moves to the tail, SW alone unlocks, and both idle/mirror guards pass. This audit already observed these results.
2. **No-op control:** step 169's NE `BUY_LAND` is already last and succeeds in the next observation; helper must leave its action unchanged. This audit's helper census did not activate there.
3. **Do not spend twice:** compare pre/post market-order multisets and assert the sole existing land order count remains one, with no added purchase or other farm action edits.
4. **Guard negative:** use a recorded eligible but baseline-funded/successful land queue (one of the 32 eligible successes) and assert it remains unchanged; the baseline land signature already differs from the starting quadrant set, so the helper must decline.

A later randomized/native block remains needed to measure whether recovered physical work converts to a win without harm on controls. The saved census alone cannot establish that.

## Hash-bound inputs and artifacts

- Candidate helper source: `candidate_funded_land_v1.py`, SHA-256 `2a4d093a4824c0fac824b292dfa4a93c2403214d74f31b703bfd913daf136eb8`.
- Exact baseline source: `baseline_cb76fbc4.py`, SHA-256 `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`.
- Completed top-20 results ledger: `cb76_top20_jobs_results.jsonl`, SHA-256 `9704679fed2e0623f60338218565a76845404fb2e0c7edc65f572ade1662f73e`.
- Majkel seat 0 trace: `rank10_ep115317514_s0.jsonl.gz`, SHA-256 `f247e2dae3105f9fbee66646fdbaa24f8eae822c66da7ad1d9a7c8dbf7a07df8`.
- Majkel seat 1 trace: `rank10_ep115317514_s1.jsonl.gz`, SHA-256 `d686a7e51c434e40458e65516801542763a74054acae2282e030237ecc3b0e84`.
- Fixed opponent action tape: `Majkel1337-submission-56663513-episode-115317514-seat0.json.gz`, SHA-256 `c0b8f6b4328d564de254e21dc58fd046a7cf249c9d4d23d83f0b97dfadb850c4`; action SHA `5216f6ebad1623f37e750bc7e407f300070b379df774cad3fc1e23b69d1b2fe1`, replay SHA `39c636521f12258f01b566e570df4e2ee57a5fe1b90cad5dba17c666e44aa6d3`.
- Census script and row-level record: `audit_funded_land_candidate.py`, `funded_land_trace_census.json`.
- Step-242 native scenario results: `check_funded_land_controls.py`, `funded_land_step242_native_controls.json`.

**Decision:** retain the one-shot funded-land deferral for the parent's frozen reacting pilot. Do not promote from the saved trace evidence; the pilot must establish paired outcomes and verify untouched controls.
