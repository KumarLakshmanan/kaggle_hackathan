# Opening fork v2 — local development results

Updated 2026-09-28 01:36 UTC. **Reject the selector for promotion: its
native reacting gate failed.** Main remains the exact uploaded 4ee file.

The stronger prefix gate passed **110/110** comparisons. In all 100
incumbent comparisons the entire observation at step 3 matched, ignoring
only runtime remainingOverageTime. The ten V43 controls had the specified
physical parity, and both arms saw identical public observations at step 1.

All **200/200** full development games finished DONE/DONE at 720 frames.
The current-policy arm exactly reproduced every incumbent reward margin
and outcome. The V43 arm's different market response rescued losses but
regressed five previously won top-team fixtures.

| Arm | Saved loss replies won in both seats | Saved top-20 won in both seats | Seat W/D/L |
|---|---:|---:|---:|
| Current 4ee / parity arm | 0/30 | 17/20 | 34/0/66 |
| V43 arm | 13/30 | 12/20 | 51/0/49 |
| Selected bounded rule (development) | 7/30 | 17/20 | 49/0/51 |

The selected rule uses V43 when the opponent has more than 1,000 coins
after its first turn and its net first-turn WHEAT purchase is at most eight;
otherwise it uses the current-policy arm. Its 24/50 both-seat sweeps preserve
every incumbent winning seat. Recovered loss replies are high frequency
farming, Dieter, Vlas Veles, two separate Ghost Rule episodes, leave you and
Navier-stokes. offhand is a split result, not a both-seat win. DECEM, Boey
and Vadim remain losses.

The unconstrained best rule scored 29/50 but lost two incumbent winning
seats, so it fails the preservation gate. The hindsight per-fixture arm
oracle ceiling is 30/50 and is not a deployable result. The selected rule's
summed margin delta is -258,954 despite 15 extra seat wins; win points are
the frozen primary objective, so that margin alone is not a rejection.

**Decision: pass the development gate into separate qualification, not
promotion.** Candidate `fb6c54136017eccc9df2652d2826a14346520c6c0d51ce855321ff51be6693f2`
is packaged in `candidate_selector.py`; the source arms and rule are hashed
in `selector_manifest.json`. The rule was fitted on all 50 saved fixtures.
These fixed replies are not independent or reacting validation. The full
goal remains 50/50, including 20/20 top-team replies.

The packaged candidate completed **100/100** integration games, each
DONE/DONE/720, with zero recorded errors including the previously hidden
V43 fallback. Its selected arm and both final rewards exactly matched the
development components in every case. Configuration seed was hidden.
The exact candidate is also backed up in the workspace root as
`main_candidate_observable_opening_20260928_fb6c5413.py`.

## Native rejection

The frozen pilot was stopped after 68 distinct completed games because its
reference-specific nonregression gate had become mathematically impossible.
All completed games finished DONE/DONE/720 with no recorded errors.

| Reacting reference | Incumbent W/D/L | Selector W/D/L | Completed games per version |
|---|---:|---:|---:|
| Current 4ee | 1/10/1 | 1/10/1 | 12 |
| V43 | 12/0/0 | 12/0/0 | 12 |
| Public market policy | 10/0/0 | 0/0/10 | 10 |

Against the public market policy, the selector chooses V43. Even winning
all six remaining candidate games would yield only six points, below the
incumbent's ten points already recorded. The pilot therefore cannot pass;
the untouched confirmation block and 54-win regression stage were not run.
The simpler first-turn classifier does not distinguish this reacting
market policy from the saved opponents it helped. Do not infer a native
gain from the seven recovered fixed replies or retune on these pilot seeds.

The checkpoint contained 32 duplicate job keys. Their hashes, actions'
public captures, telemetry, terminal rewards and statuses agree exactly;
only execution timing differs. Their execution provenance is unconfirmed.
`audit_pilot_rejection.py` retains the raw checkpoint and counts every
candidate/reference/seed/seat key only once. `pilot.json` explicitly records
68 distinct games, `complete=false`, `terminated=true`, and the irreversible
failure bound. No duplicates are treated as independent evidence.

**Final decision: reject exact fb6c5413 for promotion.** Keep its source and
development evidence as research. Main and Kaggle remain unchanged.

## Failure mechanism on one already-scored native seed

Passive event traces on seed 2908000, seat 0, reproduce both terminal cash
pairs exactly: current 4ee 130,300 versus rival 108,703 (+21,597), selector
68,737 versus rival 90,054 (-21,317). These are repeats of existing outcomes,
not another independent test. Both runs keep native shop generation.

The selector has no animal disappearances and buys both planned additional
land quadrants. It sells 264 MILK for only 3,202 coins, compared with the
incumbent's 138 MILK for 7,538. Meanwhile current 4ee earns 80,810 from WOOL
versus 6,099 for the selector. The native shop paths differ (current first
shop YARN_STORE; selector first shop BRUNCH_SPOT), so this does not isolate
a single causal product substitution. It does show that more milk production
is not a competitive gain and does not support a generic extra-feed or
land-retry patch. There are four insufficient-cash unit-order failures in
the selector trace, but their downstream effect has not been isolated.

Evidence: `native_market_{old,new}_s2908000_p0.json.gz`,
`trace_native_failure.py`, `analyze_native_failure.py`, and
`native_failure_ledger.json`. Accept this mechanism diagnosis; no new
strategy or promotion is justified by this one repeated seed.

The failed automatic worker-recycling harness was replaced by explicit
finite process-pool batches. Completed results are checkpointed, dynamic
policy modules are removed and garbage-collected, and exact candidate and
fixture hashes are checked on resume. This changed the harness only.

Reproduction: `verify_physical.py`, `screen_arms.py`, `select_rule.py`,
`build_selector.py`, then `qualify.py integration`, `qualify.py pilot`, and
conditional `qualify.py confirmation`. The independent gates are frozen in
`NATIVE_PLAN.md`. No Kaggle access, upload or main edit.
