# Roman → shared166 adapter — static staging only (2026-09-29)

## Status

This directory stages an isolated adapter for offline review. It does not
modify `main.py`, `agent.md`, either frozen source, or Kaggle. No simulator
transition, game, replay, or policy call has been run for this package. The
predicted step-2 merge-state check is **pending** because the shared simulator
is occupied.

## Frozen inputs

| Role | File | SHA-256 |
|---|---|---|
| Exact 7b Ghost + Kwa parent | `diagnostics/a44_ghost_kwa_combo_20260929/candidate_v4.py` | `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2` |
| Shared166 donor | `diagnostics/donor_opening_agents_20260928/candidate_shared166.py` | `fc403d05e29b1b317985f7ec77d1a3fa490c0264af8d639c3bfea899fcf1a849` |
| 208-row static feature panel | `diagnostics/a44_source_bridge_goose_4leaf_20260929/feature_rows.json` | `bfd178472afd40c6b457e794dbde6d5d045440fd3b2c6cb40e658c9f7a26d795` |
| Shared166 opening obligation audit | `diagnostics/donor_opening_agents_20260928/INITIAL_OBLIGATIONS.md` | `e8a30db9e26e77a81ac01720cb23eca58d234a9229a08aca23b62ea4ec0717f5` |

`preflight.py` recomputes these hashes, checks all 208 trace hashes, statically
decodes the donor's two route arrays without importing or calling its agent,
and writes `preflight.json` with the exact trigger and near-miss census.

## Proposed adapter

`adapter_layer.py` is a separate closure factory. Its caller must inject the
exact 7b parent and a **raw schedule action** callback. Do not inject the full
transformed shared166 `agent`: the donor's queue and hire-recovery transforms
keep donor worker indices internally, so post-hoc hand remapping would leave
those internal queues wrong.

1. **Step 0: preserve the parent.** Delegate the whole action unchanged to
   exact 7b. The saved target prefix shows the parent opening has already
   hired four hands and purchased two COW, two SHEEP, and six WHEAT by the
   observation at step 1.
2. **Step 1: select from public rival state, then hire one hand.** Activate
   only when the rival has exactly three hands and its farmer is at `[4, 3]`.
   Also require the expected own parent state (four hands, farmer `[4, 4]`,
   `hires_today == 4`, at least $5, and the saved COW/SHEEP/WHEAT quantities).
   Return farmer `NORTH`, PASS for each existing hand, and one `HIRE`. The
   static cost rule gives the fifth hire a $5 cost; from the saved $1,088
   balance the arithmetic predicts $1,083 after hiring.
3. **Step 2 onward: consume donor schedule commands with a hand permutation.**
   The spawn-order audit gives donor-hand slots 1–5 → actual slots
   `[4, 1, 2, 3, 5]`. Thus, to construct actual-order commands, emit donor
   commands `[2, 3, 4, 1, 5]`; subsequent hires append in matching order.
   The donor's raw action at index 2 is farmer `SOUTH`, with donor hand orders
   `PICKUP COW`, `PASS`, `NORTH`, `NORTH`, `PICKUP COW`; after mapping those
   become actual hands `PASS`, `NORTH`, `NORTH`, `PICKUP COW`, `PICKUP COW`.
   Before the first donor command, the staged layer requires the full static
   predicted state (including exact cash, hires count, worker positions and
   private inventory length). A mismatch latches a legal all-PASS fallback
   rather than issuing donor commands against unknown workers.

The saved source step-1 state predicts that moving the farmer north leaves all
four old hands on one shed-access cell each; the fifth hire then ties at
`[4, 4]`. This is a static spawn-order calculation, not a verified transition.
The expected step-2 state (farmer `[4, 3]`, five hands in the permuted order,
cash $1,083, two COW, two SHEEP, six WHEAT) must be checked in the simulator
before this adapter is frozen.

## Donor segment and compatibility boundary

The two shared166 route tables are byte-for-byte action-equal through indices
0–165; their first raw-action divergence is index 166. Indices 0–1 are not
reusable: the donor buys five WHEAT at 0 and performs five hires plus animal
buys at 1, while this adapter intentionally preserves the parent's earlier
four hires and purchases, then adds only the fifth hire at 1. The first
**structurally eligible** splice is donor action index 2 through 165, but it
is not yet established as state-compatible or competitively safe.

At donor selection time 144 the saved Roman replay shows
`PET_CAFE|PET_CAFE`, which is absent from the donor's explicit map and
therefore selects its `route0` default. Route0 alone is the relevant static
suffix after index 165. Neither this route selection nor its later outcomes
proves that the merged source state can fund/execute the schedule.

The old donor target trace at step 2 records $1,052, five hands in donor
order, and 5 WHEAT; the proposed bridge statically predicts $1,083, five
hands in actual order, and 6 WHEAT. The $31 and one-WHEAT differences, plus
the shared-market inventory difference, are real state mismatches. Existing
source inventory covers the donor's first two COW pickups, but later action
feasibility and market response remain unproven. No claim is made that the
donor segment can safely be reused until the exact post-step-2 state check and
then native reactive qualification pass.

## Frozen trigger / near-miss census

The preflight scans the step-1 observation from every hash-bound trace in the
208-row corpus. The exact trigger appears only twice: the two seats of
`live-114270587` (the target loss). Nearby observations are deliberately
excluded:

- Three rival hands, farmer unmoved at `[4, 4]`: 6 seats across
  `public-win-114188105`, `public-win-114251368`, and
  `top20-18-Kaggledew Valley 🏆-114273541`.
- Four rival hands, farmer at `[3, 4]`: 4 seats across `live-114282277` and
  `top20-07-Fourth Quadrant-114267646`.

The full rival `(hand_count, farmer_position)` histogram and row-level census
are frozen in `preflight.json`. This is a saved-panel trigger screen; the
panel traces are bound to historical `a44c8c2c` (SHA-256
`a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`), not
the exact 7b candidate. It is not independent policy validation or proof of
exact 7b step-0/step-1 parity.

## Static prerequisites before any candidate can be frozen

- Exact source, donor, panel, and target-trace hashes still match.
- Exact 7b target prefix produces the guarded step-1 own state above.
- Step-1 HIRE is legal, costs $5, appends the expected hand, and leaves
  existing animals and stock unchanged.
- The observation at step 2 matches the full predicted state, including
  worker ordering, per-worker inventories, animals, seeds, shed contents,
  hires count and cash. Market stock must also be recorded under the matched
  opponent; it is shared and can change with the opponent's concurrent orders.
- Donor raw action shapes and hire counts stay aligned with actual hand count;
  any mismatch must stop the splice instead of silently addressing the wrong
  worker.
- Only after that static/native state gate: run the target in both seats and
  paired controls against the exact parent, with reactive behavior. Fixed
  saved tapes alone cannot qualify promotion.

## Decision

**Stage for review; do not promote.** The public trigger is sparse and
uniquely identifies the saved Roman loss, and worker remapping is concrete.
The route bridge has not been tested from the exact 7b state. The saved donor
loss rescue is not evidence for this different opening. Keep the step-2 state
check pending until the shared simulator is available.
