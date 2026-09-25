# Alternative-agent audit — current top-50 panel

## Finding

**No stored candidate is a substantially stronger alternative that rescues several current losses without reversing winning controls.** The frozen `main.py` baseline is 67/100 route-pair wins and 133/200 seat wins (SHA-256 `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`). All conclusions below are limited to the 2026-09-24 top-50 route manifest; route comparisons use the exact tape/action hash and episode record, with both candidate seats. These are fixed-action replays, not adaptive match estimates. I did not use seed-grouped `paired_results` or treat other route panels as matched.

Among the stored top-50 outputs, Haide is the only full-panel public-agent comparison; no matched evidence was found for another public source. The reactive Haide check is 16/16 main wins on seeds 300001–300008, but it is a separate opponent/matchup panel.

## Comparable candidate evidence

| Candidate and exact file | Same-panel evidence | Decision |
| --- | --- | --- |
| Public Haide implementation: `kaggle_extracted_agents_2026-09-21/haideptry_master_2965.py` (SHA-256 `949e2eed410169f7a651e82bb37f6484a332a833d8c75937122701b90fc7658c`); result `diagnostics/top50_current_2026-09-24/haide_100routes.json` | Same 100 routes/100 action hashes, both seats; all 400 games across baseline/candidate are `DONE`. Three loss→win flips: URAD e112940084, −20,026→+57,158; feles99 e112939452, −346→+5,876; midnq e112940186, −13,548→+4,978. But three win→loss flips: Sida Zuo e112937057, +6,310→−2,830; arutyunoff e112936707, +181,644→−49,880; dodsters e112939378, +13,520→−15,282. Net route wins remain 67/100; mean seat margin falls from +22,160.29 to +21,794.16. URAD’s apparent rescue coincides with our cash −13,410 and replay-rival cash −90,594, so it is not an own-cash improvement. | Not stronger; exactly as many control reversals as rescues. |
| Forced route-9 cohort branch: `exp_route_cohort_selector_20260924.py` (SHA-256 `25e619422aff8972b9656cf169ef9c4fa06857ca6e71a04ccdf7c60f42cd0836`); result `route_force_9_ledger_panel_seeds.json` | Same route tapes on a 14-route loss/control panel, both seats. It converts ActiveMusyoku e112941285, −32,066→+64,016, and Boey e112940236, −39,954→+4,858. It also reverses three wins: Gleb Tumanov e112939403, +1,686→−16,980; Sida Zuo e112937057, +6,310→−18,834; istinetz e112939139, +8,090→−17,542. | Two rescues, three control regressions. Moreover, route 9 was forced by a diagnostic override from steps 144–647; this is not evidence for an observation-based selector. |
| `main_straw_tomato_swap_exp_2026-09-24.py`; result `straw_tomato_swap_100routes_20260924.json` | Exact 100-route panel: ActiveMusyoku e112937075 improves −16,466→−10,102 but remains a loss; Gatswei e112936562 worsens −13,136→−15,328. No pair outcome changes (67/100). | No rescue; one loss worsens. |
| `exp_h6_hinge_price_20260924.py`; result `h6_hinge_100routes_20260924.json` | Exact 100-route panel; 42 margins move, but no route outcome changes (67/100). | No win gain. |

The smaller tomato-start/two-shop screens also report no rescued loss; the day-6 tomato screen had no eligible route in its 12-route panel, and its separate ActiveMusyoku replay remained a loss in both seats while own cash fell. None supplies a no-control-reversal alternative.

## Observation-legal feature: hypothesis only

The most defensible feature to test next is **own realized receipts per successfully sold unit, tracked against the currently visible market quote/inventory for that product**. Own cash and shed changes plus public market state are observable; the policy must not use team, episode, replay ID, or seed. The ledger shows why it is worth testing: Excluding e112933589 and control HowardLeeTW e112935831 each sold 249 strawberries, yet own receipts differed by 20,076; ActiveMusyoku e112941285 and control Gleb Tumanov e112939403 each sold 247, with a 21,007 receipt gap (about 10.72 vs. 95.77 coins/unit). These are descriptive comparisons across different tapes, not causal A/B evidence. Treat this as a selector hypothesis—not a validated trigger or promotion recommendation—and require same-tape tests with controls before adoption.

## Files inspected

Paths below are relative to `H:\hackathan`. The initial recursive inventory was path-only; I did not read every public-agent source or run a new benchmark.

**Reports and route manifest**

- `diagnostics/top50_current_2026-09-24/RESULTS.md`
- `diagnostics/top50_current_2026-09-24/HAIDE_COMPARISON.md`
- `diagnostics/top50_current_2026-09-24/LOSS_STRATIFICATION_LUNA.md`
- `diagnostics/top50_current_2026-09-24/loss_clusters.md`
- `diagnostics/top50_current_2026-09-24/LEDGER_12_ROUTE.md`
- `diagnostics/top50_current_2026-09-24/ROUTE_COHORT_SCREEN.md`
- `diagnostics/top50_current_2026-09-24/CROP_COHORT_SCREENS_20260924.md`
- `diagnostics/top50_current_2026-09-24/routes/summary.json`

**Benchmark JSONs read or parsed**

- `diagnostics/top50_current_2026-09-24/main_100routes.json`
- `diagnostics/top50_current_2026-09-24/haide_100routes.json`
- `diagnostics/top50_current_2026-09-24/haide_25routes_screen.json`
- `diagnostics/top50_current_2026-09-24/main_vs_haide_reactive_8seeds.json`
- `diagnostics/top50_current_2026-09-24/route_force_0_6losses.json`
- `diagnostics/top50_current_2026-09-24/route_force_9_6losses.json`
- `diagnostics/top50_current_2026-09-24/route_force_128_6losses.json`
- `diagnostics/top50_current_2026-09-24/route_force_9_ledger_panel_seeds.json`
- `diagnostics/top50_current_2026-09-24/route_selector_baseline_excluding.json`
- `diagnostics/top50_current_2026-09-24/straw_tomato_swap_100routes_20260924.json`
- `diagnostics/top50_current_2026-09-24/h6_hinge_100routes_20260924.json`
- `diagnostics/top50_current_2026-09-24/tomato_day15_12seed_pilot_20260924.json`
- `diagnostics/top50_current_2026-09-24/tomato_two_shops_12seed_pilot_20260924.json`
- `diagnostics/top50_current_2026-09-24/day6_tomato_11seed_pilot_20260925.json`
- `diagnostics/top50_current_2026-09-24/day6_tomato_active_pilot_20260925.json`
- `diagnostics/top50_current_2026-09-24/carrot_cohort_first20_20260924.json`
- `diagnostics/top50_current_2026-09-24/carrot_cohort_6seed_pilot_20260924.json`
- `diagnostics/top50_current_2026-09-24/carrot_replant_6seed_pilot_20260924.json`

**Agent/policy source**

- `main.py` (read-only)
- `kaggle_extracted_agents_2026-09-21/haideptry_master_2965.py`
- `exp_route_cohort_selector_20260924.py`
- `main_straw_tomato_swap_exp_2026-09-24.py`
- `exp_h6_hinge_price_20260924.py`
- `exp_agent_day6_tomato_cohort_20260924.py`
