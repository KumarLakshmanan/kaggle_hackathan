# Pasture source-leaf native prefix plan, v6

## Purpose

V6 is a separate correction to the frozen v5 prefix harness. It does not change the candidate policy, fixture set, exact-a44 comparator, or any observation, action, leaf, or error requirement. The v5 manifest, result, progress ledger, and freeze receipt remain bound and unchanged. V6 only fixes the shared step-1 telemetry comparison and adds an auditable record of the compared shared keys and values.

The candidate remains `candidate_pasture_guard_source_leaf.py`, SHA-256 `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`. The active reference remains exact a44, SHA-256 `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`, with affected reference calls pinned to `_BRIDGE_SOURCE_AGENT`.

## Read-only v5 failure audit

The completed v5 result has 14 rows and `passed: false`. Its only failed check on each of the four fresh rows is `intended_bridge_and_leaf_telemetry_only_gate`. All four rows pass exact full-observation equality at steps 0–72, action equality at steps 0–71, the THIRD-only step-72 allowance, source selection, runtime leaf-context, leaf activation/inactivity, and zero-error checks. The ten reused donor rows remain the passing v3 rows.

Each fresh row records the exact 11 expected candidate-only telemetry keys. V5 removes only `bridge_rival_pastures` and the three `guard_leaf_*` keys from its shared-core dictionaries. It therefore leaves these seven candidate-only bridge selector keys in the candidate shared-core dictionary:

- `bridge_selected`
- `bridge_requested`
- `bridge_rival_hands`
- `bridge_common_failed`
- `bridge_guard_refusals`
- `bridge_source_guard_failed`
- `bridge_errors`

By the saved `candidate_step1_extras` set, these keys are absent from the forced-source reference telemetry. Their presence in the candidate core guarantees that v5's shared-core dictionary equality is false, regardless of whether all shared source-policy values match. The same rows show that the candidate-only key set is exactly the expected 11 keys, the separate bridge selector gate passes, and the observation-1 leaf telemetry is inactive. This is a narrow harness defect supported by the saved rows and frozen source.

## V6 telemetry gate

V6 removes the complete fixed 11-key candidate-only bridge/leaf instrumentation set from both shared-core dictionaries before comparing source-policy telemetry. It still requires the candidate-only keys to equal that fixed set exactly. It then checks selector values, rival hand and pasture counts, zero bridge/guard errors, and inactive step-1 leaf telemetry separately. Any unexpected or missing key fails. Any mismatch among the remaining shared source-policy keys fails and is recorded by key with candidate and reference values. This correction does not forgive source-policy telemetry differences.

V6 retains the rest of the frozen v5 gates:

1. Candidate and exact-a44 forced-source full observations equal at every step 0–72.
2. Actions equal at steps 0–71. ChrisTu must also match at step 72. THIRD may differ only at step 72; both step-72 actions are recorded.
3. Common opening at step 0, source restoration at step 1, procurement, and own physical/private state at steps 2–72 pass.
4. Candidate requests and selects `source` at observation 1, with public rival hands and pasture count bound to the frozen feature row.
5. The reference invokes exact-a44 `_BRIDGE_SOURCE_AGENT`; source telemetry is captured from the module-level `agent.telemetry` sink.
6. At observation 72, public rival melon/cow/sheep/goose counts match the frozen row, the reported leaf key equals the key recomputed from the actual observation, and frozen/live trigger classes agree. THIRD uses `BRUNCH_SPOT|M8+|C>S|G+` and activates goose route `113332529` exactly once. ChrisTu remains off that trigger and its leaf stays inactive; the saved shop-name difference remains explicit evidence.
7. The five donor fixtures remain off-trigger; the ten v3 rows retain exact saved-a44 trace reproduction. Policy, bridge, guard, collision, procurement, and engine errors remain zero, and both policies are active at observation 72.

## Frozen job and input bindings

The v6 matrix retains seven fixture seeds and 14 seat jobs: 10 byte-identical passing donor rows reused from v3 and four fresh source-fallback prefixes for both seats of `live-114274897` (THIRD) and `public-win-114193811` (ChrisTu). The manifest hashes the candidate, pool, all 208 feature rows, replay and action-tape inputs, seeds, exact-a44 source, engine/helpers, staged controls, and v1–v5 lineage. The 32e source is bound as historical provenance only and is not an active comparator.

The read-only v5 audit validates the v5 file bindings, result-to-progress equality, the sole false gate, each fresh row's exact observation/action evidence, all relevant selector/leaf checks, and byte-identical donor reuse. Freeze and verify perform no simulator jobs and do not produce a v6 progress ledger. Root reviews the v6 manifest and receipt before deciding whether to run prefixes.

Static commands:

```powershell
py -3 -m py_compile diagnostics\pasture_guard_source_leaf_20260928\prefix_v6.py
py -3 diagnostics\pasture_guard_source_leaf_20260928\prefix_v6.py freeze
py -3 diagnostics\pasture_guard_source_leaf_20260928\prefix_v6.py verify
```

If root approves after review and the simulator slot is free, the staged command is:

```powershell
py -3 diagnostics\pasture_guard_source_leaf_20260928\prefix_v6.py run --workers 1
```

The runner processes one fresh prefix at a time. A passing prefix receipt does not authorize the later outcome-game panel.
