# Predeclared opening queue screen (not a policy promotion)

Date: 2026-09-25. Frozen `main.py` SHA-256:
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

Hypothesis: on the exact opening where the H6 wrapper replaces a 20-buy /
15-sell wheat roundtrip, buying the five retained wheat units directly may
avoid adverse simultaneous-price/interleaving effects without changing the
intended starting stock or later farm work. This is a *hypothesis*; the
roundtrip could instead improve paired margin or finance dependent orders.

Treatment: override only `_H6_OPENING_QUEUE_TO` with
`[["BUY_PRODUCT","WHEAT",5],["BUY_SEED","WHEAT",1]]`; otherwise run
unchanged `main.py`. The treatment is observation-legal and applies uniformly
at that opening, not by seed or opponent identity. Controls are the 24 newest
completed public episodes extracted before this treatment was chosen, both
seats, with baseline 13/24 route wins, 26/48 seat wins and all `DONE`.

Screen gate before any top-50 full panel: at least 15/24 route wins and 30/48
seat wins; no baseline winning route or seat reversed; no new `ERROR`/timeout;
and rescued losses must have positive **own** cash delta, not only a decline
in fixed-tape rival cash. Report every changed route and worst cash regression.
The 24 routes are development data once screened, not an independent holdout.
Passing this screen would permit a full top-50 fixed-action panel and a fresh
reactive check; it would not by itself justify editing or submitting `main.py`.

## Result — rejected

The 24-route, both-seat screen completed with all 48 games `DONE`. It retained
**13/24 route wins and 26/48 seat wins**, with no rescued loss, so it missed
the predeclared gate. Eighteen of 48 seat-games changed margin; mean own cash
changed **−2.67** coins per game, mean fixed-tape rival cash **−1.96**, and
mean paired margin **−0.71**. The largest absolute seat margin change was 65
coins. The complete result is `opening_net5_24routes_both_seats.json`.
The opening roundtrip is not the source of the observed 317–4,003-coin live
losses. Do not promote this override or tune it to individual opponents.
