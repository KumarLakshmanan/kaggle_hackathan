# Land retry on current saved top-20 failures — 2026-09-28 IST

**Decision: reject as a top-20 fix.** The frozen current-4ee land-retry
candidate won neither seat against any of the three target action tapes.
The two winning controls remained wins in both seats, but the plan required
at least one new both-seat target win before a wider panel. No wider replay
or reacting-policy outcome test followed; `main.py` was not changed.

The predeclared `PLAN.md` and `screen.py` used the unchanged candidate
SHA-256 `675893edc7ff07517dc57f60d322341b131ecd0d5286d9728d98d423cdc35e51`
and unchanged incumbent `main.py` SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
The frozen top-20 manifest and assessment hashes matched. All ten native
engine 1.32.7 games completed DONE/DONE at 720 turns, with original seeds
and generated shops against the exact saved action tapes.

| Fixture | Baseline margin seats 0/1 | Land-retry margin seats 0/1 | Outcome |
| --- | ---: | ---: | --- |
| DECEM target | −62,163 / −62,163 | −15,338 / −15,338 | loss / loss |
| Boey target | −20,873 / −20,873 | −20,873 / −20,873 | loss / loss |
| Vadim target | −400 / −400 | −400 / −400 | loss / loss |
| DSM control | +33,114 / +33,114 | +33,114 / +33,114 | win / win |
| Majkel control | +17,814 / +17,814 | +17,814 / +17,814 | win / win |

The retry mechanism materially narrows DECEM's fixed-tape loss but does not
rescue it. These opponents do not react to changed market or worker actions.
The separate frozen native selection plan found zero eligible activations
in its first 64 scanned seeds; it did not complete its planned 2,000-seed
range or run candidate outcomes. Neither result supports promotion.
There was no Kaggle access or upload.

`screen.json` contains all game outcomes, margins, provenance and hash checks.
Reproduce with `python -X utf8 diagnostics/land_retry_top20_20260928/screen.py`.
