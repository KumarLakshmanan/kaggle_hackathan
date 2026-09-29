# Ghost wheat derivative: frozen 12-game outcome plan

Status: staged, frozen-plan intent; **no outcome games have been run by this package**. The runner has not been executed. This panel uses saved opponent action tapes and pure native transitions, so it is a fixed-tape diagnostic only. It cannot support a reactive-validation or promotion claim.

## Bound candidate and evidence

The tested file is the exact Ghost wheat derivative candidate `228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767`, built on accepted source-only Goose4+Smoothie candidate `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`. The derivative's static preflight is `aefa68e3126e9eb6554cdfe426d023953e90524a72f8da49c4986240c6f801fc`; its frozen manifest is `3a3cd881a7d2972e93c57dbc747ff16ca0c335b773b3ebafaa7f63eb440aa4d2`. The 6d full-panel combined receipt is `5463a0efa37aebad2c11559cbcd2c39bf2a9a63ec5b2279f409d6360c61ff40d`; its 104-fixture parent panel is `7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51`. The copied outcome panel is byte-identical to the six-fixture Ghost plan panel (`545c038fb0ab95530a53e58847e23233ddc3a0202fc36dae72f500ef185cbbf6`). The frozen manifest binds the runner, this plan and panel, the derivative package and preflight, 6d baseline/panel, all six replay and action-tape inputs, all twelve step-72 traces, and native engine/cache/lock helpers.

The public-state activation remains exactly the frozen rule: on the source bridge at step 72, `ICE_CREAM_SHOP|M8+|C>S|G0` with public WHEAT inventory `<= 9975` selects route `113360743`. The only expected activations are both seats of `live-114288168`; the other five fixtures (ten seats) must retain the Goose4 route `113470868` and exactly match the 6d baseline result, candidate reward, opponent reward, and margin.

## Fixed panel and frozen gates

Run all six fixtures in `fixture_id` order, seat 0 then seat 1. Each completed game must report candidate `DONE`, opponent `DONE`, 720 frames, and no candidate errors.

| Fixture | Expected activation | Step-72 WHEAT | Route | 6d baseline per seat |
|---|---:|---:|---:|---|
| `live-114255779` | no | 9977 | 113470868 | win, margin +9,559 |
| `live-114258293` | no | 9977 | 113470868 | win, margin +7,157 |
| `live-114288168` | yes | 9975 | 113360743 | seat 0 loss -2,253; seat 1 win +1,425 |
| `public-win-114209881` | no | 9977 | 113470868 | win, margin +1,337 |
| `public-win-114221853` | no | 9976 | 113470868 | win, margin +2,097 |
| `public-win-114245470` | no | 9977 | 113470868 | win, margin +10,228 |

The predeclared outcome gates are: all 12 games clean and complete; both `live-114288168` seats win; and all ten false-trigger controls exactly preserve the 6d result, candidate reward, opponent reward, and margin. Expected step-72 telemetry must match each row's source branch, key, WHEAT amount, activation bit, selected route, and Goose4 route; Goose4 turns must be 647 with zero Goose4 errors. A completed receipt reports gate pass/fail and remains diagnostic-only. Any gate failure rejects this derivative for this panel. No automatic retry or resume is permitted.

## Execution safety and command

The one-shot runner checks all frozen hashes and output absence, then acquires both `diagnostics/.shared_game_run.lock` and this folder's `run.lock`. It refuses existing output files and never resumes partial output. The root coordinator must first review the freeze and coordinate the shared lock. Exact command, when explicitly scheduled by the root:

```powershell
python -X utf8 diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/outcome_run_20260929/run.py
```

This staged package will not launch the runner. Its only claim is a frozen plan for twelve saved-tape games; no game transition or candidate policy call has occurred during staging.
