# Top-three rank single-tape controls

This bundle freezes three standalone controls from the latest-development
panel: one complete action tape each from leaderboard ranks 1, 2 and 3. It is
separate from the three rejected shared-prefix router candidates. The parent
owns the game pilot; this folder contains no game results and makes no win-rate
claim.

## Frozen sources

The source summary is
`diagnostics/fresh90_refresh_20260929/routes/development_latest/summary.json`,
SHA-256 `9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c`.
Leaderboard snapshot timestamp is 2026-09-29 17:04:23 UTC (receipt at
17:04:25 UTC), and the replay engine is 1.32.7.

| Frozen rank | Team | Submission | Episode / source seat | Source action SHA-256 |
|---:|---|---:|---|---|
| 1 | DECEM | 56654377 | 115321748 / 0 | `f5d184d72bcab70c6828a2bee46315d3552479f1783e1cda0c3a7969c2277d3b` |
| 2 | DSM | 56675988 | 115323250 / 0 | `c6da0c253b97b2bc40a77a76525ef633804d8b3b4367b4f76b40a5ecc7b49714` |
| 3 | Boey | 56640149 | 115323250 / 1 | `3fde6ab726966f1e1012d8513cf60d8061152217c6ccb8676f94ca1ecd7af405` |

Ranks 2 and 3 are opposing seats from the same public episode. They remain
separate rank-selected controls, but their source replays are not independent.
No outcomes were used to choose or describe the tapes.

## Candidate files and hashes

- `candidate_top_rank_1.py` — `2bac6d8e7b4bb8fa39247b796ab6c78c514059002f27b0461c788361a04841ce`
- `candidate_top_rank_2.py` — `85296f8e66a2c8e09723a17efbd611a284c3b6442694cf86790ec757e1bf75c9`
- `candidate_top_rank_3.py` — `6434d82e990f930e82d22f43e42d5057a675642be80f73e313740417e206899c`

Each file embeds one complete 719-action source tape only. It uses the same
`observation.step`/call-counter fallback and 0..718 clamp as the prior opening
router, exports `agent` and
`kaggle_fresh_opening_router_entrypoint(observation, configuration=None)`,
and has no switches or route-selection metadata. Static validation parsed,
compiled and loaded the modules, matched embedded action hashes to source,
and checked both callable signatures. It did not invoke either callable.

## Day-zero order comparison

Counts are from recorded actions at offsets 0–23 only. Animal and seed figures
are units ordered, HIRE is a count of HIRE orders, and crop figures are PLANT
commands. These are source schedule descriptions, not evidence that an order
or work command succeeded in the replay. Full type/item order counts and first
offsets are in [static_day0_comparison.json](static_day0_comparison.json).

| Route | HIRE orders | COW units | SHEEP units | MELON seed units | WHEAT seed units | MELON plant commands | WHEAT plant commands |
|---|---:|---:|---:|---:|---:|---:|---:|
| Top rank 1 DECEM | 4 | 2 | 3 | 6 | 13 | 6 | 13 |
| Top rank 2 DSM | 5 | 2 | 3 | 6 | 13 | 6 | 12 |
| Top rank 3 Boey | 5 | 3 | 2 | 7 | 13 | 8 | 14 |
| Rejected family 65/77 | 5 | 2 | 3 | 6 | 12 | 6 | 12 |
| Rejected family 16/83 | 5 | 2 | 3 | 8 | 15 | 6 | 12 |
| Rejected family 30/86 | 5 | 2 | 3 | 8 | 14 | 6 | 12 |

Rank 1 starts its first action with one COW and one SHEEP order, then adds to
that portfolio during day zero. The contrast to the rejected schedules is
modest and descriptive: all include early MELON/WHEAT orders, while the three
rank controls vary in hire count, animal mix, and recorded planting-command
counts. This comparison alone does not show why any route wins or loses.

## Verification and reproduction

[candidate_manifest.json](candidate_manifest.json) records every selected
source path, route/replay/archive/sidecar hash, source seat, candidate hash,
and the no-games/no-outcomes validation receipt. [PLAN.md](PLAN.md) is frozen
at SHA-256 `56682731bc1a66b54e4f0fc5e055f1b8e733a2e724e131f0fdc504c37c068a7d`.
[SHA256SUMS.txt](SHA256SUMS.txt) contains the candidate, source, static-report,
and manifest hashes.

To rebuild the candidates and receipts from the frozen source summary, run:

```powershell
python diagnostics/fresh90_leading_openings_20260930/build_single_tape_controls.py
```

That script verifies source action, replay, public-state index and sidecar
provenance, writes the three source files, compares day-zero command counts
against the six rejected-family tapes, then performs AST/compile/module-load
checks. It makes no network calls, imports no simulator, and executes no policy
actions or games. Rebuilding rewrites the candidate source files; do not run it
while a pilot is using these exact byte hashes.
