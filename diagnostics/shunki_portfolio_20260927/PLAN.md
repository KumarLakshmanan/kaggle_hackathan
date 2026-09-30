# Public Shunki schedule portfolio feasibility — 2026-09-26

The recorded ShunkiKyoya double-Yarn route won all 16 fresh selected
seat-games against reacting current `main.py`, but failed badly on arbitrary
shops. Twelve newer public episodes from the **same submitted agent**
showed one exact first-72-turn prefix. Routes with the same first shop
shared the first 144 actions, and the two repeated shop pairs had identical
719-action histories. This suggests a physical-state-compatible portfolio
that branches when each public shop appears.

Freeze the 203 completed public episode IDs returned for Kaggle submission
56553856 in `../public_route_native_screen_20260927/shunki_episodes.json`.
Read every available replay and extract ShunkiKyoya's exact 719 actions,
source seed/seat, first two shops, action and replay hashes. Preserve a
compact compressed route artifact for each; new full replay downloads can
be discarded after verified extraction to limit disk use. Record exact
prefix uniformity at turns 72 and 144 and any same-shop-pair action
conflicts. Do not use episode outcome, opponent identity, seed, or future
shops as deployed policy inputs.

Only if all collected routes share the first 72 actions and all routes
with a given first shop share the first 144 may a prospective portfolio
branch at turns 72 and 144. Missing shop pairs and same-pair conflicts
must be handled explicitly before testing. A compiled single-file agent
would then need both-seat Kaggle loader checks, fresh native reactive
development and untouched confirmation blocks across all shops, and the
saved top-100 paired panel. The successful double-Yarn tape alone cannot
be promoted. No Kaggle upload without a fresh explicit user request.
