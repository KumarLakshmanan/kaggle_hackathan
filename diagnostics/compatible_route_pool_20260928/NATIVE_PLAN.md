# Prospective qualification of a selected compatible route policy

Frozen 2026-09-28 before any reacting outcome for this route pool.
The deterministic selection rule remains in PLAN.md, with control coverage
corrected by CONTROL_FIX.md. Freeze selected source bytes in selection.json.

## Full saved panel

Only a corrected development selection passing its top-20 rescue gate may
proceed. Run its single packaged file on all 50 saved fixtures in both seats
with the native 720-turn engine and hidden configuration seed. The rewards
must equal the chosen component on each affected fixture and the incumbent
on every unaffected fixture. Require no errors, no lost incumbent winning
seat, and at least one new both-seat win. This is integration/regression,
not independent validation. Main remains unchanged.

## Independent reacting references

- Current main, SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- `public_market_smart_f6a756cf_20260927.py`, SHA-256
  `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.

These are two distinct reacting policies. Use original shop generation,
engine 1.32.7 and a 720-turn configuration throughout. Hide the configuration
seed from every agent. Both candidate and incumbent are reloaded per game.

## Eligibility scan, without final outcomes

The candidate changes only selected two-shop map branches from step 144;
its full earlier action prefix is exactly the incumbent's. To test the rare
branch with enough actual activation, scan unmodified incumbent/reference
games only through observation 144. Save only the first two shops and
completion/error metadata. Do not inspect final rewards to select seeds.

Pilot scan seeds 2909000–2909255 inclusive, in ascending order. For each
reference take the first **four** seeds where both seats reach a selected
shop-pair branch. Scan seat 0 first; only a seat-0 hit needs the seat-1
check. Reject that reference/seed if either seat is inactive. Confirmation,
conditional on pilot pass, uses 2910000–2910511 inclusive and the first
**eight** activated seeds per reference. These ranges had no prior use in
local research scripts/plans before this plan. Report activation frequency
and distinct seeds; this is a conditional activation panel, not a random
estimate of overall leaderboard performance. If either bounded scan lacks
the required number, report insufficient activation and do not extend it
after viewing strength outcomes.

## Win-rate gates

For every selected reference/seed, run unchanged incumbent and candidate
against the reacting reference in both seats. Pilot: 32 full games;
confirmation: 64 full games. Require all DONE/DONE/720 and zero recorded
policy errors. Candidate activation must occur in both seats of every
selected pair. Wins=1, draws=0.5, losses=0.

Pilot must have no reference-specific win-point regression and strictly
positive pooled win-point improvement. Otherwise reject the exact candidate
and do not tune on these seeds. Confirmation requires the same conditions
and a strictly positive lower endpoint of a 95% percentile bootstrap
interval for paired win-point improvement. Resample whole distinct seeds,
keeping both seats and all reference matches for that seed together, 10,000
times using RNG seed 2910599. Each bootstrap statistic is summed win-point
delta divided by the number of candidate seat games in the sampled seed
blocks. No margin-based rejection is added when win-rate gates pass.

A mathematically irreversible gate failure can end a run early, with the
bound and incomplete game count recorded. Each checkpoint job is counted
once and an exclusive coordinator lock prevents duplicate launches.

Before promotion, also preserve the 54 previously saved public wins and
pass both-seat local Kaggle file-loader checks. Freeze that regression's
hashes before running it. Back up main, update research memory, and perform
no Kaggle access or upload. The full user goal remains all 30 loss replies
and all 20 top-team replies won in both seats; a partial repair does not
complete the goal.
