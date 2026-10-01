# Professional engine v2 — results

Generated 2026-09-30T21:59:29.225321+00:00. No Kaggle access or upload.

## Changes

Implemented public-state opponent beliefs, executable whole-portfolio scheduler, varied future-shop/reacting-rival scenarios, group-separated fitted value model, isolated native transition caching, bounded queue/macro search and source-bound qualification.

Engineering:216 exact native/cache parity cases, an adversarial empty-order parity probe and seven focused checks pass. Fitted heldout coin RMSE5053.28 vs5938.84 cash-only; Brier0.16387 vs0.23978,73 training/11 heldout episode groups. Cache speed is workload-dependent: the repaired-build repeated-transition probe was0.02059s cached versus0.01008s uncached. No general speedup is claimed. The twelve-day online macro probe completed2592 transitions in4.158s; it selected no switch.

## Paired results

| Panel | Version | Wins | Draws | Losses | Win points | Mean relative coins | Physical turns |
|---|---|---:|---:|---:|---:|---:|---:|
| screen | baseline | 24 | 8 | 0 | 28.0 | 10198.7 | 0 |
| screen | full | 30 | 0 | 2 | 30.0 | 10140.6 | 0 |
| screen | market | 30 | 0 | 2 | 30.0 | 10140.6 | 0 |
| top20 | baseline | 32 | 0 | 8 | 32.0 | 42770.9 | 0 |
| top20 | candidate | 32 | 0 | 8 | 32.0 | 42772.6 | 0 |
| top100 | baseline | 136 | 0 | 64 | 136.0 | 30409.2 | 0 |
| top100 | candidate | 136 | 0 | 64 | 136.0 | 30295.5 | 0 |
| confirm | baseline | 94 | 30 | 4 | 109.0 | 9104.9 | 0 |
| confirm | candidate | 122 | 0 | 6 | 122.0 | 9193.8 | 0 |

Saved top20 is contained within top100. Saved opponents replay fixed actions, share episodes and overlap older model research; these are diagnostic preservation controls. Only fresh reacting/native confirmation can support promotion.

## Decision

Screen survivor: market. Promotion eligible: True.

Whole-seed paired point-rate gain: 0.101562;95% interval [0.0625, 0.125].

Root main identity is recorded in DECISION.json. This report does not automatically promote a candidate. The physical controller is experimental unless it actually activated and qualified. Future itinerary forecasts are approximate; fitted tails and stock/demand hypotheses carry uncertainty. There is no guarantee of every-opponent wins or a top10 leaderboard rank.

## Offline physical forecast tools

The twelve-day offline interface now defaults to a compatible maintenance control and rejects unsupported fitted-control forecasts. A separate full-season mode needs no executor/value model and records actual native terminal coins, harvested units, peak assets/land and established/matured commitments under hypothetical rivals. It completed18 scenario seasons /10350 transitions; wheat, carrot, cow and land+crop expansions were all rejected against maintaining the existing farm. A double-harvest control counts four wheat units once, matching native; partial budgets cannot select. These are engineering/forecast checks, not competitive qualification. Frozen agent sources were not changed by the tool refinements. Source-bound details: `season_verification.json`, `offline_full_season_verified.json`.

Every game: [ALL_CASES.csv](ALL_CASES.csv). Frozen sources, per-case telemetry and manifests are retained beside this report.

## Exact-byte local promotion

Promoted 4ea1d89ac99758c6219bcd7d07b729de4dc5836260a25037ca973343b46c6289 to root main.py after every frozen gate. Old bbff and candidate preserved in root. No Kaggle upload.
