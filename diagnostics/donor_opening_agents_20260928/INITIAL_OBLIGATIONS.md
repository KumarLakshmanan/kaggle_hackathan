# Common initial procurement — static feasibility audit, 28 September 2026

A shared turn-0 purchase can leave a physical path into all four openings, but it requires explicit branch procurement, worker indexing and timing repairs. This audit creates no policy variant and runs no benchmark games. It does not prove that later purchases can be funded against a reacting rival.

## First uses

| Opening | Cow pickups | Sheep pickups | First wheat planting | First melon planting | First strawberry planting |
| --- | --- | --- | ---: | ---: | ---: |
| source 367 | farmer at1; hand4 at2 | hand1 at2; hand4 takes2 at3 | 2 | none on day0 | 13 |
| shared151 | farmer and hand4 at1 | hands1,2,5 at1 | 17 | 12 | none on day0 |
| shared150 | hands1,5 at2 | farmer at3; hand5 at6 | 5 | 7 | none on day0 |
| shared166 | hands1,5 at2 | farmer at3; hand5 at6 | 13 | 7 | none on day0 |

Source's third sheep can be bought during market1 before its pickup at3. Its strawberry seed can also be deferred beyond turn0, provided it is funded before unit13. Source needs one WHEAT seed in market1 for PLANT2; donor151's crop seeds are not physically needed until turn12 or17. The other two donors first need their melon seeds before7.

The source's original turn-0 wheat queue has intended net acquisition of six units. Four are picked up at1, and two are sold in its market1 queue. A common five-wheat purchase would therefore change that sale; six wheat preserves the source's intended early stock, with an explicit one-unit sale/removal needed for donors that originally bought five. No choice of initial wheat quantity is adopted by this audit.

## Fifth hand for shared151

Four hands hired at0 and a fifth hired during market1 produce the same fifth-hand spawn cell as the original five hires at0, because the farmer stays at(4,4). The third sheep must also be bought during market1.

The missing fifth hand can execute its original commands one turn late through CARE:

| Turn | Delayed command |
| --- | --- |
| 2 | PICKUP SHEEP1 |
| 3 | PICKUP WHEAT1 |
| 4 | WEST |
| 5 | BUILD_PASTURE |
| 6 | PLACE SHEEP |
| 7 | FEED |
| 8 | CARE |

Its original DROP8 carries nothing after sheep placement and feeding, so omit that empty drop and resume the original WEST9. Sixteen isolated native unit transitions verify identical farm/private state for that worker's original and delayed paths at the end of8. This preserves feed and care before midnight and its next melon planting at12. It assumes required goods actually exist; full opening execution and funding remain untested. The generic existing hire-recovery helper rejects building/placement sequences, so this requires a distinct explicit opening recovery controller.

## Hand permutation for shared150/shared166

Their original farmer moves NORTH at1, then hires all five hands. Hiring four one turn earlier changes the deterministic spawn ordering. Original donor hand indices1..5 must map to actual indices **4,1,2,3,5** after the fifth hire. Exact spawn-helper calculations are in initial_obligations.json. A consistent command/inventory mapping is necessary through the day; blindly retaining donor hand indices sends workers to the wrong tiles. Original five hires and already-paid animal orders must also be replaced with only the missing procurement, or obligations would be duplicated.

## Decision

Accept the timing and indexing facts as a concrete architecture lead. They justify a separately frozen shared-procurement feasibility study. Do not modify the current three whole-opening candidates or their60-game gate. Current public rival hands/cash could inform a selection rule at1, but neither that selection rule nor its economic value is tested here. Purchases occur after unit actions, so all goods needed at1 must either already exist or have the explicit delayed execution described above.

Evidence: initial_obligations.json, initial_obligation_audit.py, exact source/candidate hashes in pool.json and preflight.json. The audit used 16 isolated unit actions and spawn calculations; zero complete outcome games.
