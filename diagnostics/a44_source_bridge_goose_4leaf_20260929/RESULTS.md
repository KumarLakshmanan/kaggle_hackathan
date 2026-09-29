# a44-bound Goose four-leaf candidate — results

**Completed:** 2026-09-29 01:40 IST  
**Decision:** Reject for promotion. Continue with other offline candidates.  
**Scope:** Frozen replay tapes only; no Kaggle access, download, upload, or
reactive opponent game was run.

## Frozen artifacts and receipts

- Candidate SHA-256: `c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632`
- a44 source SHA-256: `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`
- Candidate result receipt SHA-256: `2eb086dd41080a2c6488e6bc94616e881cbb32e41ff6891c8ef6a924bc0d0322`
- Candidate JSONL SHA-256: `789f7a071f6861ef0e368d716328a8aceabe14a80296896d98d44822f4ebcef8`
- Exact-a44 public-control receipt SHA-256: `eb2e941cffa4de59527862a8210e5df27ba2363d5ea91f93387d0af1f384e1f0`
- Panel SHA-256: `7407b5f610457d2c00837a3c82e51ae2deaa225b20f2145e01dfaa92dba1db51`
- Post-run static audit: `posthoc_audit.py`, SHA-256 `b63f3330ae3365a6b0097dfa359a2dc355c70cf19083019123b5dd6bd589bbc7`
- Post-run audit receipt SHA-256: `64876242941a2e538224791e1f9dc9b6133fb10e8cc3725d8a6cf188f3fc5a3b`

The 108 exact-a44 public controls completed cleanly: 106 wins, 0 draws,
2 losses, and 53/54 both-seat sweeps. The candidate completed all 208
seat-games across 104 fixtures; every row has 720 transitions, DONE/DONE,
and zero candidate policy errors.

## Paired results

| Panel | Candidate | a44 | Change |
|---|---:|---:|---:|
| Frozen 30 loss fixtures, both-seat sweeps | 21/30 | 17/30 | +4 sweeps |
| Frozen 30 loss fixtures, seat-game W/L | 43/60 | 34/60 | +9 wins |
| Public-win controls, both-seat sweeps | 53/54 | 53/54 | 0 |
| Latest saved top 20, both-seat sweeps | 19/20 | 19/20 | 0 |

The four rescued loss fixtures are `live-114229792`, `live-114249897`,
`live-114258293`, and `live-114267572`. On `live-114288168`, candidate seat 1
changes from a loss to a win, but the fixture remains a split result. No
previous two-seat sweep became a loss in these panels. Average paired-margin
change is +976.6 coins per seat-game on the loss panel, -379.4 on public-win
controls, and 0 on top 20.

The candidate preserves 19/20 top-user sweeps but reaches only 21/30 on the
loss goal. The predeclared target is 27/30, so it falls six sweeps short.
These results therefore do not authorize replacing the root `main.py`.

## Final runner-gate issue

The frozen `run_study.py full` completed all games and wrote the candidate
receipt, then its final report stopped at the `activation_passed` assertion.
The receipt has 188/208 raw activation flags. Inspection found exactly one
bookkeeping mismatch on 20 rows: `feature_rows.json` stores `selected_route`
as an integer while policy telemetry stores `a44_goose4_route` as a string.
The branch, key, expected 647 turns, and zero-error checks all pass on all
208 rows. Comparing only those two route values after string conversion
makes the complete activation check pass 208/208. No candidate file, game
row, or outcome was changed. `posthoc_audit.py` reproduces this read-only
normalization and binds all input hashes; the original receipts retain the
runner's raw `activation_passed` values.

## Reproduction

The games were run once with one worker:

```powershell
python -X utf8 diagnostics/a44_source_bridge_goose_4leaf_20260929/run_study.py full
```

The runner's final report assertion is expected to stop on the raw string vs
integer comparison described above. Recompute the audit without simulations:

```powershell
py -3 -X utf8 diagnostics/a44_source_bridge_goose_4leaf_20260929/posthoc_audit.py
```

This is saved-replay evidence, not independent validation of a policy change.
Any later promotion still needs the frozen preservation gates and fresh local
reactive games. Root `main.py` and the last recorded Kaggle status were not
changed or checked during this study.
