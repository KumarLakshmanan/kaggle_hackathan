# Exact ae349 DECEM terminal-market audit

## Decision

Reject a terminal-market-only change as a DECEM rescue. The exact ae349 policy
already converts the carried worker inventory to shed stock and sells every
requested unit at its final scored transition. Only two fertilizer units remain
in the shed. Selling them after the existing queue would add 44 coins from the
bound market curve, leaving the fixed-tape margin at about **-9,041**. Keep the
candidate unchanged; a 44-coin cleanup is not a rescue or promotion signal.

## Reproduction and measured transition

- Candidate `main_candidate_improved_20260929.py`, SHA-256
  `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`.
- Both exact saved DECEM seat traces were replayed against their original
  action tapes. The analyzer regenerated every candidate action exactly and
  matched the hash-bound rewards and result rows: `DONE/DONE`, 720 frames,
  own reward 86,464, rival reward 95,549, margin **-9,085** in both seats.
- At terminal transition 718, pre-market cash margin is **-16,386**. The
  opponent has no market orders. Ae349 drops carried stock, then sells 7
  carrots, 6 eggs, 2 fertilizer, 30 melons, 28 tomatoes, and 15 wheat. All
  requested units fill; the market transition adds **7,301** own cash and
  improves the paired margin by the same 7,301.
- All carried inventories are emptied. The only remaining shed stock is 2
  fertilizer. The exact market curve quotes those next two units at 22 each;
  adding them to the queue would recover 44 coins, not the 9,085 needed to win.
  This is a price calculation from the exact state, not a simulated policy
  change.

Luna Max market-feasibility and panel-design reviews independently recommended
stopping the terminal-sale rescue lane. This agrees with the earlier separate
terminal-sale timing fixture, where an 18-turn liquidation moved paired margin
by only 59 coins and shorter horizons lost; see
`diagnostics/terminal_sale_timing_20260928/RESULTS.md`.

## Scope and decision boundary

This is a fixed-tape diagnostic of the exact saved DECEM fixture. It does not
establish performance against reacting opponents. No strategy file changed,
no counterfactual policy game was run, and Kaggle was not checked or contacted. Any
further DECEM rescue work needs an earlier production or investment mechanism
large enough to address a 9,085-coin deficit; the final sale queue is closed.

## Evidence

- Trace plan SHA-256:
  `a1366dc9664065802a4c0c05a8927f7c513327e89bca11c8a92c2304e6bd6607`.
- Saved panel result rows SHA-256:
  `ebe9c97327a0086766f67c88213e2fe086ebfa8f89d8ba84db8f5ba918091562`.
- Exact analysis SHA-256:
  `e9e7d6c598656d1558463268740f27f1e7f2a3c2d15c2a8594cbd85062263ff3`.
- Trace runner receipt binds both seats to the exact candidate and native
  helpers. Per-seat trace hashes are recorded in `trace_receipt.json`.
