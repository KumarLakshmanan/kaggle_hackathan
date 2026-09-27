# Same-tile `PASS` opportunity probe — 2026-09-26

Use the two existing full native candidate-seat-0 traces, Boey and mhw,
without rerunning or changing policy. For every current-`main.py` unit `PASS`,
read only that player's observation before action. Count an immediately
legal same-tile `HARVEST`, `WATER`, `CARE`, `FEED` with carried wheat, or
`COLLECT_FERTILIZER`. Count by day band and worker; show sample records.
Exclude empty-tile planting and shed delivery because those need a funded
multi-turn plan. These are upper bounds on useful overrides: another worker
may change the tile during the same turn, and a harvest still needs delivery.

Gate: if at least one game has 30 or more such observed `PASS` opportunities
before day 24, investigate a separate local override candidate with native
both-seat, original-shop and reactive tests. Otherwise reject same-tile idle
repair as too narrow for the major losses. Two selected losses cannot support
a population-wide claim. No `main.py` change or upload from diagnosis alone.

Follow-up after the first probe met the investigation gate: raw turn counts
can repeat one waiting crop many times. Before editing a candidate, apply the
engine's first-yield and full-yield thresholds, deduplicate by day/tile/op,
and mark whether a later successful native action handled the same tile that
day. This is an exploratory mechanism audit, not a new promotion gate.
