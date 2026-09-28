# c68 versus 4ee on 18 new live-loss tapes

Frozen inputs: `manifest.json`; full game outcomes: `results.json`; paired deltas: `summary.json`.
All 18 episodes are losses from the complete 16:41 UTC live cohort. Each opponent action sequence has 719 moves.
A later 16:53 UTC live extension added one loss after this diagnostic panel was frozen; it is outside these 18 cases.
Each agent was run in both seats at the recorded seed with native shops: **72 games**, all DONE/DONE/720.
The 4ee original-seat reruns reproduce both Kaggle cash totals in all 18 episodes.

| Seat panel | c68 W/D/L | 4ee W/D/L | 4ee − c68 win points | Better / worse / same results | Mean relative-cash change |
|---|---:|---:|---:|---:|---:|
| original seat | 0/0/18 | 0/0/18 | +0 | 0/0/18 | +228 |
| swapped seat | 0/0/18 | 0/0/18 | +0 | 0/0/18 | +228 |
| all | 0/0/36 | 0/0/36 | +0 | 0/0/36 | +228 |

Both-seat sweeps over 18 sources: c68 **0**, 4ee **0**.
Relative-cash change is (4ee own − 4ee rival) − (c68 own − c68 rival) on the same tape, seed, and seat.
The `summary.json` ledger also separates own-cash and opponent-cash changes.

| Episode | Opponent | Source seat | c68 original | 4ee original | c68 swapped | 4ee swapped |
|---:|---|---:|---|---|---|---|
| 114211346 | chocolat | 0 | loss -4,293 | loss -4,132 | loss -4,293 | loss -4,132 |
| 114215872 | carbonapi | 1 | loss -6,047 | loss -6,001 | loss -6,047 | loss -6,001 |
| 114218866 | pensukesan | 1 | loss -8,673 | loss -8,665 | loss -8,673 | loss -8,665 |
| 114223292 | 吃白饭的大肥鱼 | 0 | loss -33,276 | loss -33,224 | loss -33,276 | loss -33,224 |
| 114223338 | forever young | 0 | loss -7,048 | loss -6,090 | loss -7,048 | loss -6,090 |
| 114227779 | kwa | 1 | loss -3,870 | loss -3,858 | loss -3,870 | loss -3,858 |
| 114229792 | Ebi | 1 | loss -10,538 | loss -9,989 | loss -10,538 | loss -9,989 |
| 114232208 | boominginging | 0 | loss -15,606 | loss -15,635 | loss -15,606 | loss -15,635 |
| 114235177 | mhw | 1 | loss -21,302 | loss -21,260 | loss -21,302 | loss -21,260 |
| 114236633 | Kucing Garong | 0 | loss -3,008 | loss -2,857 | loss -3,008 | loss -2,857 |
| 114238112 | Civitasmass | 0 | loss -8,281 | loss -8,178 | loss -8,281 | loss -8,178 |
| 114243994 | high frequency farming | 1 | loss -7,465 | loss -7,539 | loss -7,465 | loss -7,539 |
| 114249897 | Dieter | 1 | loss -5,474 | loss -5,454 | loss -5,474 | loss -5,454 |
| 114252835 | Vlas Veles | 1 | loss -3,013 | loss -3,023 | loss -5,281 | loss -5,282 |
| 114254310 | Junliang Ye | 1 | loss -14,988 | loss -12,934 | loss -14,988 | loss -12,934 |
| 114255779 | fasith 007 | 1 | loss -4,995 | loss -4,918 | loss -4,995 | loss -4,918 |
| 114257327 | pensukesan | 1 | loss -19,204 | loss -19,196 | loss -19,204 | loss -19,196 |
| 114258293 | keiz | 1 | loss -9,179 | loss -9,211 | loss -9,179 | loss -9,211 |

**Decision:** retain this as a counterfactual diagnostic. The opponent moves are fixed from games that 4ee lost; the opponents cannot react to c68 or a seat swap. No policy promotion or Kaggle upload follows from these results.
