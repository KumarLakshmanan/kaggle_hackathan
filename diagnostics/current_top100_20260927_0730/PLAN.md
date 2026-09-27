# Current top-100 assessment — 27 September 2026

The user requested today's current top 100 after the approved c68 upload,
explicitly excluding yesterday's leaderboard panel as the assessment source.
Freeze the fresh official CSV snapshot at 2026-09-27 07:27:24 UTC, its top
100 distinct team IDs, and exact uploaded c68fa46f bytes before testing.

For each selected team, query its active public submissions now and select
the higher public score (most recent submission breaks a tie). Query that
submission's episodes now. Select the latest completed public episode by
creation time, without looking at rewards. Require 720 frames and both
agents DONE. If the latest completed episode is structurally invalid, record
the reason and try the next most recent; never substitute a different team.
Record unavailable sources and coverage rather than calling missing tests wins.

Download those selected sources into this new collection. Retain raw bytes
losslessly as gzip, verify a decompression hash, and preserve selection
listings, submission IDs, snapshot ranks, timestamps, seeds and action hashes.
Only delete newly downloaded temporary files after verified compression.
Do not reuse yesterday's panel membership or its test results.

Run exact uploaded main.py in both seats against every selected action tape,
using its recorded native seed, 720 turns, and the engine's original shop
generation. Freeze c68 bytes for this assessment; no policy tuning during
the run. Record all outcomes, completion status, errors and timing. Report
top-10, top-50 and top-100 coverage, both-seat sweeps and seat wins/draws/losses;
list every non-swept team. Group paired seats together for interpretation.

These are new measurements against recent recorded games, not the private
reacting agents of the live teams. Their recorded actions cannot adapt to
changed market conditions or shops. This assessment cannot predict a live
rank or independently qualify a tuned replacement. The earlier 50-team
panel remains archived regression evidence. Native reactive qualification
and fresh explicit upload authorization remain required for any later change.

Decision after this assessment: pass the all-top-100 replay target only if
100/100 teams are covered, 100/100 are beaten in both seats, all 200 seats
win, and all games finish DONE. Otherwise preserve the exact failures as
the next development evidence; do not alter this criterion after results.
