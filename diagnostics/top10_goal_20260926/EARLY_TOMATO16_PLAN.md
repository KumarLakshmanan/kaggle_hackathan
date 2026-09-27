# Earlier complete tomato cohort pilot — frozen 2026-09-26 17:46 UTC

The current V219 branch can buy south-east land, plant ten tomatoes, hire a
dedicated crew, water, harvest, deliver, and sell, but only starts on day 18
after three observed Pizza Shop/Farmers Market instances. Tomatoes first
yield eight days after planting, leaving at most four producing days for that
cohort. The new loss ledger shows a large tomato cash gap on many fresh saved
routes. This pilot asks whether starting the *same complete bundle* on day 16
when at least two tomato-consuming shops and a price of at least 70 are
already visible can recover more of that gap. The established funds, land,
worker and quote checks stay in place. No opponent identity, seed, episode,
future shop or private rival inventory is a policy input.

Development panel: the 12 largest net-tomato-deficit routes among the 34
fresh paired-route losses, plus the eight current wins at snapshot ranks 2–9.
`build_early_tomato16_panel.py` freezes the exact routes and hashes. First
replay incumbent `main.py` with a day-16 observation capture in both seats
to count exposure. If fewer than three target routes have the visible shop,
quote, cash and land prerequisites, reject without implementing treatment.
Otherwise build an isolated source that changes V219's start from day 18 to
day 16 and its tomato-shop count from three to two; keep its complete work,
budget and sale path. Test the 20 routes in both seats on original seeds and
shops. Require all games `DONE`, at least two paired target-loss rescues,
zero winning-control reversal, positive aggregate own cash and paired margin
across activated routes, no V219 errors, and confirmed tomato plants/sales.
Saved actions are development data only.

Only if the development gate passes, run a fresh native 24-seed block against
reacting current `main.py`, both seats, and require positive paired majority,
positive aggregate margin, no material winning-control regression on the
remaining fresh top-100 routes, and Kaggle file-path parity before promoting
locally. Back up exact current `main.py` bytes before promotion. No Kaggle
upload is authorized.
