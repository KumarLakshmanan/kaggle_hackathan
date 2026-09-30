# Exact-V5 Roman bridge prefix probe

## Objective and limit

Check the proposed shared166 opening adapter against both seats of the saved
`live-114270587` replay. Use the exact V5 parent, its hash-bound opponent
action tape, and Kaggriculture 1.32.7 native transitions. This probe covers
only steps 0, 1, and 2, plus one transition applying donor action 2. It is not
a full game or outcome qualification.

The probe first records both exact V5 baseline prefixes. It performs no adapter
discovery if either seat differs from the historical source trace. Only after
both pass does it discover the public step-2 snapshot produced when the
adapter HIRE replaces the parent step-1 market orders. It binds each snapshot
to the seat, replay, opponent tape and action 1, plus the adapter HIRE action
and its hash. A second replay validates those provenance fields before
injection, then checks the adapter's merge guard before it emits the donor
action.

## Frozen inputs

- Exact V5 parent: `diagnostics/a44_ghost_kwa_piice_goalpanel_20260929/candidate.py`, SHA-256
  `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
- Adapter: `../adapter_layer.py`, whose public trigger and own-state guard
  require the target's exact step-1 opening.
- Raw shared166 donor schedule:
  `diagnostics/donor_opening_agents_20260928/candidate_shared166.py`, SHA-256
  `fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849`.
- Target replay: `live-114270587`, seed `2053487982`; the declared replay SHA
  is over decompressed JSON content. The freeze manifest separately records
  the exact compressed replay file bytes.
- Matched opponent action tape file SHA-256:
  `18ba3ec92eec0ec7bab95498119eebae88e7ce0ca4571eba42ffbaeb9ddda4b1`.
  Decoded action-list SHA-256:
  `4fa1c7ac2d31990c78ef1b73bc995d7cbf12e4813b6646611537274469553455`.
- Matched opponent action 1 SHA-256:
  `48e7b680c2f75b6a1d838749d1289420710bd6fb05c27275c9f2c38ac26769ff`.

## Gates

For each seat independently:

1. Exact V5 step-0 action and resulting observation 1 match the historical
   source trace. The adapter's step-0 action must equal V5 byte-for-structure.
2. At observation 1, the public trigger and full guarded own opening state
   match. The adapter emits NORTH, PASS for four existing hands, and HIRE.
3. The two-seat baseline gate passes before any adapter discovery. After that
   HIRE and the matched opponent action 1, the complete own farm and private
   state satisfy a full step-1-to-step-2 prediction, including all fields that
   should remain unchanged. Record the complete rival
   farm and shared market, each bound to this seat, replay, action-tape
   provenance, and adapter HIRE hash. Do not reuse a snapshot from the other
   seat.
4. Both seats must pass the discovery gates before either validation replay
   injects a snapshot or calls the donor. On each fresh replay, validate the
   snapshot provenance against the current seat's frozen job before injection.
   Check the complete predicted own state and public rival-farm/market merge
   before calling the adapter at step 2.
5. Its step-2 action equals the raw donor action with the specified worker
   permutation. Apply it only after the expected action matches. Then verify
   exactly two COW units are collected by the intended hands, with no
   action-shape or status error.

If either historical V5 prefix fails, skip all adapter discovery. If either
seat fails a later opening, provenance, merge, or remap gate, stop the route
splice. Do not run full games. If both seats pass, retain the adapter only as
an offline candidate for a later small target/control outcome pilot. Fixed
replay prefixes do not establish competitive strength or reactive validation.

## Execution contract

`prefix_probe.py freeze` binds all source files, the native helper and engine,
the target replay/tape, and both historical target traces. `verify` rebuilds
the intended input/job set and checks exact manifest fields and bindings; it
is read-only. `run` is one-shot, verifies again while holding the shared
simulator lock, writes seat-specific discovery snapshots and a results
receipt, and never resumes a partial attempt. It does not read or modify root
`main.py` or contact Kaggle.
