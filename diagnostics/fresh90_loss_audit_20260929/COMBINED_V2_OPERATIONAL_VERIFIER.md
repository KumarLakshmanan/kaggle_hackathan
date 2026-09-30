# Combined V2 operational verifier

Verifier source: `verify_combined_v2_operational.py`.

The runner is pinned to candidate SHA-256 `4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4`, baseline `cb76fbc4`, and the last callable `kaggle_fresh_execution_schedule_entrypoint`. It reuses the fixed-route fast-native path (`fast_game_current.play`), the reacting fast-native path (`fast_reactive.play`), `qualify.errors`, `paired_benchmark`, the existing run lock, and the `verify_native.py` / `verify_loader.py` patterns. It leaves `main.py`, `agent.md`, and the historical verifiers untouched.

## Checks it will run

- Reproduce fast-native matches for rank 1 control, rank 8 route activation, and rank 10 funded-land activation, both candidate seats. Each rerun must exactly match the saved row's rewards, result, frame count, statuses, telemetry, and error counters.
- Capture the candidate and opponent's complete 719-action streams during each fast-native run, then compare those streams to a Kaggle framework run. Require exact actions, rewards, statuses, and telemetry; require 719 logged calls per agent, 720 frames, nonnegative overage, and no status, stderr, policy, or telemetry errors.
- Select two candidate reacting-screen rows from different non-`cb76` opponents, one per candidate seat. Reproduce each row with the official fast-reactive native path, verify it against the saved screen results, then compare full actions/rewards/statuses/telemetry with Kaggle framework runs.
- Compare direct and file-loaded candidate execution against the exact `baseline_cb76fbc4.py` in both seats on seed 12929001 and the saved rank 8 and rank 10 activation seeds. Require matching rewards, statuses, candidate action hashes, and joint action hashes.
- Write `diagnostics/fresh90_improvement_20260929/combined_v2_operational_receipt.json`, with `candidate_sha256` and `passed`, for `run_reacting.py`'s confirmation gate. Detailed results go beside this verifier.

The existing top-100 result rows contain rewards/statuses/telemetry but do not contain the V2 candidate's action stream; their `action_sha256` identifies the public source route. Therefore the runner recreates the six selected fast-native transitions from the exact candidate and raw public route, checks those outcomes against the saved rows, and only then treats the captured actions as the framework comparison reference. It does not reuse the older `v2_top20_jobs_traces` as V2 action truth: those traces are bound to a different candidate SHA (`e7a5…`).

## Invocation and current status

First inspect inputs without games:

```powershell
python diagnostics/fresh90_loss_audit_20260929/verify_combined_v2_operational.py --preflight
```

After the reserved and reacting gates pass, run:

```powershell
python diagnostics/fresh90_loss_audit_20260929/verify_combined_v2_operational.py --run --confirm-gates-passed
```

`--run` is unavailable without the explicit gate flag, and preflight also requires a complete passing `combined_v2_screen_receipt.json`. All game checks use `diagnostics/.shared_game_run.lock`. The runner writes a provisional false receipt first, so an interrupted or failed run cannot leave a stale passing receipt for confirmation.

Static validation on 2026-09-30 passed Python compilation and CLI help. Preflight found the six saved top-100 rows, verified their source routes/replays and activation/control telemetry, and found the expected frozen candidate hash and entrypoint. It reported only the expected blocker that the combined V2 reacting-screen jobs/results/receipt have not yet been created. **No games were run**, and no operational receipt was created.

The saved V2 top-100 ledger has no full per-turn action tape or candidate action digest. Reproducing the six fast-native cases is therefore necessary to establish action parity; the saved rewards/statuses/telemetry alone cannot prove exact action parity. Passing this operational check is execution evidence, not an independent win-rate result.
