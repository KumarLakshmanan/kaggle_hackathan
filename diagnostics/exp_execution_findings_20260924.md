# Day-28 execution audit — no promotion

The simulator's animal refresh applies today's `CARE` credit **after** its production update. Day 28's end-of-day update is the final production refresh of the 720-step episode, so a day-28 CARE credit cannot produce a saleable unit. This is a deterministic execution miss in the current policy. In previously recorded traces, many such actions targeted animals with `fertilizer_available=true`.

The isolated [experimental agent](../exp_agent_execution_20260924.py) wraps the hash-frozen current `main.py` and changes only day-28, hours 0–22 `CARE` actions on observed animals with available fertilizer and storage headroom to `COLLECT_FERTILIZER`. It uses no route ID, seed lookup, or future shop/action information. `main.py` SHA-256 remained `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1` throughout. No Kaggle submission was made.

The [panel](exp_execution_panel_frozen_20260924.json) was frozen before running the treatment: 32 routes from 32 distinct teams, four each from `best_replay`, `failed_replay`, and six leaderboard rank cohorts spanning 101–600. Each cohort supplied two salted-hash choices and two lowest remaining pre-existing baseline pair margins. Both seats were run for each route. The new native baseline reproduced all 64 pre-existing seat margins exactly. All 256 games across the four arms finished `DONE/DONE` with 720 frames in Kaggle Environments 1.32.7.

| Test | Baseline → treatment seat results | Route-pair transitions | Margin change per game | Improved / regressed / unchanged | Shop paths changed |
|---|---|---|---:|---:|---:|
| Native | 34 W→W, 30 L→L; 0 flips | 17 W→W, 15 L→L; 0 flips | +19.609375 mean, +20 median | 60 / 4 / 0 | 0 / 64 |
| Fixed shop sequence | 64 W→W; 0 flips | 32 W→W; 0 flips | +20.84375 mean, +24.5 median | 58 / 6 / 0 | 0 / 64 |

Native treatment requested 508 replacements from 640 observed opportunities, skipping 132 for storage headroom; there were no experiment exceptions. The fixed-shop arm requested 552 replacements, skipping 88. Its eight-shop sequence was the same for both agents in every game. This modified-environment arm changes route difficulty substantially (all 64 controls won), so its margin effect is useful as a shop-path robustness check, not a native win-rate estimate. The native arm already had identical shop paths between paired policies.

The economic gain is real but small: mean margin changes by about 20 coins despite roughly eight replacements per game, and there are **no win/loss transitions**. Fertilizer can be near its $1 floor late in the game (for example, an existing recorded day-28 trace quoted $1 at market inventory 10,494). This is not a high-leverage fix and should **not** be promoted. No threshold or alternative-action search was undertaken.

Exact paired scores, telemetry, hashes, and shop paths are in [the summary](exp_execution_summary_20260924.json) and the four `exp_execution_{native,fixed}_{baseline,treatment}_20260924.json` reports. The [diagnostic runner](exp_execution_panel_20260924.py) contains the frozen selection and fixed-shop procedure.
