# Ghost + Kwa combined 58-game fixed-tape diagnostic

## Question

Do the independently tested Ghost Ice wheat route and Kwa wheat-zero route
compose on their two activation fixtures while retaining the exact 6d result
on all inactive rows? The panel also measures the user’s top-20 replay goal.
This is a fixed opponent-action-tape diagnostic, not reactive qualification or
promotion evidence.

The candidate is SHA-256
`7b354498ef2f7213e24ecb332d92d291d9515b94b2a7a845058e829572c0fca2`, formed
by appending the frozen Kwa wrapper to the frozen Ghost candidate. The parent
is the exact 6d candidate
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

## Frozen panel and gates

The panel contains both seats for the 20 saved top-team fixtures and both
seats for a disjoint nine-fixture union: six selected loss fixtures, including
the Kwa and Ghost targets, plus three saved public wins. That is 29 fixtures
and 58 games. The four target seats are the two Kwa and two Ghost activations;
the remaining 54 seats are exact controls.

Every game must finish DONE/DONE at 720 frames with no policy errors. The Kwa
target must report the source branch, Brunch key, zero rival wheat plots,
route `113535489`, 647 active turns, and a win in both seats. The Ghost target
must report the source branch, Ice Cream key, public WHEAT stock at or below
9,975, route `113360743`, 647 active turns, and a win in both seats. The other
route layer must remain inactive on each target. All 54 controls must match
the 6d result, both rewards, margin, statuses, and frame count exactly.

The top-20 objective is a **both-seat fixture sweep**: at least 18 of the 20
fixtures must be wins in both seats. The panel records the goal metric and
threshold explicitly. Any failed gate rejects this candidate composition for
this panel.

## Evidence limits

All games replay saved opponent action tapes in the local native simulator.
Even a full pass establishes only this fixed-panel result. It does not
establish the 90% target over a broader set of latest replies, general win
rate, performance against reacting opponents, leaderboard score, or promotion
readiness. Keep `main.py` unchanged.

## Commands

Static freeze and verification only:

```powershell
python -X utf8 diagnostics/a44_ghost_kwa_combo_20260929/outcome_run_20260929/preflight.py freeze
python -X utf8 diagnostics/a44_ghost_kwa_combo_20260929/outcome_run_20260929/preflight.py verify
```

After reviewing the frozen package and confirming the shared game slot is
free, the one-shot run is:

```powershell
python -X utf8 diagnostics/a44_ghost_kwa_combo_20260929/outcome_run_20260929/run.py
```

The runner never resumes or overwrites a run.
