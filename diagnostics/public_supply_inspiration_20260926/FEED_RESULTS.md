# Physical feed ownership: completed experiment, 2026-09-26

## Source and implementation

Evelyn3976's public Apache-2.0 *Kaggriculture Adaptive Market Scheduler v1*
assigns FEED to a worker carrying wheat and creates shed pickup tasks when
needed. We reviewed its source statically as untrusted reference material,
without importing or executing it. The experiment independently adapted the
physical ownership idea to our separate search agent: suppress FEED jobs when
no farm worker or shed has wheat, increase priority for a wheat carrier, and
let an empty-handed assigned worker CARE an animal rather than travel to an
empty shed. No market, portfolio-search or crop policy changed.

A: `kaggriculture_search_agent_v2_20260926.py` (and its former identical
`kaggriculture_search_agent.py`), SHA-256 `5e4023df...`.
B: `exp_public_feed_ownership_20260926.py`, SHA-256 `e2cc564f...`.
`FEED_PLAN.md` froze both panels and gates before the native games.

All games used installed engine 1.32.7, original endogenous shops, a reacting
`main.py` opponent, both seats and 720 turns. Every A/B game completed
`DONE`/`DONE` with no time-limit failure. Paired margin sums seat 0 and seat 1
candidate-minus-opponent cash for a seed.

| Panel and seed | A paired margin | B paired margin | B−A |
| --- | ---: | ---: | ---: |
| Development 2615010 | -175,996 | -157,104 | +18,892 |
| Development 2615011 | -174,200 | -159,446 | +14,754 |
| Development 2615012 | -247,977 | -220,219 | +27,758 |
| Development 2615013 | -179,936 | -195,872 | -15,936 |
| **Development total** | **-778,109** | **-732,641** | **+45,468** |
| Confirmation 2615014 | -146,322 | -180,957 | -34,635 |
| Confirmation 2615015 | -159,348 | -140,524 | +18,824 |
| Confirmation 2615016 | -161,930 | -158,978 | +2,952 |
| Confirmation 2615017 | -180,666 | -167,358 | +13,308 |
| **Confirmation total** | **-648,266** | **-647,817** | **+449** |

The candidate passed the predeclared development gate: three positive seeds,
larger aggregate paired margin, and `missing_supply` fell 366→281 across
eight games. It also passed the stated confirmation gate: +449 aggregate
paired margin and no failures; `missing_supply` fell 352→304. Confirmation
mean own cash actually fell 64,940.75→62,147.625, and one seed worsened by
34,635 margin. All 16 B seat games across the two panels still lost to
`main.py`.

**Decision:** Promote B only to the separate
`kaggriculture_search_agent.py` research artifact, preserving original v2 as
`kaggriculture_search_agent_v2_20260926.py`. The promoted SHA-256 is
`e2cc564fde5c3a61a856f2a985b76fde360e68b904b0ff5f1cde267aede53469`.
`python -m py_compile` passed; Kaggle's `get_last_callable` selected `agent`;
a full Kaggle file-path game on fresh seed 2615018 ended both seats `DONE`
(search 56,041, `main.py` 133,975). No `main.py` change, local leaderboard
claim, or Kaggle upload is supported. The confirmation gain is thin and the
separate search architecture still has a large execution gap.

Raw evidence: `feed_baseline_dev4.json`, `feed_candidate_dev4.json`,
`feed_baseline_confirm4.json`, `feed_candidate_confirm4.json`.

Reproduce with `python paired_benchmark.py --candidate
kaggriculture_search_agent_v2_20260926.py --opponent main.py --seeds
2615010 2615011 2615012 2615013 --json-out <A.json>` and substitute
`exp_public_feed_ownership_20260926.py` for B. Repeat with seeds
2615014–2615017 for confirmation. These seeds are now exposed and should
never be presented as fresh validation for a later variant.
