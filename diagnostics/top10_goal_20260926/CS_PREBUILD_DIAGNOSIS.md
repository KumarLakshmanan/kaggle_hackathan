# Cow-to-goose planner misses a prebuilt site — 2026-09-26

The current `main.py` already contains a cow-to-goose economic planner and
work-command rewrite. Its recorded source rule requires no unlocked milk
shop or yarn store. I exposed its existing `_CS_REPORT` through a
telemetry-only final wrapper, `exp_cs_observe_20260926.py`; that wrapper
changed no actions or outcomes. On the saved first-place Boey route under
the original shop sequence `PET_CAFE, BAKERY`, both seats ended with the
unchanged local -7,858-coin margin and `DONE` status.

In **both seats**, the planner reported `cs_decision=noplan@169`, with
estimated values `COW:-379,GOOSE:1216`. The value threshold favored goose
by 1,595 coins; the planner could not construct a valid rewrite from the
purchase turn. The prior passive event trace shows why: the two candidate
cow sites at `(6,4)` and `(5,2)` had already received `BUILD_PASTURE` at
steps 159 and 153, while cow purchases came at steps 169 and 176 and
placements at steps 177 and 182. Its `_cs_plan` searches for a build after
the purchase turn, so it correctly refused an incomplete late substitution.

This is a concrete **scheduling bottleneck**, not evidence that lowering
`_CS_RATIO` or `_CS_MIN_GAIN` would help. A viable experiment would have
to decide at or before the relevant build turns, then keep the structure,
animal purchase, pickup, placement, harvest, delivery, and sale actions
consistent. It must use public shops and the inherited route plan only,
with no episode ID or seed gate. Any candidate must verify the sites were
actually converted and the added eggs sold, both seats, original shops,
saved-route controls, and fresh reactive games. The current Boey tape and
the broader 100-route panel are development data.

Evidence: `cs_observe_boeyseed.json`, `cs_observe_tail.py`,
`build_cs_observe.py`, and the preexisting
`loss_trace_Boey_s0.json.gz`. **Decision:** diagnose and design a complete
early bundle; no `main.py` edit or Kaggle upload based on this observation.
