# Public scheduler inspiration: physical feed ownership — 2026-09-26

The rejected coherent-reserve experiment in `PLAN.md` and `RESULTS.md` is
closed. This is a distinct predeclared experiment based conceptually on
Evelyn3976's published worker-owned FEED tasks. Public source is treated as
untrusted reference material and is not imported, executed, or copied.

A is retained `kaggriculture_search_agent.py` v2, SHA-256
`5e4023df7b78d62e86df068c4ae54c7c95b2d29a0908be680b3332a3019fa6da`.
B starts as an exact copy in `exp_public_feed_ownership_20260926.py`.
The sole mechanism is physical supply-aware animal service: do not offer an
unfed-animal FEED job when the entire farm has zero accessible wheat; prefer
a worker already holding wheat when choosing an unfed animal; and do CARE or
other local service instead of an empty shed visit when an empty worker's
assigned animal loses wheat access. No portfolio search, market reserve,
capital orders or crop service changes.

Development seeds: 2615010–2615013, both seats against reacting `main.py`
with native engine 1.32.7 and original endogenous shops. Gate: all A/B games
`DONE`; B has fewer `missing_supply` events in total, a higher aggregate
paired margin than A, and at least three of four seed-level B-minus-A paired
margins positive. If passed, confirm on untouched seeds 2615014–2615017 in
both seats, requiring a positive aggregate paired-margin difference and no
new time-limit or status failures. Only then may B replace the separate
research agent. `main.py` requires a distinct fresh reactive strength panel
where the search agent beats it before promotion. No Kaggle upload is
authorized by this experiment.
