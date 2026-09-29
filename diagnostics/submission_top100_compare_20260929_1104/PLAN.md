# Frozen comparison: submitted files and current top 100

Snapshot: authenticated Kaggle leaderboard API, 2026-09-29 11:03:38 UTC,
exact 100 distinct teams. Freeze team IDs and order in `leaderboard.json`.
Own submission listing is `submissions.json`, collected in the same read-only
snapshot. These results will not be used to change the policy during this run.

## Files

Use exact downloaded submission bytes from the authenticated Kaggle submission
download API, each bound by SHA-256 in `downloaded/download_receipt.json`:

- 56668607 (2026-09-29 08:11:57 UTC) and 56666114 (06:55:03 UTC): exact same
  ae349d83 bytes; run once and attribute the test result to both uploads.
- 56662188 (04:09:22 UTC): 257f941d, distinct earlier version.
- 56609430 (2026-09-27 13:10:15 UTC): 4eeac9c3, older research main.

Verify each downloaded file's digest against the locally preserved source, but
run downloaded bytes. Keep each Kaggle submission's public score and timestamp
as its own time-specific observation. Do not treat different opponent histories
as a controlled head-to-head rating comparison.

## Opponent selection and local comparison

For every frozen top-100 team, query its currently listed submissions, choose
the highest-scoring entry (latest submission breaks ties), then choose its
most recent completed public 720-frame DONE/DONE episode without using the
outcome to choose. Download and hash the raw replay and extracted action tape.
If an episode is malformed, document it and try the next newest. If retrieval
fails transiently, retry the same team; keep unavailable teams in the
denominator as missing rather than replacing them. Private opponent source
files are not needed or assumed available.

Run each distinct downloaded own file against the same 100 frozen opponent
action tapes, original recorded seed, native original-shop generation, and
both candidate seats: 200 games per distinct file, 600 total if coverage is
complete. Freeze the candidate hashes and opponent action hashes before games.
Record native outcome, both rewards, margin, frame/status/error and timing.
Require 720 frames and DONE/DONE in each complete game.

Compare by opponent both-seat win sweeps and seat wins/draws/losses for top 10,
50 and 100; report ties and missing coverage. Treat both seats of a fixture as
one paired observation for any improvement claim. Use paired own-minus-rival
margin for mechanism diagnosis, not own cash alone. If counts tie, do not
manufacture a winner from mean cash or old ratings. A policy with strictly
more both-seat sweeps and no offsetting loss in W/D/L has the stronger result
on this frozen panel; otherwise report the tradeoff.

Fixed opponent tapes cannot react to changed shops, prices or our actions.
This test cannot prove a live rating or top-10 result. Original-shop native
games against multiple reacting agents are a separate promotion gate; this
task requests comparison, not a strategy change or upload.

## Method amendment, 2026-09-29, before the complete top-100 result

The full native runner was much slower than expected. Its completed prefix is
preserved in `local_results.jsonl` and will remain labeled incomplete. Before
changing the method, the pure native-transition diagnostic engine was checked
against the exact full native results for the first three complete snapshot
ranks: three distinct uploaded files, both seats, **18 cases**. Candidate and
opponent rewards, W/D/L, DONE statuses, 720 frames and complete policy
telemetry matched on every case; see `fast_native_parity.json`.

Use the same frozen 100 teams, action tapes, seeds, files, seat pairs and
comparison criteria above. Run a new, complete 600-case panel with the
native-transition diagnostic engine in `fast_game_current.py`, using replay
initial frames verified by `current_input.py`. The engine bypasses Kaggle's
file loader and framework timing, so this panel is a local fixed-tape
comparison, not 600 native Kaggle-loader validations. Preserve the initial
native prefix and report its coverage and parity separately. The method
switch is motivated by execution time; it does not select or exclude cases
based on their outcomes. No candidate source or opponent selection changes.

## Execution update

Automatic approval review blocked stopping the already running native
coordinator; the rejection did not provide a detailed reason. No process or
result was changed by that attempt. The native coordinator continues toward
all 600 games. Use its complete native results for the final comparison. The
18-case fast parity pilot remains separate supporting evidence; the proposed
fast full-panel runner was not started. The original selection and comparison
criteria still apply.
