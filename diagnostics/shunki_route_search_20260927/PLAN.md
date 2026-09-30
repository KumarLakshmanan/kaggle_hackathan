# Complete schedule search after the first two observed shops

Current submitted main wins 42/50 fresh saved matchups in both seats. The
eight losses occupy six distinct first-two-shop histories. Three of 64
possible two-shop keys are absent from the 61-key source catalogue; the
PIZZA_SHOP/ICE_CREAM_SHOP fallback is used in two losses. Tiny physical and
sale changes have not closed the gaps. Test complete schedule alternatives
that preserve the executable opening, rather than isolated action edits.

Immutable baseline: uploaded `3cc0f69f...`. Sources: the existing 203 public
Shunki episodes, with provenance in their manifest. An alternative must
match every opening worker command and market order through turn 143,
after removing only adjacent equal-quantity BUY_PRODUCT/SELL round trips.
This removes financially variable but inventory-neutral wash trades; it
does not prove cash equivalence. Never ignore seed, animal, hiring, land,
ordinary sales or supply differences. Exclude known incomplete 113445495.

Development search: for each first-two-shop history containing a current
loss, evaluate every eligible complete source schedule from turn 144 on
all fresh top-50 replay cases with that same history, initially in seat 0.
Actions before turn 144 remain byte-identical to submitted main. A chosen
source then runs coherently to the end; no later incompatible switch.
Include the existing policy as an option using its saved baseline results.
Choose by group win count first, then worst margin, then total margin. Keep
the existing policy unless win count strictly increases. No seed, opponent
identity or future shop is an input to the resulting selector.

Freeze the selected shop-to-schedule table, then run all 50 saved routes
in BOTH seats. Require all DONE, strictly more than 42 two-seat sweeps,
and no more than one existing sweep lost. All these replays are training
and regression data, never independent validation.

Before any confirmation scan or outcome, the native selection protocol was
clarified on 2026-09-27 00:23 UTC: shop RNG depends on BOTH agents, so a
seed selected against one rival does not ensure exposure against another.
Use a separate outcome-blind selection for each reacting rival. Select the
first eight seeds per changed branch (four branches, 32 seeds per rival),
inspecting only the first 144 turns and shop labels. Scan up to 2,048 seeds
per rival, starting at 2634800 for frozen 489 main, 2637000 for previous
08aa main, 2639200 for public C95, and 2641400 for reacting submitted 3cc.
Keep every earlier scan record, including nonqualifying seeds. No terminal
reward is generated during selection. Candidate bytes and replay training
choices remain unchanged by this clarification.

Play old and new in both seats on each external rival's selected panel;
play new against 3cc in both seats on its separately selected panel. This
is 448 complete native games. Require all DONE, no lower pooled external
win points, no external rival worse by more than two paired points, and
at least 20/32 paired points against 3cc. Report each branch and each
opponent separately, plus seat-specific activation. Incomplete coverage
within the frozen scan limit is not a pass. Both seats of a seed stay
together for all summaries.

Both-seat file-loader parity and root backups precede any promotion.
Main remains the validated submission during this search. No new upload
authorization is available. Ranking and 50/50 remain unproved.
