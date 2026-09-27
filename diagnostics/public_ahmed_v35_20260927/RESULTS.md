# Public V35 whole-policy screen — 2026-09-26 19:36 UTC

Downloaded the Apache-2.0 [Kaggle V35 notebook](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v35-reactive-sales-sheep-expansi)
and extracted its exact `main.py` source into `public_v35_main.py`.
SHA-256 `294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d`
matches the notebook's declared hash. A static AST audit of the top-level and
both embedded `exec` modules found only standard-library imports, with no
file, network or process calls. This source was tested as an unmodified
`agent`; it was not integrated into our artifact.

The two-seat smoke seed 2615599 finished `DONE`/`DONE`; V35 lost each seat
97,755 versus current `main.py` 103,525, margin −5,770. The predeclared
full screen used seeds 2615600–2615615, both seats, original endogenous shops
and the installed 1.32.7 native engine. All 32 games were `DONE`/`DONE`.

| Metric | V35 vs current `main.py` |
| --- | ---: |
| Paired seeds won / lost | **0 / 16** |
| Seat games won / lost | **0 / 32** |
| Mean margin per game | **−7,815.4** coins |
| Aggregate margin | **−250,094** coins |
| Mean V35 bank cash | 92,348.3 coins |
| Worst paired seed | −26,870 coins |

Raw rows, timings and each paired margin are in `reactive_dev16.json`.
The published notebook reports 2692.9 public score and strong results on its
own older cohorts; those numbers do not predict this direct matchup or our
Kaggle rating. This test covers only a reacting current `main.py` opponent,
not all top-player policies. The V35 six-sheep continuation did not overcome
the whole-policy deficit here.

**Decision: reject wholesale replacement at the first predeclared reactive
gate** (needed ≥11/16 positive paired seeds and positive aggregate margin).
Do not run the conditional top-100 promotion panel or integrate V35. No local
`main.py` change or Kaggle upload. The current artifact remains backed up as
`main_uploaded_mirror_straw24_20260926_489fe8e4.py`.
