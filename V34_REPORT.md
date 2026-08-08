# V34 replay portfolio report

V34 expands V33 using only observations available to the live agent: opponent
opening state, the first two unlocked shops, and opponent money at turn 144.
It adds counters from the newly supplied replay set and a two-turn market-timing
variant for the Keito pasture/shop signature.

## Final validation

| Panel | Unique routes | Route wins | Game wins | Exceptions |
|---|---:|---:|---:|---|
| Newly added best replays | 36 | 35 | 70 / 72 | Dmitry Larko, episode 90784785 seat 1 |
| Prior best-replay panel | 52 | 51 | 102 / 104 | Seb (allegedly), episode 90635995 seat 0 |
| Failed-replay panel | 6 | 6 | 12 / 12 | None |

All 188 validation games completed with both agents in `DONE` status. Across
the two best-replay panels V34 wins 86 of 88 unique routes. Both remaining
exceptions lose identically from either candidate seat and remained negative
after exhaustive compatible-book and observable-branch searches.

Evidence files:

- `benchmark_results/v34_final_new20_full_panel.json`
- `benchmark_results/v34_final_old_best_full_panel.json`
- `benchmark_results/v34_final_failed_full_panel.json`

The promoted files `main.py`, `submission.py`, and
`main_v34_expanded_replay_portfolio.py` are byte-identical with SHA-256:

`4d921c03bff8fb5e02a51171afa4cd67e4dce4a3df44af613ecef7db92ff4f16`

## Kaggle submission

- Submission reference: `55334365`
- Message: `v34.0 expanded observable replay portfolio`
- Validation episode: `90819791`, completed `DONE/DONE`
- Initial public rating: `600.0` (provisional, before public matchmaking)

For comparison, V32 has 71 public episodes plus one validation episode; V34
currently has only its validation episode, so the two displayed ratings are not
yet directly comparable.
