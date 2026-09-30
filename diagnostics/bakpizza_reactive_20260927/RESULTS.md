# Bakery/Pizza route-101 native reactive screen — 2026-09-26

The shop-only native scan evaluated 299 sequential seeds from 2621000 onward
and selected the first six whose first two shops were exactly Bakery then
Pizza: 2621037, 2621118, 2621123, 2621137, 2621144, 2621298. Selection
recorded shops before seeing any final game outcome. It used unchanged
`main.py` self-play to reach day 6.

The isolated candidate remapped only this observable shop pair from existing
route 107 to existing route 101. The full source hashes matched the frozen
plan. For every selected seed, both control and candidate faced a reacting
`main.py` in both seats with original shops. **All 24 games ended DONE/DONE**
and captured the intended shop pair.

| Seed | Candidate own-cash delta, both seats | Rival cash delta | Margin delta |
| --- | ---: | ---: | ---: |
| 2621037 | −10,258 | +6,604 | −16,862 |
| 2621118 | +5,234 | +8,596 | −3,362 |
| 2621123 | +9,252 | +5,126 | +4,126 |
| 2621137 | +17,758 | +22,792 | −5,034 |
| 2621144 | +7,844 | +7,634 | +210 |
| 2621298 | +6,888 | +1,352 | +5,536 |
| **Total** | **+36,718** | **+52,104** | **−15,386** |

Only **3/6** paired seeds improved margin, below the required 4/6; total
margin was negative and the worst seed was −16,862, below the −5,000 floor.
Thus the prospective reactive gate failed, even though own cash rose in
aggregate. Shared markets and the opponent's response outweighed the own
gain. **Reject route 107→101 for promotion.** No second seed block, saved
route panel, `main.py` edit, or Kaggle upload is warranted by this result.

The direct tape difference starts with an early 2-goose versus 2-cow
commitment and matching worker construction/handling, with other early
market/input changes. It is not an independent predictor of future score.

Evidence: `seed_selection.json` contains every scanned seed and shop pair;
`reactive_dev6.json` contains all seat-level cash, status, capture, hashes,
comparisons, and frozen-gate result. Reproduce with:

```powershell
python diagnostics\bakpizza_reactive_20260927\scan_shops.py
python diagnostics\bakpizza_reactive_20260927\reactive_screen.py
```
