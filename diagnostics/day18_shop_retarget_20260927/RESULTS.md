# Day-18 shop retarget result

Source: `main.py` SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
Isolated candidate: `exp_day18_shop_retarget_20260927.py` SHA-256
`3a4ceb6a2311ab6bb6edc03492aa3665e08c32057bf4263e403f95f533b4c413`.
The candidate compiled. Its seven permitted routes have identical full action
tapes for steps 0–431, so a day-18 switch is physically and financially
state-compatible by construction. The candidate uses only the current
`unlocked_shops` list and returns to the common route-2 schedule on day 27.

Native engine 1.32.7, fresh seeds 2617300–2617315, two seats, endogenous
shops, reacting unchanged `main.py`: all 32 games `DONE`/`DONE`, zero router
errors. The current route was in the compatible family on nine seeds (18
seats), but the newest shop pair selected a different route in the family on
only **one seed** (2617303, both seats). On that seed candidate cash was
177 lower per seat; paired margin was −354. The other 15 paired margins were
zero, including one seat-asymmetric but paired-neutral outcome.

**Reject at the predeclared four-activation gate.** The sole activation also
lost cash. No broader panel, `main.py` promotion, or Kaggle upload. The
strictly identical-action family is too narrow for latest-pair routing to
occur often in this 16-seed block. Raw result: `reactive_dev16.json`.

```
python diagnostics/day18_shop_retarget_20260927/build_candidate.py
python paired_benchmark.py --candidate exp_day18_shop_retarget_20260927.py --opponent main.py --seeds 2617300 2617301 2617302 2617303 2617304 2617305 2617306 2617307 2617308 2617309 2617310 2617311 2617312 2617313 2617314 2617315 --json-out diagnostics/day18_shop_retarget_20260927/reactive_dev16.json
```
