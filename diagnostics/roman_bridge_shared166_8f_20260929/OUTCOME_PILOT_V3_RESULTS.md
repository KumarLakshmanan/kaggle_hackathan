# Roman shared166 outcome pilot results

Date: 2026-09-29

## Decision

Reject the exact `6a + Roman shared166` candidate for this trigger and adapter.
The run is complete fixed-tape diagnostic evidence only. Do not promote or
upload it, and do not treat the result as reactive or independent validation.

## V2 runner stop

V2 completed six clean direct 6a baselines, then stopped before snapshot
discovery or candidate games. The prefix helper returns its checks without a
`candidate_seat` field; the runner indexed that missing field and raised a
`KeyError`. The six baseline records are preserved in
`6a_outcome_pilot_v2_20260929/baseline_outcomes.jsonl`. No candidate game ran
under v2. V3 attached the seat from each frozen prefix job before applying the
seat-specific gate.

## V3 results

Candidate `86c9d10c75493300d615c2c7f87e9361295c615e4c70801f10cee90e5c40436b`
was built on exact 6a parent
`6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc` and donor
`fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849`.
All 12 games finished DONE/DONE at 720 frames. The exact parent baselines
matched the saved 6a outcomes on the target and top-20 control. Both public-win
control baselines won, and their candidate results matched exactly.

| Fixture | Seat | 6a result / margin | Candidate result / margin |
|---|---:|---:|---:|
| `live-114270587` | 0 | loss / -18,815 | loss / -133,800 |
| `live-114270587` | 1 | loss / -18,815 | loss / -135,802 |
| `public-win-114251368` | 0 | win / +26,195 | exact match |
| `public-win-114251368` | 1 | win / +23,089 | exact match |
| `top20-18-Kaggledew Valley` | 0 | win / +4,877 | exact match |
| `top20-18-Kaggledew Valley` | 1 | win / +4,877 | exact match |

The target trigger, step-1 hire, snapshot provenance, step-2 own/public guards,
donor action remap and two cow pickups all passed in both seats. The target
games had zero Roman errors. The outcome gate failed only because neither
target seat changed its 6a loss to a win; all four controls were exact wins.

## Failure mechanism

The target trace records 719 actions. At step 24 (day 1), the simulator has
zero hired hands. V3's adapter asks the donor for an action, then
`remap_donor_hands()` rejects the route because it requires at least five
hands. The adapter sets a permanent `bridge_failed` flag and returns an
all-PASS action thereafter. Every one of the 695 actions from steps 24 through
718 is PASS, with no hands or market actions. Donor telemetry stops at 23
calls. The route spends $1,030 on 12 melon and 7 wheat seeds, plants 19 tiles,
and builds four pastures. Cows are gone by step 48, sheep by step 72, and the
19 crops become weeds by step 72. At the final recorded observation the
candidate has $53, four wheat in the shed, no crops or animals, and 20 weeds
plus four pasture tiles.

A pure action-decision probe on the saved step-24 observation confirms the
remapper returns `None` for the zero-hand state. The exact 6a parent would
sell seven wheat at step 24 and later issue four HIRE orders at step 48. This
supports the conclusion that the permanent PASS handoff, rather than trigger
collision, caused the dominant loss. Animal upkeep and the donor's opening
investment are downstream costs, not independently isolated causes.

## Frozen artifacts

- V3 panel: `4c04b4e80317afb8864a6da7708cccc843435bf98de593d87448e5e46df2913c`
- V3 freeze manifest: `33676f42f2548d76acfdc4fa564916488601980b37ff45887fdc47d755a96d29`
- V3 runner: `e7ad01fa01ecdef56e83009257fdb079a1ff2529b172a93281b43a7c285db1cf`
- V3 builder: `fe9909ca1a0614ce9b81b96837975fd0eaa49aa16c45b6a2ecc82718e59df003`
- Receipt: `9ee6a52fea59d5f22bb0abaf463412643bee2086c4d16962e2d1b83cd8a54387`
- Outcomes: `1becb1ac84c42affba0225fcec18de843fef33a15a8eea8ac027cf59497a584c`

The frozen manifest binds both runner and builder hashes. Root `main.py` is
unchanged at SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; Kaggle
was not checked or contacted.

## Next experiment

V5 is a separate, not-yet-run candidate that returns to exact 6a whenever the
donor's minimum worker count is unavailable. Its gate requires exactly one
fallback at step 24 and verifies parent actions at steps 24, 48, 72 and 718.
Run it only after its frozen-source and panel reviews pass. A fallback fix is
a hypothesis for the next pilot, not evidence of a win-rate gain.
