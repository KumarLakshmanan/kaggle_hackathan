# Fresh physical-opening candidates

This folder contains three standalone public-tape routers prepared for root’s
bounded development pilot. They are new candidate sources; they do not change
`main.py`, `agent.md`, or any earlier diagnostics. No games were run while
building or validating them, and this package does not establish a win-rate
estimate.

## Frozen source and selection

The source is the 100-team `development_latest` panel from the leaderboard
snapshot downloaded at **2026-09-29 17:04:23 UTC** (the collection receipt was written at 17:04:25 UTC). The source summary SHA-256 is
`9dc48578eb5e828d8038ff39821c8e27ddb12b1a7a4812a87622003c2db63e9c` and the
replay engine is **1.32.7**. The source data and per-tape paths and hashes are
recorded in [candidate_manifest.json](candidate_manifest.json).

For the physical prefix census, each action keeps `farmer` and `hands` exactly
as recorded. It keeps market commands in order, dropping only `SELL` and
`BUY_PRODUCT`. Across the 100 routes, this yields 96 projected first-72-action
prefixes: 92 singleton clusters and four pairs. The largest family size is two.
The three chosen families follow the frozen ordering: largest shared physical
prefix boundary first, then best leaderboard rank. Rank 16 is the only member
of these multi-tape families in the top 20 under this physical projection.

| Candidate | Family ranks | Shared physical prefix through | Base rank | Shop fork visible at |
|---|---:|---:|---:|---|
| `candidate_01_family01_rank65.py` | 65, 77 | checkpoint 144 (actions 0–143) | 65 | second unlock: `BRUNCH_SPOT` vs `SMOOTHIE_SHOP` |
| `candidate_02_family02_rank16.py` | 16, 83 | checkpoint 72 (actions 0–71) | 16 | first unlock: `FARMERS_MARKET` vs `PET_CAFE` |
| `candidate_03_family03_rank30.py` | 30, 86 | checkpoint 72 (actions 0–71) | 30 | first unlock: `ICE_CREAM_SHOP` vs `YARN_STORE` |

The omitted fourth pair is ranks 56 and 79. It also shares through checkpoint
72; the frozen ordering places it after the selected pairs because its
best rank is 56. The physical projection can group tapes whose full raw market
actions differ only in the two ignored command types; these families are not
claimed to be exact raw-action matches.

## Router behavior

Each candidate starts from the complete 719-action tape belonging to its best
rank. At offsets 72, 144, ..., 648 it may switch to another tape from the same
family only when (1) the entire projected worker and investment prefix matches
the active tape through that offset and (2) the candidate’s historical shop
sequence matches only the shops currently visible in `town.unlocked_shops`.
Among eligible tapes, it selects the lowest frozen leaderboard rank. If no
candidate qualifies, it keeps the active tape. The router reads `step` and
`town.unlocked_shops`; it does not use seed, team or opponent identity, scores,
W/D/L, or future test outcomes. It does not reuse cb76 helpers, the FarmIce
tape, or hardcoded shop-pair overrides. Team and episode identifiers appear
only in provenance reports, not in executable candidate payloads.

All six source tapes contain recorded `BUY_SEED MELON` at action offset 5 and
`PLANT MELON` at offset 7. These are commands present in the tapes; the static
scan makes no claim that they succeeded in the source replay.

## Verification and reproduction

`candidate_validation.json` records the verification result. It confirms the
frozen source and plan hashes, verifies action, raw replay, replay archive,
public-state sidecar and index hashes for all six selected source routes,
checks the recorded shop histories and source seats, and confirms complete
719-action routes on engine 1.32.7. Each standalone source parses and compiles;
its embedded policy payload contains only rank, shop history, and actions. A
single synthetic step-0 call per candidate returned its canonical first action.
The receipt records zero network calls, zero simulator imports, zero game runs,
no outcome-field use, and no reads from reserved episode-2 or episode-3 panels.

After a pilot has not locked these source bytes, the receipts can be refreshed
with:

```powershell
python diagnostics/fresh90_current_opening_20260929/validate_candidates.py
python diagnostics/fresh90_current_opening_20260929/inspect_melon_support.py
python diagnostics/fresh90_current_opening_20260929/finalize_candidate_bundle.py
```

`build_candidates.py` regenerates the selected files and their family report
from the frozen source. Do not run it during an active pilot, because the
candidate files are the exact artifacts being evaluated. Exact current hashes
are in [CANDIDATE_SHA256.txt](CANDIDATE_SHA256.txt); the frozen plan SHA is
`e4dec7ce829ad31324a3cc0ef4485daf59ecd836e79c5861acbc32831669c7d7` and the
candidate manifest SHA is `04bc8d1df1bae5f13cec33417b3e3e4f7ee71174b9a9f530c6ed06599f375571`.
