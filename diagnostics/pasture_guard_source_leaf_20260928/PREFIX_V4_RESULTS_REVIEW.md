# Pasture prefix v4 results review

Completed 2026-09-29 02:23 IST. The frozen v4 runner completed all 14 rows:
ten previously passing donor prefixes were reused under their bound v3
checks, and four fresh prefixes compared the candidate with the exact a44
`_BRIDGE_SOURCE_AGENT` branch. The recorded receipt is **complete but
failed**; no full games ran.

## Fresh prefix observations

All four fresh candidate/reference pairs had identical full observations at
steps 0–72, no policy/guard/procurement errors, and the required source
selection. On both THIRD seats, actions were identical through step 71 and
only action 72 differed; the runtime key was
`BRUNCH_SPOT|M8+|C>S|G+` and the intended route `113332529` activated once.
On both ChrisTu seats, actions and observations matched through step 72 and
the leaf stayed inactive.

The v4 receipt did not pass because of two specific gates:

- `intended_bridge_and_leaf_telemetry_only_gate` failed on all four rows.
  The runner recorded no reference telemetry from the direct a44
  `_BRIDGE_SOURCE_AGENT` call, while candidate telemetry included its
  ordinary counters and bridge/leaf fields. Both sides had empty policy and
  guard error ledgers. This is an instrumentation comparison failure; the
  empty mapping does not prove the telemetry values are equal.
- `runtime_public_obs72_feature_binding_gate` failed on both ChrisTu rows.
  Their actual runtime key was `ICE_CREAM_SHOP|M<8|C<S|G0`, with the leaf
  inactive. The check compared it with the frozen feature row from a44's
  outer dispatcher, which selected `shared151`; these v4 comparisons
  intentionally execute the source branch. Candidate and forced-source
  reference observations still matched each other at every step.

## Decision

**Do not start the full-game pilot from v4.** Preserve this completed
`passed:false` receipt and all v1–v3 artifacts. The failure does not establish
that the policy change is harmful: its mandatory gates mix a missing
reference telemetry capture with a frozen feature row from a different
dispatch path. It also does not establish that the policy change is safe or
profitable. A separately frozen v5 adjudicator must retain the observation,
action, branch, error and route checks while capturing telemetry correctly
and validating the feature key against the actual runtime observation. Root
`main.py` and Kaggle state remain unchanged.

Hashes:

- v4 candidate: `cb5afda4d13cbc2c1f2a59fafca51317950bce6b02b894e20498f58c73f71683`
- v4 runner: `7b666235d813c37102f35abce559ff83f7212fd3f1bcfddd297cc7531fc1c407`
- v4 manifest: `052ec8983686cff045f449efd4c5b37161d9c90471924f38467e8e9827d805ef`
- v4 results: `33b594d4042a4db4c59fd5d7eee5c9940ffcf7e35d918e48289c81ec285ae416`
- v4 progress: `dc2439344507db7ea976ba48f1ff4077fa7199fac022f29d54971128b25e0abe`
