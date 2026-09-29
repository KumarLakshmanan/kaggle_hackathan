# Submitted-file comparison against the 2026-09-29 top 100

**Decision:** retain `4eeac9c3` as the research `main.py`. It is the strongest of the downloaded submitted files on this frozen top-100 replay panel and has the highest recorded Kaggle public score among the four inspected submissions. Do not promote either September 29 file on this evidence. No upload was requested or made in this comparison.

## Source and upload record

The authenticated Kaggle leaderboard was frozen at **2026-09-29 11:03:38 UTC**. The four submitted `main.py` files were downloaded from Kaggle and SHA-256 checked against preserved local copies; see `downloaded/download_receipt.json`. The most recent submissions are byte-for-byte identical, so there are three distinct policies. The scores below are from a refreshed submission listing at approximately **2026-09-29 12:06:59 UTC** (`submissions_final.json`). They are time-specific public ratings, not controlled head-to-head scores.

| Submission ID | Uploaded UTC | Uploaded IST | SHA-256 prefix | Public score |
|---|---|---|---|---:|
| 56668607 | 2026-09-29 08:11:57 | 2026-09-29 13:41:57 | `ae349d83` | 1836.8 |
| 56666114 | 2026-09-29 06:55:03 | 2026-09-29 12:25:03 | `ae349d83` | 1767.8 |
| 56662188 | 2026-09-29 04:09:22 | 2026-09-29 09:39:22 | `257f941d` | 1249.9 |
| 56609430 | 2026-09-27 13:10:15 | 2026-09-27 18:40:15 | `4eeac9c3` | **2577.6** |

The root `main.py` currently hashes to the exact downloaded `4eeac9c3` file. The two `ae349d83` submissions have the same full SHA-256 `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`; their differing public scores do not reflect different code.

## Matched local results

For each of the frozen top-100 leaderboard teams, we selected the highest-scoring listed submission and its latest completed public replay without outcome filtering. All 100 action tapes were downloaded and verified: 91 distinct episodes, 719 actions each, DONE/DONE at 720 frames. Each distinct own submitted file played the same 100 tapes, original replay seed and native original-shop generation, in both candidate seats: **600 native engine 1.32.7 games**. The result ledger SHA-256 is `7ba72ea62b9b399ccc8dc1099a2d86c09ec9e8670b0a63b068d58fd309596832`. All 600 cases finished DONE/DONE at frame 720, with no recorded policy error.

| Downloaded file | Top 10 seat W/L | Top 10 both-seat wins | Top 50 seat W/L | Top 50 both-seat wins | Top 100 seat W/L | Top 100 both-seat wins | Mean top-100 seat margin |
|---|---:|---:|---:|---:|---:|---:|---:|
| `4eeac9c3` | **11/9** | **5/10** | **71/29** | **35/50** | **141/59** | **70/100** | **+24,106.64** |
| `257f941d` | 7/13 | 3/10 | 67/33 | 33/50 | 131/69 | 65/100 | +19,531.24 |
| `ae349d83` (both recent uploads) | 7/13 | 3/10 | 67/33 | 33/50 | 131/69 | 65/100 | +19,531.24 |

There were no draws. Relative to `4eeac9c3`, each newer file improves 8 individual seat outcomes but regresses 18; the newer files improve 4 team pairs and regress 9, with 87 team pairs unchanged. The average matched seat margin is 4,575.405 coins lower. `257f941d` and `ae349d83` have identical rewards and outcomes in all 200 corresponding games despite distinct source bytes; the newer guard adds no measured benefit on this panel.

## Why the older policy wins more often on this panel

The September 29 `257f941d` file layers a day-one observed opening bridge and later complete route replacements on top of the older queue policy. Its bridge chooses the donor `shared151` schedule when the opponent has at least five hands, except the guarded one-pasture case (`downloaded/main_257f941d.py`, around lines 1087–1123). Other replacements use observed shop pairs after step 144 (around lines 621–680). These additions were designed around earlier saved losses; the upload review explicitly says the saved panel was used during development and was not independent validation.

On this newly selected top-100 panel, **eight of nine** team pairs changing from wins to losses ended with the `shared151` donor branch selected. The ninth used the `BRUNCH_SPOT|PIZZA_SHOP` loss-pool route. Four team pairs changed from losses to wins: one with the donor bridge, one with a compatible route, one with a loss-pool route, and one with a guarded route. These are observed associations in complete matched games, not single-feature ablations; several layers can act in the same game. The outcome ledger and `delta_explanation.json` bind each changed team and branch.

Two top-10 examples account for all four top-10 seat regressions: against Boey (rank 5 in the frozen snapshot), `4eeac9c3` won both seats by +101,543 while `257f941d` selected `shared151`/donor route1 and lost by -33,489/-33,354. Against Anton Tikhonov (rank 7), the old +514 win in both seats became -7,481 with loss-pool route `113413613`. The newer policy does have real local rescues, including monsaraida (old -7,274, new +14,915 in each seat) and Lucien de Rubempre (old -61,318, new +11,381). The net on this panel is 18 win-to-loss seats versus 8 loss-to-win seats.

The subsequent `ae349d83` Pizza melon fallback was checked on two of the 200 matched cases and never activated (`a44_pizza_melon_guard_fallback72=false` in all 200 telemetry records). Thus it is unsurprising that its 200 rewards and outcomes exactly equal `257f941d` here. The two separate `ae349d83` Kaggle submissions are byte-identical, so their different public ratings also show that online score varies with opponent history and time; the full gap from 2577.6 to the newer public scores cannot be assigned solely to code changes.

**Interpretation:** the older September 27 `4eeac9c3` file is the better performer on this specific matched top-100 panel, including the top 10, and is also the highest-scored submitted file in the refreshed Kaggle listing. This does not prove it would earn 2577.6 again if re-uploaded, or that it would beat live reacting versions of these opponents. Opponents' private source files are unavailable; these tests use their public replayed actions, which cannot adapt to our changed actions or markets. Public scores also reflect different opponent histories. Treat the matched panel as a diagnostic comparison, not independent reactive validation or a rank forecast.

Evidence: `PLAN.md`, `snapshot_receipt.json`, `leaderboard.json`, `submissions.json`, `submissions_final.json`, `manifest.json`, `routes/summary.json`, `downloaded/download_receipt.json`, `local_run_receipt.json`, `local_results.jsonl`, and `assessment.json`. An 18-case fast native-transition parity pilot is in `fast_native_parity.json`; the complete result above uses the original native runner, not the fast pilot.
