# Carried-wheat `PASS` feed candidate — 2026-09-26

The corrected same-tile idle audit of two top-100 losses found 50 (Boey) and
34 (mhw) distinct animal/day `PASS` opportunities with carried wheat and no
later successful same-day feed. All sampled animals had zero consecutive
unfed days; this rule is intended to earn fed-care production, not prevent
escape. Both examples are consumed development routes. Source:
`../top100_refresh_2026-09-26_0708/pass_opportunities_two_losses.json`.

Freeze current `main.py` SHA-256 `489fe8e4...`. Build a separate complete
candidate by appending one wrapper: on a parent `PASS`, day 12–28, standing
on an owned cow/sheep with `fed_today=False` and at least **two** wheat in
that worker's inventory, issue `FEED`. Do not move, buy feed, change other
worker commands, or change market orders. Count triggers. This is a deliberately
small action override; a fed animal can still fail to deliver more bank cash.

First smoke both original losses in both seats, native shops. Stop if games
fail, no triggers, or aggregate own cash fails to improve. If smoke passes,
run 34 lost top-100 routes plus ten deterministic winning controls in both
seats. Advance only with all games `DONE`, positive own-cash and paired-margin
sum across original seats, at least three loss rescues, and no control-win
reversal. Fixed tapes are development/regression only. Then run 16 fresh
native reactive seeds against unchanged `main.py` in both seats, followed by
at least one saved public reactive opponent before promotion. All new tests
keep original shop randomness. Preserve main/backup. No Kaggle upload without
a fresh explicit user request.
