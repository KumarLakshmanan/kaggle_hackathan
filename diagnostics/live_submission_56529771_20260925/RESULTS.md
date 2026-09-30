# Kaggle submission 56529771: early public-match audit

The user explicitly authorized one upload of the frozen `main.py` (SHA-256
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`).
The Kaggle CLI accepted it with message `current main 2026-09-25 verified
baseline`; validation completed without an error. No experimental policy was
submitted. Its displayed rating started at 600.0 and reached **1078.8** when
the five public episodes below had completed. The rating is dynamic, not a
final rank or a predicted tournament outcome.

| Public episode | Actual opponent | Our cash | Their cash | Outcome |
| ---: | --- | ---: | ---: | --- |
| 112981997 | 巴啦啦能量 | 121,812 | 31,206 | Win |
| 112983149 | Niloofar Y. | 89,623 | 26,405 | Win |
| 112984264 | Abhiram Anil | 103,971 | 62,272 | Win |
| 112985402 | Lam Vo | 100,298 | 59,488 | Win |
| 112986520 | Ahmed Ehab Fathi | 89,902 | 63,055 | Win |

All ten player statuses were `DONE`. The downloaded Kaggle replays are the
five `episode-*-replay.json` files in this directory. For each, the
[parity script](replay_parity.py) extracted the opponent's **observed** 719
actions, then ran the unchanged local `main.py` against that fixed tape on the
episode seed in installed Kaggriculture 1.32.7. All five local runs reproduced
**both** final cash amounts and both statuses exactly. This validates the
local engine/harness for these cases, but a fixed tape still cannot show how
an opponent would adapt to a changed candidate policy. The extracted
`opponent-*.json.gz` routes are generated artifacts; they are not agent code.

Two additional direct **reactive** local checks ran the frozen main against
accessible public implementations on four preselected seeds each, both seats:

| Public implementation | Native games | Main wins | Result path |
| --- | ---: | ---: | --- |
| HarvestForge-X readable extraction | 8 | 8 | `../top50_current_2026-09-24/main_vs_harvestforge_reactive_4seeds_20260925.json` |
| Koushikrudra public H6 extracted agent | 8 | 8 | `../top50_current_2026-09-24/main_vs_public_h6_reactive_4seeds_20260925.json` |

These are small, accessible-public-code regression checks. They are not
evidence of dominance over the current private leaderboard or all possible
opponent policies. The more difficult historical top-50 fixed-action replay
panel remains 67/100 route-pair wins; current live matches have not yet
sampled enough strong opponents to resolve that gap.

Reproduce the Kaggle-vs-local parity check from the workspace root:

```powershell
python -X utf8 -m diagnostics.live_submission_56529771_20260925.replay_parity
```
