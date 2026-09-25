# Final-day hire-cap screen — 2026-09-25

**Decision: reject both caps; no full-100 run.** Neither cap adds a route win among the four frozen losses, and some winning-control margins shrink. The feles99 loss becomes substantially worse at both caps.

## Protocol

Tested the standalone [`exp_final_day_hire_cap_20260925.py`](../../exp_final_day_hire_cap_20260925.py), which imports `main.py` and only suppresses over-cap `HIRE` orders on observed steps 696–719. The cap is `MAX_FINAL_DAY_HIRES` (10 or 11); policy logic does not inspect seeds or replay/route identity. Used native `route_panel_benchmark.py`, Kaggriculture **1.32.7**, and the exact frozen `diagnostics/top50_current_2026-09-24/routes/summary.json` (SHA-256 `7b242129364b287d197a8c18964d6b9da9b990c68ebc39f1d087782bfc3b27e9`). Frozen baseline `main.py` SHA-256: `04b0bdc3bbe319d969170dd8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

All eight chosen route records were run in both candidate seats at each cap (32 seat-games total). Route ID is frozen episode ID plus source seat; filenames below are relative to the frozen `routes/` directory.

| Cohort | Exact route ID / frozen route file | Seed | Baseline paired margin |
| --- | --- | ---: | ---: |
| Near-tie loss | `112934493/seat0` — `marwar22-submission-56507022-episode-112934493-seat0.json.gz` | 830779084 | −168 |
| Near-tie loss | `112937001/seat1` — `Yannik-Schiffner-submission-56519100-episode-112937001-seat1.json.gz` | 1075971183 | −330 |
| Near-tie loss | `112939452/seat1` — `feles99-submission-56442261-episode-112939452-seat1.json.gz` | 1015350054 | −346 |
| Near-tie loss | `112936862/seat1` — `hiroshi-murakami-submission-56520330-episode-112936862-seat1.json.gz` | 1039126387 | −332 |
| Nearest positive control | `112939403/seat1` — `Gleb-Tumanov-submission-56357593-episode-112939403-seat1.json.gz` | 1231382306 | +1,686 |
| Nearest positive control | `112932413/seat1` — `Evil-Mango-submission-56451263-episode-112932413-seat1.json.gz` | 1259458766 | +2,480 |
| Nearest positive control | `112938063/seat1` — `Arda-Ceylan-submission-56508756-episode-112938063-seat1.json.gz` | 1044037877 | +3,526 |
| Nearest positive control | `112938204/seat0` — `Artem-The-Farmer-submission-56521198-episode-112938204-seat0.json.gz` | 878130961 | +5,904 |

## Results

Paired margin is the sum of the two seat margins. “Own / rival cash” is final cash in each seat-game; the two seats produced identical cash and margins for every selected route, so the listed cash pair applies to both seats. The simulator's terminal reward is the farm's final money.

| Route ID | Cap 10: paired margin; own / rival cash | Cap 11: paired margin; own / rival cash |
| --- | --- | --- |
| 112934493/seat0 — marwar22 | −100; 57,369 / 57,419 | −168; 57,331 / 57,415 |
| 112937001/seat1 — Yannik Schiffner | −280; 144,109 / 144,249 | −330; 144,082 / 144,247 |
| 112939452/seat1 — feles99 | −2,972; 87,731 / 89,217 | −2,972; 87,729 / 89,215 |
| 112936862/seat1 — hiroshi murakami | −306; 61,951 / 62,104 | −332; 61,929 / 62,095 |
| 112939403/seat1 — Gleb Tumanov | +1,660; 77,953 / 77,123 | +1,686; 77,957 / 77,114 |
| 112932413/seat1 — Evil Mango | +2,450; 86,912 / 85,687 | +2,480; 86,920 / 85,680 |
| 112938063/seat1 — Arda Ceylan | +1,040; 84,211 / 83,691 | +1,096; 84,237 / 83,689 |
| 112938204/seat0 — Artem The Farmer | +5,964; 98,817 / 95,835 | +5,904; 98,784 / 95,832 |

Each cap finished **8 wins / 8 losses / 0 draws** across seats, with **4/8 route wins**—the same route-win count as baseline. There were no loss-to-win reversals and no winning-control reversals, but control margin regressed on Gleb, Evil Mango, and Arda at cap 10, and on Arda at cap 11. Cap 10 blocked 24 hire orders; cap 11 blocked 8.

All 32 games finished `DONE` for both agents with 720 frames. Per-game wall runtime was 5.57–6.60 s at cap 10 and 5.65–6.54 s at cap 11; maximum measured candidate-agent call was 129.08 ms and 115.00 ms, respectively. Per-route runner JSONs in this directory retain both seats' final cash, margins, statuses, frames, and timings.
