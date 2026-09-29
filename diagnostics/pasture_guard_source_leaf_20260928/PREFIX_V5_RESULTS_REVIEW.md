# Pasture source-fallback prefix v5 review

**Reviewed:** 2026-09-29 02:49 IST  
**Candidate SHA-256:** `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`  
**Runner SHA-256:** `6f30dfd2449a5f558cbb3fa6634725d8c2ef2201b94cade81dc90213f9f81b09`  
**Manifest SHA-256:** `2c5b8f2d7c9cfebb2629c98ad1c5047218e34787ebd76c9b2ea6c5722cfe8e37`  
**Result receipt SHA-256:** `a670041c00631067b35ab8967984260ce5a2995444537b8651681b9a01d87cc4`.

## Result

The frozen v5 runner completed its four fresh exact-a44 source-fallback
prefixes with one worker, after statically reusing ten previously passing
donor rows. The receipt is **complete but `passed: false`**. All four fresh
rows fail only `intended_bridge_and_leaf_telemetry_only_gate`; every other
recorded gate passes.

- On both `live-114274897` seats, candidate and direct exact-a44 source
  observations match through step 72; actions match through step 71, with
  the intended route `113332529` changing only step 72. The Brunch leaf key
  matches the live observation and the guard records one activation.
- On both `public-win-114193811` seats, observations and all actions match
  through step 72. The ICE_CREAM_SHOP key is correctly off-trigger and the
  guard records zero activations.
- Every fresh row is still ACTIVE at observation 72; policy, bridge, guard,
  and procurement error ledgers are empty. This was 288 fresh native
  transitions total. No complete game was run.

## Gate diagnosis

The v5 runner's telemetry gate has a comparison bookkeeping error. It
computes the candidate-only step-1 telemetry keys and confirms they equal
the expected bridge-selector and guard-leaf key set. It then forms the
candidate's shared-core telemetry by removing only `bridge_rival_pastures`
and the three leaf fields. The remaining bridge-selector fields are still
present in the candidate core, while the direct `_BRIDGE_SOURCE_AGENT`
reference intentionally has no bridge-selector telemetry. The core maps
therefore compare unequal even though those bridge fields are explicitly
candidate-only and separately checked for source selection, rival hands,
rival pastures, and zero bridge errors. This mechanically explains the same
single failed gate on all four rows.

Do not override the v5 `passed: false` receipt or count it as policy
qualification. Its observation, action, activation, and error evidence is
useful, but the intended telemetry-only gate did not pass. A separate v6
runner may correct the comparison by excluding the entire expected
candidate-only key set from the shared-core map, while retaining exact
candidate-only-key and selector-value checks. It must bind the unchanged v5
receipt and preserve every observation/action/error gate. No full-game pilot
is authorized by this prefix result.

## Verification

- `prefix_v5.py verify` passed with 14 jobs and zero simulations before the
  run.
- An independent root audit rechecked all 528 manifest file bindings; none
  differed. The candidate SHA, exact-a44 comparator SHA, manifest, and
  static freeze receipt matched their recorded values.
- `prefix_v5.py run --workers 1` completed all four fresh rows and wrote a
  complete receipt. The result remains an explicit failed gate pending any
  separately versioned harness correction.

## Decision

**Do not promote the pasture candidate and do not launch its full-game pilot.**
Preserve v5 as failed. Continue only with a versioned, hash-bound telemetry
gate correction and static review; then rerun the four short prefixes before
considering any study pilot.
