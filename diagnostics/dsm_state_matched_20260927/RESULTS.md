# Exact-state schedule bank pilot — 27 September 2026

Candidate d634bed3 uses 122 DSM schedules, 968 state/shop keys and a verified
root backup. Sources cover all eight first shops and 58 of 64 first-two-shop
combinations. At turn 72, 112 of 122 sources share one full farm/private
state; ten sources have six other states.

The frozen native pilot on seeds 2693000–2693007 completed all 16 games
against reacting c68 in both seats, DONE/DONE and zero errors. Result:
**2 wins, 14 losses, 0 draws**; mean seat margin -24,319.1. Exact-state
matches and source switches were zero in every game. Turn-72 captures show
the intended 9 wheat, 2 strawberry, 8 melon, 3 cow, 3 sheep farm, but shed
wheat is 5 rather than the dominant source state's 7.

**Reject the unchanged candidate under its original pilot gates.** Do not
run its conditional full replay or promotion panels. Main remains exact
uploaded c68fa46f. A targeted diagnostic on the already-used pilot seed
2693000 is being run to inspect every physical/private mismatch; it is
causal development evidence, not fresh strength validation. Any revision
needs a separate plan and fresh pilot seeds.

Evidence: PLAN.md, build_manifest.json, source_boundary_audit.json,
pilot.json, preflight.json and diagnose_prefix.py.

## Prefix diagnosis completed

On already-used seed 2693000, source and native cash differ by 13 after
turn zero. A missing wheat seed appears at turn 14, its planned plant at
turn 21 fails, and its eventual two-unit harvest is absent. At turn 72,
the only non-cash difference is shed wheat 7 versus 5. After the wheat sale
at turn 72, full private state matches at turn 73, but cash is 51 lower.
This is a funding failure, not a JSON/state-hash representation mismatch.
The unchanged installed engine (SHA bc8a5487) explicitly supports DROP at
line 343; no simulator edit is needed. A separate first-market-order
intervention is frozen in diagnostics/dsm_frontloaded_bank_20260927/PLAN.md.
The original failed decision remains unchanged.
