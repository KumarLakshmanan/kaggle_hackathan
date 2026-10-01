# Dhana strength audit — 2026-09-23

This is a measured upgrade, not an unbeatable-agent claim. Root `main.py` is unchanged.

## Implementation

The old Dhana nearest-replay policy is replaced by the root's stronger V52/V51 multi-policy base, with upstream notices retained. A permanent step-72 selection now stops running unused controllers. Both controllers still receive the entire prefix, alternate actions remain detached copies, and selected-controller failures have a fallback. Unused, disabled V53 source is omitted.

The recognized opening changes BUY 20 / SELL 15 wheat to BUY 15 / SELL 10. Net wheat remains five and the subsequent seed purchase is preserved. While trailing on cash, idle/redundant worker commands can collect already-available renewable output or fertilizer; stock pressure and the final liquidation phase disable this recovery. Useful care, movement and planting are not replaced.

The new overlay uses current public farms and the player's own private inventory, not test seeds, episode identifiers, opponent private inventory or future observations. The inherited base still contains its precomputed policy tapes.

## Completed evaluations

All scores below use kaggle-environments 1.32.7, standard 720-step games and PYTHONHASHSEED=0. The runner uses the installed, unmodified official game interpreter. A win means strictly higher terminal reward; ties are separate.

| Suite | Wins | Draws | Losses | Win rate | Mean margin | Worst margin |
|---|---:|---:|---:|---:|---:|---:|
| Root development/validation: 40 seeds, both seats | 79/80 | 0 | 1 | 98.75% | +14.80 | -118 |
| Root final holdout: 20 fresh seeds, both seats | 39/40 | 0 | 1 | 97.50% | +13.50 | -3453 |
| Standalone replay panel: 58 routes, both seats | 116/116 | 0 | 0 | 100.00% | +46923.45 | +23434 |
| Full local replay archive: 5,126 routes, both seats | 8055/10252 | 0 | 2197 | 78.57% | +32122.84 | -32996 |

Across all root games: 118/120 individual wins. Summing both seat margins per seed gives 60/60 positive paired score totals (0 ties, 0 negative totals). A positive two-seat total is NOT the same as winning every individual game.

The first 80 games were used for development/validation, including retuning after failures; they are not independent held-out evidence. The final 40 games use System.Random(20260923) seeds generated after fixing the final source and parameters, without subsequent retuning. Repeated development runs are not included again in the displayed totals.

Old Dhana on the same standalone replay panel: 102/116 wins, 14 losses.

Old Dhana on the identical 200-game archive sample: 67/200 wins, 0 draws, 133 losses, mean margin -5172.59.

Unchanged root on the identical first 100 archive routes: 158/200 wins, 0 draws, 42 losses, mean margin +34463.88. Dhana's matched mean margin change: -4006.32; 0 root non-wins became wins, 9 root wins became non-wins. This is a comparison against recorded opponents, distinct from live head-to-head against root.

Fast-runner rewards/statuses exactly matched the full official Kaggle runner in both seats on seed 2147483646. Sixteen unit tests cover overlay safeguards, no input/action mutation, controller warm-up/selection, detached action copies and exception fallback. Timing numbers in JSON reports are diagnostic only: suites ran concurrently, so they are not a controlled speed benchmark.

## Coverage and limitations

Full archive match evaluation finished: 10,252 games across every extracted route in both seats.

All four local archive Parquet shards were read, plus best_replay, failed_replay, dhana/fail and live_routes. Extraction found 2,557 replay episodes and 5,126 distinct action/seed routes, with 0 skipped extraction records. Both recorded players were extracted. Exact action-and-seed duplicates were collapsed; metadata-only episode listings are not replay bodies.

**All 5,126 extracted routes were match-tested in both seats (10,252 games).** This covers every replay body found locally, after collapsing exact action-and-seed duplicates.
The archive sample was selected from a hash-sorted local manifest, not a random leaderboard sample. It overlaps development data. Replaying fixed action tapes does not reproduce an opponent's live adaptation. The 1.32.6 replay actions were re-executed under 1.32.7 rather than retaining their historical scores. Observed losses disprove a universal 100% win-rate claim. Unseen agents, seeds, engine/configuration changes and hosted resource limits remain risks.

Rejected experiments include larger opening reductions (which changed later market interactions), unconditional idle recovery and early/late sale changes that regressed validation cases.

## Reproduce

```powershell
$env:PYTHONHASHSEED='0'
$py = 'C:\Users\GIGABYTE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -B dhana/build_strength_candidate.py
& $py -B -m unittest dhana/test_strength.py -v
& $py -B dhana/strength_lab.py --candidate dhana/main.py --seeds 42 2147483646 --workers 4 --output benchmark_results/recheck_root.json
& $py -B dhana/strength_lab.py --candidate dhana/main.py --manifest analysis_artifacts/dhana_strength/json_manifest.json --workers 4 --output benchmark_results/recheck_json.json
# Full archive run: potentially several hours. --resume skips every completed game in the output file.
& $py -B dhana/strength_lab.py --candidate dhana/main.py --manifest analysis_artifacts/dhana_strength/manifest.json --workers 6 --resume --output benchmark_results/dhana_v3_archive_200.json
```

Evaluation-only dependencies live in ignored .bench_deps (kaggle-environments 1.32.7, jsonschema, pyarrow, requests, structlog, pysimdjson). The submitted main.py uses its inherited standard-library implementation; do not submit the development tools or .bench_deps.

## Provenance

Final candidate SHA-256: `bb9d577ae3c708395367f40f4b201a5abebeed63fda77d2703e3e71a7a03246f`.

Root control SHA-256: `16da7a84cfdf4a659c42d2abf3eb41738e93da7e2b0fd4df7f8f241f6b845759`.

Old Dhana SHA-256: `fc7a3bdc325ebfeecf4a54755dc0bf077f3aa871b7aaed5c1d0534e98b47b692`. Promotion keeps this exact source at dhana/backups/main_before_strength_20260922.py.

Detailed result files (with every seed, seat, score and source hash):
- [dhana_v3_root_80.json](../benchmark_results/dhana_v3_root_80.json)
- [dhana_v3_holdout_40.json](../benchmark_results/dhana_v3_holdout_40.json)
- [dhana_v3_json_116.json](../benchmark_results/dhana_v3_json_116.json)
- [dhana_v3_archive_200.json](../benchmark_results/dhana_v3_archive_200.json)
- [root_archive_control_200.json](../benchmark_results/root_archive_control_200.json)
- [dhana_before_replay_panel.json](../benchmark_results/dhana_before_replay_panel.json)
- [dhana_before_archive_200.json](../benchmark_results/dhana_before_archive_200.json)
- [dhana_v3_official_verify.json](../benchmark_results/dhana_v3_official_verify.json)
