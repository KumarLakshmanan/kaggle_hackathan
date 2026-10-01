# Professional engine v2 — results

Generated 2026-09-30T18:52:52.333971+00:00. No Kaggle access or upload.

## Changes

Implemented public-state opponent beliefs, executable whole-portfolio scheduler, varied future-shop/reacting-rival scenarios, group-separated fitted value model, isolated native transition caching, bounded queue/macro search and source-bound qualification.

Engineering:216 exact native/cache parity cases and seven focused probes pass. Fitted heldout coin RMSE5053.28 vs5938.84 cash-only; Brier0.16387 vs0.23978. Cached repeated transitions were1.65x faster in the focused local benchmark. The twelve-day online macro probe completed2592 transitions in4.918s; it selected no switch.

## Paired results

| Panel | Version | Wins | Draws | Losses | Win points | Mean relative coins | Physical turns |
|---|---|---:|---:|---:|---:|---:|---:|

Saved top20 is contained within top100. Saved opponents replay fixed actions, share episodes and overlap older model research; these are diagnostic preservation controls. Only fresh reacting/native confirmation can support promotion.

## Decision

Screen survivor: None. Promotion eligible: False.

Root main identity is recorded in DECISION.json. This report does not automatically promote a candidate. The physical controller is experimental unless it actually activated and qualified. Future itinerary forecasts are approximate; fitted tails and stock/demand hypotheses carry uncertainty. There is no guarantee of every-opponent wins or a top10 leaderboard rank.

Every game: [ALL_CASES.csv](ALL_CASES.csv). Frozen sources, per-case telemetry and manifests are retained beside this report.
