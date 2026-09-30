# Top-50 fixed-replay loss clusters — sidecar diagnosis (2026-09-24)

## Scope and reproduction

This analyzes the frozen [100-route benchmark](main_100routes.json) against the 100 original [source action tapes](routes/summary.json), selected from 50 leaderboard teams. It is an **offline, fixed-action replay**, not 100 adaptive opponents or an estimate of leaderboard rank. The benchmark candidate is `H:\hackathan\main.py` SHA-256 `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`, engine 1.32.7; the manifest SHA-256 is `7b242129364b287d197a8c18964d6b9da9b990c68ebc39f1d087782bfc3b27e9`. The read-only [sidecar](loss_cluster_sidecar_20260924.py) verifies the benchmark and manifest hashes, all 100 tape-action hashes and lengths, seat/pair arithmetic, and the 50-team/33-loss counts. Its optional trace mode additionally requires the current `main.py` to match the frozen hash. From `H:\hackathan`:

```powershell
python -B -X utf8 diagnostics/top50_current_2026-09-24/loss_cluster_sidecar_20260924.py --markdown
```

A *route loss* means the sum of its two candidate margins (candidate in seats 0 and 1) is negative. There are **67 route wins / 33 losses**, **133 seat wins / 67 seat losses**, and all 200 games finished `DONE`. Use the 100 individual route pairs, **not** the seed-grouped `paired_results`: different selected routes can share an episode seed (91 distinct episode IDs). The table below gives cash averaged across the two seats, but the margin is the **sum** across them. Reward is final cash, not inventory value. Source reward is the recorded team's cash in its original public episode with a different opponent; “replay − source” is descriptive, not a causal treatment effect.

Clustering is deliberately transparent rather than a fitted model. The panel-wide median candidate cash is **107,190**, and median replay-opponent cash is **87,925**. Losses are tagged `own-low` if our cash is below its median, `rival-high` if opponent cash is above its median, and `both` if both conditions hold. These are **score symptoms**, not mechanism labels or estimates of how much cash an intervention would recover.

| Cluster | Routes | Sum of paired deficits | Median own cash | Median rival cash |
| --- | ---: | ---: | ---: | ---: |
| rival-high | 11 | -176,136 | 113,921 | 122,899 |
| both | 15 | -335,167 | 90,136 | 102,267 |
| own-low | 7 | -56,962 | 63,262 | 69,174 |

Thus **22/33** losses include low own cash, **26/33** include high opponent cash, and **15/33** include both. Calling every loss “our production failure” would be wrong: Excluding's largest loss has our 116,023 cash, above our panel median. Calling every loss “strong opponent” would also be wrong: the marwar22 and low-cash Yannik replays are near ties in weak-cash worlds.

## Mechanisms to test, with executed evidence

### 1. Late shop demand can strand an early-committed product mix at low sale prices

The candidate's [router](../../main.py) chooses its main tape at day 6 from only the first two observed shop unlocks, then does not make a new route choice until day 27 (`_router`); later shops still move market demand and prices. In the rank-49 ActiveMusyoku route, episode 112941285, the native shops began `PIZZA_SHOP, BAKERY`, then added `BAKERY, PET_CAFE, PIZZA_SHOP, PET_CAFE, SMOOTHIE_SHOP, YARN_STORE`. Our **247 executed strawberry sales yielded only 2,648** (about 10.7/unit); 228 milk sales yielded 21,179 and 102 wool sales 7,752. Our final cash was **60,243** versus **76,276**. This is a realized-price problem, not an inference from attempted tape orders; our final shed was empty in the traced seat. The shop roster contains little strawberry/milk pull until late, while the fixed production plan keeps selling those goods into a glutted market.

One diagnostic intervention used the same seed, candidate, seat, and original fixed opponent tape, retaining the first two shops *exactly* (`PIZZA_SHOP, BAKERY`) and forcing only later unlocks to `SMOOTHIE_SHOP, YARN_STORE, PIZZA_SHOP, ICE_CREAM_SHOP, SMOOTHIE_SHOP, BRUNCH_SPOT`. The modified-environment result was our **118,160** versus opponent **100,717**. Strawberry units stayed **247**, but receipts rose **2,648 → 13,392**; milk receipts **21,179 → 55,671** and wool **7,752 → 25,962**. Our cash gained **57,917** and opponent cash gained **24,441**; the one-seat margin moved **−16,033 → +17,443**. This isolates the importance of *later shop sequence conditional on the same first-two-shop route choice*; it does **not** isolate a single item price from subsequent policy, market, and fixed-tape responses. A second, more confounded all-eight-shop replacement (`SMOOTHIE_SHOP, BRUNCH_SPOT, SMOOTHIE_SHOP, YARN_STORE, PIZZA_SHOP, ICE_CREAM_SHOP, SMOOTHIE_SHOP, BRUNCH_SPOT`) moved our cash to 169,806; do not treat either artificial path as a native match or expected gain.

**Controlled experiment:** Introduce a small, observation-legal late-demand guard after each observed shop unlock: recompute marginal, deliverable value of the remaining crop/animal schedule using public shops, current market inventory/prices, owned tiles, seed stock, worker slots, and time to harvest. On low expected net value, stop *new* purchases/plantings for the saturated product or swap only already-owned feasible lanes; preserve sunk output and sale capacity. Compare guard off/on on the same routes, seeds, and both seats, recording executed per-product units, cash receipts, purchase/labor costs, shed overflow, and own cash separately from opponent cash. First force the baseline shop sequence for both arms to estimate the direct policy effect; then run native shop RNG and fresh routes/reactive agents. Require improvement on multiple adverse-demand worlds without losing high-demand worlds. No episode ID, team name, or seed belongs in the trigger.

### 2. Favorable observed demand can be captured more fully by rival production capacity

The rank-25 Excluding route, episode 112933084, is the cleanest *opponent-cash* example: our cash **116,023** is normal-to-high, but the fixed rival route reaches **155,219** (source episode cash **115,320**, replay increase **39,899**). Native shops include two `PIZZA_SHOP` and three `FARMERS_MARKET` instances by day 15. The **public farm observation** shows 10 rival tomato tiles at day 15, 34 at day 18, and 35 at days 21/24; we had zero at day 18 and 10 at days 21/24. Our own executed trace confirms ten tomato plant actions on day 18, 500 spent on tomato seeds, and ultimately **80 own tomato sales for 16,362** (about 205/unit). At day 24 we led in public cash **69,094 to 61,236**, but by day 27 trailed **83,135 to 127,701**. This is consistent with an early capacity/mix/timing gap in a favorable tomato market, but **does not identify the rival's private inventory, sales, or product-level profit**, nor prove that copying its acreage would pay for our displaced work. Our [existing tomato branch](../../main.py) already has a strict observation-based gate and a ten-seed request, so the hypothesis is **incremental capacity/timing/servicing**, not “add tomatoes from scratch.”

**Controlled experiment:** On observed tomato-supporting shop demand and public price, test a *bounded incremental* tomato lane or earlier commitment against the current ten-seed baseline. Gate on cash after mandatory spending, owned free tiles, days remaining to first yield, water/harvest worker reservations, shed and ten-order market capacity, and a conservative sale-price scenario; abort if any certificate fails. Predeclare 0/2/4 incremental lanes rather than tuning to Excluding. Run the same route/seed/seat with the baseline shop sequence forced for both arms, then native shops and independent later episodes; inspect confirmed plants, water, harvest, deposits, tomato units/receipts, displaced product receipts, net own cash, and rival cash. A previous four-tile pilot in [RESULTS.md](RESULTS.md) did not generalize, so this is a falsifiable experiment, not a recommended promotion.

## Static-tape and shop-path cautions

- **Attempted actions are not executed economics.** Boey episode 112939032 contains 14,137 intended `SELL` units in its accessible source tape, but a tape command does not prove inventory existed or the order committed in our replay. The only opponent performance claim used here is its **public final cash, 129,837**; our own cash was 103,125. Our trace confirms 33 failed own empty-shed sell-unit attempts and an empty final own shed. For policy diagnosis, use successful **own** market commits and costs, and public rival farm/cash—not inferred rival inventory or gross rival trade volume.
- **Fixed replays can suppress or amplify the recorded opponent's cash.** Across the 67 route wins, median `(replay opponent cash − source team cash)` is **−24,060**; across the 33 losses it is **−63**. Excluding's +39,899 is an amplification. The original source match had another opponent; our new market supply, lockstep orders, and possibly shops change the economics of the same action tape. This comparison is not an estimate of live-opponent behavior. A matched reactive-agent test is needed before claiming competitive improvement.
- **A seed does not by itself hold the shop path fixed under policy changes.** In engine 1.32.7, `_end_of_day` seeds an RNG by seed/day, calls `_spawn_weeds` over *empty* tiles on both farms, then draws the next shop from that same RNG. Changing occupancy changes the number of RNG draws before the shop selection. The [event harness](../../trace_paired_game_events.py) can force a reference shop sequence or use a diagnostic fixed-draw-count weed rule; both alter the environment and must be labeled counterfactuals. A/B runs on the same seed can otherwise mix policy effects with a different shop path. Even forced shops do not freeze market prices or opponent execution, so report own and rival cash separately.

## Rank, episode, and seat dependence

Losses by snapshot rank band are **2/20** (1–10), **5/20** (11–20), **7/20** (21–30), **8/20** (31–40), and **11/20** (41–50). This is a selected two-route-per-team panel, not a monotonic strength calibration. At team level, 26/50 are two wins, 15/50 split, and 9/50 two losses. For example, rank-4 Majkel1337 loses episode 112931031 by a paired 27,560 but wins its second route by 176,876; rank-30 Yannik Schiffner narrowly loses both sampled routes while our cash changes **63,262 → 144,082** and rival cash **64,538 → 144,247**. Those Yannik routes have different seeds, action tapes, and shops; the contrast shows episode dependence, not shop-only causality. In 84/100 routes both seat runs had identical cash outcomes; only one route had opposite seat win/loss signs (arutyunoff episode 112928929, seat margins +41,674 and −709). Retain both seats for regressions, but do not treat their near-duplication as 200 independent route observations.

The finalized event-trace evidence covers **five distinct native games**, all candidate seat 0: Boey 112939032, Excluding 112933084, ActiveMusyoku 112941285, and Yannik Schiffner 112935652/112937001. Each exactly reproduced its stored candidate and opponent final cash. Excluding was executed three times while developing/checking the in-memory daily ledger (one diagnostic-print attempt failed after the simulation, then was corrected); two additional **modified-environment** simulations were run only for ActiveMusyoku. Thus there were **nine simulator executions total**, not a full-panel rerun, and no trace files were stored. To reproduce a native sample, for example:

```powershell
python -B -X utf8 diagnostics/top50_current_2026-09-24/loss_cluster_sidecar_20260924.py --trace 49:112941285:0
```

For the later-shop intervention, append `--force-shops PIZZA_SHOP,BAKERY,SMOOTHIE_SHOP,YARN_STORE,PIZZA_SHOP,ICE_CREAM_SHOP,SMOOTHIE_SHOP,BRUNCH_SPOT`. For the reconciled **own** daily ledger and public farm snapshots on the Excluding exemplar, use `--trace 25:112933084:0 --public-ledger`. Tracing is optional and intentionally targeted; the default and `--markdown` modes read only stored evidence.

## Next diagnostic before any broad allocator — preselected, not yet run

The current three score strata cannot distinguish **capacity/mix/timing**, **cohort yield/service**, and **realized sale price** on all losses. GPT-6 Pro's proposed next step is an exact daily-cash and commitment/event study on **12 routes × both candidate seats = 24 games**. That exceeds this sidecar's small fresh-simulation scope, so **it has not been run**. The panel is fixed now, before inspecting those new traces:

```powershell
python -B -X utf8 diagnostics/top50_current_2026-09-24/loss_cluster_sidecar_20260924.py --preselect-ledger-panel
```

The six losses are both routes from three double-loss teams spanning rival-high/mixed/own-low symptoms: Excluding, Boey, and ActiveMusyoku. For each loss, the sidecar greedily selects one **both-seat-winning**, distinct-team/episode control in the same rank decile. It excludes controls where public replay-opponent cash differs from that route's public source reward by over 25,000 (an obvious tape-collapse/spike risk), then minimizes `|source cash gap| + 2,000×|rank gap| + 5,000×source-seat mismatch`. This is a transparent diagnostic matching rule, **not** balance on shop paths or a statistically exchangeable control group. Source reward/seat/rank select cases only; none would become policy inputs.

| Role | Matched loss episode | Rank | Team | Episode | Source seat | Source cash | Route file |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| loss | — | 25 | Excluding | 112933084 | 0 | 115,320 | `Excluding-submission-56489132-episode-112933084-seat0.json.gz` |
| loss | — | 25 | Excluding | 112933589 | 0 | 102,330 | `Excluding-submission-56489132-episode-112933589-seat0.json.gz` |
| loss | — | 35 | Boey | 112939032 | 1 | 129,977 | `Boey-submission-56521745-episode-112939032-seat1.json.gz` |
| loss | — | 35 | Boey | 112940236 | 1 | 99,944 | `Boey-submission-56521745-episode-112940236-seat1.json.gz` |
| loss | — | 49 | ActiveMusyoku | 112937075 | 0 | 86,969 | `ActiveMusyoku-submission-56512423-episode-112937075-seat0.json.gz` |
| loss | — | 49 | ActiveMusyoku | 112941285 | 0 | 76,034 | `ActiveMusyoku-submission-56512423-episode-112941285-seat0.json.gz` |
| win-control | 112933084 | 27 | Sida Zuo | 112937057 | 0 | 119,099 | `Sida-Zuo-submission-56488930-episode-112937057-seat0.json.gz` |
| win-control | 112933589 | 24 | HowardLeeTW | 112935831 | 0 | 86,969 | `HowardLeeTW-submission-56463813-episode-112935831-seat0.json.gz` |
| win-control | 112939032 | 39 | Ryo Hasegawa | 112931133 | 0 | 117,213 | `Ryo-Hasegawa-submission-56506377-episode-112931133-seat0.json.gz` |
| win-control | 112940236 | 37 | istinetz | 112939139 | 0 | 87,808 | `istinetz-submission-56520762-episode-112939139-seat0.json.gz` |
| win-control | 112937075 | 47 | ra5anchor | 112938191 | 1 | 80,480 | `ra5anchor-submission-56500198-episode-112938191-seat1.json.gz` |
| win-control | 112941285 | 50 | Gleb Tumanov | 112939403 | 1 | 76,496 | `Gleb-Tumanov-submission-56357593-episode-112939403-seat1.json.gz` |

For each future game, record **our** exact day-open/day-close cash and successful `SELL` receipts by product, plus `BUY_SEED`, `BUY_ANIMAL`, `BUY_PRODUCT`, `HIRE`, and `BUY_LAND` spending. Reconcile each day as `opening cash + receipts − costs = closing cash`, and tie the final close to benchmark reward. Mark the first consequential differences in purchases, land/worker commitments, confirmed `PLANT`/`PLACE`, daily `WATER`/`FEED`/`CARE`, harvest, deposit, successful sale units, and per-unit receipt. Track our own seeds/shed/cargo and cohort planted/placed dates. For the rival, use **only public farm tiles/cohorts, public cash, shops, and market prices** visible in observations; never infer rival private shed, seed inventory, or hidden trade P&L from its tape.

Classify the **first consequential divergence** before prescribing a fix: (1) fewer/late feasible own commitments or wrong product mix suggests capacity/mix/timing; (2) comparable commitments but fewer confirmed care, yield, harvest, or deposits suggests cohort service; (3) comparable executed sale units but lower own receipts suggests realized price; (4) comparable receipts but greater spending suggests cost/order timing. Different routes can start on different shop/price paths, so the matched win controls generate hypotheses only. A causal policy test must then toggle **one observation-legal mechanism on the same route/seed/seat**, first with the same forced baseline shop path and then native shop RNG, before fresh-route/reactive validation. Do **not** promote a broad allocator from the three descriptive clusters.

**Evidence still missing:** the full 12-route/24-game reconciled ledger and raw commitment/service event traces; public cohort-age and service comparisons for all pairs; a decomposition of own missing units versus lower unit price versus extra cost at the first divergence; and a matched reactive-opponent check. The one completed Excluding seat-0 ledger reconciles all 30 days (e.g., day 18: 43,550 opening + 5,704 receipts − 5,220 costs = 44,034 closing) and confirms ten own tomato plants, but it cannot stand in for the preselected panel or prove whether more acreage would improve net cash.

## All 33 route losses

Generated verbatim by the sidecar's `--markdown` mode. `Own cash / seat` and `Rival cash / seat` are the two-seat averages. `Paired margin` is the two-seat sum; `Replay − source rival cash` compares the two-seat replay average with the public episode's original team cash. Decimal halves are retained where seats differ.

| Rank | Episode | Team | Cluster | Own cash / seat | Rival cash / seat | Paired margin | Replay − source rival cash |
| ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 4 | 112931031 | Majkel1337 | rival-high | 113,921.0 | 127,701.0 | -27,560 | +3,269.0 |
| 8 | 112938063 | THIRD FARM CLUB | both | 97,931.0 | 110,731.0 | -25,600 | +3,784.0 |
| 13 | 112936995 | TheEggman | rival-high | 108,201.0 | 114,800.0 | -13,198 | +131.0 |
| 13 | 112938025 | TheEggman | both | 86,974.0 | 97,228.0 | -20,508 | -13,552.0 |
| 16 | 112927794 | Otter Vibe | both | 74,562.0 | 87,932.0 | -26,740 | -13,393.0 |
| 16 | 112928740 | Otter Vibe | own-low | 68,924.0 | 69,174.0 | -500 | -41,239.0 |
| 20 | 112934493 | marwar22 | own-low | 57,331.0 | 57,415.0 | -168 | -26,379.0 |
| 23 | 112932388 | 摆烂小分队 🏆 | both | 90,135.5 | 97,068.5 | -13,866 | -4,658.5 |
| 25 | 112933084 | Excluding | rival-high | 116,023.0 | 155,219.0 | -78,392 | +39,899.0 |
| 25 | 112933589 | Excluding | both | 100,084.0 | 102,267.0 | -4,366 | -63.0 |
| 27 | 112932388 | Sida Zuo | both | 85,117.0 | 103,802.5 | -37,371 | -770.5 |
| 28 | 112940186 | midnq | both | 81,731.0 | 88,505.0 | -13,548 | -12,377.0 |
| 30 | 112935652 | Yannik Schiffner | own-low | 63,262.0 | 64,538.0 | -2,552 | -41,417.0 |
| 30 | 112937001 | Yannik Schiffner | rival-high | 144,082.0 | 144,247.0 | -330 | +16,867.0 |
| 31 | 112937931 | Planned Economy | both | 100,224.0 | 115,830.0 | -31,212 | +649.0 |
| 32 | 112940595 | AI是我的豆包 | rival-high | 109,402.0 | 112,514.0 | -6,224 | +28,506.0 |
| 34 | 112938990 | ShunkiKyoya | rival-high | 109,149.0 | 113,366.0 | -8,434 | +11,330.0 |
| 34 | 112939287 | ShunkiKyoya | both | 86,470.0 | 104,644.0 | -36,348 | +1,788.0 |
| 35 | 112939032 | Boey | both | 103,125.0 | 129,837.0 | -53,424 | -140.0 |
| 35 | 112940236 | Boey | both | 79,886.0 | 99,863.0 | -39,954 | -81.0 |
| 38 | 112937735 | chungkuangwen | rival-high | 122,588.0 | 127,469.0 | -9,762 | -915.0 |
| 39 | 112939378 | Ryo Hasegawa | both | 103,301.0 | 106,088.0 | -5,574 | +522.0 |
| 41 | 112939353 | dodsters | rival-high | 122,653.0 | 124,690.0 | -4,074 | -85.0 |
| 43 | 112936562 | Gatswei | both | 103,925.0 | 110,493.0 | -13,136 | +84.0 |
| 44 | 112939452 | feles99 | both | 89,029.0 | 89,202.0 | -346 | +5,463.0 |
| 45 | 112936862 | hiroshi murakami | own-low | 61,929.0 | 62,095.0 | -332 | -623.0 |
| 45 | 112938179 | hiroshi murakami | rival-high | 109,472.0 | 111,319.0 | -3,694 | -120.0 |
| 47 | 112927292 | ra5anchor | rival-high | 114,014.0 | 116,235.0 | -4,442 | +11,618.0 |
| 48 | 112938886 | URAD | own-low | 67,907.0 | 70,346.0 | -4,878 | -1,266.0 |
| 48 | 112940084 | URAD | rival-high | 112,886.0 | 122,899.0 | -20,026 | -611.0 |
| 49 | 112937075 | ActiveMusyoku | own-low | 79,685.0 | 87,918.0 | -16,466 | +949.0 |
| 49 | 112941285 | ActiveMusyoku | own-low | 60,243.0 | 76,276.0 | -32,066 | +242.0 |
| 50 | 112939219 | Gleb Tumanov | both | 92,571.0 | 99,158.0 | -13,174 | +1,322.0 |
