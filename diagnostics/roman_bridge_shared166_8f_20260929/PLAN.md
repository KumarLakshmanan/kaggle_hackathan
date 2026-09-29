# Roman → shared166 adapter, 8f parent (static staging only)

## Status and scope

This is a separately named follow-up to `roman_bridge_shared166_20260929`; it
does not change or replace that historical 7b package. The parent for this
package is exact composed candidate **8f939ada**. Work here is static only:
no native transition, game, Kaggle call, or edit to `main.py`/`agent.md`.

The candidate **fails closed** at the opening until an adapter-specific
step-2 public snapshot is supplied. The snapshot is currently unavailable,
because the saved step-2 observations were produced with the original parent
step-1 market action, while this adapter would replace that action with a
single HIRE. The shared market and the rival's purchases can therefore differ.

## Frozen candidate lineage and available run evidence

| Artifact | SHA-256 | What it binds |
|---|---|---|
| 8f candidate | `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62` | Exact proposed parent for this adapter |
| 8f bundled parent | `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2` | Ghost + Kwa base under 8f |
| 7b `candidate_v4.py` | `7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2` | Independent byte-identical parent copy |
| 8f test panel | `ecf09fbde109bc13922f16851257939923ada9f158dc4e33c2e5e6b1a0f4b247` | Its four-fixture/eight-seat Pizza/Ice Cream test |
| 8f outcome receipt | `7d9e9ae29f420e361aec8c3d060089eb8dd969416bf2b65cb2fd23812fada14e` | Fixed-tape outcomes, not Roman |
| 8f parent receipts | `27ea7f63a0b922dee521d323536f75d4f3650bc9e48a89f0da57ab3e04ea211d` | Direct 7b comparisons |
| 8f static preflight | `d6940502e6c2c0c4e8892f76e47fac848ecf3dcaac30479969b7735408cfc9df` | 208-seat static source probe |
| 8f outcomes log | `459065b14277c58c08f8ab577cc15bf592e8cb26f11f88b5af07a46504ab5ea7` | Same fixed-tape eight-game run |

The 8f outcome bundle contains `live-114238112` and three public controls;
it has no `live-114270587` outcome or per-turn trace. Thus 8f's exact file and
its complete available test bundle are hash-bound, but there is **no exact 8f
Roman target trace**. The 208-row Roman opening census was recorded under
historical `a44c8c2c` (SHA-256
`a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`). The
preflight additionally hashes every available Roman target trace and action
tape listed in `preflight.json`, including both seats where present. It also
verifies the 8f source begins with the complete exact 7b source prefix
(2,014,660 bytes; 8f appends 3,054 bytes) and that the separate
`candidate_parent.py` copy is byte-identical to 7b. This binds source lineage;
it does not replace the missing exact 8f per-turn target observations.

## Adapter outline

`adapter_layer.py` is a separate closure factory. It binds to the 8f source
hash and takes an injected parent and raw donor schedule callback.

1. Step 0 delegates unchanged to exact 8f.
2. Step 1 selects only when the rival has exactly three hands at `[4, 3]` and
   our saved parent state matches four hands, farmer `[4, 4]`, four hires,
   $1,088, two COW, two SHEEP, and six WHEAT. It would issue farmer NORTH,
   PASS for the four existing hands, and one HIRE (static hire cost $5).
3. Step 2 requires both the exact predicted own state and a complete public
   snapshot: the entire rival farm plus the whole shared market. That snapshot
   must be tagged with the exact matched rival action-tape hash, action index
   1, action hash, and the exact adapter step-1 action hash. Before spending
   the fifth-hire cost, step 1 checks this provenance plus the complete
   six-field rival-farm schema and full market inventory/prices schema. Step 2
   compares every rival-farm and market value again. An absent or partial
   snapshot leaves the exact parent in control without hiring; a mismatch
   after activation latches an all-PASS diagnostic fallback and never applies
   donor commands. With the current `expected_step2_public=None`, the bridge
   does not activate or spend a hire.
4. After a verified merge only, raw shared166 schedule hands are remapped with
   donor slots `[1,2,3,4,5]` → actual slots `[4,1,2,3,5]`.

## Matched opponent evidence and why the current snapshot cannot be reused

The original target replay is hash-bound at
`3b93e403b761ebf6aac26884ec86fbb7abd151730a6c3201401f8c2ff5aa68e5`; its
saved raw-route tape is
`18ba3ec92eec0ec7bab95498119eebae88e7ce0ca4571eba42ffbaeb9ddda4b1`.
The tape's actions 0 and 1 exactly match the opponent's actions in raw replay
steps 1 and 2, respectively. In particular, the matched rival action for our
adapter's step 1 is tape action index 1, SHA-256
`48e7b680c2f75b6a1d838749d1289420710bd6fb05c27275c9f2c38ac26769ff`.

For both saved source seats, the historical step-1 rival farm and step-2
rival farm/market match the raw replay. Those step-2 values are retained as a
**historical parent control snapshot**, with their source trace hashes. The
parent's recorded own step-1 action has six market orders; the proposed
adapter step-1 action has only HIRE. That change alters the shared market and
can alter the rival's purchases, cash, and stock. Therefore the historical
step-2 snapshot is not valid as the adapter's expected state and is never
passed to the runtime guard. No static calculation here can establish the
adapter-specific rival farm/market result. Until a matched one-turn native
check supplies and freezes it, `expected_step2_public=None` keeps the branch
inactive.

The static preflight also binds the historical a44 traces for both seats, the
residual-execution traces and receipts for the earlier `8dde995d` candidate,
both shared166 donor traces, both shared151 donor traces, the raw replay, the
loss-class event trace, and the matched action tape. The 8f outcome rows are
only eight fixed-tape results on four fixtures; none is the Roman target.
Exact 8f step-0/1/2 state snapshots remain pending.

## Donor route scope

The shared166 donor's route0/route1 arrays are equal for action indices 0–165
and first diverge at 166. Its Roman step-144 shop pair is
`PET_CAFE|PET_CAFE`, unmapped by the donor and so defaults to route0. The
structurally eligible segment begins at action 2, after the adapter bridge;
this is not evidence that the custom merge state can safely execute it. The
donor's own full traces are hash-bound only as comparison artifacts.

## Pending checks

- Exact 8f Roman step-0/step-1/step-2 observations and action records are not
  present. The byte-prefix relationship to 7b is verified, but exact 8f
  per-turn state and output in this target seat remain pending.
- The public snapshot after our custom HIRE and the matched opponent tape
  action is unavailable. Step-2 donor activation is therefore disabled.
- Once the shared simulator is free, run a one-turn matched-action check in
  each seat; bind the resulting full rival-farm and market snapshots and
  verify private inventories, worker positions, cash, hires, and goods.
- Only after that, test both Roman seats plus paired controls and broader
  reactive behavior. Fixed tapes alone cannot qualify the change for
  promotion.

## Decision

**Stage only; do not promote.** The 8f parent lineage and available target
artifacts are hash-bound. The Luna Max concern is addressed with a complete
public farm/market and matched-action guard, checked before the hire and again
at step 2. Exact 8f Roman observations and the adapted step-2 public state
remain unverified, so the splice stays disabled.
