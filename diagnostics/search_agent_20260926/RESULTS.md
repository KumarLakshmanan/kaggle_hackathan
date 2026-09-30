# Independent forward-search agent — 2026-09-26

## Decision

**Reject promotion to `main.py` and do not upload.** The separate
`kaggriculture_search_agent.py` is a working, standalone experimental agent,
but it loses every tested reactive game against the current incumbent. It
cannot be described as a leaderboard improvement.

## Architecture

The candidate reads only the legal observation and its own private shed. At
each day boundary it runs a bounded beam search over multi-tile crop and
livestock commitments. Each node forecasts both players' cash effect on the
shared nonlinear market under three future-shop and rival-output scenarios,
charges capital, land, and approximate labor, and selects the best portfolio.
Workers execute that portfolio with persistent tile jobs and observed-state
replanning. This is inspired by a chess engine's candidate search and
evaluation, but the economic forecast is approximate and has no guarantee of
optimal play. No incumbent route tape, future shop path, seed, or hidden rival
inventory is used in the policy.

The retained experimental file is the reproducible v2 source, SHA-256
`5e4023df7b78d62e86df068c4ae54c7c95b2d29a0908be680b3332a3019fa6da`.
Its exact snapshot is `kaggriculture_search_agent_v2_20260926.py`. The v1,
v3, v4, and v5 versions are also preserved as separate snapshots. The
incumbent `main.py` is unchanged at SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.

## Native results

All games below used the installed Kaggriculture 1.32.7 engine, default
endogenous shops, a reacting `main.py` opponent, complete 720-turn episodes,
and both seats per seed. All players ended `DONE`. Seeds 8–11 were examined
after the development variants on seed 0.

| Candidate | Seeds | Paired wins | Seat wins | Mean seat margin | Mean own cash | Evidence |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| v1 single-tile beam | 0–7 | 0/8 | 0/16 | −106,011 | 45,745 | [`native8.json`](../search_agent_20260926_native8.json) |
| v2 bundle beam, retained | 8–11 | 0/4 | 0/8 | −88,281 | 59,863 | [`v2_native_holdout4.json`](../search_agent_20260926_v2_native_holdout4.json) |
| v5 timed strawberry fertilizer | 8–11 | 0/4 | 0/8 | −88,435 | 53,576 | [`v5_native_holdout4.json`](../search_agent_20260926_v5_native_holdout4.json) |

On development seed 0, v2 earned 58,632 in both seats versus 124,341
for the reacting incumbent (−65,709 margin in each seat). The reconstructed
v2 snapshot reproduced those totals exactly. The other completed changes
were rejected separately at the seed-0 development gate:

| Variant | Change | Seat wins | Mean seat margin | Decision |
| --- | --- | ---: | ---: | --- |
| v3 | Deeper bundles, larger cash buffer, stable wheat reserve | 0/2 | −82,527 | Reject; both seats lost |
| v4 | Funding order and early shed delivery | 0/2 | −96,693 | Reject; own cash rose but paired margin worsened |
| v5 | Timed strawberry fertilizer | 0/2 | −79,228 | Reject; both seats lost and later seeds also failed |

Raw seed-0 files are the adjacent `v3_seed0.json`, `v4_seed0.json`, and
`v5_seed0.json` artifacts.

The retained source beat a passive agent on seed 42 with 71,813 versus
3,000, `DONE`/`DONE`. Kaggle's actual file-path loader selected the final
`agent` callable; its first market action was nonempty and file-path and
direct-callable games matched terminal cash and opening action exactly.
This is an entrypoint check, not strength evidence.

## What the trace taught us

- A four-single-tile search expanded too slowly. In the inspected seed-0
  game, v1 built four livestock and four crops on day one, while the
  incumbent built 24 productive tiles. The bundle search increased
  investment pace, but could not close the full-game gap.
- The forecast valued a *complete* portfolio while the executor bought
  inputs and assigned workers one turn at a time. Capital and market-order
  timing left some forecast animals unbuilt. V3 tried a deeper beam and
  stricter cash buffer; it earned only 42,194 and 33,521 versus the
  incumbent's 136,549 and 104,220 on seed 0.
- In the v3 seed-0 seat-0 trace, the search agent made 1,579 `PASS` worker
  actions, 86 fertilizer collections, and 83 feed actions. The incumbent
  made 418 `PASS`, 375 fertilizer collections, and 349 feed actions.
  Portfolio value without a spatially efficient worker schedule was
  misleading. These counts are trace diagnostics, not independent policy
  validation.
- V4 raised own cash on seed 0 to 67,746, but the reacting rival rose to
  164,439, so paired margin fell to −96,693. Shared-market effects make own
  cash gains insufficient for promotion. V5's fertilizer assumption was
  overly optimistic relative to execution and did not pass fresh seeds.

The next serious architecture would need a joint planner for purchase order,
worker routes, shed delivery, and market settlement, with a physical
transition model checked against the installed engine. More portfolio-only
search depth is not supported by these results.

## Reproduction

```powershell
python -m py_compile kaggriculture_search_agent.py
python paired_benchmark.py --candidate kaggriculture_search_agent.py --opponent main.py --seeds 8 9 10 11 --json-out diagnostics\search_agent_20260926_v2_native_holdout4.json
```

This block was used to evaluate the retained source; reusing it during
further tuning would make it a development block. Any future promotion
requires new, unexposed native reactive seeds and both-seat checks. No
Kaggle upload was requested or performed in this work.
