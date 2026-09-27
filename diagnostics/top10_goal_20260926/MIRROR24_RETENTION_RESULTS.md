# Fresh mirror24 versus mirror12 retention check — 2026-09-26

The predeclared native block in `MIRROR24_RETENTION_PLAN.md` compared exact
current/uploaded `main.py` SHA-256 `489fe8e4...` against the prior uploaded
source snapshot SHA-256 `08aa268a...`, with both agents reacting and native
shops on seeds 2612600–2612623, both seats. All 48 games ended `DONE` and
candidate telemetry reported no errors.

The current source won **18 of 24 paired seeds**, lost five, and tied one;
it won 34 of 48 seat-games, lost 12, and tied two. Aggregate candidate margin
was **+14,326 coins**, with own cash 4,842,106 and reacting rival cash
4,827,780. The five negative paired margins were small (−186 to −6); the
largest positive was +2,582. The sale-advance branch activated in 46/48
games. The maximum measured candidate call was 459 ms on this local parallel
run. Raw result: `reactive_mirror24_retention24.json`.

**Decision: retain the current mirror24 local source.** This independent
reactive block agrees with the two earlier favorable blocks and meets the
predeclared retention criterion. The latest Kaggle submission's 2165.0 score
versus the older source's 2221.0 remains a live sample difference, not a
controlled refutation of the head-to-head result. This self-play result does
not demonstrate higher rank against the broader field: the team is still
rank 876 on its better older score in the 17:07 snapshot, and the current
agent still wins only 66 of 100 fresh fixed leader routes. No `main.py`
change or Kaggle upload occurred.
