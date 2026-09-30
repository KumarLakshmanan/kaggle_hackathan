# Prospective reacting qualification — frozen 2026-09-28

Proceed only if exact candidate
`068030868689db5eb1e9a4a4427bededa8fbc13cae14e1003eb6be5440a6da42`
passes `native_full.json`. No fresh strength outcomes have been run under
this plan. Use only local engine 1.32.7, original shops, 720-turn games,
hidden configuration seed and fresh policy modules in each game.

## References and component control

Reacting references are current 4ee main
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`
and `public_market_smart_f6a756cf_20260927.py`
`f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.
For every selected reference/seed/seat, compare three candidate arms:
current main, route-only d271754e, and new 06803086. The route-only control
is SHA `d271754e609f1f089ea80d60186c24b4d14e357720ace34a47aa584c081504ed`.
It distinguishes gains from the partial-plant guard from route-only gains.

## Outcome-blind coverage selection

Pilot range: **2920000–2922047**, first two both-seat seeds in each stratum
per reference. Confirmation, only if pilot passes: **2923000–2927095**,
first four both-seat seeds in each stratum per reference. These ranges had
no previous occurrence in local research markdown before this plan.

Run only the new candidate/reference prefix through observation 336,
recording statuses, shops at 144 and telemetry, never terminal outcomes.
Seat 0 first, opposite seat only after a needed hit. Select ascending seeds
independently per reference and stratum:

- **Route branch:** both seats show YARN_STORE/FARMERS_MARKET at 144.
- **Other guard activation:** both seats have a different first-two shop
  pair and at least one partial-plant guard activation before 336.

The strata are disjoint. Route-branch activation and actual guard
activation are reported separately. If the finite range lacks any required
coverage, do not advance or promote. This is a deliberately conditional
panel, not a population estimate or a leaderboard-score forecast.

The pure native prefix helper may accelerate selection only after its
eight-game engineering parity passes. Freeze helper SHA
`4f6061926f07402c87112e44d8ee28551dc62773b8141a89cba1c5744a6ecba9`,
core SHA `5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795`,
and initial-template SHA
`7d300be7e59ecd210eb8df5ad503c3971f6d869dee593daeffec1b3224cee7e1`.
Before strength, repeat every selected prefix through the original native
framework in both seats, requiring exact shops/telemetry/status/frame
parity and zero policy errors. A mismatch stops qualification.

## Win-point gates

The pilot has 8 reference/seed pairs and **48 full native games** across
three arms and both seats. Confirmation has 16 pairs and **96 games**.
All games must be DONE/DONE/720 with no recorded errors. All selected
other-guard cases must retain guard activation; route cases must retain
route activation. No reference may lose new-arm win points relative to
either current main or the route-only control. Require strictly positive
pooled win-point gain against both controls in each stage.

Confirmation also requires strictly positive lower endpoints of two
95% paired-seed bootstrap intervals, one against each control: 10,000
draws, RNG 2927099; resample whole distinct seeds together, keeping both
seats and all reference games using that seed. Normalize by new-arm game
count. Report per-stratum W/D/L and paired cash changes diagnostically;
do not add a cash-only veto after observing results. Early stopping is
allowed only when a per-reference gate is mathematically impossible.

Before promotion, freeze/pass all 54 saved public-win regressions and
both-seat local file-loader checks. Preserve main and root backups. This
plan authorizes no Kaggle access or upload. The 50/50 user goal remains.
