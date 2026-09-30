# Day-11 sheep commitment experiment — predeclared 2026-09-26

## Frozen baseline and mechanism

Incumbent is the local `main.py` SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The Kaggle entrypoint is its final `kaggle_main_entrypoint`; direct local
evaluation calls `agent`. Engine: `kaggle-environments==1.32.7`, 720 turns,
two seats, standard configuration, native seed and endogenous shops/market.
The September 25 and 26 top-100 saved-action panels (59/100 and 69/100
positive summed paired margins) are reused regression data, not validation.

The incumbent's six-sheep project requires at least two visible Yarn Stores.
The first intervention asks whether one visible Yarn Store can pay for the
**complete existing project**. The project buys SE land and six sheep for
7,000 coins, hires workers, buys wheat, builds pastures, places sheep, feeds,
cares, harvests wool/fertilizer, delivers it, and sells. The alternative uses
the incumbent's tested executor; it does not issue a sheep purchase alone.

Trigger: the first day-11 call to the existing sheep eligibility predicate
where exactly one Yarn Store is among the three shops already unlocked,
the existing predicate's other requirements hold (including wool quote,
wheat quote, land/occupancy, no duplicate project and next-day purchase
funding), and the only relaxed condition is its two-Yarn count. Every input
comes from the current legal observation and incumbent route state.

A: unchanged incumbent. B: a bounded, observation-only counterfactual
controller compares the fully funded sheep project against continuing the
incumbent's native route, including time-indexed capital/feed/worker
obligations, land/storage, sale dates and shared wool/fertilizer price paths.
It selects the project only if its estimated paired-margin gain is positive
under each of three future-Yarn scenarios; ties and model failures fall back
to A. C: the same feasible six-sheep executor is always allowed at the
trigger. C tests whether the controller adds value beyond a simple relaxed
shop gate. A/B/C differ at this single decision; all other route and market
layers remain identical.

## Falsifiable prediction, units and gates

Six sheep can produce roughly 24 saleable wool units per three-day cycle.
Four monetizable cycles at a 220-coin current quote give a gross upper
reference of about 21,120 coins before price impact. The 7,000 capital cost,
approximately 18 days of six wheat feed units (at a quote no greater than
45, up to 4,860 coins before price changes), worker wages, storage limits and
possible fertilizer receipts must be charged. A plausible net effect is
several thousand coins, enough to matter for close losses but unproven for
the largest losses. This is a scale argument, not an outcome claim.

Development native seeds: 2612000–2612015, both seats, each A/B/C against
the trusted incumbent `main.py`, with shops, rival actions and market free to
react. Each seed is one independent shop block; its two seat outcomes are
correlated. A mechanism-OFF wrapper must match direct `main.py` exactly in
both seats before treatment. Inspect own cash, rival cash, paired margin,
paired and seat wins, worst regression, triggered/confirmed projects,
invalid/no-op consequences and maximum measured call time. Do not expand
the development block or adjust the selector after looking at outcomes.

If B improves paired wins with no winning-control reversal, both seats DONE,
and no material downside, freeze it and run both saved top-100 regression
panels, then untouched consecutive native seeds 2612100–2612115, both seats.
The saved panels are fixed-action controls. Untouched native games provide
reactive confirmation against the trusted incumbent, not against the full
leaderboard. Promotion requires actual paired-win improvement on the
relevant broad panel and independent/reactive confirmation; cash gain alone
does not suffice. If B fails the development gate or never activates, reject
this mechanism and retain `main.py` without post-hoc tuning. No new Kaggle
submission is authorized by this experiment.

The existing `paired_benchmark.py` imports local agents in the same process,
so only the trusted local `main.py` and our new wrapper may be used for native
reactive tests. Saved opponent actions may be read as data, but unfamiliar
downloaded opponent source must not be executed by this runner.
