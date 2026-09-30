# Guarded seed prefund: rejected at frozen top-20 gate

2026-09-27. Candidate `d8b8c293180e3cbbec1f123fa2b52a2bd95d11ddc8b8b74c6a69cc4e8c55dae6`
is exact uploaded 4eeac9c3 plus `tail.py`. The frozen plan hash is
`a88629895f11e8bd7e27e71cf9f81cf897acd83a1dd32343bc548548e8da526d`.
The hash-named backup is at the workspace root. `main.py` was not edited.

The rule only considers leading adjacent `BUY_SEED`, `SELL WHEAT` orders when
cash cannot buy one seed unit. Both idle-rival and hypothetical-mirror
market simulations must show the sale fills, at least one extra seed is
bought, all other resource commitments are preserved, and modeled immediate
market externality stays within 20 coins. It changes no quantities or worker
commands.

## Frozen development result

All 40 games against the fresh 16:35 UTC top-20 saved action routes completed
DONE/DONE/720, both seats, zero telemetry errors. The rule activated in six
games: both seats each of Boey, Vadim Vasilenko and DECEM. All other games
were exact cash/outcome controls. Both old and new score **16/20 both-seat
sweeps**. No prior winning seat was lost, but neither required Boey nor Vadim
loss became a win. The first development gate failed, so the conditional
current-100/original-50 regressions, 384-game native confirmation and loader
qualification were not run. The saved-action results cannot validate
strength against reacting opponents.

| Fresh top-20 case | Old margin per seat | New margin per seat | Δ own cash | Δ rival cash | First changed turn |
|---|---:|---:|---:|---:|---:|
| Boey | −2,819 | −6,510 | −35,290 | −31,599 | 187 |
| Vadim Vasilenko | −5,821 | −7,355 | −1,900 | −366 | 180 |
| DECEM | −63,151 | −11,602 | +32,583 | −18,966 | 175 |

`causal.json` compares matched native traces in seat 0, exactly reproducing
the benchmark cash. Each first difference is solely the adjacent sale/seed
swap, preserving the market-order multiset. In Boey, the next observation
has two extra WHEAT seeds; in Vadim and DECEM it has one. Every farmer and
hand action list matches the base for all 719 calls in all three cases. Farm
tiles first diverge two turns later for Boey and Vadim, and two turns later
for DECEM (at 189, 182 and 177 respectively). The third native shop at turn
216 then differs in every case: Boey SMOOTHIE→BRUNCH, Vadim FARMERS→BRUNCH,
DECEM SMOOTHIE→YARN. Physical occupancy changes future shop RNG and the
entire subsequent cash path, even though the scheduled worker commands are
unchanged. The immediate 20-coin forecast guard cannot bound this effect.

The broad 7673 planned-funding component previously failed its 1,280-prefix
activation gate. This narrower rule does activate in three recorded opponent
routes, but its prespecified win gate fails. A DECEM margin gain that still
ends in a loss does not offset the two worsening target losses under the
competition's win objective.

**Decision: reject `d8b8c293` for promotion.** Preserve the candidate and
traces as research. Do not edit or upload `main.py` on this evidence.

Evidence: `PLAN.md`, `build_manifest.json`, `pilot.json`, `top20.json`,
`causal.json`, `trace_prefund_*.json.gz`, and the base traces in
`diagnostics/new_main_failure_diagnosis_20260927/`.
