# Smoothie-gated wheat-to-strawberry crop-cycle pilot — 2026-09-26

## Hypothesis and panel

The refreshed rank-11 saved route for 吃白饭的大肥鱼 earned 61,201 strawberry-sale coins against our 46,284, with 41 rival versus 33 own strawberry plants confirmed over the episode. The observation-legal candidate `exp_smoothie_straw_20260926.py` replaced exactly funded WHEAT seed purchases and PLANT commands in route 116's day-11 cohort only if the first three observed shops were `PET_CAFE,BRUNCH_SPOT,SMOOTHIE_SHOP`. It made the same replacement in the day-12 cohort only when the fourth shop was also `SMOOTHIE_SHOP`. The two windows have eleven and eight seed/plant requests. It did not use opponent identity or future shops.

The predeclared six-route panel included that fresh top-20 loss, two earlier `PET_CAFE,BRUNCH_SPOT` winning controls, and three other-shop controls. Both seats were run under native engine 1.32.7; all 12 games finished DONE. Only the target activated, changing 19 seed units and 19 plant commands per game. Its paired margin **worsened -21,358 → -26,796**; the other five routes reproduced the incumbent exactly. There was no rescue.

An exact event trace on target seat 0 found 52 confirmed strawberry plants versus 33 in the incumbent, and 65 more executed strawberry sale units for **+8,489** receipts. The longer-lived replacement crowded out later cycles: 115 fewer carrot sale units (**-6,417** receipts), 128 fewer wheat sale units (**-4,456** receipts), 3,256 more wheat-product spending, and 1,900 more strawberry-seed spending. Own final cash fell **105,386 → 98,567**, while fixed-rival cash fell 116,065 → 111,965. The shops were identical in both runs. These figures describe complete replay effects; individual components are not separable causal treatments.

**Decision: reject.** The pilot proves the proposed crop-cycle swap can increase the target product's output yet lower net cash and paired margin. A viable dynamic crop plan must account for subsequent wheat/carrot occupation, animal feed, full worker schedule, seed funding, harvest, delivery, and sales. No `main.py` edit or Kaggle upload.

Evidence: `create_smoothie_panel.py`, `smoothie_straw_6routes_summary.json`, `smoothie_straw_6routes.json`, `smoothie_straw_tail.py`, `smoothie_team_treat_trace_s0.json.gz`, and `diagnostics/top20_refresh_2026-09-26/top20_team_trace_s0.json.gz`.
