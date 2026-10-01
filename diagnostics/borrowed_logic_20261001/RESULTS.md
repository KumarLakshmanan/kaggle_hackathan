# Borrowed logic comparison — October 1, 2026

No Kaggle access or upload. Six source-frozen alternatives tested under PLAN.md. Engineering:144 native boundary/reset cases and physical feed/delivery probes pass.

## Results

| Panel | Version | Tested | Wins | Draws | Losses | Matched point gain | Mean coin margin | Clean |
|---|---|---:|---:|---:|---:|---:|---:|---|
| screen | accounting | 12 | 0 | 0 | 12 | -10.0 | -109661.5 | True |
| screen | baseline | 24 | 16 | 8 | 0 | +0.0 | 3166.0 | True |
| screen | belief | 12 | 8 | 0 | 4 | -2.0 | 1994.3 | True |
| screen | combined | 12 | 0 | 0 | 12 | -10.0 | -56387.1 | True |
| screen | dynamic | 12 | 0 | 0 | 12 | -10.0 | -79645.0 | True |
| screen | endgame | 12 | 2 | 0 | 10 | -8.0 | 493.7 | True |
| screen | feed | 12 | 2 | 0 | 10 | -8.0 | -1718.8 | False |

**belief stopped prospectively:** Even all remaining wins cannot produce positive pooled gain. Upper bounds: `{"4ea": {"baseline_points": 4.0, "maximum_points": 4.0}, "bbff": {"baseline_points": 8.0, "maximum_points": 8.0}, "v35": {"baseline_points": 8.0, "maximum_points": 8.0}}`. Untested cases are explicitly listed in screen_receipt.json; no results are imputed.

**feed stopped prospectively:** Operational gate irreversibly failed. Upper bounds: `{}`. Untested cases are explicitly listed in screen_receipt.json; no results are imputed.

**accounting stopped prospectively:** Even all remaining wins cannot avoid reference-level regression. Upper bounds: `{"4ea": {"baseline_points": 4.0, "maximum_points": 4.0}, "bbff": {"baseline_points": 8.0, "maximum_points": 4.0}, "v35": {"baseline_points": 8.0, "maximum_points": 4.0}}`. Untested cases are explicitly listed in screen_receipt.json; no results are imputed.

**dynamic stopped prospectively:** Even all remaining wins cannot avoid reference-level regression. Upper bounds: `{"4ea": {"baseline_points": 4.0, "maximum_points": 4.0}, "bbff": {"baseline_points": 8.0, "maximum_points": 4.0}, "v35": {"baseline_points": 8.0, "maximum_points": 4.0}}`. Untested cases are explicitly listed in screen_receipt.json; no results are imputed.

**endgame stopped prospectively:** Even all remaining wins cannot avoid reference-level regression. Upper bounds: `{"4ea": {"baseline_points": 4.0, "maximum_points": 4.0}, "bbff": {"baseline_points": 8.0, "maximum_points": 4.0}, "v35": {"baseline_points": 8.0, "maximum_points": 6.0}}`. Untested cases are explicitly listed in screen_receipt.json; no results are imputed.

**combined stopped prospectively:** Even all remaining wins cannot avoid reference-level regression. Upper bounds: `{"4ea": {"baseline_points": 4.0, "maximum_points": 4.0}, "bbff": {"baseline_points": 8.0, "maximum_points": 4.0}, "v35": {"baseline_points": 8.0, "maximum_points": 4.0}}`. Untested cases are explicitly listed in screen_receipt.json; no results are imputed.

Stopped candidates use their matched baseline subset, not the full24 controls. Both seats are kept in each paired seed. Cash is diagnostic; wins/draws/losses determine selection. Saved September29 top20 is a subset of top100; fixed tapes are regression controls and cannot establish live strength.

## Decision

Selected: `None`. Promotion eligible: **False**. Locally promoted: **False**.

No borrowed addition earned the frozen promotion criteria. Retain the independently qualified current engine; the six experimental candidates remain available for inspection.

Every executed case is in ALL_CASES.csv; JSONL ledgers retain telemetry and exact source identities. No guaranteed wins, Kaggle score estimate or top10 rank follows from these local tests.
