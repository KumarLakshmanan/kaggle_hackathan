# Fresh current top-20 replay assessment — frozen 2026-09-27 16:35 UTC

The user requested a new official leaderboard top-20 snapshot, each team's
latest completed public episode, and exact current `main.py` against all 20
recorded action tapes in both seats. This is a read-only strength assessment;
it does not change the policy or upload a submission.

The candidate is SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`,
uploaded as Kaggle submission 56609430. Preserve a byte-exact local copy
before games. Freeze the 20 distinct team IDs at ranks 1–20 in the newly
downloaded official CSV. For each, query current team submissions, choose
the highest publicly scored active submission (newest submission breaks a
tie), then query episodes and choose the newest completed public episode by
creation time without outcome filtering. If it is not a 720-frame DONE/DONE
episode, document the structural failure and try the next most recent. Do
not substitute a prior panel's episode.

Store the original CSV and compressed replay bytes with SHA-256 receipts,
submission and episode listings, source timestamps, source seat and seed,
719 static actions and their hashes. Never execute downloaded code. Use
native Kaggle engine 1.32.7 with the source seed and original shop generation.
Run two games per team, candidate in each seat. Count win/draw/loss by final
bank coins and both-seat sweeps. Require all 40 games to complete 720 frames
with DONE/DONE and zero recorded agent errors. Compare overlapping source
episodes with observed public cash totals when available, and record whether
native shops diverge from the source by turn 144. Treat fixed tapes only as
replay diagnostics, not independent evidence of strength against reacting
private policies.

Decision: Accept the assessment as complete only if all 20 selected teams
are represented and all 40 games finish cleanly. Report exactly which teams
are not swept; no policy promotion decision follows from this fixed-tape
panel alone.

## Added paired control before its run

At 16:43 UTC, the root task requested a diagnostic comparison with the prior
uploaded c68fa46f policy. Freeze the same 20 action tapes, same source seeds,
both seats, native original shops and the immutable
`main_uploaded_disjoint_integrated_20260927_c68fa46f.py` (SHA-256
`c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad`).
Run 40 more games and report paired changes in outcomes and margins. This is
a controlled replay comparison, not independent reacting-policy validation.
