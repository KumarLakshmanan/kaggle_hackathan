# Pizza/Bakery complete-route library screen — 2026-09-26

In the 07:08 top-100 saved route panel, all three routes with first-two shops
`PIZZA_SHOP,BAKERY` lose under current `main.py`, with total paired deficit
38,080. The incumbent uses complete route 120 for this observable shop pair.
The agent library contains 40 other routes, most sharing the full opening
through step 143. This is a development search for a better **whole route**
commitment, not a claim that fixed opponent actions validate live strength.

Freeze `main.py` at SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
Build one isolated copy per compatible route ID (all IDs except route 1,
whose pre-day-six opening differs), each changing only the
`PIZZA_SHOP,BAKERY` day-six mapping. Screen alternate IDs in seat 0 against
the three frozen lost public action routes on their original seeds with
original shops; require DONE/DONE. Rank by the minimum of the three margin
improvements, breaking ties by their sum, with no tuning of candidate rules.

Advance only if the selected route improves **both own cash and paired
margin on all three** seat-0 targets, and total margin improvement is at
least 15,000 coins. Then test that frozen route in both seats on all three
targets and any same-shop winning controls in older panels. Only after that
would an outcome-blind native shop-matched fresh seed scan and reacting
opponent test be justified. Passing fixed tapes never justifies main edit or
Kaggle upload. If no route meets the initial gate, reject the library switch.
