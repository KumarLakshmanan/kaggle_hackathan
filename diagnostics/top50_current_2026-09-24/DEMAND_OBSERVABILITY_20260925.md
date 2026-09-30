# When the strawberry commitment precedes the demand signal

Two frozen `main.py` native event traces provide a useful limit on the
low-price-strawberry hypothesis. The agent's **first** strawberry seed purchase
occurs at step 130 (day 5) in both routes, before the second shop unlock at
step 144 (day 6). It ultimately buys 33 seeds and sells 247 strawberries in
each game, according to the reconciled [12-route ledger](LEDGER_12_ROUTE.md).

| Route | Shops visible at first strawberry buy | Shops visible at day-6 route choice | Executed strawberry receipts | Own final cash |
| --- | --- | --- | ---: | ---: |
| ActiveMusyoku 112941285 loss | `PIZZA_SHOP` | `PIZZA_SHOP`, `BAKERY` | 2,648 | 60,243 |
| Gleb Tumanov 112939403 winning control | `BAKERY` | `BAKERY`, `PET_CAFE` | 23,655 | 77,957 |

Neither first shop directly demands strawberry. The differing future shops and
market paths can explain a large part of the receipt contrast, but those
future outcomes are unavailable at the first purchase. The installed 1.32.7
interpreter draws each shop type with replacement at an unlock; it does not
guarantee that currently weak strawberry demand stays weak, nor that a shop
supporting strawberry arrives. The two first-shop states differ, so these
routes are not identical-observation counterfactuals; they are evidence of
early commitment under uncertainty, not proof that no early predictor exists.

Consequently, an observation-legal sizing policy must quantify the option
cost of waiting or diversification over future demand, not use the realized
future shop path to decide retrospectively. The prior late-tomato Half/Omit
pilot did not test this early strawberry decision. No policy edit or Kaggle
submission was made from these traces.

## Early omission ablation

A separate readable candidate, `exp_early_strawberry_omit_20260925.py`, omits
the incumbent's full strawberry seed purchases and plant commands when the
first visible shops lack strawberry demand. This observation-time rule
triggered in both of the above routes and suppressed 33 seed units and 33
plant commands in each. It leaves incumbent hires and later task scheduling
unchanged, so it is an economic screen, **not** a coherent production planner.

| Route | Native baseline own/rival | Native omission own/rival | Matched-shop baseline own/rival | Matched-shop omission own/rival |
| --- | ---: | ---: | ---: | ---: |
| ActiveMusyoku loss, seat 0 | 60,243 / 76,276 | 92,040 / 97,632 | 60,243 / 76,276 | 62,088 / 77,294 |
| Gleb winning control, seat 0 | 77,957 / 77,114 | 52,287 / 97,475 | 77,957 / 77,114 | 58,706 / 103,204 |

Both candidate seats also lost in the native screen, all `DONE`. On the loss,
the spectacular native own-cash increase (+31,797) shrank to **+1,845** under
the baseline's exact forced shop sequence; the loss remained a loss. On the
control, omission destroyed own cash (−19,251 even under matched shops) and
reversed a baseline win. With native dynamics, removing the plants changed
the **second** shop drawn at step 144 in both games, before the incumbent's
day-6 route choice. The native and controlled results therefore measure
different continuations; the native gain is not a robust crop-profit estimate.
Reject this rule; do not promote it or tune a replay-specific exception. The
pilot does not rule out a diversified or dynamically serviced portfolio, but
it rules out claiming this simple omission handles both adverse and favorable
market paths.

Source files: `demand_active_low_trace_20260925.json.gz` and
`demand_gleb_control_trace_20260925.json.gz` in this directory. Their scores
match the frozen top-50 benchmark.
The pilot output is `early_straw_omit_two_route_native_20260925.json`; matched
baseline/candidate and native-candidate traces are named
`demand_{active,gleb}_{base,omit}_fixedshops_trace_20260925.json.gz` and
`demand_{active,gleb}_omit_native_trace_20260925.json.gz`.
