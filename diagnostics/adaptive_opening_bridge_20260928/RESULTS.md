# Adaptive opening bridge feasibility — 28 September 2026

## Decision

Both frozen architectures pass the bounded engineering gate. Preserve the
two candidates for a separately frozen strength screen; neither is qualified
for promotion. No complete games or terminal wins were evaluated here.

`prefix.py` completed at 2026-09-28T17:19:05.323396+00:00, exit 0.
All 32 paired prefixes passed: two variants, eight rival opening classes,
both seats, 24 native turns each, plus their original-branch controls.
This is 64 prefixes and 1,536 native transitions, not 32 complete games.

| Variant | Passed pairs | Source selections | Donor151 selections | Donor150 selections |
| --- | ---: | ---: | ---: | ---: |
| five_hand | 16/16 | 12 | 4 | 0 |
| five_or_zero | 16/16 | 2 | 4 | 10 |

The eight classes were idle, reacting source32e, reacting original donor151,
reacting original donor150, reacting marketf6, and saved DECEM114267880,
Boey114266440 and Yaroslav114283577 tapes. Reacting and idle prefixes use
the Yaroslav initial fixture. This small engineering panel does not measure
general win rate or replace independent reacting qualification.

## Verified execution

- Every common turn0 and selected turn1 completed its required purchases,
  worker spawns, moves and pickups in both native seats.
- Every proposed branch passed the idle/mirror funding guard; there were
  zero donor refusals, common procurement failures, source guard failures
  or policy errors.
- Source restoration and donor150 matched their original branch's complete
  own physical/private state at end1. Donor151 matched at end8 after its
  explicit delayed fifth-worker bridge omitted the empty DROP.
- All 32 pairs matched complete own physical/private state at end23,
  after native first midnight. Donor150 comparison canonicalizes day0
  hands/inventories using its frozen 4,1,2,3,5 mapping.
- The preflight audit confirms transformed schedules feed raw donor
  actions, market/plant helpers and hire recovery before those helpers
  inspect positions. Original observed-shop selection at turn144 is
  preserved; archived shop labels are provenance only.
- All frozen pool bindings and both candidate hashes remained unchanged
  after the run. Root main remains 4eeac9c3.

## Cash differences at end23

Cash was excluded from the physical convergence gate and recorded separately.
Every five_hand prefix had zero own and rival cash difference from its
original branch control. For five_or_zero, source, donor151 and donor150
reacting classes also had zero differences. Its donor150 selections on the
following classes had these differences in each seat:

| Rival class | Delta own cash | Delta rival cash | Delta paired margin |
| --- | ---: | ---: | ---: |
| idle | +1 | 0 | +1 |
| marketf6 | -2 | +2 | -4 |
| DECEM tape | +1 | -1 | +2 |
| Yaroslav tape | +11 | -1 | +12 |

These are day0 transaction effects, not evidence of terminal improvement.
Physical convergence does not imply later shared-market or shop equivalence.

## Frozen artifacts and reproduction

Run from the workspace using `python -X utf8
diagnostics/adaptive_opening_bridge_20260928/prefix.py` in a clean copy of
the folder without result files. Existing evidence is immutable: the helper
refuses to overwrite its completed receipt and checks its bound inputs.

| Artifact | SHA-256 |
| --- | --- |
| candidate_five_hand.py | ceed697f9af3927fe4abc5b62e9e1e0ad7358361b3581a087da86558c8294d46 |
| candidate_five_or_zero.py | be5172f7db0df094a61c22279b0d9e944445d501e7ad63493c43157257e1e47a |
| prefix_results.json | befb989d8e8f5c393df3d9ad2a41eddff2e04a84001d36b66f60958a12d02e31 |
| pool.json | d119cdc9e78aaa245ab2a8d76f87d77e717207600dece0b80d840cca84fa86ce |
| PLAN.md | 91abe736c16b2ed732aa08cc43eb46660d232b0a4fd5487c70becd69bdd5abb4 |
| preflight.json | 6e07e4530cc102318ff6cf827dd9245fab791f1b5e146fdf0b184cf249051e65 |

Individual compressed traces are bound by SHA-256 in the receipt. Exact
fallback source is 32e299fe047a79290d5025b4e2be455ae13d948020beae2d77cb44a7c17dc31e.

Next research must freeze its complete-game panel and criteria before new
outcomes, preserve every source32e winning seat, retain at least 18/20 top
sweeps and improve public-loss wins. Resource coordination is required
before starting that screen. Root main, source, existing donor candidates,
their plans, and Kaggle remain untouched.
