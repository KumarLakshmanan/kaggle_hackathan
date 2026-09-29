# Exact-V5 isolated pasture four-seat pilot

## Scope

Test candidate `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`
against its exact parent `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
The panel contains both seats of the THIRD loss (`live-114274897`) and both
seats of the ChrisTu control (`public-win-114193811`). Each seat is run once
with the parent and once with the candidate: eight full native fixed-tape
games total.

## Frozen gate

- All eight games finish DONE/DONE at 720 frames with no candidate errors.
- Both candidate THIRD seats win with positive margin and the paired parent
  seats lose.
- Both candidate ChrisTu control rows match their paired parent on result,
  both rewards, margin, statuses, and frame count.
- Runtime telemetry confirms the public five-hands/one-pasture trigger only
  on THIRD; the source Brunch route `113332529` activates there for 647 turns.
  Existing Ghost, Kwa, Goose4, and Pizza/Ice Cream routes remain inactive.
- Any failure rejects this derivative for further composition. A pass is only
  a focused fixed-tape result; it does not establish reactive performance.

The parent, candidate, traces, replay tapes, and native engine helpers are
hash-bound by `frozen_manifest.json`. The runner takes the shared simulator
lock and a package-local one-shot lock. It never reads Kaggle or changes
`main.py`.
