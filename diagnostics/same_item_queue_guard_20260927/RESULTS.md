# Same-item queue guard — 2026-09-27

The exact uploaded `main.py` was copied to `candidate.py` and augmented with
the frozen same-item guard in `PLAN.md`. Candidate SHA-256 is
`f8ba652449f657939272ce7946d22ddb757b56a5c017f62c035b6d6d024b873c`.
The main file remains unchanged at `4eeac9c3...f783ed`.

The targeted development screen used the fresh 16:35 UTC top-20 source
action tapes, each hash verified, in both seats under engine 1.32.7 with
native original shops. All ten games finished DONE/DONE/720. The guard was
active on 74–116 turns per game; it is not a no-op.

| Rival | Incumbent margin per seat | Guard margin per seat | Guard outcome |
|---|---:|---:|---|
| DECEM | -63,151 | -63,142 | loss/loss |
| Boey | -2,819 | -2,935 | loss/loss |
| Vadim Vasilenko | -5,821 | -5,790 | loss/loss |
| Majkel1337 | -77,373 | -77,365 | loss/loss |
| Yizhou | +66,082 / +64,024 | +66,072 / +64,014 | win/win |

The previously identified Yizhou queue/land threshold did not reverse:
its margin stayed close to 4ee rather than the earlier c68 result. None
of four required top-20 losses flipped. **Reject this candidate at the
predeclared targeted gate.** The conditional full top-20 and reacting native
panels were not run. Fixed action tapes do not establish broad policy
strength. No `main.py` edit or Kaggle upload occurred.

Evidence: `PLAN.md`, `candidate.py`, `targeted.py`, `targeted.json`, and
`../current_top20_20260927_163500/MATCHUPS.md`.
