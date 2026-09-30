# Farming methods and timing experiments — 2026-09-27

The user explicitly requested changes to farming methods, timing and logic.
Use land-retry source `5002b442...` as an unpromoted experimental control.
Keep the promoted-artifact candidate `3cc0f69f...` and current main intact.

Two separately frozen variants:

1. **Fertilize before watering:** when the current command is WATER and
   the next recorded command for that worker is FERTILIZE on the same day,
   fertilize now and water next turn. Require a visible one-off crop,
   carried fertilizer, not already watered, no active fertilizer, and a
   crop age in its yield-gaining watering window. Skip shop boundaries.
   Do not buy resources or alter movement. This can add a yield unit to
   the same crop before the existing harvest.
2. **Wheat crop substitution:** translate every CARROT planting, seed
   purchase, explicit transfer and sale to WHEAT. Both first mature in
   two days; wheat seed costs 10 versus carrot 20, while prices, later
   growth and market competition differ. This is a coherent crop-chain
   experiment with unchanged worker paths and calendar, not an assumed
   gain. Report failures or leftover crop effects rather than hiding them.

Development for each: all eight known losses, both seats, native shops.
Require DONE, zero wrapper exceptions, nonzero activation, and at least
one newly won two-seat matchup before testing the full 50. Full-panel gate:
more than 42 sweeps and at most one lost source sweep. Stop a failed arm.

If an arm passes, freeze its bytes and use untouched native seeds
2633800–2633815, both seats, source 3cc and candidate versus frozen main,
previous main, public C95; candidate also versus reacting source 3cc.
Require all DONE, aggregate external win points at least source's,
no rival worse by over two paired points, at least 10/16 paired points
against source, and at least four activated seed pairs. If activation is
too sparse, use a separately frozen conditional study. Compare the two
arms independently; do not combine unvalidated changes after seeing data.
Both-seat file loading and root backups precede any promotion.
