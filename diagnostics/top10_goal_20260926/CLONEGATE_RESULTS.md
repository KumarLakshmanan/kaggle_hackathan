# Physical-mirror-gated sale advance — 2026-09-26

## Policy and evidence

`exp_sale_look8_clonegated_20260926.py` is the unchanged submitted `main.py` plus `clone_gate_tail.py`. At each turn from 144 through 717, it uses an eight-turn sale-advance lookahead only when the two **public** farms have identical tiles, farmer position, and farm-hand positions. Otherwise it retains the submitted four-turn lookahead. The rule uses no replay ID, seed, opponent name, future shop, or private rival inventory.

| Check | Result |
| --- | --- |
| Current saved top-100, both seats, 200 games | All DONE; 59/100 positive paired margins and 118/200 seat wins for both policies. No rescued or reversed result. Candidate own cash -838 total; fixed-rival cash -1,094. Gate matched during 70 games; extra-advance action occurred in 38. Max candidate call 660.1 ms under eight workers. |
| Reacting `main.py`, development seeds 2609200–2609207, both seats | Candidate 16/16 wins; own cash -34, reacting-rival cash -5,572 versus matched self-play controls. Every game activated. |
| Reacting `main.py`, **fresh predeclared** seeds 2609300–2609307, both seats | Candidate 15/16 wins versus 1/16 control wins. The gate activated in 14 games and won 14/14; the other seed had zero activation and reproduced the control's seat-dependent +5,691/-5,691 margins exactly. Own cash +4,648 and reacting-rival cash -8,196 total versus matched controls. All 32 games DONE; max candidate call 269.1 ms under four workers. |
| Public reactive H6 agent, four seeds, both seats | All eight terminal cash pairs **exactly identical** to saved incumbent controls; gate did not activate. All DONE. |
| Public reactive Haide agent, three seeds, both seats | All six incumbent wins preserved. Margins rose by 3, 0, and 62 coins per seat on the three seeds, with one or 14 extra-advance turns in the changed cases. All DONE. |

The saved top-100 panel has been used for development, so its neutral result is a regression screen rather than independent win-rate evidence. The matched reactive mirror tests establish a causal advantage against this specific near-clone. The public-agent checks cover only two available implementations. The gate may fail or hurt against a different adaptive rival whose public farms temporarily match; the rule does not justify a top-ten or 100/100 claim.

## Decision

**Promote the exact tested candidate to `main.py` as an incremental near-mirror improvement.** The original submitted file is backed up byte-for-byte as `main_before_top10_goal_20260926_04b0bdc3.py`. Do not upload until a fresh explicit user request; the current Kaggle submissions remain the older hash. Continue work on the much larger production and routing gaps.

Evidence in this directory: `clone_gate_tail.py`, `clonegated_top100_routes.json`, `clonegated_top100_comparison.json`, `reactive_clonegate_native.json`, `reactive_clonegate_fresh.json`, `clonegated_vs_public_h6_reactive.json`, and `clonegated_vs_haide_reactive.json`. The exact route comparison script is `compare_look8_top100.py clonegated`.
