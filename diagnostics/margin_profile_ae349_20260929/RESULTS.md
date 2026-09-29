# Margin profile of ae349d83 — 2026-09-29

This is an offline analysis of completed artifacts, not a new game run. It
compares exact candidate `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`
with uploaded257 on the 102 saved rows and 24 matched native reactive
scenarios. Root `main.py` and Kaggle were not touched.

## Saved panel

- Archived losses: 54 wins / 0 draws / 6 losses across 60 seats; 27/30
  two-seat fixture sweeps (90%).
- Top 20: 38 wins / 0 draws / 2 losses across 40 seats; 19/20 two-seat
  sweeps (95%). DECEM remains the single top-20 fixture lost in both seats,
  at -9,085 margin per seat.
- The only nonzero paired margin change is `live-114218866` (Pensukesan),
  +45,291 per seat. The candidate keeps the loss but reduces its margin from
  -53,956 to -8,665. The other 98 goal-panel seats and both public-win
  controls have zero margin change.

Weakest current saved wins include `live-114267572` (+244 / +6,475 by seat),
`live-114223338` (+313 / +313), `live-114271958` (+670 / +670), and
`live-114283577` (+902 / +902). Top-20 narrow wins are Majkel1337 (+2,867),
Unknown Mother-Goose (+4,471), Fourth Quadrant (+4,844), and Kaggledew
(+4,877), with the same margin in both seats for each listed matchup.

## Reactive panel

There are 24 matched scenario rows (48 full games across the two arms), four
seeds and both seats against each of three policies. Candidate and uploaded257
are identical in every paired outcome and reward: **8W / 14D / 2L**, with
zero paired-margin delta. The ae349 Pizza melon fallback telemetry shows zero
activations in these 24 candidate scenarios.

## Decision

The saved-panel win targets are met, but ae349's sole saved margin gain is a
single loss getting smaller; there is no measured reactive margin gain. Do
not present the saved margin repair as live strength. Future work should
target the narrowest verified wins or a remaining loss with a paired own-minus-
rival cash objective, and require actual activation plus fresh reacting
validation before any promotion claim. The previously tested end-day melon
delivery route is not a broad margin improvement: it gained 1,637 margin per
seat on offhand but lost 565 per seat on Unknown Mother-Goose, so its frozen
gate failed.

## Bound inputs

- Candidate SHA-256: `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`
- Saved outcomes SHA-256: `ebe9c97327a0086766f67c88213e2fe086ebfa8f89d8ba84db8f5ba918091562`
- Saved receipt SHA-256: `218297125b45a782f903b2a7aaa178597b708a53f0ffac4f196b404f7b95ce2d`
- Reactive outcomes SHA-256: `db611d202ab6879666a60b49ce70cc2025b8dc380319f718ed05caba7e407be6`
- Reactive receipt SHA-256: `53e0968303b1e26c4ec6dfc0681edb2f939d156b9635c5a1aaca5fb99233479e`

Sources: `diagnostics/combined_agent_257f_20260929/saved_panel/` and
`diagnostics/combined_agent_257f_20260929/reactive/`.
