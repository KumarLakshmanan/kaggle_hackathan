# Strawberry mirror quote guard — rejected, 2026-09-26

The isolated candidate `exp_mirror_straw_quote60_20260926.py` (SHA-256
`6c1d950191cc876755163c8df2de23d8e146a14a3ee34ab33e70098ee203c808`)
was built from current submitted `main.py` SHA-256 `489fe8e4...` under the
frozen [plan](PLAN.md). On a visible physical mirror it skipped only extra
24-turn strawberry sale advances when the current quote was below 60, half
the configured base price. Scheduled sales, other products, production and
non-mirror behavior were unchanged.

The baseline was the existing exact current-source screen on the same 29
public losses and ten closest wins, all original seeds and both seats. It had
reproduced all 39 original-seat Kaggle cash pairs. The candidate completed
all 78 games `DONE`/`DONE`, with zero reported errors and maximum measured
call of 183 ms. Across the **39 original seats**, it rescued **zero of 29**
losses, reversed the +163 FinalSunFlower control win to −190, reduced own cash
405, increased fixed-rival cash 2,000, and reduced paired margin 2,405.
Sixteen original-seat margins changed. Full both-seat panel wins fell from
22/78 to 20/78; paired route wins fell from 12/39 to 11/39.

**Decision: reject at the predeclared development gate.** The five-rescue,
positive own-cash and positive paired-margin requirements all failed. No
fresh reactive or top-100 promotion screen was exposed to this weak candidate;
`main.py` and Kaggle submission remain unchanged. Fixed rival action tapes
are diagnostics only. See `quote60_dev_candidate39.json` and
`quote60_dev_comparison.json` for every matchup.
