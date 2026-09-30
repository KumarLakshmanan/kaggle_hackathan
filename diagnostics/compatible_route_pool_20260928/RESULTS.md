# Compatible route pool — 2026-09-28 01:59 UTC

**Reject after the reacting pilot (2026-09-28 02:18 UTC).** The saved-panel
gain is real on those tapes, but the candidate fails the frozen
reference-specific win-point gate. Main remains exact uploaded 4ee.

The finite pool contains 10 BRUNCH/BRUNCH schedules, 10 YARN/FARMERS schedules
and 12 SMOOTHIE/ICE schedules, deduplicated by complete actions. Every route
shares its group's incumbent actions through step 143. The original 128
games and 44 missing affected-control games all completed DONE/DONE/720
without recorded policy errors. As documented in CONTROL_FIX.md, 44
unaffected-control games are retained but excluded from route selection;
the corrected selection uses all 128 relevant games, with both seats.

The unchanged policy was an explicit option. The predeclared selection rule
preserves incumbent wins, then maximizes both-seat wins, then win points,
then summed paired margin delta. It selected two whole-route replacements:

| Observed first two shops | Route | Affected saved fixtures, margin in each seat |
|---|---:|---|
| BRUNCH_SPOT / BRUNCH_SPOT | 113373693 | leave you +3,256; DECEM -10,636 |
| SMOOTHIE_SHOP / ICE_CREAM_SHOP | 113377257 | Vadim +3,771; Yizhou +102,559 |
| YARN_STORE / FARMERS_MARKET | Keep incumbent | No tested route rescues Boey; some regress Kaggledew |

The single combined candidate is
`b6ebf9ad0a40b85a45f93cf1605126f34c7bd729c197a32cb872a8f2c716147c`,
saved as `candidate_selected.py` and backed up in the workspace root as
`main_candidate_compatible_routes_20260928_b6ebf9ad.py`.

## Full saved-panel integration — 2026-09-28 02:07 UTC

**Pass:** the single combined file finished all 100 native games, with
DONE/DONE/720, no recorded errors, exact selected-component rewards on
affected fixtures, and exact incumbent rewards everywhere else. Every
incumbent winning seat is preserved.

| Saved panel | Incumbent both-seat wins | Candidate both-seat wins | Candidate seat W/D/L |
|---|---:|---:|---:|
| 30 public losses | 0/30 | 1/30 | 2/0/58 |
| Current top 20 | 17/20 | 18/20 | 36/0/4 |
| Combined | 17/50 | 19/50 | 38/0/62 |

Evidence: `full_panel.json` and its raw checkpoint. This qualifies the file
for the prospective reacting pilot; it does not qualify promotion. The
bounded prefix-only activation scan has started, using the frozen native
plan SHA `074325a9eb5d3209ef69a0277c8a7bdfe522036cd0f165fd85e8dc16a9ec8ff0`.

## Reacting pilot — completed 2026-09-28 02:18 UTC

The bounded outcome-blind scan completed 240 prefixes. It found the first
four eligible seeds per reference after scanning 112 seat-0 seeds against
4ee and 120 against market. Both seats activated on every selected seed.
The resulting 32 full games all finish DONE/DONE/720 without recorded
policy errors; all 16 candidate games activate the selected route layer.

| Reacting reference | Incumbent seat W/D/L | Candidate seat W/D/L | Win-point difference |
|---|---:|---:|---:|
| Current 4ee | 1/6/1 | 7/0/1 | +3 |
| Public market policy | 6/0/2 | 4/0/4 | -2 |

The pooled win-point difference is +1, but the predeclared gate also
requires nonregression on each reference. Against market at seed 2909080,
the incumbent wins both seats by 12,164; the candidate loses both by 5,483.
This rejects the exact combined candidate. This is an outcome-based gate,
not a new cash-margin threshold. No confirmation, public-win regression,
file-loader promotion test or main replacement follows. The source and
root-folder backup are retained as rejected research artifacts. Do not
retune on these pilot seeds and call them independent confirmation.

Evidence: `pilot_eligibility.json`, `pilot_prefixes.jsonl`,
`native_pilot.json` and `native_pilot.jsonl`.

These saved-replay outcomes are development evidence only. Do not infer a
leaderboard gain or combine this candidate with the rejected opening
selector. DECEM and Boey remain unsolved; the full 50/50 objective is unmet.

Evidence: pool.json, screen.json (original coverage), controls.jsonl,
corrected_screen.json (128 relevant games), selection.json, PLAN.md and
CONTROL_FIX.md. No Kaggle access or upload.
