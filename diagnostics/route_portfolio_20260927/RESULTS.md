# Complete-route portfolio screen — 2026-09-26 19:59 UTC

Four isolated full-source variants changed only one first-two-shop mapping at
step 144; each keeps an existing complete funded route tape and all reactive
layers. Exact source SHA-256 hashes are in `variants.json`. `main.py` remains
SHA-256 `489fe8e4...` and its uploaded backup is unchanged.

Every relevant saved route was rerun on its original seed in both seats with
native shops: new Boey and DECEM losses plus all three known same-shop-pair
07:08 comparators. All 20 games ended `DONE`/`DONE`. Raw cash pairs, own and
rival deltas, first-two shops and predeclared gate decisions are in
`fixed_screen.json`.

| Variant | Target margin change per seat | Target own cash change per seat | Other same-pair routes | Gate |
| --- | ---: | ---: | --- | --- |
| Ice Cream/Bakery 105→110 | Boey +409 | +895 | Victor +2,436 margin/seat | Fail |
| Ice Cream/Bakery 105→123 | Boey +1,558 | −2,495 | Victor −607 margin/seat | Fail |
| Bakery/Pizza 107→110 | DECEM +447 | +3,904 | RS Turley −1,281; Yizhou +2,933 margin/seat | Fail |
| Bakery/Pizza 107→101 | DECEM +2,688 | +3,634 | RS Turley +218; Yizhou +1,950 margin/seat | Fail |

The Bakery/Pizza route-101 variant had positive own cash and margin on all
three development routes and no outcome reversal. Its target improvement
was below the predeclared **+5,000 margin per seat** threshold, so the first
promotion gate failed. The other three also failed that threshold; the
Ice Cream/Bakery route-123 variant reduced own cash on its target.

**Decision: reject all four mappings for promotion under this experiment.**
Do not reinterpret the positive fixed-route deltas as live strength or run
the conditional reactive promotion stage. A broader shop-pair route selector
would be a separate prospective experiment with fresh reactive opponents.
No `main.py` change or Kaggle upload.
