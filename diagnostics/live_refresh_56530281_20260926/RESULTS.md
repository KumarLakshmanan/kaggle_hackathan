# Fresh public live audit — 2026-09-26

The newest 40 completed public episodes available for uploaded submission
56530281 were downloaded read-only. They are distinct from the prior 24-game
audit. The uploaded policy is SHA-256
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`;
the current local `main.py` is the unuploaded mirror-gated policy, SHA-256
`6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`.
No new Kaggle submission was made.

## Actual live results

The uploaded policy won **9/40** episodes and lost 31/40. Both players were
`DONE` in every episode. Nineteen losses were under 1,000 coins. Among the
31 losses, 24 matched the opponent's farmer actions on at least 718 turns;
14 of those also matched hand actions on at least 700 turns. Across all 40,
median exact matches were 719 farmer, 699 hands, 563.5 market, and 552 full
turns. The replays show many near-shared production paths with economically
meaningful market differences. They do not establish that the opponents use
the same code or will respond the same way to a changed policy.

The raw replays and per-episode outcomes are in `episode-*-replay.json` and
`audit_latest_40.json`. The sample is a recent public slice, not a random
tournament sample or a substitute for the moving leaderboard rating.

## Local parity and sale-gate diagnosis

`extract_routes.py` produced 40 distinct opponent action tapes and
`summary.json`. Replaying the byte-identical uploaded backup on each original
seed and seat reproduced **40/40 exact final own cash, rival cash, margins,
and both `DONE` statuses**. This validates the local engine and tape
extraction for this sample. With each tape also run in the opposite seat,
the uploaded backup won 11/40 positive summed paired margins and 21/80 seat
games. All 80 games finished `DONE`.

The current local eight-turn physical-mirror gate likewise won 11/40 paired
routes and 21/80 seats. It rescued three uploaded-policy paired losses and
reversed three wins. It activated in 68/80 seats for 815 extra advance turns;
across the panel own cash rose 737 coins and fixed-rival cash fell 10,550.
The six outcome changes had identical public physical farms at day 6; early
cash gap and similar market actions did not separate rescues from reversals.
The results are in `live40_comparison.json`, `gate_feature_audit.json`, and
the two first-divergence traces. **These are fixed-action development
replays. They do not measure a live adaptive response to the gate.**

Reproduce the read-only extraction and local comparisons from the workspace
root:

```powershell
python -B -X utf8 .\diagnostics\live_refresh_56530281_20260926\audit_fresh.py
python -B -X utf8 .\diagnostics\live_refresh_56530281_20260926\extract_routes.py
python -B -X utf8 .\route_panel_benchmark.py --candidate main_before_top10_goal_20260926_04b0bdc3.py --summary .\diagnostics\live_refresh_56530281_20260926\summary.json --workers 8 --json-out .\diagnostics\live_refresh_56530281_20260926\submitted_backup_40routes.json
python -B -X utf8 .\route_panel_benchmark.py --candidate main.py --summary .\diagnostics\live_refresh_56530281_20260926\summary.json --workers 8 --json-out .\diagnostics\live_refresh_56530281_20260926\main_local_40routes.json
python -B -X utf8 .\diagnostics\live_refresh_56530281_20260926\compare_local_gate.py
```

## Decision

Retain this audit as a diagnosis and development panel. It gives no basis
for promoting another sale-gate change or predicting a leaderboard gain.
Independent reactive checks remain necessary for a policy change.
