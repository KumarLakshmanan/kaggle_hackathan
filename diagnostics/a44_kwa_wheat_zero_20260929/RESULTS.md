# Kwa wheat-zero route splice results

## Decision

Keep this as a successful, narrow fixed-replay rescue and advance it to
reactive native qualification. Do not promote it into root `main.py` yet. The
six-game panel was frozen before the run and all six outcome gates passed,
but saved action tapes do not establish behavior against a reacting opponent.

## Candidate and trigger

Candidate SHA-256:
`36f1a351c4b85b62d7c5fb07489927821d98823c57d0e7131e19eb186951a54e`

Parent 6d SHA-256:
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`

At observation 72, the wrapper selects route `113535489` only when the a44
bridge selected `source`, the public shop key is
`BRUNCH_SPOT|M8+|C<S|G0`, and public rival WHEAT plots equal zero. It reads no
fixture identity. Static preflight rehashed all 208 bound trace rows: exactly
the two seats of `live-114227779` trigger; none of 40 top20 seats or 108
public-win seats trigger. Four same-key wheat-positive control seats remain
inactive.

## Frozen six-game outcome check

The runner used one worker under the shared lock and recorded append-only
attempt and outcome ledgers. All games finished `DONE`/`DONE` at 720 frames,
with no candidate errors. All six gates passed.

| Fixture | Seats | Result and margin | Delta vs 6d combined receipt |
|---|---:|---:|---:|
| `live-114227779` (Kwa target) | 0, 1 | Win, +4,118 each | +7,976 each |
| `live-114236633` (wheat-positive control) | 0, 1 | Win, +5,360 each | 0 |
| `live-114257327` (wheat-positive control) | 0, 1 | Win, +2,992 each | 0 |

The target was a 6d-combined loss at −3,858 in both seats, so this rule flipped
one fixture into a two-seat sweep. Integrated saved-panel totals therefore
move from **22/30 to 23/30** loss sweeps (76.7%). Top20 remains **19/20** and
the saved public-win panel remains **53/54**. Four additional loss sweeps are
needed to reach 27/30. The combined 6d receipt marks the target's underlying
control row as decision-equivalent reuse; the runner binds that exact receipt
and requires the four non-target controls to match it exactly.

## Reproduction and limits

Run receipt: `runs/six_game_run_001/outcome_receipt.json`.
Append-only records: `runs/six_game_run_001/attempts.jsonl` and
`runs/six_game_run_001/outcomes.jsonl`.
Static preflight receipt: `preflight.json`.
Frozen run plan and gates: `PLAN.md` and `manifest.json`.

This was fixed-tape evidence only. No Kaggle page, leaderboard, or new replay
was checked or downloaded. Root `main.py` remains unchanged at SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
