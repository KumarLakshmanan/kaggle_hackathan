# Pasture source-leaf native prefix plan, v5

## Purpose and scope

This version corrects the v4 prefix harness after its four fresh source-fallback rows were completed and failed two harness checks. It retains the same frozen candidate, fixtures, policy comparator, source-only Brunch goose leaf, and behavior gates. It does not change the candidate policy or run complete games.

The candidate remains `candidate_pasture_guard_source_leaf.py`, SHA-256 `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`. The active reference remains the exact a44 source, SHA-256 `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`; affected reference calls pin its `_BRIDGE_SOURCE_AGENT` entrypoint. The pool and feature receipt remain hash-bound and contain all 208 frozen rows.

## Read-only v4 audit and corrections

The v4 receipt is complete and reports `passed: false`. Its four fresh rows still establish candidate-versus-exact-a44 full-observation equality for steps 0–72 and action equality for steps 0–71. Both THIRD rows differ only at action step 72; both ChrisTu rows have no action differences. The 10 donor rows are unchanged passing v3 rows.

The telemetry failure is in v4 instrumentation. It read telemetry from `policy_fn.telemetry` after directly invoking the saved nested `_BRIDGE_SOURCE_AGENT`. That function's global `agent.telemetry` writes resolve to the exact-a44 module's outer `agent.telemetry` sink. V5 snapshots and checks that module sink for candidate and reference. It still requires equal shared source-policy telemetry, only the expected bridge and leaf instrumentation keys on the candidate, the expected source branch selection, inactive leaf telemetry at step 1, and zero policy, bridge, guard, and procurement errors.

The ChrisTu feature failure also comes from the reference context. The saved feature row was captured through the outer dispatcher and names `BAKERY`; the forced-source reference replay reaches `ICE_CREAM_SHOP` at observation 72. The frozen and runtime exact leaf keys are both off-trigger, and their rival melon, cow, sheep, and goose counts match. V5 records both shop names and keys, requires those non-shop counts to match, and requires the frozen and live contexts to have the same exact-leaf trigger status. THIRD must match `BRUNCH_SPOT|M8+|C>S|G+` in both contexts. ChrisTu must remain off that key in both contexts. This preserves the leaf-specific safety check while exposing the known shop difference.

## Frozen prefix matrix

The manifest includes seven fixture seeds and 14 seat comparisons:

- Five donor fixtures (`live-114232208`, `live-114235177`, `live-114279308`, `top20-03-Boey-114266440`, and `top20-06-Majkel1337-114263239`) contribute 10 reused passing v3 candidate-versus-a44 rows. Reuse is permitted only with byte-identical job definitions, candidate and comparator hashes, complete passing checks, and exact saved-control replay.
- `live-114274897` (THIRD) and `public-win-114193811` (ChrisTu) contribute four fresh candidate-versus-exact-a44 forced-source rows, both candidate seats for each fixture.

Every fixture replay, 719-action tape, seed, candidate, exact-a44 source, engine, native helper, cache, control receipt, v1–v4 lineage file, and v3/v4 prefix result is bound by SHA-256 in the v5 manifest. The four affected jobs use exact a44 `_BRIDGE_SOURCE_AGENT`; no 32e source comparison is active.

## Required gates

For each of the four fresh rows:

1. Candidate and forced-source reference observations are fully equal at steps 0 through 72.
2. Candidate and reference actions are equal at steps 0 through 71. ChrisTu must also match at step 72. THIRD may differ only at step 72; both step-72 actions are recorded.
3. The common opening action at step 0, source restoration action at step 1, and procurement/state checks pass. Own physical and private observations match at steps 2 through 72.
4. The candidate requests and selects `source` at observation 1. Its recorded rival hand and pasture counts must equal the bound public observation. The reference call is the exact-a44 source entrypoint.
5. Source-policy telemetry at observation 1 matches through the module-level `agent.telemetry` sink. Candidate-only bridge selector and guard telemetry must match the bound source decision. Leaf telemetry is inactive at observation 1. Policy, bridge, guard, collision, and procurement error counters stay zero; both policies remain active at observation 72.
6. At observation 72, rival melon/cow/sheep/goose counts match the frozen feature row. The live key is recomputed from the actual public observation and must equal the candidate's reported leaf key. THIRD's frozen and live keys must both equal `BRUNCH_SPOT|M8+|C>S|G+`; its goose route `113332529` must activate exactly once. ChrisTu's frozen and live keys must both be off that exact trigger and its leaf route must remain inactive. Shop-name differences are recorded as evidence, never discarded.
7. The five donor fixtures remain off the leaf trigger and their ten reused rows remain passing with exact saved-a44 trace reproduction.

No mismatch is permitted in observations, candidate branch selection, error counters, leaf route/key telemetry, or any action outside THIRD step 72. V5 does not infer that the ChrisTu shop mismatch is harmless by itself; it records the mismatch and only accepts it when both recomputed leaf keys remain off the exact trigger and the four relevant public counts match.

## Static freeze and execution sequence

The static audit is read-only and must confirm the preserved v4 hashes/results, all 10 reusable donor rows, all four v4 affected rows, the exact-a44 comparator, 208 feature rows, and the 14-job matrix. `freeze` and `verify` run no simulator jobs. Root reviews the frozen v5 manifest and receipt before any prefix execution.

Static commands:

```powershell
py -3 -m py_compile diagnostics\pasture_guard_source_leaf_20260928\prefix_v5.py
py -3 diagnostics\pasture_guard_source_leaf_20260928\prefix_v5.py freeze
py -3 diagnostics\pasture_guard_source_leaf_20260928\prefix_v5.py verify
```

Only after root review and an explicit free simulator slot, the staged prefix command is:

```powershell
py -3 diagnostics\pasture_guard_source_leaf_20260928\prefix_v5.py run --workers 1
```

The runner submits one prefix at a time and writes a manifest-bound progress line after each completed row. The prefix proof is not authorization to start the 14 outcome games; those remain under root's separate sequencing and review.
