# Fresh first-place Boey saved-route loss — 2026-09-26

An exact native seat-0 event replay of the refreshed Boey public action route
reproduced current `main.py` cash **93,585** versus fixed-rival **96,475**,
margin **−2,890**, both `DONE`. The saved route's source seed was 958156682;
the full trace is `boey_trace_s0.json.gz`. The shops began `YARN_STORE,
PIZZA_SHOP` and later included Bakery, two Farmers Markets, Ice Cream Shop,
and another Pizza Shop. The physical-mirror sale gate never opened, so another
mirror-sale adjustment cannot address this case.

The exact executed-transaction ledger reconciles the 2,890-coin deficit with
zero unexplained cash. Relative to Boey, our net cash was higher by 15,494
from strawberry, 12,054 from tomato, 3,160 from milk and 2,030 from melon.
Boey gained 13,180 more net wheat cash, 5,281 more wool, 5,133 more egg, and
4,784 more carrot. Our extra land and hiring expense totaled **7,553** coins
(7,000 versus 3,000 land; 7,955 versus 4,402 hires). All item-level net cash
differences sum to +4,663, and the expense difference is −7,553, yielding
−2,890 exactly.

Boey executed 4,151 wheat sales and 3,558 wheat purchases; our agent executed
361 sales and 154 purchases, leaving net market wheat flows of 593 versus 207
units. Its gross wheat turnover is therefore not 144,186 coins of free
revenue: it spent 124,521 on product wheat. The engine quotes a product buy
at post-buy inventory, so an immediate buy/sell round trip against an
unchanged market nets zero. Boey also planted 215 wheat and 72 carrot crops
in this game, versus our 166 wheat and 28 carrot; our farm instead planted
more strawberry and tomato. This is a portfolio and labor-allocation
difference whose terminal effect depends on later shops and the shared
market. Cutting hires or land alone would also remove production.

**Decision:** treat Boey as a complete-schedule efficiency problem. Test any
replacement as a funded route with work, feed, delivery, and sales intact;
measure own and rival cash on both seats and reacting fresh seeds. No direct
policy change or upload follows from this fixed-action ledger.
