# Fresh public Step1009 native pilot — rejected

Completed 2026-09-27 08:22:19 UTC. Candidate SHA-256:
`55be5d5f124c8daaaa63c1a29ba4aab096004909666f04748007603c67b7d2a8`.
The public archive was statically extracted, its declared hashes verified,
and LICENSE/NOTICE preserved. Two newly updated notebooks contained this
same policy; they are one candidate, not independent corroboration.

## Frozen pilot result

- Eight fresh native seeds 2697000–2697007, both seats: **4 wins, 12 losses,
  zero draws** versus exact uploaded c68.
- All 16 games completed DONE/DONE over 720 frames.
- Mean seat margin: **-5,655.75** coins. Seat pairs had identical margins.
- **80 caught internal errors**, all `_S839_REPORT.errors`; no engine
  failure or disqualification. Other reported error counters were zero.
- Both policies received configuration seed `None`; the engine generated
  original shops and both policies reacted to the evolving game.
- Kaggle's final callable and module.agent both select the intended
  `step1009_step1008_fortyfirst_final_fixedsell_closure_agent`.

| Seed | Margin in each seat | Caught errors per game |
|---|---:|---:|
| 2697000 | -198 | 10 |
| 2697001 | -20,585 | 0 |
| 2697002 | -12,488 | 9 |
| 2697003 | -7,897 | 2 |
| 2697004 | +4,766 | 9 |
| 2697005 | +16,302 | 2 |
| 2697006 | -19,301 | 0 |
| 2697007 | -5,845 | 8 |

## Decision

**Reject the unchanged candidate.** It fails both the predeclared
12/16-point requirement and zero-error requirement. Do not run its
conditional replay panels or confirmation cohort. Preserve the exact
source and root backup for diagnosis; main.py remains c68. A repair would
be a separate candidate requiring a new frozen plan and untouched seeds.

Evidence: PLAN.md, build_manifest.json, pilot.json; source extraction and
license receipts in ../public_refresh_20260927_0812/step1009/.

Reproduction (already completed; pilot.py refuses to overwrite evidence):
`python -B -X utf8 diagnostics/public_step1009_native_20260927/pilot.py`
