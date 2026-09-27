# 2026-09-26 yarn route-12 screen — reject

The incumbent `main.py` is SHA-256
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
An identical backup is `main_before_top10_goal_20260926_04b0bdc3.py` in the
workspace root. The standalone experimental candidate
`exp_yarn_route12_20260926.py` changes only the day-6 router: when the first
two observed shops include `YARN_STORE` and the incumbent selects route 9, it
selects existing complete route 12. No replay ID, opponent name, seed or future
shop is a policy input. The base-control wrapper reproduced all terminal cash
and statuses on its first two sampled routes exactly.

## Saved-route development screen

`create_yarn_panel.py` froze all 22 yarn-opening routes in the September 25
top-100 panel plus six spread non-yarn controls. Both seats were run on each
route under engine 1.32.7; all 56 games were `DONE`. `compare_yarn12.py`
matched exact action hash, seed and source seat to the previously saved
incumbent result.

| Cohort | Incumbent paired wins | Route-12 paired wins | Losses rescued | Wins reversed | Own cash change, two seats total | Fixed-tape rival cash change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 22 yarn routes | 13 | 16 | 4 | 1 | +82,568 | +49,738 |
| 6 non-yarn controls | 6 | 6 | 0 | 0 | 0 | 0 |

The broad switch rescues Crop Dustas, Yannik Schiffner, fasith 007 and keiz
by paired margin, but reverses Dmytro Maliarenko from +1,697 to -30,076 per
seat. It also worsens Fourth Quadrant from -4,266 to -34,637 per seat.
Yannik and fasith's apparent rescues lower **own** terminal cash and lower
the fixed-tape rival's cash more. These replays do not model opponent reaction.
The treatment JSON, exact comparison and panel manifest are in this directory.

## Independent reactive check

`scan_native_yarn_seeds.py` preselected the first eight seeds from a fixed
range whose public first two shops included `YARN_STORE` under incumbent
self-play. `reactive_yarn12.py` then ran incumbent versus itself as an exact
control and the candidate versus an actively reacting incumbent, both seats
for each seed. All 32 games were `DONE`; every treatment activated, and every
control game tied.

**Route 12 lost all 16 reactive seat-games** (mean margin -15,518.375 coins;
range -31,691 to -3,918). Across the 16 matched control/treatment games it
increased own cash by 78,186 total but increased the reacting rival's cash by
326,480. Native shop paths can diverge after the intervention, so these totals
describe the complete native policy effect, not a fixed-shop attribution.
The maximum candidate call was 914.9 ms under four-worker local contention,
close to the one-second action budget.

**Decision: reject.** The candidate does not move into `main.py` or Kaggle.
The 22-route fixed-tape gain was misleading for live competition strength;
no narrower selector should be claimed from these outcomes without a new
observation-time hypothesis and independent reactive evidence.

Reproduce:

```powershell
python -X utf8 diagnostics\top10_goal_20260926\create_yarn_panel.py
python -X utf8 route_panel_benchmark.py --candidate exp_yarn_route12_20260926.py --summary diagnostics\top10_goal_20260926\yarn22_controls6_summary.json --workers 8 --json-out diagnostics\top10_goal_20260926\yarn12_28routes.json
python -X utf8 diagnostics\top10_goal_20260926\compare_yarn12.py
python -X utf8 diagnostics\top10_goal_20260926\scan_native_yarn_seeds.py
python -X utf8 diagnostics\top10_goal_20260926\reactive_yarn12.py
```
