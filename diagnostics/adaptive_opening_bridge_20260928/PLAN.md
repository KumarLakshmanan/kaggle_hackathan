# Adaptive common opening bridge — bounded feasibility, 28 September 2026

Exact fallback source is animal-liquidity32e299fe; root main, source,
existing donor candidates and their frozen plans remain unchanged.
This plan is frozen before new prefix outcomes. It creates exactly two
variants and no full-game strength screen at this stage.

## Two fixed variants

Both use source's raw turn0 action, retaining the original ten market
positions and net six wheat, two cows and four hires. Reduce the sheep
order from three to two and replace the strawberry seed order in place
with a zero-quantity SELL STRAWBERRY order. Native parsing treats that
nonpositive order as a no-op; the action schema is an unrestricted object.
Unit commands remain source's PASS commands. No source queue optimizer may
rearrange this explicit common turn0 action.

At observation1, variant **five_hand** requests shared151 if the public
rival has at least five hands; otherwise it requests source. Variant
**five_or_zero** makes the same decision and additionally requests
shared150 if the rival has zero hands. No identity, seed, episode, fine
cash fingerprint or future shop may influence this choice. The native
funding guard described below may refuse a requested donor and use source.
Each admitted branch remains its entire source/donor policy thereafter.

Source branch raw market1 is its original four-order queue, followed by
BUY_ANIMAL SHEEP1 and BUY_SEED STRAWBERRY1. This restores the deferred
obligations before the first sheep pickup/seed use. Its existing helper
stack sees this changed executable opening from the start; helpers may
then optimize turn1 and later actions normally.

Shared151 branch retains the raw first four hand commands at1, with the
missing fifth hand's command set to PASS. Market1 is SELL WHEAT1, HIRE,
BUY_ANIMAL SHEEP1, BUY_SEED MELON6, BUY_SEED WHEAT2, in that order. The sale
is permitted only when current total wheat is exactly six and the donor's
original commitment is five. Fifth-hand commands at2..8 are original
commands1..7; omit its original empty DROP8 and resume original WEST9.

Shared150 branch moves the farmer NORTH at1 and gives the existing hands
PASS. Preserve original market1 positions: replace the first four HIREs
and already-paid COW/SHEEP orders with zero-quantity SELL STRAWBERRY
placeholders, retain the fifth HIRE, then append BUY_SEED WHEAT1 and SELL
WHEAT1. This sale has the same six-versus-five commitment guard. Apply the
audited donor-to-actual hand permutation4,1,2,3,5 to all day0 hand commands
before every helper call. Future days use original indexing after native
midnight clears the hands.

## Executable schedule and transition guards

Each donor runs in an isolated namespace containing its unchanged donor
helper stack. Modify its in-memory raw routes at0/1 and its day0 delayed
or permuted hand commands before helpers run. Its `_donor_action`, raw
queue reference and hire-recovery schedule all read that same executable
route. Source's in-memory opening has common0/source-restoration1 before
source helpers run. Original disk artifacts remain byte-identical.

At0 initialize source and both donor modules with that executable common
schedule, then emit the exact common raw action. At1 compute the requested
branch's helper-transformed action, then apply the embedded native unit,
atomic planting and market transitions under idle and complete-action
mirror forecasts. The mirror duplicates our current farm/private and uses
public rival money; it is hypothetical, never rival-private information.

Both forecasts must end with exact required inventory/seeds, original land
and empty farm tiles, correct worker positions and four/five paid hires,
and nonnegative cash. Source requires two owned cows, three sheep, four
total wheat, one wheat seed and one strawberry seed. Shared151 requires
two cows, three sheep, five wheat, six melon seeds and two wheat seeds;
its fifth hand is correctly spawned but holds nothing until2. Shared150
requires two cows, two sheep, five wheat and one wheat seed, plus the
verified permuted spawn positions. Exact inventories after prescribed
pickups are checked too. Failed donor guards restore source action1;
failed source guards are recorded as feasibility failures, not hidden.

## Fixed engineering panel and gate

Use both seats, both variants, and exactly eight opening classes: idle,
reacting source32e, reacting original donor151, reacting original donor150,
reacting public_market_smart_f6a756cf, plus the frozen raw DECEM114267880,
Boey114266440 and Yaroslav114283577 tapes. All begin from the verified
compact source fixture initial state for their own saved fixture where
applicable; reacting classes use the saved Yaroslav fixture seed/config.
Only24 turns per prefix. No terminal win/loss result is evaluated.

For each of32 variant/class/seat prefixes, also run one24-turn control
with the originally requested complete source/donor opening against the
same rival class. Guard refusal is reported and fails that requested
branch's feasibility gate; it is not counted as a donor success. Require
all initial common procurement and turn1 guard/actual procurement checks
to pass, no policy errors, both selection branches activated on their
intended classes, and exact own physical state/inventory at the end of1
for source/shared150 or8 for shared151 relative to the original branch.
Canonicalize donor150 hand and inventory order with4,1,2,3,5. Also require
exact own physical state/private at the end of23, excluding cash and the
shared market/opponent state. Report cash and rival changes separately.

Native transition checks use the exact already validated native core.
Bind `stream_replay_io_20260928/cached_input.py`, `initial_states.json`,
`fast_game_cached.py` and its complete parity receipt in the new pool;
the prefix helper uses the verified compact initial-state reader. Bind
the donor pool, obligation audit, candidates, all tapes, source bytes,
this plan and new helper bytes before any prefix outcomes. Work serially,
one short prefix at a time, with fresh modules and explicit cleanup.

If either architecture is infeasible under these fixed checks, preserve
the failure and reject that variant without changing quantities, selector,
delay, permutation, guard or panel. Engineering corrections discovered
before outcomes must be documented before execution. A pass only justifies
a separately frozen full-strength development screen once memory headroom
is available. Such a later screen must preserve every source32e winning
seat, retain at least18/20 top-team sweeps, and increase public-loss wins.
Original-native full games, separate reacting qualification, all54 public
wins and actual file-loader checks remain required before promotion.
No Kaggle access, uploads or source/root-main edits.
