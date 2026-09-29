# Native log counter correction — 2026-09-29

The second launch completed its first direct native Pet target game in seat
0 with DONE/DONE and 720 frames, then stopped at the checker assertion
`len(env.logs) == 719`. No file-loader game was started and no parity receipt
or Kaggle upload was produced. The prior checker, builder, plan, manifest and
static freeze are preserved here.

The installed engine's `core.py` appends initialization logs in `reset()`
(line 359), and `run()` resets an initial environment again (line 320).
Therefore the count of all log records includes initialization records.
Actual agent-call records have the `duration` field emitted by `agent.py`
lines 208–212. Root corrected the checker to count those records separately
for each player, still requiring exactly 719 calls for both, and to retain
the raw log count. Direct mode also checks the TimedAgent's 719-call counter.
All original 719-action parity, result, status and runtime checks remain.

The same six-seat/twelve-game scope and candidate are retained. Failure
diagnostics and per-game progress were added so any further mismatch retains
its observed values. This is a measurement correction, not a policy edit or
a waiver of an agent execution failure.

Archived manifest: `7e72f95d7229ccb14d97e3723023418becde7dec6d0dc880323793784d680872`.
Archived freeze: `6f3ed58c19edcd48f56a57ca9c912f09b0df23d56d7384a1722f24e0092a0c56`.
