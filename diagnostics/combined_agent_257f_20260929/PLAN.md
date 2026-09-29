# New standalone candidate compared with uploaded 257 — 2026-09-29

## User request and scope

Build a separate standalone agent using justified prior approaches, test it
locally, and provide the result of every test case plus a final comparison.
This request does not authorize another Kaggle upload. Preserve root research
`main.py`, the exact last uploaded file, prior experiments and all failed runs.

Baseline: `diagnostics/upload_pet_source_guard_20260929_257f941d/main.py`,
SHA-256 `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`.
Its recorded saved panel has 27/30 archived-loss sweeps, 19/20 top20 sweeps,
92W/0D/8L across 100 seats, plus two winning Pet public-control seats.
The 102-row reference receipt SHA-256 is
`4086a1ebd23431efedcbd178a7e5367cc1e84d8999b1843a4e62d891aa5f2997`.

## Research lanes

1. Diagnose harmful public-production route choices while preserving the
   winning controls that use the same route/category. Stage the exact source
   change and its public-state rationale before any outcome run.
2. Diagnose whether saved-replay route substitutions harm physically similar
   reacting rivals. Require compatible schedules and public observations;
   opponent identities, episode IDs and hidden seeds must not select actions.
3. Reuse the separate exact-257 melon-delivery experiment only if its frozen
   prefix, preservation and target/control requirements pass. Do not repeat
   its games while another task owns the shared simulator lock.

Each lane first gets a small explicit both-seat target/control pilot with
source hashes and case list fixed before execution. Failed hypotheses are
reported and excluded from a combined file. Combining independently useful
changes still requires testing the combined file because they can interact.

## Saved-panel comparison

Run the exact combined candidate on all 102 reference fixture/seat cases.
Use the exact257 reference rewards after first reproducing the relevant
baseline pilot rows. Keep the two public controls distinct from the 100-seat
goal panel. Require clean completion, no policy errors, preservation of all
previous winning seats, and at least 27/30 archived-loss and 19/20 top20
both-seat wins. Report all remaining losses and all cash-margin regressions.

Wins/draws/losses are primary. A saved-panel improvement means either more
W/D/L points, or equal points with a higher aggregate paired cash margin and
no aggregate top20 margin reduction. This is development/regression evidence,
not independent policy validation or a calibrated leaderboard forecast.

## Final fresh original-shop reacting comparison

The seed block **2026092981–2026092984** was searched across existing local
diagnostic JSON/JSONL/Python/Markdown sources before outcomes; no existing
references were found. Use every seed, every opponent and both seats with
both exact257 and the new candidate: 2 arms × 4 seeds × 3 opponents × 2 seats
= **48 native games**. Bind the final candidate hash before starting.

Reacting opponents:

- Root research `main.py`, SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- Exact uploaded257 baseline, SHA-256
  `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`.
- `diagnostics/public_ahmed_v35_20260927/public_v35_main.py`, SHA-256
  `294e7e4d9d4b97413646960d318043e0f9116ce58f42fe02afd4716614a4e96d`.

The native engine chooses original shops. Mask the episode seed from policy
configuration. Require DONE/DONE at frame720 and no policy/runtime errors;
use the native action timeout plus overage rules, not an invented strict
one-second cutoff. Match rows by seed/opponent/seat. Score win=1, draw=0.5,
loss=0, and group both seats/all opponents within each seed when reporting
uncertainty.

Evidence of a fresh W/D/L improvement requires strictly higher pooled points,
no per-opponent point regression and at least three of four nonnegative
whole-seed point deltas. If points tie, report any paired-margin gain as a
margin result only; if the new logic never activates, its reactive benefit
is unvalidated. Four seed blocks are a limited screening sample, not proof
of a score or top10 ranking.

Finally check the standalone candidate's actual Kaggle file-loader entrypoint
and full action parity in both seats of an activated case and a control.

## Deliverables

- Separate standalone candidate and exact uploaded-baseline backup in the
  workspace root; no silent replacement of the ongoing research baseline.
- Source-bound JSON results and a readable Markdown table for every pilot,
  saved-panel case and final native comparison, including rejected attempts.
- Clear separation of measured improvement, no-change results, failures,
  and unverified future leaderboard performance.

Only the root task launches games under `diagnostics/.shared_game_run.lock`.
