# Exact-prefix-compatible later-shop selector — 2026-09-26

The first-two-shop lookup was broadly strong on two fresh seed blocks but
failed its frozen tail-risk gate, with a large mismatch when the third
shop was YARN_STORE. The source route audit found 127/164 observed
three-shop sequences with an exact first-216-action-compatible alternative.

Freeze `../shunki_portfolio_20260927/later_shop_analysis.json` and its
203 verified source routes. Keep the same common first 72 actions and
first-shop/pair selections as the prior lookup. At each later shop reveal,
switch to the newest public route with the matching *observed* shop
prefix only when all actions before that turn are exactly identical to
the current route. Otherwise retain the current route. The mapping uses
no source result, seed, opponent identity, or future shop as input.
Package this in a separate single-file candidate and check Kaggle's
final callable plus both-seat file-loader parity.

The previously seen seed 2630130 may be replayed only as a mechanism
check, not independent validation. Then run new untouched native seeds
**2630200–2630215**, both seats and original shops, versus reacting
unchanged `main.py` with matched main-vs-main controls. A development
pass requires all 64 games DONE/DONE, at least 12/16 positive paired
seed margin changes, 24/32 positive seat margin changes, positive
aggregate own-cash change, worst paired margin change at least −10,000,
and first-two shops matching in at least 30/32 seat comparisons. Only a
pass warrants a separate untouched confirmation block and the fixed
top-100 diagnostic panel. No `main.py` promotion from development data
alone and no Kaggle upload without a fresh explicit user request.
