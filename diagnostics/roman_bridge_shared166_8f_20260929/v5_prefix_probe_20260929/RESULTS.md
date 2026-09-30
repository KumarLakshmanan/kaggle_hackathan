# Exact-V5 Roman bridge prefix result

## Outcome

The bounded two-seat probe passed for `live-114270587` against the frozen
shared opponent action tape. Both seats reproduced every recorded V5 source
check through step 2. Both adapter discoveries then passed, and both fresh
validation replays passed all provenance, state, merge, worker-remap, native
pickup, and active-status checks.

For each seat, the step-1 HIRE produced the complete predicted own farm and
private state at step 2. The seat-specific rival farm and shared market matched
the discovered snapshot on the fresh replay. The adapter emitted the expected
remapped donor action: the farmer moved SOUTH; worker slots 2 and 3 moved
NORTH; slots 4 and 5 each picked up one COW. The native transition credited
exactly two COW units to those intended workers, and both players remained
ACTIVE.

| Check | Seat 0 | Seat 1 |
|---|---:|---:|
| Historical V5 prefix | Pass | Pass |
| Post-HIRE own-state prediction | Pass | Pass |
| Seat/replay/tape/action provenance | Pass | Pass |
| Rival-farm and market merge | Pass | Pass |
| Expected donor remap | Pass | Pass |
| Two COW pickups by intended workers | Pass | Pass |
| States active after action | Pass | Pass |

## Scope and decision

This is a fixed-tape prefix diagnostic: it covers the opening and one donor
action, not a full game, reactive opponent, win rate, or score. It supports
continuing to a small target/control outcome pilot only. It does not support
promotion or a Kaggle upload.

The probe did not read or edit root `main.py` and did not contact Kaggle. The
shared simulator lock was released after the run.

## Frozen evidence

- Parent V5 SHA-256: `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`
- Adapter SHA-256: `0f0c5e6e3db158754e4500de051311c1bace8a114cd11dbd467b934f0872e19d`
- Donor SHA-256: `fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849`
- Freeze manifest SHA-256: `c4373d03310495d2a4cdfc3c861c24345dac8dd44f0baa102aa68d68e9838214`
- Snapshot ledger SHA-256: `fc745a6decef1613d5357ad1c002fbffc6685d8b4856485ff370a090d83c8b92`
- Result receipt SHA-256: `86508e558d08e4c38143c949fb6e36a56ec459a3b941f6841bc7ee510084c406`

The runner re-derived and verified the exact job set and all 19 frozen input
bindings before running. The final receipt is
`prefix_receipt.json`; its `passed` field is true for both seats.
