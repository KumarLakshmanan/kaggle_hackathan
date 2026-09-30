# Exact cash diagnosis of 17 later public games — 2026-09-26

The frozen cohort contains 17 distinct public rival action histories from
submission 56572390: seven wins and ten losses. `freeze_routes.py` recorded
the original seed, our seat, replay cash, and action hash for each route.
`trace_ledgers.py` reran unchanged `main.py` (SHA-256 `489fe8e4...`) against
all 17 on their original seeds and seats with Kaggle engine 1.32.7. All
games ended DONE/DONE and **all 17 reproduced both terminal cash totals
exactly**. The ledger therefore explains these recorded matches; it is not
independent validation of a policy change.

The ten losses sum to **−30,651** terminal margin. Six were ahead after day
19. Their aggregate net item-cash differences were MILK **−13,800**,
CARROT **−13,293**, and WOOL **−10,117**, partly offset by FERTILIZER
**+3,776** and WHEAT **+3,412**. The later period alone contributed MILK
**−8,606**, WOOL **−10,669**, and CARROT **−7,336**. The three largest
losses have distinct mechanisms:

| Rival (episode) | Final margin | Day-19 margin | Evidence |
| --- | ---: | ---: | --- |
| Takahiro Someya (113800419) | −7,097 | −252 | WOOL net cash −7,009 with equal total wool sale units (367 each). |
| DeeperNet (113783438) | −3,507 | −4,375 | CARROT net cash −10,320; other products partially recovered. |
| Ryoya Tsuruoka (113783439) | −14,711 | −6,707 | MILK net cash −12,816; 30 fewer late milk sale units. |

The focused Takahiro timeline reproduced exact terminal cash again and
traced successful WOOL sale units. Both agents sold **367 units**, yet ours
received **48,313** coins versus **55,322**, a **7,009** receipt gap. On
day 27, both sold 27 wool units, but our receipt was only **699** versus
**3,479** (−2,780). The rival sold 12 at turn 666 when the preturn quote
was 174, then 12 at turn 667 when it was 137. Our 12-unit sale began at
turn 669 when the quote was 72, with nine more at turn 670 when the quote
had fallen to 1. Day 21 adds a **−1,717** wool gap with 36 units each:
the rival's 24 later units went at turns 521–522, ours at 524–525. These
two days account for **4,497** of the 7,009 wool receipt gap. The
replay actions show this is principally **worker delivery timing**: on day
27 the rival's wool carriers moved from `(7,5)/(7,6)` toward the shed on
turns 664–665 and placed 12 wool on turns 666–667. Ours stayed at the sheep
tiles to `CARE`/`HARVEST`/`COLLECT_FERTILIZER` and did not start moving until
turn 667; it placed wool on turns 669–670. On day 21 the rival wool carrier
harvested and walked west on turns 518–520, then placed at turn 521; ours
fed/cared/collected fertilizer and arrived to place at turn 524. At turn
666 our shed held zero wool despite 41 units carried, so a market-order-only
advance could not have sold the rival's early batch. The timeline uses
observation frame `t` and action frame `t+1`, correcting the earlier
replay-index mistake in the separate milk model experiment.

**Decision:** this is a concrete late wool delivery timing hypothesis, but the
fixed public routes establish only where the submitted agent lost money.
Do not promote a policy, edit `main.py`, or upload from these traces. A
targeted **carrier-delivery schedule** candidate would need an isolated
source and fresh both-seat native games with reacting opponents and original
shops, including its effect on rival cash and paired margin. A simple
extra SELL order alone does not address the observed delay.

Evidence: `routes/summary.json`, `cash_ledgers_17.json`,
`takahiro_wool_timeline.json`. Reproduce with:

```powershell
python -X utf8 diagnostics\new_live17_diagnosis_20260927\freeze_routes.py
python -X utf8 diagnostics\new_live17_diagnosis_20260927\trace_ledgers.py
python -X utf8 diagnostics\new_live17_diagnosis_20260927\wool_timing.py
```
