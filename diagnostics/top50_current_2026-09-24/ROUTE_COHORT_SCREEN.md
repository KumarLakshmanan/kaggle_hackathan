# Day-6 route-cohort counterfactual (local only)

The temporary `exp_route_cohort_selector_20260924.py` loads the frozen `main.py`
and substitutes one of its existing precomputed routes from step 144 through 647.
It makes no use of team names, episode IDs or replay actions. This is a
counterfactual screen of production mixes, **not** a standalone submission or a
learned selector. The unforced wrapper exactly reproduced Excluding episode
112933084 in both seats (own 116,023, rival 155,219, paired −78,392).

On the six preselected loss routes from Excluding, Boey and ActiveMusyoku,
forcing route 0 rescued 0/6, route 9 rescued 2/6, and route 128 rescued 1/6.
All 36 games finished. The route-9 rescues were ActiveMusyoku episode
112941285 (paired −32,066 → +64,016; own cash +58,102 across seats) and Boey
episode 112940236 (−39,954 → +4,858; own cash +35,966). Other loss margins
often worsened, notably ActiveMusyoku episode 112937075 (−16,466 → −41,684)
and Excluding episode 112933084 (−78,392 → −97,128).

The predeclared 12-route ledger set plus two unrelated routes sharing its
episode seeds was then run under forced route 9, both seats (28 DONE games).
Relative to frozen main, it converted two original losses to wins but **three
original wins to losses**: Gleb Tumanov 112939403, Sida Zuo 112937057, and
istinetz 112939139. Those three reversals lost 19,064, 16,502 and 22,196
candidate cash across seats, respectively. Route 9 therefore fails the
winning-control gate and is **not** promoted into `main.py`.

The two rescues had different first-two observed shop pairs:
`PIZZA_SHOP, BAKERY` and `BRUNCH_SPOT, PET_CAFE`. The three control reversals
also span different shop pairs. This small panel does not support a simple
shop-only selection rule; inventing one from these labels would be overfitting.

Commands, run from the workspace root:

```powershell
python route_panel_benchmark.py --candidate exp_route_cohort_selector_20260924.py --summary diagnostics/top50_current_2026-09-24/routes/summary.json --seeds 1803729554 --workers 2 --json-out diagnostics/top50_current_2026-09-24/route_selector_baseline_excluding.json
python route_panel_benchmark.py --candidate exp_route_cohort_selector_20260924.py --summary diagnostics/top50_current_2026-09-24/routes/summary.json --seeds 1736078920 1080335140 1016478476 409584214 1803729554 189381835 --workers 4 --candidate-override _EXP_ROUTE=9 --json-out diagnostics/top50_current_2026-09-24/route_force_9_6losses.json
```

The same six-loss command used `_EXP_ROUTE=0` and `128` for their respective
screens. A 12-seed, 14-route extension is stored in
`route_force_9_ledger_panel_seeds.json`. Seed selection includes two additional
teams because public episodes can involve two top-50 teams. These are native
shop draws but fixed opponent actions; route changes can also alter weed RNG,
later shops and rival cash. A rescue is not a causal effect of one product.
