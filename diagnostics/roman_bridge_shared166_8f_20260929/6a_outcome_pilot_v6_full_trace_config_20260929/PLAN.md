# 6a + Roman fallback outcome pilot

This freeze supersedes the unrun v5 and first v6 drafts. V4's frozen inputs
were followed by a correction to the fallback-reason label; its source no
longer matched its manifest, so v4 is preserved but will not be executed. Luna
Max review found v5 sampled only four turns, and found the first v6 oracle
passed `None` instead of the native replay configuration. This package replays
every post-fallback turn and passes the same verified configuration as the
native runner.

This tests the fallback correction to v3. In v3, the adapter continued
calling the five-hand donor schedule until the day boundary, where the game
reset the hand list to zero. Its remapper rejected that shape, and the
fail-closed path passed for all remaining 695 turns. Both target games became
large losses. The v3 record is preserved in the adjacent package; it is not
reused as v4 outcome data.

V6 returns control to exact 6a whenever snapshot guards, donor execution, or
worker-count remapping fail. It records the reason and step. On this frozen
tape, the expected fallback is at step 24 after the normal zero-hand day
boundary. The pilot loads a fresh 6a parent, calls it once on step 0 to mirror
the candidate's opening call, skips steps 1 through 23 while the adapter owns
those turns, then feeds it every candidate observation from step 24 through
718 in order. It loads the same verified replay configuration as the native
runner and sets `seed` to `None` before every parent call, matching the actual
candidate invocation. It requires all 695 resulting parent actions to match
the trace. This preserves parent route state across the fallback period.
Candidate and adapter telemetry include the fallback count, step and reason.

## Objective

Test both seats of `live-114270587`, with both seats of
`public-win-114251368` and `top20-18-Kaggledew Valley 🏆-114273541` as controls.
Run six direct 6a baselines first, then six candidate games, for 12 full
native games. A candidate target sweep raises the current 26/30 loss panel to
27/30 only if both seats beat their 6a baselines while all controls remain
exact wins.

## Required order and gates

1. Verify the frozen inputs, runner/builder hashes, and shared simulator lock.
2. Run all six 6a baselines first. Require clean DONE/DONE at 720 frames,
   target losses, controls wins, and exact saved-panel matches where present.
3. Run the exact 6a opening prefixes for both target seats; require all
   source checks before discovering snapshots.
4. Discover both snapshots before validating either, then validate both fresh
   replays. Require own/public state, provenance, remapped action and two COW
   pickups by worker slots 3 and 4.
5. Only after all discovery and validation gates pass, write the fresh
   6a-bound snapshot ledger and run six candidate games.
6. Require both target seats to become positive-margin wins over 6a losses;
   exactly one parent fallback at step 24 because hands fall below the donor
   schedule's five-worker minimum; and
   matching 6a parent actions at every step from 24 through 718 (695 actions)
   after feeding the exact 6a parent the same step-0 call as the candidate.
7. Require all four controls to remain positive wins and match their paired
   6a results, rewards, margins, statuses and frames exactly. Require all
   games to finish DONE/DONE at 720 with no candidate errors.

Any failed gate rejects the candidate. Results are fixed-tape diagnostic
evidence only: no reactive qualification, independent validation, promotion
or Kaggle readiness is implied. `candidate.py` is an offline loader for
hash-bound workspace artifacts, not a standalone Kaggle submission. Root
`main.py` and Kaggle are out of scope.
