# Early cow-to-goose bundle — 2026-09-26

## Question and implementation

The existing cow-to-goose planner favors goose economically on the saved Boey
route but cannot rewrite the already-built pasture when it decides at turn 169.
`CS_PREBUILD_DIAGNOSIS.md` records the turn-level cause. I built separate
experimental candidates that decide at turn 153 from public unlocked shops,
rival geese, and the existing planner state. The complete bundle changes the
pasture build, animal buy, pickup, placement, and later egg sales. It uses no
episode ID, opponent name, seed, or unrevealed future shop. The two final
variants convert either two planned sites or one site at `(6,4)`:

| Candidate | SHA-256 | Physical sites in every activated saved route |
| --- | --- | --- |
| `exp_early_goose_gated_20260926.py` | `2525f6fb71e3b5ac379cc8e44b64d7f000049e5789c13df9adf0c9dd28ff8035` | Two |
| `exp_early_goose_gated_one_site_20260926.py` | `cca6d84d8ac2950b610cea2d56b7df8d9017be2f184547ac2839b938b1ce9c1c` | One |

The complete two-site pilot selected Boey, Gatswei, and Planned Economy and
improved all three. It left ActiveMusyoku, QQ, and Ryo at exact baseline cash
and actions; QQ and Ryo already had successful earlier planner goose swaps.
Earlier ungated and incomplete pilots were not eligible for promotion. The
six-route pilot artifacts and builder/tail files are in this directory.

## Matched saved-action panels

The September 25 top-100 development panel has 100 distinct action tapes,
each tested in both seats with the original shop sequence. Every run below
ended `DONE`, and the final variants recorded zero wrapper errors.

| Policy | Paired route wins | Seat wins | Rescues | Reversals | Activated routes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Current `main.py` | 59/100 | 118/200 | — | — | — |
| Two sites | 59/100 | 118/200 | Hikaru Umeda | lingxiaojun | 10 |
| One site | 60/100 | 120/200 | Hikaru Umeda | 0 | 10 |

On the two-site run, total own cash rose 37,316 while rival cash rose 37,278
across the panel: aggregate margin gained only 38 coins. One-site own cash
rose 24,142 and rival cash rose 18,850, net margin +5,292. The one-site
Hikaru rescue changed the paired margin from -196 to +2,902. The same policy
worsened three activated routes, notably elmo by 5,264, trantrikien239 by
3,536, and lingxiaojun by 2,360 paired-margin coins. Boey improved by 2,110
but remained a loss (-13,606 paired margin).

On the separately refreshed September 26 top-20 fixed-action panel, the
one-site version stayed at **17/20** route wins. It improved TheEggman's
paired margin by 2,556 without rescuing that loss, worsened
吃白饭的大肥鱼 by 12,624 while it remained a loss, and worsened Azat Akhtyamov
by 2,670 while remaining a win. All 40 games ended `DONE`. This is another
saved-action check, not independent adaptive validation.

## Native reactive checks

Against the current `main.py` reacting normally, each experiment used a
fresh, predeclared 16-seed block, both seats, plus matched main-vs-main
controls. All 128 games across the two blocks ended `DONE`.

| Candidate | Seeds | Activated games | Treatment margin sum across 32 games | Matched control margin sum |
| --- | --- | ---: | ---: | ---: |
| Two sites | 2610200–2610215 | 2 | +4,678 | 0 |
| One site | 2610216–2610231 | 4 | -2,020 | 0 |

Two sites activated only on seed 2610213 and gained +2,339 per seat: own
cash +2,429, rival cash +90. One site activated on seeds 2610228 and
2610229 and lost -268 and -742 per seat respectively. Own cash rose +455
and +1,063, but rival cash rose more (+723 and +1,805). Cross-testing the
two sizes on these same three seeds found one site +1,420 versus two sites
+2,339 on 2610213; one site -268/-742 versus two sites -1,651/-1,819 on
2610228/2610229. Extra goose production magnified both gains and losses.

At turn 153, seeds 2610213 and 2610228 had the same shops
`BRUNCH_SPOT,PET_CAFE`, the same cow/melon/sheep/strawberry/wheat counts on
both farms, and the same quoted egg and milk prices. By turn 696 their
unlocked shop lists differed: the winning seed had two milk-shop entries,
while 2610228 had four. Seed 2610229 also had four milk-shop entries. The
different future shops and market effects are consistent with the result, but
this small comparison does not isolate their causal contributions. The day-6
public gate cannot distinguish the first two seeds from those visible facts;
the saved routes cannot establish an adaptive win rate.

## Decision

**Reject both variants for promotion.** One-site has a one-route gain on a
reused fixed-action development panel but no win-count gain on the refreshed
top-20, and its fresh reactive block lost margin when activated. Two sites
reversed a saved-route win and has even larger losses on the adverse reactive
seeds. `main.py` remains SHA-256
`6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`;
there was no Kaggle upload. The next economic planner should optimize
**expected final margin against the rival**, including future-shop
uncertainty and market effects, instead of own animal revenue alone.

Evidence: `early_goose_gated_top100_routes.json`,
`early_goose_gated_top100_comparison.json`,
`early_goose_gated_one_site_top100_routes.json`,
`early_goose_gated_one_site_top100_comparison.json`,
`early_goose_gated_one_site_top20_refresh.json`,
`reactive_early_goose_fresh.json`,
`reactive_early_goose_one_site_fresh.json`,
`early_goose_two_site_cross_2610228_29.json`,
`early_goose_one_site_cross_2610213.json`, and
`early_goose_reactive_dose_capture153.json`, and
`early_goose_reactive_dose_capture696.json`.
