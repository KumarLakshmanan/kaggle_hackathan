# Kaggriculture V14 engineering report

## Outcome

`main.py`, `submission.py`, and `v14_route_x_r3.py` are the same standalone
30,331-byte agent.

- SHA-256: `9a670767d2821389fd2141fb3d7782df565a73ccf184d2f68b6cff19dfa8e425`
- Route-action SHA-256: `6f432897b709617b2d3be9cc09716d30d07f74dd511dc51c5ef2b1c7e29a9b61`
- Kaggle engine used for verification: `kaggle-environments==1.32.4`
- Runtime dependencies in the submission: Python standard library only

No agent can guarantee every stochastic ladder game, especially against an
identical clone. V14 is the strongest locally validated candidate in this
workspace; it does not yet have an official Kaggle rating.

## Sources audited

- `README.md`
- `INSTRUCTIONS.md`
- `pipelines/177-180-fresh-top-30-v21-1-conditional-memory.ipynb`
- `pipelines/kaggriculture-getting-started.ipynb`
- `pipelines/kaggriculture-v21-tactical-memory.ipynb`
- `pipelines/my-2026-08-04-high-score-pipeline.ipynb`
- `pipelines/v13-r3-top-meta-order-safe-premium-control.ipynb`

The audit showed that complete long-horizon routes outperform locally greedy
planning because labor, watering, feeding, harvesting, shed access, and market
orders must remain coherent for 719 actions. The previous dynamic V4 claim was
based on the simplified simulator and did not transfer to the official engine.

## Architecture

V14 uses a Stockfish-like separation of concerns:

1. **Complete route book:** a 719-turn public-replay-derived field, labor, and
   economy plan. It was selected because it beat V13-R3 on fresh paired seeds.
2. **Legality and recovery layer:** aligns hand counts, clamps SELL quantities to
   projected shed stock, repairs weed-blocked plant/build actions, and falls back
   safely on exceptions.
3. **Tactical market layer:** when a near-clone is detected, shifts a bounded
   part of the next premium SELL one turn earlier and subtracts exactly that
   quantity from the next turn. Same-turn base order priority is preserved.
4. **Endgame layer:** liquidates remaining sellable shed inventory at the final
   actionable turn.

The rejected public-state route selector was not included. Its eight-seed shop
rule achieved only 8/12 correct route choices on unseen seeds, while choosing
Route-X globally won 10/12 paired seeds. Preserving the stronger full route was
safer than adding an overfit branch.

## Main benchmark evidence

All head-to-head tests used both seats and the official 720-frame engine.

| Candidate / opponent | Games | Game W-L-D | Paired W-L-D | Mean margin |
|---|---:|---:|---:|---:|
| V13-R3 vs old v21 | 16 | 16-0-0 | 8-0-0 | +10,104 |
| V13-R3 vs prior dynamic `main.py` | 8 | 8-0-0 | 4-0-0 | +190,870 |
| V13-R3 vs v21.1 | 8 | 8-0-0 | 4-0-0 | +2,105 |
| V14-equivalent Route-X+R3 vs V13-R3 | 40 | 30-10-0 | 15-5-0 | +759 |
| Exact V14 vs v21.1 fresh control | 4 | 4-0-0 | 2-0-0 | +4,462 |
| Exact V14 vs old v21 fresh control | 4 | 4-0-0 | 2-0-0 | +8,902 |
| Exact V14 vs 12 compact live-route proxies | 24 | 24-0-0 | 12-0-0 | +10,174 |

The live-route panel includes the two public routes that defeated the prior
2,557-rated v21.1 submission in captured ladder episodes. A replay proxy is an
approximation of the original opponent's hidden-state logic, so this panel is
strong local evidence, not an official leaderboard result.

## Exact-artifact verification

- `main.py`, `submission.py`, and `v14_route_x_r3.py` have identical hashes.
- All Python files compile successfully.
- No team name, episode ID, submission ID, or local path occurs in either
  submission file.
- Exact V14 self-play: 6 draws across three seeds, all statuses `DONE`.
- Final filename self-play at seed 424242: `123,819 / 123,819` from both seat
  arrangements.
- Measured mean action time: approximately 0.31-0.40 ms.
- Largest measured action in the selected validation runs: 182.1 ms, below the
  one-second Kaggle action limit.

Raw results are retained under `benchmark_results/`. `paired_benchmark.py`
reloads modules for every game to prevent state leakage and records per-game
rewards, statuses, margins, wall time, and agent-call timing.

## File map

- `main.py`: promoted Kaggle submission file
- `submission.py`: byte-identical alternate submission filename
- `v14_route_x_r3.py`: immutable named copy of the promoted artifact
- `main_v4_dynamic.py`, `submission_v4_dynamic.py`: backups of the replaced V4
  dynamic files
- `paired_benchmark.py`: official-engine paired-seat benchmark harness
- `collect_live_routes.py`: compact public replay-action collector
- `build_v14.py`: deterministic V14 artifact builder
- `live_routes/`: compact action-only public replay proxies
- `benchmark_results/`: raw JSON evidence

## Kaggle state at completion

The CLI reported five submissions used and zero remaining for 2026-08-06.
Therefore V14 was not submitted during this run. Submit only after the daily
allowance resets, then evaluate its live episodes rather than trusting the
initial asynchronous rating alone.
