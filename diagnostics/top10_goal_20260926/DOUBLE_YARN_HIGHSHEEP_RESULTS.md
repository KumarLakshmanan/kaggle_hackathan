# Double-Yarn, high-sheep route-12 pilot — rejected, 2026-09-26

Isolated candidate `exp_double_yarn_highsheep_20260926.py` (SHA-256
`91a96c63d649430aff1cd9a468245a7aa9ef8abedcb1ff20f88997bed183533f`)
wrapped the submitted `main.py` hash `489fe8e4...`. On turn 144 it selected
the existing complete sheep route 12 only if the incumbent had chosen route
9, the first two observed shops were `YARN_STORE,YARN_STORE`, and the rival
had at least three visible sheep pastures. The route stayed fixed through
turn 647. The hypothesis and promotion gate were frozen in
`DOUBLE_YARN_HIGHSHEEP_PLAN.md` before treatment games.

The new top-100 panel contained four double-Yarn routes: three large
high-sheep losses and one two-sheep negative control. All eight treatment
seat-games ended `DONE`, the gate activated on all six target seat-games,
did not activate on the control, and reported zero errors.

| Rival | Old paired margin | Pilot paired margin | Effect |
| --- | ---: | ---: | --- |
| mhw | −92,486 | +9,218 | Apparent rescue |
| ShunkiKyoya | −45,570 | −58,866 | Worsened 13,296 |
| AI是我的豆包 | −39,652 | −45,898 | Worsened 6,246 |
| dodsters, two-sheep control | −2,269 | −2,269 | Exact control |

The mhw reversal does **not** meet the predeclared own-cash gate. Across its
two seats, the pilot reduced our terminal cash by 37,386 coins and the fixed
rival's cash by 139,090, so its paired-margin gain came entirely from
opponent cash suppression. In the other two target routes, our cash rose
but fixed rivals' cash rose even more. Market and later shop paths can change
when our actions change; fixed opponent actions are not independent
validation of a live win. Raw paired treatment and exact comparison:
`double_yarn_highsheep_4routes.json` and
`double_yarn_highsheep_comparison.json`.

**Decision: reject at the predeclared development gate.** The treatment
failed the own-cash requirement and materially worsened two targets, so
broader saved-panel and fresh reactive testing are not justified. The
uploaded/local `main.py` remains unchanged; no Kaggle upload is authorized.
