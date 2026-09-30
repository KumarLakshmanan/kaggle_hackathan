# Reacting Haide near-clone diagnostic — gate failed, 2026-09-26

The saved public Haide implementation (SHA-256 `4f3ca95d...`) was run as a
reacting opponent in the native engine on fresh seeds 2614350–2614357,
both seats. Current `main.py` and the exact half-base candidate each faced
Haide on the same seed/seat with independent endogenous shop draws. All 32
games ended `DONE`; treatment had zero reported errors and a 174 ms maximum
measured call.

The half-base rule triggered in **8/16** treatment games. Relative to the
matched current-agent control, two paired seeds improved, two worsened, and
four tied. Across all 16 matched seat comparisons, own cash changed **−44**,
Haide cash changed **−2,416**, and paired margin changed **+2,372**. Current
agent won 14/16 seat games; treatment won 16/16, with no win reversal.

The predeclared diagnostic gate required at least five improving paired
seeds and positive own-cash change. **It failed both.** This one-opponent
result does not repair the earlier reactive self-play gate failure or show
general leaderboard strength. Retain `main.py`; no Kaggle upload. Raw
matched results and hashes: `reactive_haide_halfbase.json`.

Reproduce: `python -B -X utf8
diagnostics/mirror_stock_frontload_20260927/reactive_haide_halfbase.py`.
