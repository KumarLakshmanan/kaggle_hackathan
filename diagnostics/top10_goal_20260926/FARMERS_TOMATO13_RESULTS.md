# Day-11 tomato cohort under two Farmers Markets — 2026-09-26

## Hypothesis and pilot

The 41 stored route tapes contain no `PLANT TOMATO` commands, while some high-ranked saved opponents earn substantial tomato receipts. This **does not mean the final `main.py` policy never plants tomatoes**: its V219 overlay can independently add a late ten-tomato cohort after day 18. The pilot tested whether replacing route 104's thirteen day-11 strawberry seed purchases and plant requests with tomato, then selling deposited tomato from the shed, could improve two current losses with `FARMERS_MARKET,FARMERS_MARKET` first shops. The third route with that pair, THUNDER THUNDER, was a predeclared winning control. Three other-shop routes were negative controls. All runtime inputs are observation-legal; the experimental copy is `exp_farmers_tomato13_20260926.py`.

The candidate changed 13 planned seed units and 13 planned plant actions on route 104. The six-route screen ran both seats, all 12 games DONE. Exact action hashes/seeds match the saved current top-100 incumbent panel.

| Route | Incumbent paired margin | Candidate paired margin | Result |
| --- | ---: | ---: | --- |
| Arda Ceylan | -41,703 | -38,822 | Loss remains |
| Artem The Farmer 🍅 | -10,858 | -46,336 | Loss much worse |
| THUNDER THUNDER | +48,319 | -1,696 | **Win reversed** |
| Boey, AI是我的豆包, 3정훈 controls | Unchanged | Unchanged | Route gate inactive |

The exact event traces reveal why the THUNDER control failed. Under native shops, the incumbent's later V219 overlay planted ten tomatoes and sold 80 units for 17,021 coins; the candidate's thirteen early tomatoes caused V219's own-tomato qualification guard to decline that dedicated late cohort. The candidate sold 51 tomato units for only 4,874 coins and lost 16,443 strawberry-receipt coins. Its own terminal cash fell 107,378 → 86,689 in seat 0. Native later shops also diverged, but pinning the incumbent shop sequence **still reversed the same seat** from +20,399 to -332 margin. Thus the failure is not explained solely by shop RNG.

Arda's incumbent V219 branch did not activate: it planted no tomato and sold none. The candidate sold 51 tomatoes for 4,082 coins, raising own seat-0 cash 68,261 → 74,620, but the fixed rival rose 89,307 → 92,628; the loss remained. With incumbent shops pinned, its seat-0 margin was -19,989 versus the incumbent's -21,046. These are development tapes, not adaptive opponents.

## Decision

**Reject the early-cohort replacement as implemented.** It reversed a large winning control and failed both target losses. The mechanistic follow-up below tests whether retaining the late cohort changes this decision. No change to `main.py` or Kaggle.

## Additive follow-up — also rejected

`exp_farmers_tomato13_additive_20260926.py` relaxes V219's own-tomato qualification guard only for route 104; its remaining cash, shop, land, and labor checks still apply. The same frozen six-route panel finished all 12 games DONE. Arda remained -38,822 paired margin, Artem worsened to -47,890, and THUNDER stayed a win but fell from the incumbent's **+48,319 to +11,089**. Other-shop controls remained exact. The additive branch therefore failed the winning-control and loss-rescue gates; do not promote or broaden this cohort.

An exact THUNDER seat-0 event trace confirmed the mechanism: incumbent planted ten tomatoes, sold 80 for 17,021 coins, and earned 43,651 from strawberries. The additive candidate planted **23 tomatoes** and sold 131 for **16,468** coins, while strawberry receipts fell to **27,208**. Its own terminal cash fell 107,378 → 90,671. More tomato units did not replace the displaced strawberry value in this market.

Evidence: `farmers_tomato_additive_6routes.json`, `farmers_tomato_additive_tail.py`, and `thunder_additive.json.gz`.

Evidence: `farmers_tomato_6routes_summary.json`, `farmers_tomato_6routes.json`, `farmers_tomato13_tail.py`, `loss_trace_Arda_s0.json.gz`, `arda_treat.json.gz`, `arda_treat_fixedshops.json.gz`, `thunder_base.json.gz`, `thunder_treat.json.gz`, `thunder_treat_fixedshops.json.gz`, and `summarize_loss_traces.py` in this directory.
