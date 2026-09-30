# Fresh physical-opening router plan (frozen before candidate generation)

## Scope and source freeze

This is a static architecture experiment using only the 100 newest
completed-public episode tapes from the 2026-09-29 17:04:23 UTC leaderboard
snapshot. It must not read `routes/episode_2/` or `routes/episode_3/`, use
episode outcomes, access Kaggle/network, run the game engine, or modify
`main.py`, `agent.md`, or any prior diagnostics. Source summary:

`diagnostics/fresh90_refresh_20260929/routes/development_latest/summary.json`

SHA-256:

`9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c`

Each source row must be runner-eligible and bind one complete 719-action route
to a downloaded 720-frame DONE/DONE public replay, its raw replay hash, source
team, frozen leaderboard rank, seat, and public-state sidecar.

## Physical action projection

For each action, preserve `farmer` and `hands` exactly. Preserve the ordered
`market` list after removing only `SELL` and `BUY_PRODUCT` commands. Retain
every other market command and preserve the relative order of retained
commands. Hash the full prefix as SHA-256 over sorted-key compact UTF-8 JSON
with `ensure_ascii=False`. Do not normalize worker order, command arguments,
amounts, or turn placement.

## Family and candidate selection

1. Cluster the 100 source tapes by the projected actions `[:72]`.
2. Keep clusters with at least two complete tapes. Rank families by:
   descending member count; descending maximum shared projected prefix
   length among unlock boundaries `72, 144, ..., 648`; ascending best
   frozen leaderboard rank; then ascending sorted rank list.
3. Build at most three separate standalone candidates from the first three
   families in that order. The initial canonical tape is the member with the
   best (lowest) frozen leaderboard rank in its family. The router embeds
   only family tapes, each as its original complete raw 719-action sequence.
4. At turns `72, 144, ..., 648`, the router may switch to a different tape
   only if its entire projected action prefix through the current turn equals
   the active tape's prefix and its recorded shop history at every unlock
   boundary so far equals the ordered prefix of `town.unlocked_shops` that is
   visible now. Choose the eligible tape with the best original frozen
   leaderboard rank, breaking a same-rank tie by episode ID. If none qualify,
   keep the active tape. Do not inspect future shop entries in embedded tape
   metadata during a choice.
5. Between unlock boundaries, continue the active whole tape. Do not use seed,
   opponent identity, opponent actions, score, W/D/L, actual future shops, or
   a test outcome to select or alter a tape.

This router is a new standalone tape-based candidate. It does not transplant
cb76's old DATA payload, market queue helpers, partial-planting helper, the
FarmIce special tape, or any hardcoded shop-pair override. No offline result
from fixed tapes constitutes policy validation or a >90% win-rate claim.

## Validation allowed before review

- Verify source manifest/hash and every input tape's action, replay, and
  sidecar provenance without reading outcomes.
- Verify family membership and prefix/shop-history facts from the frozen
  development tapes only.
- Parse/compile each generated standalone source and inspect the router AST.
- Decode its embedded routes and call the agent only at synthetic step 0 to
  confirm the first returned action equals the selected canonical tape's
  action 0. Do not run a simulator, game, route rollout, or outcome benchmark.
- Record exact candidate hashes and validation receipts. Send the plan,
  manifest, source files, and hashes to root for review before any pilot.
