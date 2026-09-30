# Fresh-replay improvement plan — 2026-09-29

User request: continue improving uploaded cb76fbc4, target more than 90% wins,
use subagents if helpful, and download the latest replays. This request
authorizes collection and local research. A new upload needs a fresh request.

## Baseline and preservation

- Exact submitted source: `main_candidate_minimal_repair_20260929_cb76fbc4.py`,
  SHA-256 `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`.
- Root main.py remains `4eeac9c3`; preserve existing edits and past evidence.
- Make new candidates as standalone files in this experiment directory.
- Root coordinates games with the shared benchmark lock. Parallel agents
  collect data and audit code; they do not launch competing game batches.

## Data and outcomes

Collection directory: `../fresh90_refresh_20260929`. Freeze a new authenticated
leaderboard snapshot and the latest three available completed public episodes
per current top100 team, selected without outcomes. Record missing data and
duplicate episodes explicitly. Also collect currently available public episodes
of submission 56680167. Do not substitute yesterday's panel for current data.

The newest episode per team is the development panel. Evaluate both candidate
seats under the public episode's original initial state and native transitions.
Target: strictly more than 90% seat wins (>180/200 if all 100 teams available).
Report top20 separately (>36/40), draws/losses, number of teams won in both
seats, margins, and distinct episode counts. Rankings and these action tapes
are time-specific. Fixed tapes cannot react to changes in our policy.

Reserve second/third latest episodes until a candidate is frozen. These are
replay generalization controls, not independent policy validation. Shared
episodes can correlate teams and adjacent episodes can correlate shops.

## Development and qualification

1. Verify baseline bytes and run complete newest-episode baseline in both seats.
2. Diagnose mechanisms, using prior rejected experiments to avoid repetition.
   Favor executable resource/market decisions based on current observations.
   No hard-coded opponent names, episode IDs, seed lookup, or future shops.
3. Before candidate games, freeze each candidate source hash, hypothesis,
   focused pilot, controls, and decision threshold in its own plan/manifest.
   Reject a candidate on execution errors or materially worse win outcomes.
   Cash margins diagnose effects; wins/draws/losses determine strength.
4. For a pilot survivor, run all newest top100 cases and then reserved replay
   controls. Record each gain and regression against exact cb76 baseline.
5. Evaluate original-shop reacting games against cb76, ae349, public V35,
   and C95 in both seats. Development seeds: 22929001–22929008. Candidate
   and cb76 use the same seeds/opponents/seats. Require positive total point
   gain (win=1, draw=.5), no per-opponent aggregate point regression, at least
   six of eight nonnegative seed blocks, clean completion.
6. Verify full native framework parity and actual file-loader behavior in both
   seats on activated and control cases. Require exact actions/rewards and
   no timeout, schema, loader, or policy errors.
7. Only for a frozen survivor: untouched native seeds 22929101–22929132,
   four opponents, both seats, both versions (512 games). Require positive
   aggregate win-point gain, positive 95% bootstrap lower bound grouping all
   opponents and both seats per seed, no per-opponent aggregate regression,
   and clean execution. Do not extend this block in response to its outcomes.

An outcome panel used to select a candidate becomes development data. If an
independent panel rejects it, preserve that candidate and report rejection;
do not silently tune on that panel and keep calling it independent.

## Delivery

Keep all source hashes, frozen manifests, receipts, per-case results and
backups. Add dated findings and explicit promotion/rejection decisions to
agent.md. Deliver an improved file only with its measured scope and limits;
report honestly if >90% or independent qualification remains unmet. Saved
win percentages do not imply an online rating or top10 probability.
