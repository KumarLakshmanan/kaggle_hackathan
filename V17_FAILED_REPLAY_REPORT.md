# V17 Failed-Replay Analysis and Regression Report

## Failures analyzed

| Episode | Opponent | Original result | Root cause |
| --- | --- | ---: | --- |
| 90638959 | mochogo | -316 | Identical production family; same-turn market priority across multiple products |
| 90648579 | MD Concepcion | -3,742 | Different, higher-value industrial production route; much more premium output and far less wheat churn |
| 90649380 | Arun Mallikarjuna | -418 | Identical production family; alternate market-order priority |

The two clone losses were not farm collapses.  Both sides finished with the same
14 animals and empty inventories; the margins came from order sequencing on the
shared nonlinear market.  MD Concepcion was a genuine strategic difference:
its route sold substantially more strawberry, milk, wool, and melon while
buying roughly one quarter as much market wheat.

## V17 architecture

`main.py` now contains two ordinary, readable 719-turn action books.

1. The primary route uses the clean worker plan from the strongest clone family
   and the Arun market-priority policy, which was the strongest clone minimax
   policy in focused testing.
2. The alternate route uses MD Concepcion's industrial plan after removing four
   replay-specific weed-repair scars.
3. The opponent's public money after turn zero selects the compatible route.
   The MD opening uniquely leaves approximately $25; the narrow $18-$32 interval
   avoids classifying unrelated openings as MD.
4. A one-turn bridge purchases the five wheat needed by the MD route because
   V17 keeps the primary route's common turn-zero action.
5. Bounded market counterplay now covers every sellable product, not only
   premium goods, permits batches up to 100, and remains active through turn
   718.  It can only advance quantities already scheduled for the following
   turn and removes those quantities from that following sale.
6. Existing legality checks, hand alignment, shed clamping, stochastic weed
   recovery, complete legal move generation, and final liquidation remain.

No hidden state is used: the branch signal is the opponent farm's public money.

## Exact failed-replay regression

On each replay's original seed, V17 won from both seats:

| Opponent route | Seat 0 margin | Seat 1 margin |
| --- | ---: | ---: |
| mochogo | +41 | +41 |
| MD Concepcion | +787 | +787 |
| Arun Mallikarjuna | +306 | +306 |

## Broader verification

All checks used `kaggle-environments==1.32.5`.

| Check | Result |
| --- | --- |
| Historical 20 routes + 3 failed routes, both seats | **46-0** |
| Paired opponent result | **23-0** |
| Broad-panel mean margin | **+7,861.17** |
| Three failed routes, 3 fresh seeds, both seats | **18-0** |
| Fresh-seed failure margins | **+217 to +860** |
| Self-play | 151,896-151,896; both `DONE`; 720 frames |
| Broad-panel mean decision time | 0.378 ms |
| Self-play maximum observed decision time | 122.448 ms |
| Compile | PASS |
| Encoded/encrypted construct scan | none found |

Result files:

- `benchmark_results/v17_portfolio_current23_panel.json`
- `benchmark_results/v17_failed_routes_multiseed.json`
- `benchmark_results/v17_main_self_validation.json`
- `benchmark_results/md_route_current20_panel.json`

Final `main.py` SHA-256:

`7B1B3DAB2CCE79EFB318A57F9961295EB16969015E1E3A9B6CE9D6EBBD14F684`

These tests establish empirical coverage of every supplied failure and the
captured historical panel.  They cannot mathematically guarantee a win against
every future strategy or an identical copy, which must tie.
