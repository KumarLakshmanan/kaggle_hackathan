# Fresh Kaggriculture replay collection — 2026-09-29

This directory holds a read-only Kaggle snapshot and runner-ready routes for
the current uploaded candidate `cb76fbc4` (submission `56680167`). No games
were run and no submission was uploaded as part of this collection.

## Snapshot and collection scope

- The authenticated leaderboard CSV was downloaded at 2026-09-29 17:04:23 UTC;
  the frozen snapshot receipt was written at 17:04:25 UTC. It contains 10,167
  teams. The ZIP SHA-256 is
  `be1de293017680577f2cf2e77f01dc03f94066faac8d20a39a9480d2959d6ce2` and the
  CSV SHA-256 is
  `48251a714ba7164c66c81a8277740541c6e3a51523a673f220a638d9cd2993db`.
- For each of the frozen top 100 teams, the selected submission is the public
  submission with the highest public score (latest submission date breaks a
  tie). The collection includes its three newest completed public episodes,
  selected by creation time without looking at outcomes.
- All 300 team/episode slots are preserved. They refer to 240 distinct public
  episode IDs, with 60 repeated episode IDs across team slots. Unique counts by
  slot are 84 for the development latest episode, 92 for reserved episode 2,
  and 96 for reserved episode 3. These tiers can share the same physical game
  episode when both teams are represented in the top 100.
- Initial concurrent listing requests received 64 HTTP 429 responses. The
  bounded serial retry recovered all 64; there are no remaining unavailable
  team listings, episode slots, or current-submission downloads. Retry details
  and the original failures are preserved in `listing_retries.json` and
  `retry_preserved/`.
- The collector finished at 2026-09-29 17:29:13 UTC. Every downloaded replay
  has engine version `1.32.7`, statuses `DONE/DONE`, and 720 frames. There are
  267 unique replay archives total: 240 unique top-100 episodes plus 27 public
  episodes from submission 56680167. Each archive has a paired public-state
  projection and action/provenance index.
- Per-frame projections retain both seats' public `town.unlocked_shops` and
  `market.inventory` / `market.prices`. The replay API did not expose a
  separate demand field in these records.

## Runner summaries

| Use | Summary |
| --- | --- |
| Latest episode per top-100 team; development only | `routes/development_latest/summary.json` |
| Early top-20 subset | `routes/development_top20/summary.json` |
| Reserved second-newest episode; do not use for development | `routes/episode_2/summary.json` |
| Reserved third-newest episode; do not use for development | `routes/episode_3/summary.json` |
| Uploaded submission's own 27 public action tapes | `routes/current_submission_56680167/summary.json` |
| Rival action tapes from those same 27 games | `routes/current_submission_56680167_opponents/summary.json` |

Each top-100 tier has 100/100 runner-eligible rows. Summary SHA-256 values:

| Summary | SHA-256 |
| --- | --- |
| `routes/development_latest/summary.json` | `9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c` |
| `routes/development_top20/summary.json` | `f0dd406cf56c35af607524d14dc94cf2a858723e316b739d76220ab906838011` |
| `routes/episode_2/summary.json` | `5d1468477cf5a6c6d0a3b060232e58957a8ca8c48a1070b2ccb0ee8dbbefef0d` |
| `routes/episode_3/summary.json` | `e7b0896967439c0ee9b46ff11aa9d62fc97e347cc6fc48d9e051b08f5246e7e6` |
| `routes/current_submission_56680167_opponents/summary.json` | `13379d1947786d129da8a6b38ab6f3aed97a2a5f1d3ce4740418f1d699166a89` |

The rival-action summary stores the actual other-seat tape, verified against
both the source row's `opponent_action_sha256` and the public-state index for
all 27 episodes. Opponent team IDs map to the frozen full leaderboard. The
exact rival submission ID is not present in the downloaded replay/listing, so
`submission_id` is deliberately null rather than guessed. Each row retains
the uploaded agent's original seat, result, action hash, and submission ID;
its `rank` (101–127) is explicitly a runner bookkeeping index, not a
leaderboard rank. The actual rank, when listed in the full snapshot, is stored
separately as `team_rank_at_snapshot`.

The independent opponent-route builder's integrity receipt is
`routes/current_submission_56680167_opponents/receipt.json`. It confirms
27/27 rival hashes against both recorded sources, 27/27 team-ID matches, no
game runs, and no additional Kaggle calls.

## Submission 56680167

The status check at 2026-09-29 17:04:25 UTC found submission `56680167`
COMPLETE at public score `1840.6`. All 27 completed public episodes available
in its listing were downloaded, with no result-based episode selection. Its
public record is 24 wins, 0 draws, and 3 losses. The loss episodes are:

| Episode | Uploaded seat | Rival (seat) | Uploaded result |
| --- | ---: | --- | --- |
| `115319884` | 1 | Maher el Ouahabi (0) | Loss |
| `115315638` | 1 | coolin666 (0) | Loss |
| `115302829` | 0 | Tomohiro Nagai (1) | Loss |

See `current_submission_56680167_wdl.json` for all 27 outcomes and episode
timestamps. These are the uploaded submission's public match records, not a
fresh independent estimate of win rate.

## Static opening/prefix census

`static_prefix_census.json` compares the 100 newest top-team tapes with the
exact embedded `_DATA` from the staged uploaded file, whose SHA-256 is
`cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`. The
script decodes the embedded literal without importing or executing the agent.
It does not read the reserved episode-2 or episode-3 routes and does not
inspect outcomes.

The upload has seven distinct realized 72-action opening prefixes in its own
27 public episodes, so there is no single universal realized opening tape.
The most common two occur 12/27 and 10/27 times. None of the latest 100 tapes
exactly matches any of those 27 uploaded realized raw action prefixes. The
newest 100 have 97 unique raw 72-action prefixes; the largest exact clusters
are three tied pairs at ranks `[30,86]`, `[65,77]`, and `[16,83]`. The top 20
have 20 distinct raw prefixes; rank 16 is in one of the tied pairs.

For the physical-schedule comparison, the worker-only projection preserves
`farmer` and `hands`. A second projection also preserves `HIRE`, `BUY_LAND`,
`BUY_SEED(S)`, and `BUY_ANIMAL` orders in their original relative order while
dropping `SELL` / `BUY_PRODUCT` and their interleaving. Expected actions 0–71
come from `_DATA['opening']`; expected actions 72–143 append the deployed
first-shop raw route selected from the exact uploaded route map for the
episode's frame-72 first shop. Both projections match all 27 own uploaded
public tapes through 72 and 144 actions, which is the in-sample extraction
check. Neither projection matches a latest top-100 tape: 0/100 at both prefix
lengths, including 0/20 top-20 tapes. This is static action-pattern evidence,
not a policy benchmark or an outcome claim.

## Provenance and verification

- `manifest.json` records selection, download, retry, and completeness details.
- `snapshot.json` records leaderboard download source, timestamp, archive
  member, and hashes.
- `api_raw/`, `listings/`, `raw_archive/`, `episode_index/`, and
  `retry_preserved/` retain source responses, raw replays, projections, and
  recovery evidence.
- `collection_errors.json` has empty arrays for unavailable listings,
  unavailable episode slots, and current-submission errors.
- `build_current_opponent_routes.py` rechecks raw replay hashes, seat/name
  assignments, 719-action lengths, rival action hashes, and both action hashes
  in the index while building the separate rival summary.
- `verify_collection.py` is available for a full recheck. A full run was
  stopped while CPU-heavy local benchmarking was active; the 27-row rival
  builder checks completed, and the collector/retry receipts report all top-100
  route tiers complete.

No fixed replay tape in this collection should be treated as independent
validation of a policy change.
