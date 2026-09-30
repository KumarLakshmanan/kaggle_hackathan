# Frozen live-loss tape counterfactual — 2026-09-27

Use all 18 losses in the complete `cohort_164140.json` public episode listing
for submission 56609430, with no further outcome filter. Extract the 719
opponent actions from each exact raw replay. Run the exact uploaded 4eeac9c3
backup and exact preceding c68fa46f backup against the same opponent action
tape, seed, and native engine, with the agent in each seat: 18 × 2 × 2 = 72
games. Let the native engine generate the original seed's shops. Do not
override shops or edit an agent.

Before interpreting results, require the 4ee original-seat run to reproduce
both final cash totals and outcome from its Kaggle replay for all 18 episodes.
Require all 72 native games to finish DONE/DONE in 720 frames. Record hashes
for both agents, source replays, extracted action routes, and runner. Compare
paired W/D/L and relative cash margins over the 36 episode-seat pairs, and
report original-seat and swapped-seat outcomes separately. The fixed opponent
actions cannot respond to changed play; results are diagnostics, not an
independent estimate of reactive strength or a promotion gate.
