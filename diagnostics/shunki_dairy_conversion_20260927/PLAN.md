# Coherent goose-to-cow substitution under two milk shops

Parent is frozen experimental selector 94f0602f, still unpromoted. The
PIZZA_SHOP/ICE_CREAM_SHOP branch uses complete source 113537968. Its five
geese are all bought after turn 144, when both shops are visible, and no
coop exists before that point. In the Breaking1800 ledger eggs average
43.9 coins versus milk 230.4; the rival earns 17,831 more milk coins. There
are no failed own worker actions in that trace. Test a production change.

On this branch only, from turn 144, coherently change all remaining goose
purchases, PICKUP and PLACE commands to COW, BUILD_COOP to BUILD_PASTURE,
and EGG sale/drop orders to MILK. Worker paths, feed, care and harvest cadence
are kept; cows mature later, so the native experiment must measure the net
result. Both species have compatible daily feed/care but different yields.
This is a new candidate, not a change to the ongoing 94f confirmation.

Before building, verify the selected tape has no goose purchase, pickup,
placement or coop construction before 144. Static preflight found three
explicit PLACE EGG shed drops (303, 402, 588); convert those to milk too.
Allow no other unhandled egg unit commands. This correction precedes the
first candidate build and all outcomes. Development includes all three top-50 PIZZA/ICE matchups in both
seats (Arda Ceylan, Breaking1800, ymg_aq). Require at least one additional
both-seat win, no previously won seat lost, all DONE, and nonzero coherent
edits. Otherwise reject without further tuning on these outcomes.

If this passes, run all 50 saved matchups in both seats, requiring a strict
increase over the parent's 45 sweeps and no prior sweep lost. These are
training/regression results only. An independently frozen native protocol
and both-seat loader parity must still pass before any promotion. Main and
the uploaded artifact remain 3cc throughout this experiment.
