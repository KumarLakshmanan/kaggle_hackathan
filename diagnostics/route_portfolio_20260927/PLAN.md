# Existing complete-route portfolio screen — 2026-09-26

Current `main.py` SHA-256 `489fe8e4...` selects route 105 for
`(ICE_CREAM_SHOP, BAKERY)` and route 107 for `(BAKERY, PIZZA_SHOP)` at
step 144. In the newest saved top-20 routes, it lost to Boey by 16,062/seat
on Ice Cream/Bakery and DECEM by 9,876/seat on Bakery/Pizza. Exact item
ledgers show egg/wheat gaps in both, milk in Boey, carrot in DECEM.

The embedded route tapes are complete funded daily schedules. After step144,
route 105/107 each plan three geese, four cows and four sheep purchases;
route 110 plans five geese, four cows and two sheep; route 123 plans three
geese, five cows and three sheep; route 101 plans five geese, two cows and
four sheep. These are schedule counts, not actual executed purchases.

Freeze four isolated source variants that change only one ordered shop-pair
mapping, leaving all parent action layers intact:

1. Ice Cream/Bakery 105→110 (more geese, fewer sheep).
2. Ice Cream/Bakery 105→123 (more cows, fewer sheep).
3. Bakery/Pizza 107→110 (more geese, fewer sheep).
4. Bakery/Pizza 107→101 (more geese, fewer cows).

Use the new Boey/DECEM routes as consumed development targets and all known
same-shop-pair routes from the 07:08 top-100 panel as comparators: winning
Victor @ Tufa Labs for Ice Cream/Bakery; winning RS Turley and lost Yizhou
for Bakery/Pizza. Match each
route's original seed, both seats, original shops; compare exact terminal
cash to frozen incumbent results. A variant reaches fresh reactive testing
only if all games are `DONE`, its target gains at least 5,000 paired-margin
coins per seat with positive own-cash change, no saved winning control
reverses, and aggregate margin over its target/control set improves. A fixed
route screen is a development filter, not independent validation. If none
passes, reject route remapping. No `main.py` change or Kaggle upload without
stronger native reactive evidence and the required fresh upload request.
