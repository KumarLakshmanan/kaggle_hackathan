# Bakery/Pizza complete-route prospective reactive screen — 2026-09-26

The earlier five-route fixed-action portfolio rejected route 107→101 because
its DECEM target gained only 2,688 margin per seat, below its frozen 5,000
gate. It did improve own cash and margin on all three saved Bakery/Pizza
routes. Treat that finding only as development motivation for a new,
independent native test. Route 101 is a complete funded existing action tape,
selected at the day-6 shop observation; no replay ID, seed, future shop, or
rival private information is used in the policy.

Freeze `exp_route_bakpizza_101_20260927.py` at SHA-256
`dfd82dd45769379f39adc299e90b8c721f2eff7e352b4070699aff81cbd72c9c`
against unchanged `main.py` SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
Scan native seeds starting at 2621000 in increasing order, stopping at six
seeds whose first two shops after day 6 are exactly Bakery then Pizza or
after 1,000 seeds. The scan runs incumbent self-play through step 144 and
records shops only; it does not inspect final outcomes. Six matches are
required to proceed.

For each selected seed, run control (`main.py` versus reactive `main.py`) and
candidate (frozen route-101 variant versus reactive `main.py`) in both seats,
with original shops. Require all games DONE, positive total own-cash delta,
positive total paired-margin delta, at least four of six seeds with positive
paired margin delta, and no seed with paired margin delta below −5,000.
If this development gate passes, select a second untouched sequential seed
block and repeat before any full saved-route regression or `main.py`
promotion. A fixed-action panel alone cannot validate the policy. No Kaggle
upload is authorized.
