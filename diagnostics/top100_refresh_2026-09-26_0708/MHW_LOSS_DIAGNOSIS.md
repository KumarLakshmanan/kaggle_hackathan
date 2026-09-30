# Largest fresh-panel loss: mhw — 2026-09-26

An exact native event trace on the source seed and candidate seat 0
reproduced the current `main.py` loss: 105,885 versus 151,676 coins,
margin **−45,791**, both `DONE`. The paired fresh-panel margin across both
seats was −92,486. Source:
`mhw-submission-56548646-episode-113602930-seat1.json.gz`; executed trace:
`mhw_trace_s0.json.gz`.

The first two visible shops were both `YARN_STORE`. At day six the rival had
eight strawberry tiles versus our four, but strawberry cash was not the
realized deficit: **our strawberry sales earned 7,028 versus rival 3,908**.
The rival's wool sales earned **159,937 versus our 99,516**, a 60,421-coin
advantage. At day 18 the rival held 36 sheep versus our 17; it had spent
18,000 on sheep versus our 8,500. The extra 9,500 sheep outlay was much
smaller than the wool-receipt gap. We were ahead by 18,579 bank coins at day
18, but behind by 30,704 at day 24.

This case supports testing a *complete* sheep-heavy continuation on visibly
double-Yarn scenarios with a rival sheep lead. A prior broad Yarn route-12
switch lost every fresh reactive self-play game, so fixed-route improvement
alone cannot justify promotion. The isolated gated pilot and its
predeclared screen are in `../top10_goal_20260926/DOUBLE_YARN_HIGHSHEEP_PLAN.md`.
**Decision: diagnose only; no main-file change or Kaggle upload.**
