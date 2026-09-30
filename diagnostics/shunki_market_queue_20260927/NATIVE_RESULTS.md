# Original native protocol — strict external-gain gate unmet

2026-09-27 02:29 UTC. All 384 planned games completed DONE/DONE. The
candidate a2d2869c recorded zero queue errors.

| Comparison | Current 3cc | Candidate a2 |
| --- | ---: | ---: |
| New versus reacting 3cc | Not an old/new control block | 64/64 wins |
| New versus best-active 1f | Not an old/new control block | 64/64 wins |
| Versus historical 489 | 54/64 wins | 54/64 wins |
| Versus public C95 | 54/64 wins | 54/64 wins |

Both direct head-to-head gates passed. The external non-regression condition
passed, but the separately required strictly positive external win-point
gain did not: both policies earned 108/128. **Decision under this plan:
reject promotion.** Neither the original criteria nor these results are
being rewritten. The file remains unchanged and unpromoted.

This criterion excludes the measured wins against the current versions from
its pooled improvement measure. A separate prospective win-rate reassessment
will compare old and new against the same four opponents on untouched seeds,
with a pooled metric across all four and explicit external non-regression.
The old findings remain evidence; fresh outcomes are required for promotion.

The original final aggregation hit a null telemetry field from the historical
artifact after all 384 rows were saved. This was repaired by treating null as
empty telemetry and recomputing the unchanged gates. No games were rerun.
The repair and hashes are recorded in confirmation.json. Two diagnostic
reuses of native losses found no failed own purchases; lack of funding does
not explain those two losses. They are not independent validation.
