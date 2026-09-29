# Full saved top-20 and 30-loss goal evaluation

## Question

Does the frozen Ghost + Kwa composite meet both saved-corpus objectives:
18/20 or more top-team fixtures swept in both seats, and 27/30 or more frozen
public-loss fixtures swept in both seats?

The candidate is the frozen combined V4 SHA-256
`7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`, derived
from exact 6d candidate
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

## Frozen fixtures and gates

The top-20 set was already run for this exact candidate in
`diagnostics/a44_ghost_kwa_combo_20260929/outcome_run_20260929/`; its
hash-bound receipt records 19/20 both-seat sweeps. This run evaluates both
seats on every fixture in the full frozen 30-loss set, for 60 new games, and
combines that result with the existing top-20 receipt. The sets are disjoint.

Require all 60 new games to finish DONE/DONE at 720 frames with no policy
errors and passing route telemetry. The two Kwa and two Ghost trigger seats
must win with positive margin. All other 56 loss-panel seats must exactly
match the 6d baseline on result, both rewards, margin, status, and frames.
Count a fixture as a sweep only when both seats win. The goals are at least
18/20 top-20 sweeps and 27/30 loss30 sweeps. Baseline 6d has 19/20 and 22/30.

## Evidence limits

This measures performance on the same saved opponent action tapes used to
select the routes. It is the full frozen corpus result, not independent
generalization or reactive-opponent qualification. A pass is not by itself
promotion evidence. Keep `main.py` unchanged and do not access Kaggle.

## Commands

Build the panel and statically freeze/verify it:

```powershell
python -X utf8 diagnostics/a44_ghost_kwa_goalpanel_20260929/build_panel.py
python -X utf8 diagnostics/a44_ghost_kwa_goalpanel_20260929/preflight.py freeze
python -X utf8 diagnostics/a44_ghost_kwa_goalpanel_20260929/preflight.py verify
```

After review and a free shared game slot, run once:

```powershell
python -X utf8 diagnostics/a44_ghost_kwa_goalpanel_20260929/run.py
```

The loss30 runner is one-shot and does not resume or overwrite results.
