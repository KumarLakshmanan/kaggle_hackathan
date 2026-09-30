# Fresh overall win-rate reassessment

Frozen 2026-09-27 02:30 UTC, before evaluating these seeds. The exact
candidate remains a2d2869c1d53bcfcedc8514d004f73bbab27ec6ef22b34d23241e718e4c1bf47.
No source changes or new parameters are selected from the original native
results. That protocol did not qualify the artifact, because it demanded
an extra win against two historical/public controls; their win counts tied.
Its 128 wins against current 3cc and best-active 1f were excluded from that
pooled-gain measure. This new protocol directly measures overall win points
against all four policies, consistent with AGENTS.md's competition objective.

Use untouched native seeds **2672000–2672015**, both seats, original shops.
Evaluate old 3cc and new a2 separately against each of:

1. Reacting current 3cc (including the old self-play control).
2. Actual leading active 1f (including old-versus-1f control).
3. Historical 489.
4. Public C95.

Total: 16 seeds × 2 seats × 4 opponents × 2 versions = **256 games**.
Reload modules each game. Preserve both seats and all four opponents in
whole-seed statistical blocks. Score wins 1, draws 0.5, losses 0.

Promotion criteria, all required:

- All games DONE/DONE; zero candidate queue errors.
- Candidate has no fewer win points than old against either 489 or C95.
- Candidate earns at least 12/16 paired points against each 3cc and 1f.
- Candidate pooled points exceed old across all four equally weighted
  opponents, and the 95% percentile interval from 10,000 whole-seed bootstrap
  draws has a strictly positive lower bound (bootstrap RNG seed 2672999).
- Keep the completed 43/50 replay sweep result, with no old sweep lost.
- Both-seat file-path/direct loader parity for the exact candidate bytes.

The four references are available benchmark policies, not a random sample
of all live opponents; 3cc and 1f are closely related. This study cannot
guarantee a live rank or a win against every opponent. The goal of 50/50
and top 10 remains separate and unmet. No upload is authorized by this plan.
