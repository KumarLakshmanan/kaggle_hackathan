# Boey rank-35 sell-attempt diagnosis — 2026-09-25

## Scope and frozen inputs

This is an offline replay diagnostic against the exact captured opponent tapes. Boey episodes 112939032 and 112940236 are both rank-35 loss routes. The two preselected winning controls are Ryo Hasegawa 112931133 (clear high-cash win) and Gleb Tumanov 112939403 (thin positive lower-cash win). Every route is replayed with our agent in both seats. The frozen baseline `main.py` SHA-256 is `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`; capture mode refuses to run if it differs.

## Native baseline results

| Route | Seat | Our terminal cash | Rival terminal cash | Margin | Empty-shed SELL units | Quoted-price sum* | After same-step sale | No prior same-step sale | Direct on-access execution ceiling‡ | Successful SELL units / receipts | Final carried → terminal sells† |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| boey_112939032_s0 | 0 | 103,125 | 129,837 | -26,712 | 33 | 2,100 | 14 | 19 | ≤101 | 1574 / 128,464 | CARROT 3/3, WHEAT 2/2, WOOL 1/1; final shed empty=True |
| boey_112939032_s1 | 1 | 103,125 | 129,837 | -26,712 | 33 | 2,100 | 14 | 19 | ≤101 | 1574 / 128,464 | CARROT 3/3, WHEAT 2/2, WOOL 1/1; final shed empty=True |
| boey_112940236_s0 | 0 | 79,886 | 99,863 | -19,977 | 48 | 1,956 | 21 | 27 | ≤129 | 1614 / 104,374 | CARROT 3/3, EGG 8/8, FERTILIZER 2/2, WOOL 3/3; final shed empty=True |
| boey_112940236_s1 | 1 | 79,886 | 99,863 | -19,977 | 48 | 1,956 | 21 | 27 | ≤129 | 1614 / 104,374 | CARROT 3/3, EGG 8/8, FERTILIZER 2/2, WOOL 3/3; final shed empty=True |
| control_gleb_112939403_s0 | 0 | 77,957 | 77,114 | 843 | 38 | 2,300 | 14 | 24 | ≤359 | 1592 / 102,932 | CARROT 5/5, EGG 8/8, FERTILIZER 1/1, WOOL 1/1; final shed empty=True |
| control_gleb_112939403_s1 | 1 | 77,957 | 77,114 | 843 | 38 | 2,300 | 14 | 24 | ≤359 | 1592 / 102,932 | CARROT 5/5, EGG 8/8, FERTILIZER 1/1, WOOL 1/1; final shed empty=True |
| control_ryo_112931133_s0 | 0 | 146,852 | 122,851 | 24,001 | 35 | 2,720 | 9 | 26 | ≤75 | 1757 / 186,185 | CARROT 3/3, WHEAT 2/2, WOOL 4/4; final shed empty=True |
| control_ryo_112931133_s1 | 1 | 152,445 | 127,647 | 24,798 | 34 | 2,871 | 9 | 25 | ≤228 | 1757 / 191,798 | CARROT 3/3, WHEAT 2/2, WOOL 4/4; final shed empty=True |

\* The quoted-price sum is only the value of hypothetical units at those historical quotes. It is not forgone revenue: the candidate had zero stock of the named product when each unit was committed.

‡ A generous same-turn upper bound from matching inventory already carried at a shed-access tile, not already being dropped, and still within the current SELL quantity. It assumes the action can be replaced by a deposit without opportunity cost and prices do not fall across added units. It excludes cargo farther from the shed; it is not a realized gain.

† `item x/y` compares successful terminal-step unit sales with the final action's requested quantity. The last observation's carried goods are not terminal inventory if that final action deposits and sells them.

## Failure signature on Boey 112939032

- Seat 0: 33 failed units (CARROT: 1 units, quote-sum 40, FERTILIZER: 7 units, quote-sum 263, MILK: 8 units, quote-sum 379, STRAWBERRY: 5 units, quote-sum 1,072, WHEAT: 4 units, quote-sum 156, WOOL: 8 units, quote-sum 190); event steps: t80 WHEAT×1, t119 FERTILIZER×1, t167 WOOL×1, t288 FERTILIZER×1, t326 WHEAT×1, t332 WHEAT×1, t354 WHEAT×1, t368 FERTILIZER×1, t382 STRAWBERRY×1, t389 WOOL×1, t408 MILK×1, t409 FERTILIZER×1, t429 STRAWBERRY×1, t442 WOOL×1, t493 STRAWBERRY×1, t507 STRAWBERRY×1, t513 STRAWBERRY×1, t515 WOOL×1, t526 FERTILIZER×1, t527 MILK×1, t568 WOOL×1, t570 MILK×1, t577 WOOL×1, t615 MILK×1, t624 WOOL×1, t633 MILK×1, t634 MILK×1, t637 MILK×1, t649 WOOL×1, t673 FERTILIZER×1, t680 MILK×1, t698 FERTILIZER×1, t708 CARROT×1. Every failure has zero own cash delta, zero item stock before/after, and unchanged market inventory. 14 failed units came after at least one successful same-item sale by us during that same market phase; 19 had no same-step sale before the failed unit. Pre-action carried inventory is not evidence of unsold cargo at the failure point because unit actions and successful sales happen earlier in the turn.
- Seat 1: 33 failed units (CARROT: 1 units, quote-sum 40, FERTILIZER: 7 units, quote-sum 263, MILK: 8 units, quote-sum 379, STRAWBERRY: 5 units, quote-sum 1,072, WHEAT: 4 units, quote-sum 156, WOOL: 8 units, quote-sum 190); event steps: t80 WHEAT×1, t119 FERTILIZER×1, t167 WOOL×1, t288 FERTILIZER×1, t326 WHEAT×1, t332 WHEAT×1, t354 WHEAT×1, t368 FERTILIZER×1, t382 STRAWBERRY×1, t389 WOOL×1, t408 MILK×1, t409 FERTILIZER×1, t429 STRAWBERRY×1, t442 WOOL×1, t493 STRAWBERRY×1, t507 STRAWBERRY×1, t513 STRAWBERRY×1, t515 WOOL×1, t526 FERTILIZER×1, t527 MILK×1, t568 WOOL×1, t570 MILK×1, t577 WOOL×1, t615 MILK×1, t624 WOOL×1, t633 MILK×1, t634 MILK×1, t637 MILK×1, t649 WOOL×1, t673 FERTILIZER×1, t680 MILK×1, t698 FERTILIZER×1, t708 CARROT×1. Every failure has zero own cash delta, zero item stock before/after, and unchanged market inventory. 14 failed units came after at least one successful same-item sale by us during that same market phase; 19 had no same-step sale before the failed unit. Pre-action carried inventory is not evidence of unsold cargo at the failure point because unit actions and successful sales happen earlier in the turn.

## Immediate delivery counterfactual ceiling

- Episode 112939032: t368 FERTILIZER up to 1×44; t570 MILK up to 3×19; gross upper bound ≤101 per seat. This assumes replacing the unit action with a deposit has no value or worker cost and holds price fixed; it is not a tested policy gain.
- Episode 112940236: t368 FERTILIZER up to 1×45; t489 FERTILIZER up to 1×28; t570 MILK up to 2×28; gross upper bound ≤129 per seat. This assumes replacing the unit action with a deposit has no value or worker cost and holds price fixed; it is not a tested policy gain.
The 2026-09-24 panel consultation used roughly 4–6k/seat as a scale target for strategic changes. These single-turn local ceilings are only about 2.5–3.2% of 4k, before displaced-action cost or falling sale quotes, and below 0.7% of either Boey route's paired deficit.

## Engine-level cause and decision

In Kaggriculture 1.32.7, `_process_market` resolves each player's queued market orders in per-unit lockstep. `_commit_unit('SELL', ...)` immediately returns false when that item's shed count is zero, before changing cash, shed, or market inventory; the engine then marks that player's current order done. The other player's quoted unit still commits. Thus these failed units are not rejected sales of available stock and do not directly leak money or market supply. The table's quoted-price sum is deliberately not counted as a loss.

The current policy already has a sale-lead/reservation layer. The high-value STRAWBERRY examples at steps 382 and 429 are instructive: matching carry was deposited before the market. At t382 `SELL STRAWBERRY 16` sold 8 units, then the ninth attempt failed; at t429 `SELL STRAWBERRY 12` sold 10, then the eleventh attempt failed. The goods were not stranded. On Boey 112940236 at t649, `SELL FERTILIZER 18` committed 16 units before its first empty-shed failure; later queued `BUY_PRODUCT FERTILIZER 2` and `SELL FERTILIZER 1` still committed. The queue did not lose that later execution. Across the panel, 14–21 of the Boey failed units and 9–14 on the controls follow a successful same-item sale in that same market phase. The remaining units have no stock at commit time. The per-seat upper bound for immediately reachable, not-already-delivering carry is shown in the table and assumes away the displaced worker action and any price decline; it is not realized cash. For Boey 112939032, the last pre-action carried CARROT/WHEAT/WOOL quantities are matched against actual terminal-step SELL commits in the table; the final shed is empty, so this snapshot is not unsold terminal value. No cash-scale fix is justified, so no candidate is implemented and `main.py` is unchanged.

Fixed-shop reruns are unnecessary for this negative finding: no treatment changes occupancy or market actions, and the native baseline replays reproduce the frozen cash outcomes. A policy-level deferral/reordering candidate would require its own matched fixed-shop and native test before any claim.

## Reproduction

From the repository root, run the standalone capture and report driver:

```powershell
python -B -X utf8 exp_boey_sell_20260925.py --capture --report
```
Capture mode skips existing files and writes only missing traces under the approved diagnostic directory. The equivalent single-game CLI is `python -B -X utf8 trace_paired_game_events.py --candidate main.py --opponent 'rawroute:<absolute-route-json.gz>' --seed <seed> --candidate-seat <0-or-1> --json-gz-out diagnostics\boey_sell_20260925\baseline_<route>_s<seat>.json.gz`.

All generated trace/report files are confined to `diagnostics/boey_sell_20260925/`.
