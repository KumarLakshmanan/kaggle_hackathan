# Price-floor identifiability correction — 2026-09-28

The initial FLOW_PLAN full-product inference claim failed. Its eight seat
runs compared 4,190 transitions before stopping each run on the first
mismatch; only DECEM's two runs reached all 690. Failures involve MILK or
WOOL. Native `_commit_unit` removes sold stock and credits cash at price 1
but does not add those units to market inventory. They are invisible in
shared supply, so the original formula cannot identify those net sales.
Original source, checker and failed result are preserved as
`before_floor_censor_*`; the original plan is retained unchanged.

Correct the feature's definition: return an unknown value for any product
whose price could have reached 1 during the market phase. Never treat it as
zero. For products that cannot be bought, pre-market inventory and observed
post-market inventory (adding back known subsequent town consumption) bound
the highest inventory. For WHEAT/FERTILIZER, use the conservative bound
initial market inventory + our exact post-worker stock + the rival shed
capacity. Buying then reselling cannot raise the aggregate supply above the
initial market plus existing sheds; deposits occur before the market.

Before rerunning, require all 5,520 non-midnight seat-transitions to be
visited, exact inference for every non-censored product, and at least 80%
product-transition coverage in total. Report all skipped values and reasons.
This repairs an accounting feature, not a candidate strategy. No winner
selection, route outcome or promotion criterion changes.
