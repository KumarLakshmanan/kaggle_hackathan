# Kaggriculture live code-example static comparison

This report is static: it reads downloaded notebook sources and decoded literal agent payloads. It never executes notebook cells or submits to Kaggle.

- Extracted payloads: **15**
- Unique source hashes: **13**
- Duplicate rank groups: **[5, 24], [8, 41]**
- Production file: `H:\hackathan\main.py` (2,892,150 bytes; 31,975 lines)

## Extracted sources

| Rank | Title | Bytes | Lines | Agent defs | Main markers | Hash |
|---:|---|---:|---:|---:|---|---|
| 5 | 🌾 (Rank Top10)Read the Market, Choose the Farm 📈 | 61,980 | 1,004 | 2 | market=80, sell=43, milk=10, weed=9, fertilizer=8, wool=8 | `d39dba50793d` |
| 7 | Kaggriculture - Strongest Farmer of Today? | 229,540 | 3,127 | 1 | market=205, sell=80, route=74, buy=47, seed=43, fertilizer=37 | `faaa594aa855` |
| 8 | Kaggriculture / Hamburger 🍔 | 150,378 | 333 | 1 | market=729, fertilizer=431, sell=401, buy=356, pickup=339, harvest=338 | `00e8ab594a39` |
| 10 | Kaggriculture 2026 V1 | 325,681 | 3,497 | 29 | market=313, route=174, sell=155, fertilizer=131, buy=110, seed=74 | `2b39ca79aa80` |
| 12 | Kaggriculture Frontier Lab / High-Score + Visuals | 131,794 | 10 | 1 | market=720, buy=493, sell=384, fertilizer=375, harvest=271, pickup=216 | `31b7c0f72dc7` |
| 14 | Wide-Sigma CMA Tuned Scenario-Aware (submitted) | 58,753 | 1,812 | 1 | market=60, fertilizer=41, seed=24, pickup=13, harvest=10, milk=8 | `aae73ff7f010` |
| 15 | V20-Adaptive-R1 / Multi-Route Agent | 148,200 | 1,013 | 1 | market=80, sell=43, milk=12, weed=9, fertilizer=8, pasture=8 | `8ac34abce129` |
| 22 | Kaggriculture: Breaking the Tie  | 158,309 | 239 | 1 | route=36, market=18, sell=7, buy=6, milk=1, wool=1 | `c6f96a8521dc` |
| 24 | kaggriculture-beginner-friendly | 61,980 | 1,004 | 2 | market=80, sell=43, milk=10, weed=9, fertilizer=8, wool=8 | `d39dba50793d` |
| 26 | Graph + Reinforcement Learning | 18,946 | 247 | 1 | market=19, weed=8, sell=7, milk=4, pickup=3, wool=2 | `f029fa0cb66a` |
| 41 | notebook76f6a59396 | 150,378 | 333 | 1 | market=729, fertilizer=431, sell=401, buy=356, pickup=339, harvest=338 | `00e8ab594a39` |
| 44 | 02 Adaptive Replay Agent | 25,939 | 467 | 1 | market=42, sell=20, weed=9, milk=6, pasture=4, wool=4 | `3c41010de371` |
| 47 | [Farm] Top solution in LB! | 40,593 | 1,074 | 1 | market=32, fertilizer=25, seed=16, sell=16, harvest=13, weed=13 | `7c35800ee64c` |
| 54 | TestKaggriculture / Hamburger 🍔 | 42,865 | 1,077 | 1 | market=38, seed=23, fertilizer=22, milk=17, sell=12, harvest=8 | `e852b9a2e846` |
| 59 | Diversified Scheduler Baseline / Kaggriculture | 10,247 | 331 | 1 | seed=23, harvest=12, market=12, sell=5, buy=2, weed=2 | `fad8a5b0bd89` |

## Interpretation

The downloaded leaderboard code is dominated by a small number of repeated source families. The rank-1 and rank-7 executable sources were both full-panel ties with V53 on the fresh 120-route panel; the rank-2 source had a higher mean margin but one fewer paired win. Static presence of market, fertilizer, timing, or route logic is therefore not treated as evidence of a stronger policy without paired replay verification.

The production agent remains unchanged by this report. Experimental router files and replay benchmarks are kept separately so a future promotion can be audited against the same panel.
