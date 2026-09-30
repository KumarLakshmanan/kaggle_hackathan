# Expanded Kaggriculture player/code comparison — 2026-09-22

## Data collected

- Refreshed the score-sorted leaderboard to 200 teams. The added cohort is ranks 101–200 (scores 2,783.2–2,723.1).
- Downloaded 179 public replay action tapes from that cohort: 80 teams had two recent public episodes, 19 had one, and one had none. All tapes contain 719 actions and have distinct action hashes.
- Pulled all 100 entries from the next public code-listing page. Across the first three pages already collected, this gives 297 unique notebook references. The new page has 77 notebooks with code cells, 28 agent-like sources, 9 complete agent files, and 10 statically recovered embedded payloads.
- Notebook cells and embedded payloads were parsed, not executed. Some examples rely on local modules, `ctypes`, or dynamic `exec`; those are not safe drop-in policies.

## Current-agent replay benchmark

`main.py` (V53) was run with `PYTHONHASHSEED=0` against every new tape, once in each seat: 358 games over 179 paired routes. All games completed without agent/runtime errors.

| Measure | Result |
|---|---:|
| Paired route wins / losses | 71 / 108 (39.7% wins) |
| Individual game wins / losses | 134 / 224 (37.4% wins) |
| Mean / median coin margin | +344 / -294 |
| Mean agent time per call | 9.49 ms |
| Maximum observed call | 770 ms |
| Mean game wall time | 14.86 s |

The positive mean margin is skewed by a few large wins; most paired routes were losses. The README says rating depends on win/loss/tie, not the size of the coin margin, so this is not a strong rating result.

Largest repeated loss groups by mean paired margin were Leonid Kozinkin (2 routes, about −49.1k), yy (2, −26.0k), and LagrangianLocomotive (2, −24.0k). Jeryos had one especially large loss (about −33.1k).

## Failure-regime probe

On a spread of 24 V53-losing routes, the agent and replay player commonly had similar early farms. The mean cash gap (our agent minus replay player) moved from about +32 at turn 72 to −76 at turn 180, −617 at turn 360, −1,553 at turn 540, and −2,618 just before the final decision at turn 718. The hand-count gap stayed essentially zero throughout. By turn 540, our farms averaged 2.67 more empty pasture tiles, 0.33 fewer sheep, 0.12 fewer cows, and one fewer melon; 34/48 seat-games still had matching overall asset counts.

This points toward weaker middle/late conversion of land and livestock into banked cash, rather than opening or worker count alone. It is a correlation from this replay sample, not proof of a single cause. The turn-718 cash gap is also close to the eventual mean loss, suggesting the final decision rarely rescues a deficit already accumulated earlier.

## New code-agent comparisons

Two self-contained page-3 agents were statically reviewed and screened on 24 routes V53 lost (48 games per agent, both seats):

| Candidate | Notable logic | Paired wins on V53 loss routes | Errors |
|---|---|---:|---:|
| Page rank 66, “full engine teardown + my agent” | Hungarian/min-cost worker-to-task assignment; dynamic task and animal planning | 0 / 24 | 0 |
| Page rank 58, “Kaggriculture” | Adaptive hire controller, crop deadlines, milk-price and livestock targets | 0 / 24 | 0 |

Neither full policy is a viable replacement on this panel. The assignment solver is a potentially useful *isolated* experiment, but it has not been shown to improve V53 when transplanted, so it was not added to `main.py`. Several other extracted examples are starter-level, stochastic, or depend on non-portable local artifacts; keyword counts alone are not evidence of strength.

As a V53-wrapper control, the older V52 base was also run on those same 24 loss-route seeds: it won 0/24 too. V52 and V53 had identical paired margins on 23 routes; V53 was slightly better on one. The new cohort therefore does not implicate the V53 wrapper as the source of these losses.

## Additional experiments from the loss analysis

Three local V54–V56 rank-2 router variants were also screened on the same 24 V53-losing routes (48 games per variant). Each completed with zero runtime errors, zero paired wins, and a mean paired margin of −5,213.5 coins. They are not evidence of a robust improvement on this cohort.

A trace of the large Leonid Kozinkin loss (seed 726125330) exposed a possible livestock/capacity issue: at turn 265 our farm had 8 cows, 4 sheep, and 5 empty pasture tiles, while the replay farm had 8 cows, 8 sheep, and 2 empty pastures; by turn 360 our cash was about 5,147 lower. This is a lead for further testing, not proof that sheep purchases alone solve the deficit.

The first isolated V57 sheep-capacity wrapper was an invalid test: it checked for `SHEEP` in `market.inventory`, but that observation field contains trade goods and no animal-stock keys. An instrumented replay confirmed its animal-order sequence was exactly the same as V53, and its 24 paired margins exactly matched V53. It was discarded; no gain is claimed and it was not merged into the production file.

## Files and safety

- New leaderboard snapshot: `kaggle_leaderboard_live_2026-09-22_expanded.json`
- New replay tapes: `live_leaderboard_routes_2026-09-22_ranks101-200_2ep/`
- New code page: `kaggle_code_examples_live_2026-09-22_page3_top100/`
- Complete-agent static comparison: `KAGGLE_CODE_STATIC_COMPARISON_2026-09-22_page3.md`
- Embedded-payload static comparison: `KAGGLE_EMBEDDED_STATIC_COMPARISON_2026-09-22_page3.md`
- V53 full benchmark: `benchmark_main_v53_leaderboard_ranks101-200_2ep_2026-09-22.json`
- Candidate screen: `benchmark_codepage3_rank58_66_current_loss_routes_2026-09-22.json`
- Older router screen: `benchmark_v54_v55_v56_newleaderboard_losses_2026-09-22.json`
- Sheep-wrapper screen and confirming trace: `benchmark_v57_sheep_guard_current_loss_sample24_2026-09-22.json`, `analysis_artifacts/trace_v57_leonid_kozinkin_seed726125330.json.gz`
- Representative V53 trace used to identify the livestock/cash pattern: `analysis_artifacts/trace_v53_leonid_kozinkin_seed726125330.json.gz`
- Turn-72/180/360/540/718 captures: `benchmark_v53_capture72_loss_sample24_ranks101-200_2026-09-22.json`, `benchmark_v53_capture180_loss_sample24_ranks101-200_2026-09-22.json`, `benchmark_v53_capture360_loss_sample24_ranks101-200_2026-09-22.json`, `benchmark_v53_capture540_loss_sample24_ranks101-200_2026-09-22.json`, `benchmark_v53_capture718_loss_sample24_ranks101-200_2026-09-22.json`

The earlier round above did not change `main.py`; its hash statement is historical. No Kaggle submission command was run in that round.

## Follow-up: ranks 201–300 and code pages 4–5

This follow-up used a fresh score-sorted leaderboard snapshot containing 400 teams. The added ranks 201–300 span scores **2,720.2–2,675.2** (mean **2,697.73**). The replay downloader found **185 distinct public 719-action tapes** from all 100 teams: 85 teams supplied two tapes and 15 supplied one. Every tape passed the action-count and SHA-256 validation checks.

The next two public code pages added 200 listing entries with no overlap between the pages. Static extraction found:

- Page 4: 93 notebooks with code, 26 agent-like sources, 11 complete agents, and 9 embedded payloads.
- Page 5: 88 notebooks with code, 25 agent-like sources, 11 complete agents, and 13 embedded payloads.
- Across both pages: 44 extracted file instances and 39 unique source hashes after deduplication.

Notebook cells were never executed. Native-library candidates, suspicious oversized dynamic sources, and non-portable artifacts were excluded. The selected local source policies were AST-scanned before controlled execution.

### Candidate policy screen

Nineteen distinct policies were screened on 12 evenly spaced new routes, both seats (456 seat-games). The best source was the page-5 rank-94 embedded policy at **3/12 paired wins**, while the current agent won **4/12** on the same routes. Rank 100 reached 2/12 and rank 90 reached 2/12. Public-state/router claims in notebook titles were not accepted as evidence; their controlled results did not justify replacing the production policy.

The page-5 rank-12 economics policy initially exposed an import-harness issue (`dataclass` could not resolve its defining module). The benchmark loader was fixed to register imported modules in `sys.modules`; after the fix it completed 24 games with zero errors and **0/12 paired wins** (mean paired margin about **−121,982**). This is a harness-corrected negative result, not a policy failure caused by the original import bug.

### Isolated opening ablation

The current policy and a transparent direct-wheat opening variant were run on all 185 new routes in both seats:

| Policy | Paired wins/losses | Individual wins/losses | Mean margin | Mean call time |
|---|---:|---:|---:|---:|
| Current V52/V53-disabled base | 62 / 123 | 117 / 253 | +451 | 9.477 ms |
| Direct five-wheat opening | **66 / 119** | **126 / 244** | **+1,075** | 9.497 ms |

The opening change flipped four paired losses to wins and no wins to losses; 151 of 185 route margins were identical. It buys five wheat directly at step 0 instead of buying 20 and immediately selling 15, preserving the net wheat quantity. A smaller top-100 screen had one regression, so this is an evidence-backed improvement—not a claim of universal dominance.

The rule has now been promoted transparently into `main.py` as a guarded step-0 rewrite. A post-promotion 12-route check matched the standalone V58 wrapper exactly: **5/12 paired wins**, **7/12 losses**, zero errors. Compilation passed for `main.py`, `paired_benchmark.py`, `candidate_policy_pool_benchmark.py`, and `route_panel_benchmark.py`.

## Current artifacts and submission safety

- Expanded leaderboard: `kaggle_leaderboard_live_2026-09-22_top400.json`
- New replay panel: `live_leaderboard_routes_2026-09-22_ranks201-300_2ep/`
- Page-4/page-5 listings and downloaded notebooks: `kaggle_code_examples_live_2026-09-22_page4_top100/`, `kaggle_code_examples_live_2026-09-22_page5_top100/`
- Static reports: `KAGGLE_CODE_STATIC_COMPARISON_2026-09-22_page4.md`, `KAGGLE_CODE_STATIC_COMPARISON_2026-09-22_page5.md`
- Full baseline/ablation results: `benchmark_main_v52_ranks201-300_2ep_2026-09-22.json`, `benchmark_v58_ranks201-300_full_2026-09-22.json`
- Candidate screen: `benchmark_code_page4-5_ranks201-300_screen12_2026-09-22.json`
- Fixed rank-12 rerun: `benchmark_code_rank12_ecobot_ranks201-300_screen12_fixed_loader_2026-09-22.json`
- Post-promotion check: `benchmark_main_promoted_v58_ranks201-300_screen12_fixed_2026-09-22.json`

Current `main.py` SHA-256: `4FD95DD8C2C998B0368804F0C4A4088F66541DE74F4436CCBFE866BB58147C03`. No Kaggle submission was made, and no future submission should be run without explicit user authorization.

## V54 shop-route validation (2026-09-22)

The fresh live top-100 replay panel contained five `YARN_STORE -> ICE_CREAM_SHOP` cases where the existing route-9 policy lost every paired replay. A transparent route sweep over routes 0–12 found route 10 to be the only positive aggregate on the three additional seeds. The validated static route-table change was applied to the outer engine and its V49/V51/V52 embedded namespaces.

| Policy | Games | Paired wins/losses | Mean margin | Mean wall time |
|---|---:|---:|---:|---:|
| Previous `main.py` | 340 | 86 / 84 | +11,003.75 | 9.29 s |
| V54 route-10 table fix | 340 | **89 / 81** | **+11,188.77** | **9.24 s** |

The 12-route screen also improved from 6/12 paired wins and +5,496.79 to 8/12 and +7,034.79. No Kaggle submission was made.
