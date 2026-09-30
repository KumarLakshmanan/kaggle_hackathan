# Pasture prefix v3 — result review

**Completed:** 2026-09-29 01:55 IST  
**Decision:** Do not start the full-outcome pilot. Correct the comparator and
repeat the affected prefix checks against exact a44.

## Frozen bindings

- Candidate: `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`
- Runner: `1def02d1978cc3fa03d14dbb24ffb8382768d08d9358e88ab7acf7caec04c6a2`
- Manifest: `d62c0d2f955cb4da658c13d63b2b7b15bf36fbd8bfa0d18dacd93b9d5121b196`
- Result receipt: `2689b164e553660a61e08d116c2d9c955acce6e332fe088754f1e10039acdba4`
- Progress ledger: `28b2e2ea4e1c41cde91b2f98c7ef9ca8e6956fd2a807f988735af567c70d3f8c`

The run completed 14 jobs / 1,008 native transitions. All processes remained
`ACTIVE` at observation 72, and the error/guard ledgers are empty. The ten
donor-control jobs compared with exact a44 all passed. The four target/fallback
jobs did not pass the frozen gates.

## Why the four target rows are inconclusive

The pool binds the candidate base and `source` fallback to exact a44
(`a44c8c2c…727090f`). However, v3 compares the two `source` fallback fixtures
against `main_candidate_animal_liquidity_20260928_32e299fe.py` instead. The
exact32e file has different turn-0/turn-1 market orders and cash, so all four
fallback jobs fail their opening action/state comparison before they can
answer whether the a44-based policy is compatible.

On both THIRD seats the candidate does select the source branch for the
pasture-bearing opening, and the intended step72 leaf activates at
`BRUNCH_SPOT|M8+|C>S|G+` with route `113332529`. On both ChrisTu seats the
source branch is selected and the leaf remains inactive. No policy or guard
errors occurred. The ChrisTu runtime feature mismatch is also measured
against the wrong exact32e reference context. These are harness-comparator
failures, not valid candidate pass/fail outcome evidence.

Preserve the v3 receipt as run. V4 must compare these four jobs against exact
a44, require observations equal through step72 and actions equal through
step71, then permit and record the single intended THIRD leaf action at step72.
Reuse the ten already-passing v3 donor controls only if the v4 manifest binds
the same candidate and exact-a44 comparator. No terminal outcome game has
been run; the candidate remains unqualified and no promotion is allowed.
