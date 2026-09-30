# Pasture guard + source Brunch leaf outcome

## Decision

Reject this candidate for promotion and do not use its two target wins as
isolated evidence for the Brunch route. Preserve the outcomes as descriptive
fixed-tape results. The exact-control gate failed because the candidate changed
the step-1 bridge branch on the target and control games.

## Frozen candidate and panel

Candidate SHA-256:
`5b4ef52d19cb8ffb310b2bb067c725810241668667a0b5b468ac09b6b9215506`.
It derives from exact 6d parent
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.
The patch changed the step-1 selector from
`shared151 if rival hands >= 5` to `shared151 if rival hands >= 5 and rival
pastures == 0`, then added the source-only Brunch route
`BRUNCH_SPOT|M8+|C>S|G+ -> 113332529` at step 72.

The four fixed-tape games were clean, DONE/DONE at 720 frames, with no policy
errors. Both `live-114274897` target seats won: seat 0 margin +5,983 versus
the frozen 6d margin -17,760 (delta +23,743); seat 1 margin +2,235 versus
-17,099 (delta +19,334). Both `public-win-114193811` controls also finished,
but each margin changed from +1,226 to +8,353 (delta +7,127); candidate
reward and rival reward both changed. Therefore `all_outcome_gates_passed` is
false despite the target wins.

## Why the control changed

The derivative selected the `source` bridge at step 1 on all four games
because each rival already had one pasture. The frozen 6d feature census
records `shared151` on those four jobs. Inactive Brunch telemetry on the
ChrisTu controls only says the new step-72 leaf did not fire; it does not undo
the earlier policy change. The earlier prefix comparison forced 6d onto its
source branch and therefore did not establish default-6d control parity.
These two target wins cannot be attributed to the Brunch leaf.

All evidence uses saved opponent action tapes and local native transitions.
It is not reactive-opponent validation. Root `main.py` and Kaggle status were
not changed or checked.

## Receipts

- Outcome receipt SHA-256: `0c7ecfbc89a0110c7aa18796ce2d814643262d6589c412fedf5e8016c302a1ec`
- Outcomes JSONL SHA-256: `83598f5fea57693e9202bcf8b061f5f05e1dd44d922eddcdf81d21a846b9a468`
- Run manifest SHA-256: `3693de79b1d76af529c1a1b442d27fc18633880ce32ee752e9a88e2cda4e1810`
- Frozen outcome manifest SHA-256: `e5062341f4d0ab410c009dadc528e93421050797802c949aa473ee375c098dd7`

