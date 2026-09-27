# Shop-selected Matt route family — 2026-09-26

The read-only collection `matt_route_family/summary.json` contains eight
recent public Matt Motoki action schedules from the same submission, across
seven observed first-two-shop pairs. Five have identical first-24 actions,
but there are four distinct first-24 hashes and six distinct first-96 hashes
in the sample. The routes are a family of shop and state-dependent plans,
not one portable 719-turn tape.

`build_matt_shop_family.py` built an isolated candidate (SHA-256
`fb7831e4db2bb706184227fff3e5b7cef50a450cdf569b28ed9ee0b191b372d0`)
from the submitted `main.py` hash `08aa268a...`. It starts from one common
opening, swaps the complete planned tape when public first and second shops
match a collected route, and leaves the existing observation-based wrappers
around that plan. It reads no opponent identity, seed, or future shop. This
is a development hypothesis, not a promoted policy.

Against its own saved base route on source seed 141084327, it won by 12,850
coins in each seat, both `DONE`. Against reacting current `main.py` on four
new predeclared native seeds 2611680–2611683, it lost **all four seed pairs
and all eight seat-games**, mean margin -12,938 coins. The maximum agent call
was 1,423 ms in this pilot. All players ended `DONE`. Raw results:
`matt_family_base_source_pair.json` and `matt_family_reactive_fresh4.json`.

**Decision: reject for promotion.** Shop-keyed tape selection with the
existing wrappers does not preserve the donor plan's advantage in reactive
games. The saved source route is development data and cannot override the
fresh reactive failure. No `main.py` edit or Kaggle upload.
