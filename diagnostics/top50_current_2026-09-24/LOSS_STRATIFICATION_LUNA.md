# Top-50 loss stratification for the next candidate test

## Evidence base

This is a read-only selection from the frozen `main.py` replay in [RESULTS.md](RESULTS.md), joined to exact route records in [`routes/summary.json`](routes/summary.json). The benchmark candidate SHA-256 is `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`; the manifest SHA-256 is `7b242129364b287d197a8c18964d6b9da9b990c68ebc39f1d087782bfc3b27e9`. All 200 seat games finished `DONE`: 67/100 route-pair wins and 133/200 seat wins, across 100 route records and 91 source episode IDs.

The transparent cash-symptom split in [loss_clusters.md](loss_clusters.md) uses panel medians of 107,190 own cash and 87,925 replay-opponent cash: 11 `rival-high`, 15 `both`, and 7 `own-low` losses. These are outcome strata, **not causal mechanism labels**. The panel below samples two losses from each stratum, plus five non-loss controls. `mean cash` averages each route's two seat replays; `S0/S1` are candidate margins in candidate seat 0/1; their sum is the route-pair margin. The source seat in a filename is the original tape's seat, not the candidate's replay seat.

## Replay panel

Replay each exact tape in both candidate seats. File names are relative to `diagnostics/top50_current_2026-09-24/routes/`.

| Stratum / role | Exact source route record (rank; seed) | Frozen baseline evidence and why retain it |
|---|---|---|
| Rival-high loss | `Excluding-submission-56489132-episode-112933084-seat0.json.gz` (25; `1803729554`) | Mean cash 116,023 / 155,219; S0/S1 −39,196/−39,196 → pair −78,392. The public farm trace shows a large tomato-acreage gap (34 rival tiles vs. 0 of ours on day 18); our trace records 80 tomato sales for 16,362. This is consistent with a capacity/mix/timing hypothesis, not proof that copying acreage is profitable. |
| Rival-high, high-cash near-tie loss | `Yannik-Schiffner-submission-56519100-episode-112937001-seat1.json.gz` (30; `1075971183`) | 144,082 / 144,247; −165/−165 → −330. Keeps a tiny negative paired result in a high-cash world so a candidate is not judged only on large deficits. |
| Both loss | `Boey-submission-56521745-episode-112939032-seat1.json.gz` (35; `1016478476`) | 103,125 / 129,837; −26,712/−26,712 → −53,424. The own trace reports 33 failed empty-shed sell-unit attempts; this flags an execution/capacity question but does not establish the first cause. Opponent tape `SELL` intent is not executed-economic evidence. |
| Both loss, separate team/episode | `ShunkiKyoya-submission-56504886-episode-112939287-seat0.json.gz` (34; `2059405774`) | 86,470 / 104,644; −18,174/−18,174 → −36,348. A second large `both` symptom without claiming the same mechanism; no event trace is available for this route. |
| Own-low loss, realized-price hypothesis | `ActiveMusyoku-submission-56512423-episode-112941285-seat0.json.gz` (49; `1080335140`) | 60,243 / 76,276; −16,033/−16,033 → −32,066. The recorded 247 strawberry sales returned 2,648 (about 10.7/unit), making this the strongest direct low-realized-price case; later shop sequence is a plausible, not isolated, cause. |
| Own-low, weak-cash near-tie loss | `marwar22-submission-56507022-episode-112934493-seat0.json.gz` (20; `830779084`) | 57,331 / 57,415; −84/−84 → −168. Retain as a low-cash sign/noise guard, not a high-upside target. |
| Positive near-tie control | `Sida-Zuo-submission-56488930-episode-112937057-seat0.json.gz` (27; `1024379262`) | 116,848 / 113,693; +3,155/+3,155 → +6,310. Rank- and cash-adjacent to Excluding. This selects Sida Zuo's seat-0 tape specifically; the manifest also has a separate SpaTaro tape from that episode, which is **not** an additional panel row. |
| Clear positive, high-cash control | `Ryo-Hasegawa-submission-56506377-episode-112931133-seat0.json.gz` (39; `1038853615`) | Mean cash 149,648.5 / 125,249; +24,001/+24,798 → +48,799. Checks for regressions in a strong-cash win. |
| Positive, lower-cash control | `Gleb-Tumanov-submission-56357593-episode-112939403-seat1.json.gz` (50; `1231382306`) | 77,957 / 77,114; +843/+843 → +1,686. A thin positive near the lower end of the cash range, close in rank to ActiveMusyoku. |
| Positive low-cash control | `team-submission-56483899-episode-112926581-seat0.json.gz` (5; `880965919`) | 64,940 / 61,591; +3,349/+3,349 → +6,698. Adds a genuinely low-cash positive route beside the marwar22 near-tie loss. |
| Seat-sensitivity control (route win) | `arutyunoff-submission-56520482-episode-112928929-seat0.json.gz` (36; `1067488506`) | Mean cash 113,105 / 92,622.5; S0/S1 +41,674/−709 → pair +40,965. One seat loses, but the paired route wins. Keep both seat results visible; do not call this a route loss. |

## Test use and limits

- This is 11 route records, **not** 22 independent opponents: run all 11 source tapes in candidate seats 0 and 1 (22 games per arm), then compare candidate vs. frozen baseline route-by-route. Keep seat margins and their sum; do not use seed-grouped totals where source episodes are shared.
- If the candidate changes occupancy or action timing, first compare with the reference shop sequence forced in both arms, then run a separate native-shop-RNG pass. Same seed alone may not preserve shops when earlier actions change RNG draw counts. Report own cash, rival cash, successful own units/receipts by product, costs, and service/overflow evidence separately.
- Route IDs, team names, rank, source seat, and seed are **sample/replay identifiers only**. The candidate must apply one observation-legal policy across the panel; no identity-based branches or per-route tuning. For a crop/mix candidate, use public shop demand, prices, inventory, owned land, cash, time, and feasible worker/shed/order capacity—not hidden rival inventory or source-tape knowledge.
- This panel is development/regression evidence, not a fresh holdout: the exact routes and several traces have already been inspected. Fixed action tapes are not adaptive opponents; replay opponent cash can move materially, and the source episode used a different opponent. Targeted mechanism evidence is strongest for ActiveMusyoku and Excluding; Boey has only the failed-sell observation noted above. ShunkiKyoya and the near-tie cases remain unexplained. Require fresh routes or reactive-agent confirmation before promotion.
