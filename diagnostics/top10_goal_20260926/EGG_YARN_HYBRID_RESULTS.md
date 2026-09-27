# Complete mixed-herd route pilot — 2026-09-26

## Hypothesis

The refreshed top-100 DSM saved route beat local `main.py` by 17,199 coins
per seat with first shops `BRUNCH_SPOT,YARN_STORE`. Its executed ledger shows
203 eggs sold for 11,921 coins, while our yarn-heavy route sold zero eggs.
The standard router forces route 9 whenever Yarn Store appears; it does not
consider whether an egg shop was also observed. I tested three existing,
complete, precomputed mixed-herd routes (100, 101, 117) for the two visible
shop orders containing Brunch Spot and Yarn Store. No route is selected by
opponent identity, episode, seed, or future shops. The experiment changes the
whole day-6 onward schedule rather than isolated animal orders.

Before running candidates, `create_egg_yarn_panel.py` froze four older
original-shop routes with this shop pair: three baseline losses (Gleb
Tumanov, ShunkiKyoya, keiz) and one winning control (Matin Urdu), plus the
new DSM loss. Both seats were tested for each route. All 40 candidate-plus-
baseline seat-games ended `DONE`; there were no status failures.

| Saved route | Current paired margin | Route 100 | Route 101 | Route 117 |
| --- | ---: | ---: | ---: | ---: |
| DSM | -34,398 | -43,740 | -35,096 | -50,462 |
| Gleb Tumanov | -8,326 | -5,430 | +3,444 | -6,358 |
| Matin Urdu, winning control | +50,236 | +67,819 | +46,046 | +33,218 |
| ShunkiKyoya | -6,882 | -39,618 | -31,102 | -43,558 |
| keiz | -42,646 | -62,088 | -51,704 | -69,468 |

Route 101 rescued Gleb but worsened DSM and the other two losses, with a
24,220-coin paired-margin regression on ShunkiKyoya. Routes 100 and 117
rescued no loss and also materially worsened ShunkiKyoya and keiz. Egg sales
alone did not cover the lost wool, wheat, and other effects of a full route
switch. The source DSM trace and `analyze_top20_loss_traces.py` ledger are in
`diagnostics/top100_refresh_2026-09-26/DSM_trace_main_s0.json.gz`.

**Decision: reject all three route switches.** The five-route original-shop
pilot failed before any broad fixed-panel or reactive treatment run; those
further runs would not rescue the hypothesis that a single mixed route is
safe for this observed shop pair. `main.py` and Kaggle were unchanged.

Evidence: `egg_yarn_5routes_summary.json`, `egg_yarn_route100_5routes.json`,
`egg_yarn_route101_5routes.json`, `egg_yarn_route117_5routes.json`,
`create_egg_yarn_panel.py`, and `build_egg_yarn_hybrid.py`.
