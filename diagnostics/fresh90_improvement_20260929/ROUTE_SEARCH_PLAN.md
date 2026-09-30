# Current-loss complete-schedule search — development only

The new top20 baseline has four losing teams, ranks8/9/10/19, under three
observed two-shop pairs: ICE_CREAM_SHOP|SMOOTHIE_SHOP, YARN_STORE|BAKERY,
YARN_STORE|PET_CAFE. The rollout chooser activated but rescued none. This
experiment tests physical complete alternatives directly to identify which
commitments can rescue these losses; it makes no forecast or online claim.

For each pair, enumerate all145 existing library schedules whose full raw
first144 actions equal the actual common opening and first-shop prefix.
Deduplicate identical tails. Each separate candidate changes only that pair
and descendants to one complete schedule; all earlier actions and cb76
repairs stay intact. No new opponent-state fingerprint or identity gate.

Stage1: every compatible alternative against every affected losing top20
fixture in seat0. This is an explicitly one-seat development screen, not a
both-seat result. Select up to3 alternatives per pair by number of target
wins, then sum of target margins, then route ID (ascending). Only routes
with at least one target win advance.

Stage2: test each selected alternative on ALL current top100 fixtures sharing
that pair, in BOTH seats, including baseline winners. Require clean games,
no lost baseline winning seat, and a positive win-point gain across the
affected set. Select the passing route with most wins, then greatest minimum
target margin, then summed margin, with route ID breaking ties.

Combine passing pair rules only; pairs are disjoint in observed-shop space.
Verify full newest top100 and top20 in both seats, preserving every baseline
win. A >90% saved result would remain training evidence. Test the same exact
candidate on reserved second/third latest episodes, then PLAN.md's four-policy
reacting block. Original native/loader checks and untouched32seed confirmation
are required for promotion. Do not train on reserved outcomes and still call
them independent.

Keep unsuccessful source files and all per-case results. If no route passes,
record rejection and retain cb76. This request does not authorize upload.
