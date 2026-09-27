# Prefix recruitment implementation details

Recorded before any conditional recruitment results. Recruit with purchase-only
control in seat 0. Each seed runs four reference prefixes concurrently, but
admit cases in the frozen seed-major/reference order. Stop after the first
16 eligible cases; extra prefixes in the final four-reference batch remain
logged but are not admitted. No terminal outcomes are produced or inspected.

The environment keeps episodeSteps=720. A wrapper around Environment.step
raises a private stop exception outside agent execution after an eligible
observation or observation turn 288, before applying those actions. Thus
prefix truncation does not change the environment's horizon, shop behavior
or agent configuration. Both policies receive configuration.seed=None.

Actual funding activation means at least one seat in each selected paired
case; both seats are always evaluated and reported. A selected case with
neither seat active fails qualification. All original PLAN.md coverage,
win-point, completion and error gates remain unchanged.
