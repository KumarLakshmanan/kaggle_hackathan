# Pizza/Bakery complete-route library screen — 2026-09-26

The frozen `main.py` source (SHA-256 `489fe8e4...`) uses route 120 when the
first two shops are Pizza then Bakery. Three distinct saved top-100 public
routes with that pair were paired losses: Aaweg, chocolat and 吃白饭的大肥鱼.
All 39 other route IDs compatible with the day-six opening were screened as
isolated whole-route remappings against those three recorded action routes in
seat 0, on original seeds and shops. **All 117 native games ended DONE/DONE.**
The full variant hashes and results are in `variants.json` and
`fixed_screen.json`.

The predeclared ranking selected route 124 by the largest minimum margin
improvement across the three cases. Its margin deltas were +619, +55 and
+265, total **+939**. Its own-cash deltas were +268, +327 and **−730**,
total **−135**. It was the only alternative with positive margin deltas in
all three cases. The largest aggregate margin gain from any route was only
+2,196 (route 103), but that route regressed one case.

**Decision: reject the route-library switch.** Selected route 124 fails the
required positive own-cash improvement on every case and misses the
predeclared +15,000 total-margin threshold by a wide margin. These are fixed
opponent tapes and would not independently validate a reactive improvement
even if the gate had passed. No both-seat escalation, reactive test,
`main.py` edit, or Kaggle upload follows. The existing complete routes do not
solve this shop-pair cluster; a different funded production schedule is
needed to pursue it.

Reproduce:

```powershell
python diagnostics\pizzabakery_route_search_20260927\build_variants.py
python -X utf8 diagnostics\pizzabakery_route_search_20260927\screen_routes.py
```
