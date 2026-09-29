# 6a + Roman two-seat outcome pilot

This freeze supersedes the adjacent `6a_outcome_pilot_20260929` draft before
any game runs. Its runner explicitly permits its own held one-shot lock during
the in-lock hash verification; all other runtime outputs must still be absent.

## Objective

Test a fresh composition of exact 6a with the shared166 Roman opening adapter
on both seats of `live-114270587`. Use both seats of `public-win-114251368`
and `top20-18-Kaggledew Valley 🏆-114273541` as near-miss controls. Run six
direct 6a baselines first, then six candidate games, for 12 full native games.

The current 6a panel is 26/30 loss sweeps and 19/20 top20 sweeps. A Roman
target sweep would raise the saved loss panel to 27/30 while retaining the
top20 target, but only if this candidate actually wins both target seats and
preserves the controls.

## Required order and gates

1. Verify the frozen package and current shared simulator lock.
2. Run all six 6a parent baselines first. Require clean DONE/DONE at 720
   frames, target losses, and control wins. On the target and top20 control,
   require exact agreement with the hash-bound completed 6a panel.
3. Before adapter discovery, run exact 6a baseline prefixes for both target
   seats and require all recorded step-0 through step-2 source checks.
4. Discover snapshots for both seats before validating either one. Require
   the fresh 6a post-HIRE own state, rival farm, and market to match the
   historical V5 snapshot values and the complete HIRE projection.
5. Validate both fresh snapshots on new 6a replays. Require provenance,
   own/public merge guards, remapped donor action, two COW pickups by worker
   slots 4 and 5 (zero-based indices 3 and 4), and ACTIVE states.
6. Only after both snapshot validations pass, write the new 6a-bound snapshot
   ledger and run six candidate games.
7. Require both target seats to change from 6a losses to positive-margin
   wins. Both controls must remain wins and match their paired 6a results,
   rewards, margins, statuses, and 720-frame completion exactly. Confirm
   Roman activation occurs only on the target and all games finish cleanly.

Any failed gate stops dependent work and rejects this composition. The run is
fixed-tape diagnostic evidence only; it does not establish reactive strength,
independent validation, promotion, or Kaggle readiness. `candidate.py` is an
offline loader for hash-bound workspace artifacts, not a standalone Kaggle
file. Root `main.py` and Kaggle are out of scope.
