# Fund the complete state-matched opening — 27 September 2026

The exact-state bank d634bed3 is rejected under its original gates. An
already-used-seed diagnostic isolates its missed compatibility: against c68,
the first market queue spends 13 more coins than its source, a wheat seed
purchase fails at step 13, a planned plant at step 21 no-ops, and the day-3
harvest yields two fewer wheat. At step 72 the farm matches exactly except
cash, but shed wheat is 5 rather than 7; at step 73 all private supplies
match again after the sale, with 51 fewer coins. Keep this causal diagnosis
separate from independent validation.

Create a separate candidate from exact d634bed3 bytes. Move its existing
BUY_PRODUCT WHEAT order to position zero only on step zero. Do not change
quantities, farming actions, state matching, source selection, or later
orders. This is a funding-order intervention for the complete opening, not
an extra expansion. Save an exact root-folder backup and freeze the hash.

Use untouched seeds 2693100–2693107 against exact reacting c68, both seats,
720 turns, original native shops. Run all 16 games. Original pilot criteria
apply independently: at least 12/16 win points, exact turn-72 compatibility
in both seats on at least six seed pairs, actual schedule switches in both
seats on at least six pairs, all DONE/DONE, zero errors. Report margins as
diagnostics, not an additional rejection gate. Do not reuse d634's games.

If this passes, follow the unchanged conditional replay and fresh native
qualification requirements from the d634 PLAN.md. Preserve main.py. A later
upload would need new explicit user approval; none is pending or requested.
