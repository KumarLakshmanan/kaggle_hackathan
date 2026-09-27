# Double-Yarn, high-sheep complete-route pilot — 2026-09-26

The fresh top-100 panel has three large losses on two observed Yarn Stores
where the rival already had at least three sheep on day six: mhw,
ShunkiKyoya and AI是我的豆包. In mhw's exact native trace, the rival earned
about 60,400 more wool cash and held 36 sheep versus our 17 at day 18.
The prior broad route-12 switch improved some saved routes but lost every
fresh reactive self-play game. This pilot asks a narrower, new question:
does a *visible rival sheep lead*, together with two Yarn Stores, identify
cases where the existing complete sheep route 12 helps?

The isolated candidate wraps the current `main.py` chassis router at the
day-six route choice. It selects route 12 only if the first two publicly
visible shops are both `YARN_STORE`, the incumbent selected route 9, and the
rival has at least three visible sheep pastures. It then holds route 12
through turn 647; the existing day-27 route-2 ending remains. The gate uses
no opponent identity, seed, replay, private inventory or future shop.

Development screen: all four double-Yarn routes in the new panel (three
target losses and one two-sheep negative control), both seats and original
shops. Require at least one target rescue, higher own terminal cash on the
rescued route, no control reversal, all agents `DONE` and no gate errors
before testing older panel controls. If that passes, run all gate-eligible
routes in the older panels and fresh reactive games against a high-sheep
reacting agent on independent shop-matched seeds, with baseline controls.
Only a broad positive result could justify local promotion; a new Kaggle
upload would require a separate explicit user request.
