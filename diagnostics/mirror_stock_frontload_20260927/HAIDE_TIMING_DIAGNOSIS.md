# First changed sales in reacting Haide games — 2026-09-26

Native action traces of the four Haide seeds with nonzero A/B margin deltas
reproduced the previously measured terminal cash pairs exactly. Only the
first candidate-caused action difference in seat 0 is summarized below;
later actions are endogenous and can diverge. Rival sale times are trace
diagnostics, unavailable to the agent when it acts.

| Seed | First candidate sale | Incumbent sale | Haide sale | Own cash delta | Paired margin delta |
| ---: | --- | --- | --- | ---: | ---: |
| 2614351 | step 637, 21 units, quote 64 | 643, quote 32 | 639, 21 units | +822 | +1,444 |
| 2614352 | 673, 17 units, quote 116 | 692, quote 128 | 691, 17 units | −133 | +508 |
| 2614353 | 637, 21 units, quote 66 | 643, quote 74 | 645, 20 units | −215 | −270 |
| 2614355 | 609, 7 units, quote 64 | 613, quote 72 | 617, 7 units | −496 | −496 |

The same visible price jump across the 60-coin guard preceded both the
strong gain in seed 2614351 and the regression in seed 2614353. In the gain,
Haide sold before the incumbent's scheduled sale and depressed its quote.
In the regressions, the incumbent would have sold before Haide at a higher
quote. Prior sale cadence alone does not yield a clean separating rule in
these four examples. A state-based opponent sale forecast would need
independent predictive evaluation followed by reactive policy games.

**Decision: diagnosis only; keep the half-base candidate rejected.** Do not
encode the observed future Haide actions, episode IDs or seed identities into
the competition policy. `main.py` and Kaggle remain unchanged. Evidence:
`haide_first_changes.json`, reproduced by
`diagnose_haide_first_changes.py`.
