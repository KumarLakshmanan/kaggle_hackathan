# Fast reacting harness engineering parity — 2026-09-28

Extend the already transition-verified pure native core to two reacting
local policies. Policies receive only their own private state, public
observations and a configuration with seed hidden. The simulator alone
uses the offline seed. Use a saved step-zero template and verify it
against a newly initialized local native environment before any games.

Repeat eight already-known native pilot games, both seats of each:
4ee vs 4ee seed 2909021; b6eb vs 4ee seed 2909080; b6eb vs market seed
2909080; and 4ee vs market seed 2909112. Compare terminal rewards,
statuses, 720-frame count and complete candidate telemetry to the
existing native_pilot.json. Require exact equality and no errors in
either policy. These repetitions are engineering tests and add no
independent strength evidence. If a policy has time-dependent behavior,
report any mismatch rather than treating it as exact.

Accept the helper only for development or outcome-blind prefix selection.
It does not replace original-framework strength, schema, runtime or file
loader checks. Any future selection still requires its own prospectively
frozen candidate hashes, ranges, activation rule and gates. No Kaggle.
