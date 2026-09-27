# Eight-turn sale-advance experiment — 2026-09-26

## Hypothesis and candidate

Moving already stocked, tape-planned cash-product sales up to eight turns early could beat near-mirror rivals to a better quote. `exp_sale_look8_20260926.py` is a self-contained copy of production `main.py` with only `_ADV_LOOK` changed from 4 to 8 for policy behavior. Its final telemetry assignment exposes the existing counter. Production `main.py` was not changed.

## Checks

- Setting the candidate's `_ADV_LOOK` back to 4 reproduced the production self-play final cash and status exactly on seed 2609200 in both seats.
- A fresh, predeclared run on eight consecutive seeds 2609200–2609207, both seats, compared the candidate against a **reacting** production `main.py` with matched production self-play controls. The candidate won all 16 treatment seat-games, with 444 advanced-sale turns total and no non-DONE result. Relative to the controls it gained 2,440 own coins and reduced reacting-rival cash by 8,162, for a combined margin advantage of 10,602. All 16 treatment games activated the change. This establishes a near-mirror benefit, not broad-opponent strength.
- On the complete saved current top-100 panel, the candidate finished all 200 seat-games DONE. Paired positive-margin route wins were **59/100 both before and after**. It rescued Knight of Favonius (-7,040 → +192 paired margin) and reversed Snorlax (+1,092 → -624). Seat wins changed 118/200 → 119/200 (three rescued, two reversed). Its total own cash fell 21,101 coins and fixed-rival cash fell 12,242. Across the 100 routes, 37 margins improved, 63 worsened; own cash increased on 31 and decreased on 69. Candidate max measured call was 1,459.9 ms under eight parallel workers.

## Decision

**Reject unconditional eight-turn lookahead for production.** The reactive mirror gain is real on the checked seeds, but the complete, already-used fixed-action panel shows no route-win improvement and predominantly worse own cash. A narrower observation-legal rule would require a new predeclared test and independent reactive opponents before promotion. No Kaggle upload.

Evidence: `look8_identity_seed2609200.json`, `main_selfplay_seed2609200.json`, `reactive_look8_native.json`, `look8_top100_routes.json`, `look8_top100_comparison.json`, `compare_look8_top100.py`, and `reactive_look8.py` in this directory.
