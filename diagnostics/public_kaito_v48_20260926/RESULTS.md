# Public v48 route-data screen — 2026-09-26

The public `40/40 Early Floor | 39/46 Top-10 | v48 Fast Routes` notebook
contains a compressed agent artifact. `decode_static.py` extracted its
verified 107,008-byte source and six 719-turn JSON action routes **as text/data
only**. The downloaded Python source was never imported or executed. The
decoded artifact SHA-256 is
`dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a`.

I built `data_route_candidate.py` from the route JSON with a small, locally
written visible-shop router and hand-count alignment. This probes the full
route *data* from turn zero, but omits the public policy's weed repair,
market-order scoring, clone preemption and terminal treatment. It is therefore
**not** a benchmark of the author's complete agent.

Predeclared native seeds 2614000–2614007 were run with endogenous shops and a
reacting current `main.py` opponent in both seats (16 games, installed engine
1.32.7). Candidate SHA-256 was `e017da3d6da795f03c8cf61a6479b740058644da2b9f6abd7c20ab4c84b64d55`;
the incumbent was `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
All 16 games ended `DONE`/`DONE`, with 0/8 positive paired seeds and 0/16 seat
wins. Candidate cash totaled 1,494,918 versus 1,924,688 for the reacting
incumbent, a −429,770 paired-margin total. Each seed lost in both seats;
individual paired margins ranged from −24,178 to −112,614. The largest
candidate call measured 4.46 ms.

The route data schedules four initial sheep, expanding to ten on its fast Yarn
branch, but no tomato seed purchases anywhere. Our incumbent schedules six or
eleven sheep in its comparable static routes and also relies on other
production layers. Static order totals do not represent executed purchases,
sales, or cash, so these counts are only a mechanism sketch.

**Decision: reject the data-only v48 route transplant.** The native result is
too weak to justify replacing `main.py` or screening this challenger on saved
top-100 routes. It does not rule out the author's full policy. Keep current
`main.py` unchanged; no Kaggle upload was made. Raw game results and hashes are
in `reactive_screen.json`.
