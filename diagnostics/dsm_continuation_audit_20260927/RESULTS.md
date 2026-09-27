# Rejected DSM continuation — first divergence identified

Four passive native traces reproduce both original cash totals exactly on
seeds 2693100 and 2693103, both seats. This is the first and worst paired
seed from the rejected pilot, selected for diagnosis, not fresh validation.
All cash is accounted for. The original dd420938 rejection remains.

Failed purchase counts alone were misleading. On seed2693100, the complete
physical/private state matches its selected source 113869422 at **every
turn 72–144**, despite several failed seed requests. At turn72 both have
55 coins. Those requests do not demonstrate a new missing-supply defect.

For seed2693103, source114016188 also matches every physical/private field
through turn119. Native/source turn72 cash is 55/53. The first divergence is
a new weed at (0,0) at turn120. Through turn140 this weed is the **only**
physical/private difference. The planned strawberry planting at turn140
then fails, leaving an unused seed; water and later work at that plot fail.
This prevents exact state matching at turn144 and precedes severe later
schedule divergence. The source's early failed cows/seeds cannot explain
that first physical divergence.

Actor4 reaches (0,0) for commands PLANT STRAWBERRY at140, WATER at141,
PASS at142 and143. A same-day DIG/PLANT/WATER replacement over140–142
could restore the intended crop without displacing another productive
command. This is a concrete **untested** repair hypothesis. It must reserve
an existing seed, exclude competing same-crop plantings during the window,
and verify the exact repaired endpoint plus complete-game market effects.

**Decision:** accept the passive source comparison; reject a generic queue
reordering response to these failures. Develop a separate narrow weed repair
experiment if proceeding. No new policy strength, promotion, or upload.

Evidence: audit.json, source_comparison.json, compare_sources.py, traces/.
Source replay hashes are verified before comparisons. The source comparison
initially assumed every archive was gzip; that read-only harness error was
fixed to accept the already preserved plain JSON files too. No game rerun
or policy change was required by that fix.
