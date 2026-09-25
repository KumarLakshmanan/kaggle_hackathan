# Day-6 public-state selector screen for the sheep-heavy route

The unconditional route-9 counterfactual won 58/100 route pairs versus the
frozen 67/100 baseline: four losses rescued, 13 winning routes reversed. Its
200 completed native games are in `route_force_9_100routes_20260925.json`.
Because both its rescues and reversals are large, the next question was
whether a *publicly observable* day-6 predicate can select it reliably.

The frozen `main.py` was replayed once more with `--capture-step 144`, both
seats on all 100 exact historical action tapes. Every public capture exists at
step 144, all 200 games completed, and final cash/status for every game exactly
matches `main_100routes.json`. The capture file is
`main_100routes_capture144_20260925.json`. The observer includes only current
shops, public prices/market inventory, public farms/cash, and our private shed;
the screen did not use seed, opponent identity, replay actions, future shops,
or hidden opponent inventory as features.

The [reproducible screen](route9_public_selector_screen_20260925.py) evaluated
single-feature threshold rules on predeclared coarse grids: current money,
visible rival cow/sheep and crop counts, the first-two-shop demand counts, and
public product inventory. A rule needed at least six triggered routes from
three teams and positive training utility, scoring one rescue but penalizing
one reversal threefold. The exact script asserts that the capture outcomes
reproduce the frozen baseline and that both candidate files share the same
route manifest and engine version.

| Choice | Route wins / 100 | Seat wins / 200 | Losses rescued | Wins reversed |
| --- | ---: | ---: | ---: | ---: |
| Frozen main | 67 | 133 | — | — |
| Route 9 unconditionally | 58 | 113 | 4 | 13 |
| Best admitted single-feature rule fitted to all 50 teams | 67 | 133 | 0 | 0 |
| Whole-team leave-one-out selected rules | **64** | **127** | **0** | **3** |

The full fit chose **no switch**: no simple rule passed the training gate.
Across 50 leave-one-team-out folds, 47 also chose no switch. The other three
each selected a different threshold and together reversed three previously
winning held-out routes without rescuing any held-out loss. This is a negative
screen, not a proof that no more complex observation-based selector exists.
The feature/rule family was designed after inspecting this development panel,
so even its grouped holdout is not an independent new-route validation.

One visible ambiguity is concrete: the same first-two-shop pair
`PIZZA_SHOP, BAKERY` includes one large route-9 rescue and one reversal.
Their public farms and cash are not identical, so this does not prove an
impossibility theorem; it does rule out claiming that pair alone is a safe
trigger. No route selector was promoted to `main.py` or submitted.

Run from the workspace root:

```powershell
python -X utf8 diagnostics/top50_current_2026-09-24/route9_public_selector_screen_20260925.py
```
