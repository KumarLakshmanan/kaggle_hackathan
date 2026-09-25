# Predeclared executable-stock H6 ranking screen

Date: 2026-09-25. Frozen submitted agent SHA-256:
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

Hypothesis: the final H6 SELL-slot ranking uses requested rather than
executable stock quantity. Its score may overrate large but partially empty
sale orders, so sorting only the existing SELL slots by the price-impact score
computed with currently projected post-unit stock could improve own receipts.
The policy may also harm price timing or lose sale-credit funding; no gain is
assumed. Do not alter unit actions, order contents, quantities, number of
orders, or the positions of non-SELL orders.

`h6_executable_rank_exposure.py` found 25 queue-changing turns across the 24
actual public replays. This is a development exposure test, not a policy
validation. The standalone candidate will skip any queue containing a
duplicate SELL of the same product or a BUY_PRODUCT of a product it also
sells, to avoid hidden dependencies. It then re-sorts the existing SELL
slots by the existing H6 demand/price-impact function after replacing each
requested quantity *for scoring only* with `min(requested, projected stock)`.
No opponent current action, replay ID, seed or future shop is read.

Screen: all 24 recent live opponent tapes on their original seeds, both seats,
against the identical frozen baseline (13/24 route-pair wins, 26/48 seat wins,
all `DONE`). Report every route/seat outcome and own/rival cash changes.
Proceed to the historical 100-route panel only if the candidate reaches at
least 15/24 routes and 30/48 seats, reverses no baseline win, has no new
error or timeout, and each rescued loss increases own terminal cash. Passing
would still require independent reactive games. A Kaggle upload is not
authorized by this screen.

## Result — rejected

The standalone candidate completed all 48 original-seed/both-seat frozen
games, all `DONE`; maximum measured call was 691 ms. It won **13/24 route
pairs and 26/48 seats**, exactly the baseline, with no loss rescued. Fourteen
route margins changed, ten downward and four upward. The largest paired
regression was 32 coins and the largest improvement was 20; a 360-coin loss
improved by only eight per seat, while several close losses worsened.
The predeclared 15/24 and 30/48 gate failed. Full results:
`h6_stock_rank_24routes_both_seats.json`, compared with the existing
`baseline_24routes_both_seats.json` by `compare_route_panel_outcomes.py`.
Do not promote this to `main.py`; the many overrequested sale quantities do
not translate into a meaningful ranking gain on these replays. No Kaggle
upload was made.
