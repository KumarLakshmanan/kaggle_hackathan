# Wool-carrier delivery interrupt — 2026-09-26 21:09 UTC

The isolated source `exp_wool_delivery_interrupt_20260927.py` (SHA-256
`33b630564791fe4ee274d8f88e090b138abaf7d82ed1439d02355b211fca4779`)
concatenated unchanged `main.py` with one late wool-carrier wrapper. It
compiled and Kaggle's file-path loader chose the unique final callable;
seed-0 file-path and direct-call games matched both terminal cash values
in both seats and ended DONE/DONE.

The first draft's raw-route lookahead never activated on the diagnosed
Takahiro replay: the raw route had ten hands, while a later controller
produced the wool carriers' commands. Before fresh testing, the frozen
rule was corrected to observe the parent command at runtime and release
the interrupted hand when the parent next attempted `PLACE WOOL` or the
day ended. The corrected fixed-route check reproduced the baseline
−7,097 loss and changed it to −1,328: own cash +2,199, rival cash −3,570,
paired margin +5,769. It triggered four hand deliveries and sold 48 wool
units early. This saved-action result only establishes executability;
the opponent did not adapt its actions and it cannot validate the policy.

On **fresh native seeds 2625000–2625015**, unchanged `main.py` and the
candidate each faced reacting unchanged `main.py` in both seats, with
original shop draws. All **64 games ended DONE/DONE**, control/candidate
shops matched within every pair, and the candidate reported zero errors.
Only **one of 16 paired seeds activated**. On seed 2625006 (YARN_STORE /
YARN_STORE), six hand triggers and 48 early wool units in each seat raised
own cash 480 and lowered rival cash 472, improving margin **952 per seat**.
Across the pair, own cash rose **960**, rival cash fell **944**, and margin
rose **1,904**. The other 15 pairs were exact no-change outcomes. The
predeclared minimum of four activated paired seeds failed, so later gates
and a saved-route panel are not evidence for promotion.

**Decision: reject this rule as too sparse for the leaderboard goal.** Keep
`main.py` at SHA-256 `489fe8e4...`; no edit and no Kaggle upload. Do not
tune thresholds on these sixteen development seeds. The larger recurring
losses still require a broadly effective funded production/delivery policy.

Evidence: `PLAN.md`, `saved_diagnostic.json`, `file_parity_seed0.json`,
`reactive_fresh16.json`, `wrapper.py.txt`. Reproduce:

```powershell
python diagnostics\wool_delivery_interrupt_20260927\build_candidate.py
python -X utf8 diagnostics\wool_delivery_interrupt_20260927\file_parity.py
python -X utf8 diagnostics\wool_delivery_interrupt_20260927\saved_diagnostic.py
python -X utf8 diagnostics\wool_delivery_interrupt_20260927\reactive_fresh16.py
```
