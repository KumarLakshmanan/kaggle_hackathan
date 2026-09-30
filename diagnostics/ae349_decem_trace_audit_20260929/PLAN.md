# Exact ae349 DECEM execution trace audit

## Question

Does the exact current candidate expose a new worker-execution or funding
bottleneck on the remaining DECEM fixed-replay loss, beyond the mechanisms
already examined in the local DECEM studies?

## Scope and interpretation

This is a diagnostic replay only. It reruns the already-scored DECEM fixture
against its saved 719-action opponent tape in both candidate seats, using the
exact ae349 source. It does not change a policy, select a route, or provide
independent validation. A trace observation can motivate a later hypothesis;
it cannot establish that a proposed change improves reactive play.

Stop after both-seat trace parity and the read-only event analysis. Any later
strategy experiment must get its own frozen plan and candidate hash.

## Frozen inputs

- Candidate: `main_candidate_improved_20260929.py`, SHA-256
  `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`.
- Saved-panel manifest: `diagnostics/combined_agent_257f_20260929/saved_panel/comparison_manifest.json`, SHA-256
  `b5f7be800528fb8d070caa9fbaf3493c3b934c3176a6416590d2d6a2dd3ab3fe`.
- Exact ae349 result rows: `diagnostics/combined_agent_257f_20260929/saved_panel/comparison_manifest_results.jsonl`, SHA-256
  `ebe9c97327a0086766f67c88213e2fe086ebfa8f89d8ba84db8f5ba918091562`.
- Saved-panel receipt: SHA-256
  `218297125b45a782f903b2a7aaa178597b708a53f0ffac4f196b404f7b95ce2d`.
- Fixture: `top20-01-DECEM-114267880`, seed `1390733823`, both candidate
  seats. Replay SHA-256 `1d6a1d7ce66a2e07bd1576528e930ac5f13777fdb88f673eea3aa0a4c34c8072`;
  opponent-action SHA-256
  `a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226`.
- Native helper bindings are checked by the runner and recorded in its
  receipt. Kaggle and network access are out of scope.

## Checks

Require both replays to match the hash-bound ae349 reference row in result,
both rewards, margin, statuses, frame count, policy errors, and telemetry.
Require all 720 frames and unchanged source hashes. Preserve both traces and
report any candidate mechanism as a diagnostic lead only.
