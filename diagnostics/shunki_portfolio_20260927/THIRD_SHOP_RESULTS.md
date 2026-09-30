# Later-shop route audit — 2026-09-26 22:02 UTC

All 203 frozen public replay SHA-256 values and source seats were
reverified while extracting each visible shop reveal sequence. The
first-two-shop values exactly matched the earlier manifest. The source
set contains 164 distinct three-shop sequences across 61 shop pairs;
coverage becomes sparse for longer sequences (197 distinct four-shop
prefixes, 202 five-shop prefixes).

Starting from the frozen newest-route choice for each first-two-shop
pair, 127/164 three-shop prefixes have a source route with an **identical
first 216 actions**, allowing an exact-history-compatible switch when
the third shop appears. This yields 66 actual third-shop route switches.
The analogous exact-prefix rule permits 15 fourth-shop, two fifth-shop,
and one sixth-shop switch. It leaves 37 three-shop prefixes on the
previous route because no exact-compatible source exists; this avoids
pretending that state-dependent early actions are interchangeable.

For ICE_CREAM_SHOP/BRUNCH_SPOT/YARN_STORE, the exact-compatible rule
switches from episode 113445495 to 113347600 at turn 216. This directly
addresses the source-route mismatch observed on fresh seed 2630130,
but a cash improvement is not yet established.

**Decision: proceed to an isolated later-shop candidate and fresh
reactive development block; no `main.py` edit or Kaggle upload.** The
public route histories establish route availability and prefix
compatibility only. See `THIRD_SHOP_PLAN.md`, `shop_sequences.json`,
`later_shop_analysis.json`, `collect_shop_sequences.py`, and
`analyze_later_shops.py`.
