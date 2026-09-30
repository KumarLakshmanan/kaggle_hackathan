# Two-demand-shop late tomato bundle — 2026-09-26

## Hypothesis and panel

The local `main.py` V219 branch has a complete day-18-to-29 ten-tomato
investment: it pays for south-east land, seed and additional workers, plants,
waters, harvests, deposits and requests sales. It currently requires at least
three observed Pizza Shop/Farmers Market shops. Three saved high-ranked losses
had exactly two such shops on day 18, 30,000–48,000 available coins and tomato
quotes of 73, 82 and 75. The standalone candidate
`exp_v219_tomato2_20260926.py` changes only the eligibility count from three
to exactly two for otherwise qualifying public observations. The existing
full work and budget checks remain in force.

The six-route pilot was frozen before treatment with two September 25 top-100
losses (Boey and Arda), a fresher Boey top-20 loss, a THUNDER winner where
V219 was already eligible, and Ghost Rule/Dmytro winning controls. All were
tested in both candidate seats under engine 1.32.7. The predeclared gate for
continuing was at least one loss-to-win flip with positive own-cash change,
no control-win reversal, and all games DONE; subsequent work would require
the full top-100 and fresh reactive checks.

## Results

| Saved action tape | Current paired margin | Candidate paired margin | Own cash change, both seats | Fixed-rival cash change |
| --- | ---: | ---: | ---: | ---: |
| Boey, older top-100 loss | -15,716 | -16,696 | +12,840 | +13,820 |
| Arda Ceylan | -41,703 | -42,759 | -3,131 | -2,075 |
| Boey, refreshed top-20 loss | -5,722 | -9,776 | -3,624 | +430 |
| THUNDER THUNDER win | +48,319 | +48,319 | 0 | 0 |
| Ghost Rule win | +21,850 | +21,850 | 0 | 0 |
| Dmytro Maliarenko win | +3,346 | +3,346 | 0 | 0 |

All 12 games finished DONE. On each of the three targeted routes and both
seats, the broadened eligibility activated, V219 committed, and ten tomato
plants were confirmed. The telemetry counted 70 tomato sale *requests* per
game; that count is not a claim that all units executed. The two existing
V219 winning controls and the inactive control reproduced the incumbent's
terminal cash exactly. Each targeted loss grew in paired margin. In the older
Boey route our cash rose, but fixed-rival cash rose more.

## Decision

**Reject two-shop eligibility.** It missed the frozen pilot gate on all three
losses, so no larger fixed-tape or reactive run is justified for this rule.
The intervention shows that adding a mechanically complete bundle still needs
to account for market feedback and rival effects. The current `main.py` SHA-256
remains `6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`.
No Kaggle upload occurred. Fixed action tapes do not model adaptive rivals.

Reproduce from the workspace root:

```powershell
python -B -X utf8 diagnostics\top10_goal_20260926\build_tomato2.py
python -B -X utf8 diagnostics\top10_goal_20260926\create_tomato2_panel.py
python -B -X utf8 route_panel_benchmark.py --candidate exp_v219_tomato2_20260926.py --summary diagnostics\top10_goal_20260926\tomato2_6routes_summary.json --workers 6 --capture-step 432 --json-out diagnostics\top10_goal_20260926\tomato2_6routes.json
```
