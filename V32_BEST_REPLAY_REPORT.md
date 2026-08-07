# V32 best-replay optimization report

## Replay corpus inspected

All 22 JSON replays in `best_replay/` were parsed and both player action
tapes were extracted. The episodes were:

`90613978`, `90614707`, `90615512`, `90616293`, `90617094`, `90617877`,
`90618657`, `90619447`, `90620234`, `90621013`, `90621805`, `90622597`,
`90623398`, `90625760`, `90630506`, `90631991`, `90632793`, `90633595`,
`90634400`, `90635194`, `90635995`, and `90659792`.

The corpus contains 44 seat-specific tapes and 39 unique action tapes.
The extracted routes and metadata are in `best_replay/routes/`.

## Architecture changes

- Replaced the primary five-hire/no-product book with the Dahoui route. It
  wins both seats against all four replay agents that use this opening.
- Retained Wufang as the broad five-hire/product fallback.
- Added readable THUNDER and Aastik counter books. They are selected at turn
  144 only when the first two shops observed in the live public state match a
  verified pattern. Unknown patterns keep the Wufang fallback.
- Added two delayed, state-compatible counters for the Seb `90620234` and
  `90621013` pasture openings. Seb-specific shop mappings are additionally
  gated by the publicly observed turn-one pasture/seven-hand opening so they
  cannot collide with normal openings.
- Delayed low-price strawberry sales for the one remaining Seb pattern. This
  improves its per-game margin from `-3,370` to `-2,410` without affecting
  other replay families.
- Removed the primary-only market reorder because it degraded the Dahoui
  book. Existing weed recovery, market validation, bounded preemption,
  terminal liquidation, and legal-action recovery remain in place.

All action books are plain Python lists. No compression, encryption, encoded
payload, dynamic evaluation, hidden seed, or replay episode ID is used by the
agent. Selection uses only observations available to a submitted agent.

## Best-replay verification

Kaggle Environments 1.32.5, each unique route played twice with seats swapped:

- Unique routes: 39
- Route results: 38 wins, 0 draws, 1 loss
- Individual games: 76 wins, 0 draws, 2 losses
- Mean margin: `+2,320.21`
- Median margin: `+2,381`
- Mean decision time: `663.99 us`
- Maximum observed decision time: `216.14 ms`
- Status: all 78 games `DONE`

The remaining loss is `episode-90635995-seat0.json.gz`, at `-2,410` in each
seat. A search over every replay-derived book compatible through turn 144
found no book that flips it. Its exact winning book requires a different
turn-zero seven-hire/pasture economy, while the initial observation is
identical across opponent families, so it cannot be selected from opponent
information before the first action.

## Regression gates

- Exact failed-replay panel: 12/12 games won; 6/6 opponents won.
- Historical panel: 46/46 games won; 23/23 opponents won.
- All 58 regression games completed with `DONE` status.
- `main.py` compiles and is byte-identical to the verified V32 candidate.

Machine-readable evidence:

- `benchmark_results/v32_final_best_replay_panel.json`
- `benchmark_results/v32_failed_routes_exact_seeds.json`
- `benchmark_results/v32_current23_panel.json`
- `benchmark_results/v31_remaining_delayed_counter_search.json`
