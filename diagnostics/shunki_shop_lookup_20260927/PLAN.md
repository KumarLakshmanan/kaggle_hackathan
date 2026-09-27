# Coarse public-route shop lookup probe — 2026-09-26

The exact 203-route portfolio feasibility gate failed because one source
policy reacts to visible weeds, money, and market quotes even within an
identical first-two-shop pair. Test a deliberately coarse lookup to quantify
whether its shared opening and shop-specific schedules transfer at all.
This is a new experiment, not a relaxation of the failed exact-action gate.

Freeze the source manifest from
`../shunki_portfolio_20260927/route_manifest.json`. Choose the first listed
(newest) public episode per first shop and per first-two-shop pair, without
using episode outcome, seed, opponent identity, or later shops. All 203
sources have an identical first 72 actions. Use that common opening through
turn 71, select the first-shop route from turn 72, and select the pair route
from turn 144. For one of the three missing pairs, retain the first-shop
route. Do not adjust actions for weeds, money, prices, or later shops in
this probe. Only already observed shops may be used for routing.

Package the lookup in a separate, single-file Kaggle candidate. Check the
final callable and both-seat file-loader parity. Then use untouched native
seeds **2630000–2630015**, both seats and original shops, against reacting
unchanged `main.py` with main-vs-main matched controls. Require all 64
games DONE/DONE, same first-two shops within each seat comparison, at
least 12/16 positive paired-seed margin changes, 24/32 positive seat
margin changes, positive aggregate own-cash change, and no paired-seed
margin regression below −10,000 before escalating to the fixed top-100
diagnostic panel and a separate untouched confirmation block. Failure
rejects this coarse lookup. No `main.py` edit based on the development
block alone and no Kaggle upload without a fresh explicit user request.
