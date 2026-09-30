# Complete high-strawberry donor plans through the existing adaptive layers

2026-09-26. `build_adaptive_donor_route.py` made isolated candidates from the
submitted `main.py` (SHA-256 `08aa268a...`). It replaced all 41 chassis
action plans with one public opponent's complete 719-turn plan, updated the
opening installer so it could not restore the old first 96 turns, and kept the
existing observation-based wrappers. These candidates are research artifacts,
not uploads. The donated actions were extracted from public replays and are
fixed; the surrounding wrappers remain reactive.

| Donor | Candidate SHA-256 | Day-six strawberries | Original saved route, both seats | Fresh reactive versus `main.py` |
| --- | --- | ---: | ---: | ---: |
| DSM | `81b60260...` | 9 | -45,849 per seat on source seed | Not run after source failure |
| Lucas Boesen | `4c189b45...` | 10 | +2,581 per seat, rescuing current baseline's -20,044 | 1/8 seed pairs, 2/16 seats; mean margin -21,884 |
| Matt Motoki | `6affe721...` | 10 | +5,071 per seat, rescuing current baseline's -18,241 | 0/4 seed pairs, 0/8 seats; mean margin -14,192 |

All source and reactive games ended `DONE` in both seats. The donor source
seeds were 1681313608 (DSM), 585659362 (Lucas), and 2000357383 (Matt).
The Lucas reactive block used predeclared fresh seeds 2611600–2611607;
Matt used 2611650–2611653. The Lucas candidate also beat its fixed action
donor by 6,490 per seat on unrelated seed 1199581324, while the incumbent
lost to that fixed donor by 2,005. Yet versus reacting `main.py` on the same
seed it lost by 23,074 per seat. The native shop sequences differed across
these matches; this is a scenario change as well as an opponent-policy change.
The candidates did reproduce their donated day-six strawberry portfolios, so
the failure is in the later adaptive fit and shop uncertainty, not opening
installation.

**Decision: reject all three single-schedule candidates for promotion.**
One or two fixed-action rescues are not evidence of a live-strength gain;
the independent reactive blocks strongly contradict such a gain. No
`main.py` edit or Kaggle upload.

Read-only collection of eight newer public games from Matt's same submission
found seven distinct shop pairs, four distinct first-24-action hashes and six
distinct first-96-action hashes. Five games shared an exact first 24 actions,
but the later plans varied. See `matt_route_family/summary.json` and the
compact action routes. This gives a concrete basis for a separate shop-aware
family experiment; it does not itself establish that family routing works.

Raw tests: `adaptive_dsm_source_pair.json`,
`adaptive_lucas_true_source_pair.json`, `adaptive_lucas_seed1199581324_pair.json`,
`main_lucas_seed1199581324_pair.json`,
`adaptive_lucas_reactive_seed1199581324_pair.json`,
`adaptive_lucas_reactive_fresh8.json`, `adaptive_matt_source_pair.json`, and
`adaptive_matt_reactive_fresh4.json`.
