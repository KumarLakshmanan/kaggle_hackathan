# Day-26 complete-route transition result

Source snapshot: `main.py` SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
Isolated candidate: `exp_early_route2_20260927.py` SHA-256
`86e832519ad1a5d76efb38a97b7fb02dbce62b49c6a75de804478774820d5bc3`.
The 22 executable step-648 thresholds were consistently advanced to 624;
compressed route data and comments were untouched. The route-2 tape differs
from selected route tapes on every day-26 turn, while all compared tapes are
identical from day 27 onward. Python compilation passed.

Native engine 1.32.7, new seeds 2617000–2617003, two seats each, original
shops, candidate against reacting `main.py`: all eight games `DONE`/`DONE`.
Paired margins were −446, +1,148, −58 and +252 coins; candidate own cash
was ahead 112 coins per game in aggregate. Only **two of four** paired seeds
improved, below the predeclared three-of-four gate.

**Reject.** The one-day complete transition has a small, inconsistent effect.
No extended panel, `main.py` promotion, or Kaggle upload. Raw results:
`reactive_dev4.json`. Reproduce with:

```
python diagnostics/late_route_transition_20260927/build_candidate.py
python paired_benchmark.py --candidate exp_early_route2_20260927.py --opponent main.py --seeds 2617000 2617001 2617002 2617003 --json-out diagnostics/late_route_transition_20260927/reactive_dev4.json
```
