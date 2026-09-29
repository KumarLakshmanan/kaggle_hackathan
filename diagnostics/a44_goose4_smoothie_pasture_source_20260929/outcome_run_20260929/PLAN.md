# Exact-6d pasture derivative: four-game terminal outcome pilot

## Scope

This separate fixed-tape outcome pilot tests the frozen pasture derivative
SHA-256 5b4ef52d19cb8ffb310b2bb067c725810241668667a0b5b468ac09b6b9215506
against the two already bound opponent action tapes:

| Fixture | Panel role | Seats | Frozen 6d combined result |
|---|---|---:|---|
| live-114274897 | THIRD target | 0, 1 | losses at margins -17,760 and -17,099 |
| public-win-114193811 | ChrisTu control | 0, 1 | wins at margin +1,226 per seat |

The control baseline is the exact 6d combined-results receipt. Its rows for
these four seats are marked as decision-equivalent reuse of the frozen
Goose4 candidate; that provenance is recorded alongside the baseline values.
The outcome runner requires both THIRD seats to win. Both ChrisTu seats must
exactly preserve the frozen baseline result, own reward, rival reward, margin,
statuses, and frame count.

These are full 720-frame native fixed-tape games, not reactive-opponent
validation. They cannot support promotion by themselves.

## Frozen inputs and outcomes

The manifest binds the 5b derivative, exact 6d parent candidate, 6d combined
results and upstream manifest, 104-fixture parent panel, both selected replay
files and action tapes, the four bound source-trace provenance files, and the
passed four-seat prefix result, manifest, static preflight, and freeze receipt.
It also binds the Kaggriculture 1.32.7 engine source, extracted native
transition core, state/check helpers, replay cache loader and contents,
cached game helper, and existing lock helper.

The runner checks the step-1 public hand and pasture counts against both the
frozen census and the passed prefix rows. On every seat it requires the source
branch, source guard telemetry, reset-route-map check, active candidate,
720 frames, DONE/DONE status, and empty policy/engine error telemetry.

For both THIRD seats it additionally requires the runtime Brunch goose key,
route 113332529, and exactly 647 counted active turns after observation 72.
For both ChrisTu seats it requires the prefix-bound non-Brunch runtime key,
no Brunch route, zero leaf turns, and zero leaf errors.

The runner uses one sequential worker and acquires both
diagnostics/.shared_game_run.lock and a study-local lock. It refuses to
resume or overwrite any run directory or receipt. A failed/interrupted
attempt is preserved for review and cannot be restarted by this runner.

## Static freeze and review commands

These commands only hash and inspect frozen files, validate the prefix
receipt and compile the runner source. They do not call an agent or advance
the simulator:

    python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/outcome_run_20260929/build_outcome.py freeze
    python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/outcome_run_20260929/build_outcome.py verify

Only after root review and release of the shared game slot, the single
terminal run command is:

    python -X utf8 diagnostics/a44_goose4_smoothie_pasture_source_20260929/outcome_run_20260929/run_outcomes.py

No terminal outcomes were run during this freeze.
