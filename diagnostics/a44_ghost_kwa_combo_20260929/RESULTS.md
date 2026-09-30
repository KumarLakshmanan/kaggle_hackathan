# Ghost + Kwa combined V4 fixed-tape outcome run

Date: 2026-09-29 (UTC run completion: 2026-09-28 23:32:34)

## Candidate and panel

Candidate SHA-256: `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`.
It composes the independently tested Ghost Ice wheat route and Kwa wheat-zero
route on the exact 6d parent, `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

The V4 panel SHA-256 is
`8f9eec84d361de731d95de88d76c5e78bf2c6bab58012a376daa5bdf466d15bd`.
It contains 20 saved top-team fixtures and a disjoint nine-fixture union:
six fixtures tagged `loss30` and three saved public wins, for 29 fixtures and
58 seat games. The static freeze bound 147 inputs; its manifest SHA-256 is
`277931bcc49350690a160e465ba8d96a0a4feb7c5be2af8de039bf60808723c9`.
Three Luna Max read-only reviewers found no execution blocker before the
run.

## Results

The one-shot run completed all 58 games cleanly at DONE/DONE/720 with zero
policy errors. All telemetry checks passed, all four expected trigger seats
won, and all 54 inactive controls exactly matched the 6d baseline on outcome,
both rewards, margin, statuses, and frame count.

- Saved top-team set: **19/20 both-seat sweeps (95%)**, meeting the 18/20
  threshold and matching the 6d baseline. No top-20 row activated either
  route.
- Kwa target `live-114227779`: both seats changed from loss at margin -3,858
  to win at +4,118.
- Ghost target `live-114288168`: seat 0 changed from loss at -2,253 to win at
  +1,298; seat 1 remained a win, moving from +1,425 to +1,298. The fixture is
  now a both-seat sweep.
- The six `loss30`-tagged fixtures selected for this composition panel contain
  four exact win/win controls plus the two target fixtures. The composition
  therefore sweeps all six, compared with four of six under 6d. This is not
  the full 30-loss result.

Receipt SHA-256:
`c576c106f4e40b009fba58cc2642d73c70571880bd940f75ca3b128a85cc51c9`.
Append-only outcome ledger SHA-256:
`c31cd08a2aa8f8090a30fc3dd94d8ccd9b725a326326a91a5ffa478b31f8b2d3`.
The machine-readable results are in `outcome_run_20260929/outcome_receipt.json`
and `outcome_run_20260929/outcomes.jsonl`.

## Decision and limits

Retain this as a promising offline composition, not as a promotion. It passes
the saved top-20 threshold and rescues two fixtures, but the run covered only
six of the frozen 30 loss fixtures. The exact 6d baseline had 22/30 sweeps, so
the feature census suggests a 24/30 result if the other 28 fixtures remain
unchanged; that projection still falls short of 27/30 and must be checked by a
full 30-loss run. Continue offline loss research, test the candidate across all
30 losses and 20 top-team fixtures, then qualify any final candidate against
reacting opponents before considering `main.py` promotion. `main.py` and
Kaggle were untouched.

This run replays saved opponent action tapes. It does not establish reactive
performance or independent generalization. The frozen manifest verifies the
static receipt’s contents and references, but does not bind its own file hash
(avoiding a manifest/receipt hash cycle). The preflight docstring still says
“18-seat,” and its synthetic telemetry test is narrower than the real
four-trigger checks; these are recorded non-blocking audit caveats.
