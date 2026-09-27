# Relaxed mirror gate screens — 2026-09-26

Current `main.py` uses 12-turn early sale lookahead only when both complete
farms (tiles, farmer, and hands) match. To target near-mirror saved-route
losses, two separate candidates relaxed only that gate:

| Candidate | SHA-256 prefix | Match condition | Losses rescued | Changed loss routes | Sum of paired-margin changes |
| --- | --- | --- | ---: | ---: | ---: |
| `exp_sale_tilegate12_20260926.py` | `a481eeeb` | Exact farm tiles, ignoring worker positions | 0/31 | 4 | −62 |
| `exp_sale_layoutgate12_20260926.py` | `e747aa73` | Crop/animal layout, ignoring growth state and worker positions | 0/31 | 5 | −326 |

Each candidate ran against all 31 September 26 top-100 saved-action losses
in both seats, with native engine 1.32.7 and original shop sequence. All
124 games ended `DONE`; neither candidate won a seat game or route pair.
The tile gate activated early sales on seven routes and the layout gate on
seven. The layout gate's largest improvement was +328 paired coins for
Hikaru Umeda, and its largest regression was −842 for Subramanya N. These
are previously used development tapes, not reactive opponents.

**Reject both gates before a full winning-control or reactive run.** Neither
addresses the saved losses, and the aggregate margin worsens. Current
`main.py` and Kaggle submission 56569042 remain unchanged. The raw panels
are `tilegate12_losses31.json` and `layoutgate12_losses31.json`.
