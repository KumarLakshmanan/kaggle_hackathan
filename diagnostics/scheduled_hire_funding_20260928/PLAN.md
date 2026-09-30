# Fund already scheduled workers — prospective 28 September 2026

## Mechanism and fixed intervention

In the exact 8dde Junliang Ye trace (episode 114254310), step 192 queues
four existing hires after 18 wheat purchases. Only two hires execute; eight
strawberry plants become weeds at step 215 after missing two days of water.
The extra two planned hires cost five coins. This is distinct from adding
unscheduled opening workers or buying another animal bundle.

Test one fixed rule on two separately backed-up parents: original main
4eeac9c3 and integrated experimental 8dde995d. The latter's independent
pilot is still running; neither its replay gains nor its qualification
transfer to this new candidate.

Only at the first turn of a day, move existing HIRE orders as a block
immediately before the first existing BUY_PRODUCT WHEAT order. Preserve
all other order positions relative to one another; add no orders or work.
Consider only a queue where at least one hire originally follows that
wheat purchase. Predict original/proposed market execution under idle,
current-queue mirror, and raw-schedule mirror assumptions (deduplicated).
Require in every scenario:

- All scheduled hires now execute, strictly more than originally.
- Seeds, land and all non-wheat shed quantities are unchanged.
- At most one wheat unit is sacrificed, and remaining shed wheat covers
  every currently unfed animal on the public own farm.

These are explicit approximations, not a forecast of full future profit.
The actual remaining feed/sale schedule and opponent response must be
measured in intervention traces and complete games. No seed, opponent
identity, private rival state or future shop is used by the rule.

## Frozen development screen

For each parent+rule file play both seats of six saved fixtures:
Junliang Ye 114254310, Yaroslav 114283577, kwa 114227779, DECEM 114267880,
Boey 114266440 and Majkel1337 114263239. Total 24 games. Original main and
8dde controls are the exact completed original-native panel rows, with
full reward/telemetry provenance. Save full intervention traces.

Each arm must have clean DONE/DONE/720 and zero policy errors; preserve
every winning seat of its own parent and rescue at least one formerly
lost fixture in both seats. No cash-only veto. Report which hires changed,
actual hired hands, feed shortages, early plant deaths, own/rival final
cash and paired margin. If neither arm qualifies, reject without widening
or retuning this rule. Preserve both files and all results.

If an arm qualifies, freeze the selected exact file, verify native parity
on these games and the full 50-target regression. Then declare a new
independent reacting pilot/confirmation protocol with fresh seeds before
any of those outcomes. Require wins/draws/losses improvement over its
parent and main, at least two reacting references, original shops, both
seats together, meaningful activation and whole-seed uncertainty. All 54
saved public wins and actual file-loader parity remain mandatory before
any local promotion. No promotion or upload follows from this screen.

The parent candidates, existing native plans and main remain untouched.
No Kaggle access is authorized.
