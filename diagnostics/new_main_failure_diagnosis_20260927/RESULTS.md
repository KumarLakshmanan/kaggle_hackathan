# Failure diagnosis of uploaded 4eeac9c3

2026-09-27. This read-only audit uses 4ee native replays against recorded
opponent actions and all 61 public games of submission 56609430 available
at the 16:53 UTC cutoff. The opponent routes are data; no downloaded agent
code was executed. Recorded tapes diagnose mechanisms and do not validate a
new policy's strength against reacting opponents.

The frozen 16:35 UTC current top-20 assessment has 16/20 both-seat sweeps.
Its four losses are DECEM −63,151, Boey −2,819, Vadim Vasilenko −5,821 and
Majkel1337 −77,373 per seat. The earlier 11:37 current top-100 panel has
73/99 external sweeps and the original-50 panel has 44/50, as recorded in
`shunki_purchase_iterated_20260927/panels.json`. All cited games finish
DONE/DONE/720 in both seats.

## Actual live progression

The 61 public 4ee episodes audited here are 42 wins and 19 losses. In 15/19
losses our cash is ahead at turn 144, yet all 19 trail by turn 432. The
opponent has at least eight MELON plots at turn 144 in 19/19 losses **and
41/42 wins**. Rival melon occupancy alone is therefore not a useful
loss-specific trigger. The gap arises as the investment, labor and sale
schedule plays out after the opening; the saved observations do not by
themselves establish which different full schedule would win. Exact per-game
cash, shop and tile snapshots are in `live_ledger.json`; raw live archives
and receipts are under `diagnostics/new_live_56609430_20260927/raw/`.

## Physical and cash ledgers on new 4ee losses

Passive engine event hooks reproduce exact terminal cash. The table nets
gross product SELL receipts against `BUY_PRODUCT` costs; seed, animal, land
and hire costs are additional. "Harvest" counts are worker HARVEST commands
that changed farm/private state, not output units.

| Panel, rival | Margin | Our net product trade | Rival net product trade | Changed HARVEST own/rival |
|---|---:|---:|---:|---:|
| Fresh top-20 Boey | −2,819 | 166,229 | 170,340 | 445 / 514 |
| Fresh top-20 Vadim | −5,821 | 97,874 | 103,536 | 452 / 487 |
| 11:37 Boey | −12,993 | 126,159 | 141,126 | 437 / 529 |
| 11:37 DECEM | −1,586 | 144,238 | 147,179 | 451 / 547 |
| Original-50 Snorlax | −15,276 | 87,424 | 102,858 | 454 / 554 |

These are sample loss mechanisms, not a claim that adding isolated harvests
would fix them. The original-50 Snorlax trace has no failed own market
purchases, and the 11:37 IsaiahP near loss (−81) has none either. The large
gross WHEAT receipts in many games include purchased wheat round trips, so
gross sales are not a production measure. The net product trade shortfalls
and lower changed harvest counts point to whole physical commitments and
their market response as the remaining high-value research area.

There is also a precise seed funding defect in several distinct losses.
Fresh top-20 Boey turn 187 has 9 coins, fails to buy a 10-coin WHEAT seed,
then sells existing WHEAT for 309; Vadim turn 180 has 3 coins, fails the
same 10-coin purchase, then sells WHEAT for 256. Earlier 4ee current-100
Boey, DECEM and Majkel traces show analogous failed seed orders followed by
sales. This observation justified a narrow experimental candidate, frozen
under `diagnostics/seed_prefund_20260927/PLAN.md` before outcomes. It
activated in both seats of Boey, Vadim and fresh DECEM, but made Boey and
Vadim lose by more, and rescued no top-20 loss. The full 40-game gate failed;
see that experiment's `RESULTS.md`. A one-seed state change altered crop
occupancy, the third shop and both players' later cash. **Reject this
seed-prefund intervention for promotion.**

## Next testable direction

A new candidate should supply a **complete funded midgame production
schedule**, including seeds/animals, land, hand travel, feeding, harvest,
delivery and sales, then score `delta_own - delta_rival`. The natural isolated
insertion point is the route selector at `main.py` lines 28–41 after public
shops and rival tiles are visible. Its first-stage feasibility gate must
require exact pre-switch state compatibility and enough activations; prior
day-six and day-18 route switches in `agent.md` failed native or activation
gates. To target the near top-20 losses, freeze Boey/Vadim and a set of
winning controls before any new route outcomes, then require a both-seat
rescue without losing prior wins, followed by fresh original-shop reacting
games against more than one reference. This is a research proposal, not a
qualified current candidate.

**Decision:** preserve uploaded 4eeac9c3 and all existing worktree edits.
No agent change or upload is supported by this audit.

Evidence: `live_audit.py`, `live_ledger.json`, `analyze.py`, `ledger.json`,
the nine `trace_*.json.gz` files in this directory, and the source panel
assessments cited above.
