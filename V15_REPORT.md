# V15 Transparent Kaggriculture Agent

## Outcome

`main.py` is now the strongest locally tested agent in this workspace.  The
submission is plain, inspectable Python: no Base85, zlib, `eval`, marshalled
code, or encoded action blobs.

Kaggle submission: `55316955` (`v15.0 transparent search agent`).  Kaggle
validation completed successfully.  The displayed `600.0` immediately after
validation is the competition's initial rating for a new bot, before ladder
games establish its skill; it is not a measured game score.

## Architecture

1. A clean 719-turn principal variation supplies long-horizon production and
   worker scheduling.
2. Every action passes through hand alignment, shed-capacity checks, and safe
   market quantity clamping.
3. Runtime weed repair replaces blocked `BUILD`/`PLANT` commands with `DIG`,
   retries the intended command, and catches the actor back up.
4. A public-state opponent signature and bounded one-turn market lookahead can
   move premium sales ahead of likely competing sales, then repay the shift.
5. Explicit unit and market move generators cover the full command vocabulary
   and provide a survival-first recovery policy if the principal evaluator
   fails.
6. The final turn liquidates every remaining sellable shed product in current
   price order.

The production actions come from the clean member of the strongest observed
route family.  Market-order priority comes from the best four-seed tie-breaker
member of that family.  This removes replay-specific weed scars instead of
blindly copying a stochastic episode.

## Verification

All simulator checks used `kaggle-environments==1.32.5`, matching the current
live replay engine.

| Check | Result |
| --- | --- |
| Compile | PASS |
| Encoded/encrypted construct scan | none found |
| Kaggle-style self-play | 106,200–106,200, both `DONE`, 720 frames |
| Final exact-file current-20 panel | **40 wins, 0 draws, 0 losses** |
| Paired opponent routes | **20 wins, 0 draws, 0 losses** |
| Final-panel mean coin margin | **+10,406.175** |
| Final-panel mean decision time | **0.323 ms** |
| Final-panel maximum observed decision | **111.972 ms** |
| Four-seed top-clone tie-break (raw Route-0) | 20 wins, 4 losses; positive aggregate on every seed |
| Clean-route A/B | paired-neutral vs raw route; 6–0 vs three clone routes on fresh seed |
| Versus previous V14 on engine 1.32.5 | +4,520 from either seat on validation seed |

Primary result files:

- `benchmark_results/main_final_current20_panel.json`
- `benchmark_results/main_final_self_validation.json`
- `benchmark_results/v15_engine_1325_validation.json`
- `benchmark_results/route0c_readable_tiebreak.json`
- `benchmark_results/v15_market0_clean_ab.json`

## Reproduction

`build_readable_main.py` deterministically rebuilds `main.py` from the selected
plain route sources.  The final SHA-256 is
`81E3A19F5F7478EC00FA09C3BEA06FDA016EF8ABB1035E8EA61CA7CC32653D22`.

No finite policy can guarantee every possible match: an identical opponent
must tie, stochastic states can be unseen, and future opponents may introduce
new strategies.  The 40–0 result is empirical dominance over the currently
captured live panel, not a mathematical proof over the complete game tree.
