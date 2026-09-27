# Additional check against the highest-scoring active upload

Frozen at 2026-09-27 01:17 UTC, before the pruned candidate's new terminal
confirmation outcomes. The 01:15 live snapshot shows submission 56590642
at 2,539.4 and rank 163, higher than younger 56591314 at 1,849.1. Age makes
those scores an imperfect strength comparison, but promotion should also
check the exact artifact currently carrying the team's leaderboard rank.

Run this stage only if the main 240-game native protocol passes. The rival
is exp_shunki_visible_repair_20260927.py, exact SHA-256
1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b.

Starting at seed 2650000, scan only the first 144 native turns against this
reacting rival. Select the first four seeds for each of the three retained
branches, max 2,048 scans, without generating terminal results during
selection. Play both current 3cc and candidate db981415 in both seats on
these 12 selected seed pairs: 48 complete native games. Require all DONE,
no lower candidate pooled win points than 3cc, and at least 8/12 paired
points for the candidate against this active rival. Incomplete coverage
is not a pass. Preserve exact hashes, all scan records, and seat activation.

No upload approval is available; this stage is a local promotion check.
