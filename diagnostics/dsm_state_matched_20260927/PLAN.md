# Exact-state schedule bank — prospective experiment, 27 September 2026

Previous goal turn made verified progress: c68 was uploaded with fresh
authorization, validated remotely, and tested in 200 new current-top-100
games. It scores 77/100 both-seat sweeps (36/50 for the current top 50), so
the live-top-10 and all-top-50 objectives remain incomplete.

## Candidate definition, frozen before native games

Use every one of the 121 structurally eligible DSM submission 56582621
episodes in the completed collection manifest, plus that same submission's
new source from today's fresh top-100 manifest. Deduplicate by episode ID.
No reward filtering or source ranking by terminal cash. Order sources by
creation time descending, breaking ties by episode ID descending. Default
to the complete schedule of the newest source.

At turns 72, 144, ..., 648, key the currently observed revealed shop prefix,
the full current own public farm excluding only money, and all own private
supplies. Hash canonical JSON. Switch to the newest source whose recorded
boundary matches that exact key, otherwise continue the existing complete
schedule. Preserve all recorded action quantities and execution commands;
this first experiment contains no market or worker repairs. Return deep
copies. Reset selection on step zero. Count errors, exact matches, source
switches and turn-72 compatibility. The runtime uses no seed, rival identity,
hidden rival supplies, or actual future shops. Future scheduled actions are
offline plans and do not imply knowledge of future observations.

The build manifest must freeze source hashes, the exact candidate hash and
a root-folder backup before playing games. Audit the number of distinct
turn-72 farm/private states and observed first/second-shop coverage. Neither
those passive statistics nor a source's leaderboard score establish strength.

## Native pilot

Use fresh seeds 2693000 through 2693007, both seats, against exact uploaded
c68fa46f. Use engine 1.32.7, original native shop generation and 720 turns.
All 16 specified games run and are reported; no outcome-driven seed changes.

Pass only if all games finish DONE/DONE with 720 frames and zero candidate
errors; candidate earns at least 12/16 win points (draw = 0.5); exact
turn-72 source compatibility occurs in both seats on at least six of eight
seeds; and at least one actual source switch occurs in both seats on at
least six of eight seeds. Keep paired seats together. Cash margins diagnose
mechanisms but have no separate rejection threshold. Failure rejects this
candidate unchanged; preserve results and use a separate plan for a revision.

## Conditional development and qualification

Only after the native pilot passes, run all 100 current-team tapes in both
seats and all 50 earlier regression tapes in both seats. These are development
panels, with no reuse permitted for this new policy. Require more than 77
current-top-100 sweeps, more than 36 current-top-50 sweeps, and at least 44
earlier-top-50 sweeps; report every gain and every lost incumbent matchup.
The objective remains winning all required matchups, not these interim gates.

If those gates pass, freeze an untouched native confirmation on seeds
2694000 through 2694015. Run old c68 and this unchanged candidate against
four reacting references: c68, 1f221922, historical 489fe8e4 and public C95,
both seats (256 games). Require all DONE and zero candidate errors, at least
24/32 new points against c68, no reference-specific point regression versus
old c68, and a positive lower bound on the pooled paired-seed win-point
gain in a fixed 10,000-resample percentile bootstrap (random seed 2694099).
The same seed resample includes both seats and all four references.

Require final file-path parity in both seats before any promotion. Preserve
current main.py and its uploaded backup throughout research. Any new upload
requires fresh explicit user authorization; the c68 approval is consumed.
