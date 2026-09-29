# Pasture source-fallback prefix v6 review

**Reviewed:** 2026-09-29 03:04 IST  
**Candidate SHA-256:** `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`  
**V6 runner SHA-256:** `18692b763631326e228f712e04fbddadaefc460522152e246b3c400d6ffd098f`  
**V6 manifest SHA-256:** `fd0744ee1e4becc5c192da62c6dca85d6f640f6fc92abb68531a86137763f01f`  
**V6 result receipt SHA-256:** `5e445fbcb87455a2ca0137f9005b978aa4fe9a251cc9fd465a77e4fa6afef3b4`.

## V5 failure and v6 correction

V5 remains a complete failed receipt. Its four fresh rows failed only the
step-1 telemetry-only gate. V5 recorded all eleven expected candidate-only
bridge/leaf telemetry fields, but filtered just four before comparing shared
telemetry. Seven bridge selector fields remained in the candidate's shared
map and were absent from the direct source reference, making the equality
fail regardless of the shared policy telemetry.

V6 is a separately frozen harness version. It removes the complete,
predeclared eleven-key instrumentation set from the shared-core comparison,
still requires the candidate-only set to match exactly, and separately
checks bridge selection, public hands and pasture counts, zero bridge errors,
and inactive step-1 leaf telemetry. It records any remaining shared-core
value mismatches and fails if one exists. All observation, action, trigger,
source-selection, active-status, and error gates remain intact. The candidate
policy and frozen jobs are unchanged from v5.

## Result

The fourteen-job receipt is **complete and `passed: true`**. It reuses ten
previously passing donor rows bound to the v3 receipt and runs four fresh
exact-a44 source-fallback prefixes, one worker, 288 fresh native transitions.

- Both seats of `live-114274897` match exact-a44 source observations through
  step 72 and match actions through step 71. The only action difference is
  the intended step-72 Brunch route `113332529`; the leaf activates exactly
  once per seat and the shared-core telemetry difference list is empty.
- Both seats of `public-win-114193811` match exact-a44 source observations
  and actions through step 72. Its `ICE_CREAM_SHOP|M<8|C<S|G0` leaf remains
  inactive, with no route selected and zero activations.
- All four fresh jobs stay active at observation 72. Policy, bridge, guard,
  and procurement error ledgers are empty. All other recorded gates pass.

Root independently checked every one of the 534 v6 manifest file bindings;
none differed. The v5 runner, plan, manifest, freeze receipt, progress, and
failed result hashes remained unchanged during v6 review and execution.

## Decision

This validates the short prefix mechanism only. The result explicitly sets
`full_game_outcomes_run: false` and
`study_pilot_authorized_by_prefix: false`. It does not prove a terminal win,
does not qualify the pasture candidate for promotion, and does not update the
22/30 best local loss-sweep result. Keep root `main.py` unchanged. Any outcome
pilot needs its own frozen plan and must compare against the current
Goose4+Smoothie candidate on the affected fixtures.
