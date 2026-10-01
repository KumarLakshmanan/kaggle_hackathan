# Executable search engine — frozen first experiment, 2026-09-30 IST

The user requests a new engine that generates strategy decisions and an agent
that improves on existing opponents. Universal wins cannot be promised.

## Architecture and scope

Generate action programs rather than selecting among archived strategy files.
Use copied exact native transitions for movement, work, supplies, purchases,
market settlement and day boundaries. Offline beam search generates local
production actions and market sequences, and reports scenario coin outcomes.
Unknown rival private stock and future randomness are explicitly hypothetical.

The first deployable candidate retains exact root 4ee's complete worker
schedule, and searches market order movement/splitting/merging to depth3 with
48 nodes and width3. Require identical resulting physical/private state for
both players, no own cash decline, and no coin-margin decline in each of three
scenarios (idle, mirror, frontloaded mirror with additional stock). Accept only
a positive summed margin gain. This is one-turn search, not complete farm
strategy invention. The offline broader planner is experimental and its
approximate leaf valuation is not a win probability or season forecast.

## Frozen qualification

Baseline is root `main.py`, exact4eeac9c3. Preserve a byte-identical backup.
The builder binds baseline, core and engine hashes to a standalone candidate.
No file promotion or Kaggle upload occurs on creation.

1. Verify physical stock forecasting and native-core parity on synthetic
   initial/midgame states in both seats, market lockstep, capacity and planting.
2. Development pilot: native transitions on seeds33000001–33000004 against
   reacting4ee and cb76, both seats; include matched baseline games:32 games.
   Require clean games, positive aggregate point gain, no per-opponent point
   decline and activation in at least two distinct seeds. Reject no-gain.
3. Saved current top20 from snapshot2026-09-29 22:34IST, both seats for
   baseline and candidate:80 games. Require no total point decline. The
   snapshot is saved evidence, not refreshed or independent validation.
   If this passes, complete the same saved top100 panel (400 version/seat
   games total, reusing the identical80 top20 cases). Require no aggregate
   point decline and report every lost and gained seat. This extension is
   declared before any saved candidate outcomes and addresses the user's
   request to assess all saved leaderboard opponents.
4. For a survivor only: fresh seeds33000101–33000116, four reacting policies
   (4ee, cb76, publicV35, publicC95), both seats, both versions:256 games.
   Require positive point gain, positive whole-seed95% bootstrap lower bound,
   no per-opponent decline, clean native completion and framework/file-loader
   checks in both seats with full action/reward parity before promotion.

Freeze new source and new test blocks for any later result-informed revision.
Do not tune on rejected independent blocks while claiming independence.
Record all cases, coins, runtime and source hashes. A complete engine delivery
can be rejected for competition promotion if it fails the frozen comparison.
No upload is authorized by this request; AGENTS.md requires a fresh upload request.
