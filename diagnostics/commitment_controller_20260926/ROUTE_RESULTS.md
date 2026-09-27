# Day-6 whole-route controller — rejected, 2026-09-26

## Frozen implementation and actual evaluation

The unchanged local incumbent is `main.py` SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The isolated challenger `exp_route_commitment_20260926.py` SHA-256
`13f9f07984949b13ef214e8d266141f25afee18da9d5e9decaedd026ea16282c`
loads those exact bytes and intercepts only the step-144 route decision.
It compares the full route-9 and route-0 tape commitments, including the
shared route-2 terminal schedule, with an observation-only forecast of
purchases, escalating hires, land, physical output, delivery/sale slots,
feeding, public market prices and visible-rival output under three future
Yarn scenarios. The stateful incumbent is called once per observation.
The selected existing route is then executed by its native worker, market,
reactive and safety layers. `PLAN2.md` froze trigger, arms, cases and gates
before the native development run. This model's future geometry and rival
sales remain approximations; its simulated continuations are **not** engine
rollouts or guarantees of feasible settlement.

Engine: installed `kaggle-environments==1.32.7`, standard 720-turn native
configuration. The OFF wrapper exactly matched direct `main.py` cash and
captured day-6 state on seeds 2613000 and 2613001 in both seats; all four
were `DONE`. Source and case evidence are `route_off_parity_2seeds.json`
and `route_A_dev16.json`.

The fixed development block was seeds 2613000–2613015, both seats, versus
trusted reacting local `main.py`. Shops and shared markets evolved natively;
the seed is the independent draw, and seats are paired within each seed.
All 96 A/B/C games ended `DONE`, with no wrapper errors.

| Arm | Paired wins / losses / draws (16) | Seat wins / losses / draws (32) | Own cash | Rival cash | Sum of paired margins | Worst paired delta | Changed seeds | Maximum timed-agent call |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A native incumbent | 0 / 0 / 16 | 0 / 0 / 32 | 3,348,826 | 3,348,826 | 0 | 0 | 0 | 381 ms |
| B route controller | 0 / 0 / 16 | 0 / 0 / 32 | 3,348,826 | 3,348,826 | 0 | 0 | 0 | 1,407 ms |
| C always route 0 at trigger | 0 / 2 / 14 | 0 / 4 / 28 | 3,354,218 | 3,366,512 | −12,294 | −8,164 | 2 | 908 ms |

Exactly two seeds qualified: 2613002 (Yarn/ Bakery) and 2613015
(Bakery/Yarn). B forecast minimum route-0 paired-margin deltas of −14,808
and −13,972, respectively, and stayed with route 9 in both seats. C forced
route 0 and lost −4,082 and −2,065 per seat. The same result held in each
seat within these two seed blocks. There were zero rescued baseline draws or
losses, zero reversed incumbent wins (A self-play drew), and the worst seat
delta was −4,082. C's aggregate `Δown = +5,392`, `Δrival = +17,686`, so
`Δmargin = −12,294`: an own-cash improvement was competitively harmful.
`route_abc_dev16_comparison.json` contains all full seed/seat joins.

## Exact executed-cash diagnosis on the two changed seeds

`route_ledger_activated_s0.json` was reconstructed from four complete
engine-event traces of A and C in seat 0. The terminal A/C cash pairs and
status exactly match `paired_benchmark.py`; seat 1 terminal deltas match
seat 0 in both seeds. Every coin reconciles to successful market-unit or
atomic transactions; `other_cash` is zero. The native shop sequences were
identical between A and C in each of these two games. The rival still
reacted, and its sale prices changed with the shared market.
On seed 2613002 the earliest policy divergence is exactly step 144: route 9
began with five HIRE orders after wheat/fertilizer sales, while route 0
began with seven HIRE orders after a fertilizer sale. The next observation
showed 1,069 versus 937 own coins. At step 155 an incumbent worker built a
pasture successfully while the corresponding route-0 worker's WATER action
changed no state. The divergence thus propagated through funding and worker
tasks long before terminal revenue could be compared.

| Seed | Δown | Δrival | Δmargin | Main executed change |
| --- | ---: | ---: | ---: | --- |
| 2613002 | +2,403 | +6,485 | −4,082 | Own fertilizer receipts +1,618 and 22 extra units; 35 fewer own wool units. Rival wool receipts +8,046, including price effects. |
| 2613015 | +293 | +2,358 | −2,065 | Own fertilizer receipts +1,548 but wool −1,499 and milk −841; rival wool receipts +4,005 even with four fewer units, showing price impact. |

These exact ledgers support a market-interaction explanation for the losses;
they do not isolate each physical cause of the changed sale units. The
trace recorded own non-`PASS` worker actions that produced no state change:
20→59 on seed 2613002 and 24→66 on seed 2613015. Empty-shed SELL
failures increased 31→38 and 31→34, respectively. Each arm had one
insufficient-cash BUY_PRODUCT event on these seats. The extra worker no-ops
are direct evidence that complete tape transplantation still suffers
execution mismatch; they are not alone proof that a specific deadline was
missed. The
forecast overestimated route-0 losses in magnitude, and its static rival
estimate cannot predict the native rival's price response. In the first
sheep experiment, a changed native shop path also dominated one seed. Here
the two activated route-control shop paths happened to stay identical.

## Decision, limits and reproduction

**Reject B and C.** B never switched a route and failed the primary paired-win
gate. C lost both activated paired blocks. The B timed-agent maximum in the
full run was 1.407 seconds, above the reported one-second action budget;
other Python jobs were contending for the machine, so this is an operational
risk observation rather than a clean isolated runtime measurement. A direct
single-observation model call on a previously used case took 37 ms, but
that narrow timing excludes the full agent and runner overhead. Strength
already fails, so no deployment-timing qualification, saved-route regression,
untouched 2613100–2613115 block, integration into `main.py`, or upload was
performed. The untouched block remains unopened by this experiment.

This is the second distinct challenger mechanism after the rejected day-11
sheep overlay. Under the user's stop rule, the diagnosis is reassessed and
no further variant is being tuned. The remaining limitation, even with
exact execution, is the route architecture's inability to make reliable
competitive commitment choices from the currently visible signal when
future shop demand, worker throughput and rival market response can change
the sign or scale of a project. The 16-seed local self-play block is a
development result against one trusted reacting opponent; it does not
estimate leaderboard win rate against other policies.

Reproduction commands (the seed list is the literal frozen block):

```powershell
python -B -X utf8 paired_benchmark.py --candidate main.py --opponent main.py --seeds 2613000 2613001 2613002 2613003 2613004 2613005 2613006 2613007 2613008 2613009 2613010 2613011 2613012 2613013 2613014 2613015 --capture-step 144 --json-out diagnostics/commitment_controller_20260926/route_A_dev16.json
python -B -X utf8 paired_benchmark.py --candidate exp_route_commitment_20260926.py --opponent main.py --seeds 2613000 2613001 2613002 2613003 2613004 2613005 2613006 2613007 2613008 2613009 2613010 2613011 2613012 2613013 2613014 2613015 --candidate-override _MODE=model --capture-step 144 --json-out diagnostics/commitment_controller_20260926/route_B_dev16.json
python -B -X utf8 paired_benchmark.py --candidate exp_route_commitment_20260926.py --opponent main.py --seeds 2613000 2613001 2613002 2613003 2613004 2613005 2613006 2613007 2613008 2613009 2613010 2613011 2613012 2613013 2613014 2613015 --candidate-override _MODE=force --capture-step 144 --json-out diagnostics/commitment_controller_20260926/route_C_dev16.json
python -B -X utf8 diagnostics/commitment_controller_20260926/analyze_route_dev.py
python -B -X utf8 diagnostics/commitment_controller_20260926/route_ledger_compare.py
```
