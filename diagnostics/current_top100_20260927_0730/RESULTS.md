# Fresh top-100 assessment — 27 September 2026

## Result

Exact uploaded c68fa46f, submission **56602057**, wins **77/100 matchups in both seats** and **155/200 seats**.
Seat draws: 0; losses: 45. The all-top-100 target is not achieved.

| Current leaderboard cohort | Teams covered | Both-seat sweeps | Seat wins | Draws | Losses |
|---|---:|---:|---:|---:|---:|
| Top 10 | 10/10 | 7/10 | 14/20 | 0 | 6 |
| Top 50 | 50/50 | 36/50 | 72/100 | 0 | 28 |
| Top 100 | 100/100 | 77/100 | 155/200 | 0 | 45 |

## Freshness and method

Official leaderboard snapshot: **2026-09-27T07:27:24Z**. All 100 team sources were selected from fresh API queries and downloaded into this collection.
Source games were created between **2026-09-27T06:57:19.428000 UTC** and **2026-09-27T07:29:19.687000 UTC**; 84 distinct episodes cover 100 teams.
Episodes reused from yesterday's 50-team panel: **0**. No prior test outcomes were reused.

For each snapshot team, select its higher-scoring active submission and latest complete public replay without filtering for wins. Run the exact uploaded file against each action tape in both seats, on its recorded seed, with original native shop generation. The candidate remained frozen throughout.

All games DONE/DONE with 720 frames: **True**. Error telemetry: {"farmice_errors": 0, "integration_gate_collisions": 0, "mirror_quantity_errors": 0, "quantity_errors": 0, "queue_errors": 0}.

These opponents are recorded action tapes, not the teams' private reacting agents. They cannot respond to changed decisions or future shop differences. This result is a development benchmark, not a forecast of live rating or rank.

At turn 144, the native shop prefix differs from the source recording for **65/100 teams** in at least one seat. This follows from replaying fixed actions under changed farm states and original native shop generation; it limits conclusions about the live policies.

## Matchups not won in both seats

| Snapshot rank | Team | Seat 0 cash margin | Seat 1 cash margin |
|---:|---|---:|---:|
| 2 | Boey | -80,054 | -80,054 |
| 5 | Majkel1337 | -10,279 | -10,279 |
| 7 | Unknown Mother-Goose | -790 | -790 |
| 18 | Arda Ceylan | -5,963 | -5,963 |
| 22 | We wanna be tomatos | -6,231 | -6,231 |
| 23 | yuto083 | -7,817 | -7,817 |
| 24 | Artem The Farmer 🍅 | -21,459 | -21,459 |
| 25 | Kaggledew Valley 🏆 | -4,085 | -4,085 |
| 29 | elmo | -9,783 | -9,783 |
| 35 | Yannik Schiffner | -3,137 | -3,137 |
| 39 | marwar22 | -4,249 | -4,249 |
| 43 | Cow Boy | -16,758 | -16,758 |
| 46 | arutyunoff | -4,714 | -4,714 |
| 49 | Excluding | -3,238 | -3,238 |
| 54 | Snorlax | -1,058 | -1,058 |
| 55 | dodsters | -3,929 | -3,929 |
| 60 | lingxiaojun | -9,860 | -9,860 |
| 62 | Christoffer Thimsen | -4,660 | -4,660 |
| 71 | ready or not here i come | -13,207 | +5,097 |
| 77 | redblackbst | -1,680 | -1,680 |
| 82 | fuxi | -16,718 | -23,181 |
| 91 | 3정훈 | -725 | -725 |
| 100 | AkiraOnojp | -1,085 | -1,085 |

## Decision and evidence

Reject the claim that c68 beats all current top-100 replays. Preserve this baseline and the losing cases for the next candidate; this assessment alone does not justify replacing or re-uploading main.py.

- Frozen protocol: PLAN.md.
- Fresh source selection and hashes: manifest.json and listings/.
- All 200 game records: assessment.json.
- Every team result and replay date: MATCHUPS.md.
- Machine-readable summary: summary.json.
- Exact uploaded root backup: main_uploaded_disjoint_integrated_20260927_c68fa46f.py.
- Development-only losing subset and state captures: non_swept_routes.json and non_swept_context.json. Selecting these after outcomes does not make them validation data.
