# Preparation repair — 28 September 2026

The first coverage-preparation attempt stopped before candidate generation
or new policy games because top-team fixture records use `source_seat`
rather than the public-cohort field `source_candidate_seat`. Since the
grouping uses shared public shops, preparation now reads both players'
step-144 shop lists and requires equality. For top-team fixtures it also
checks both existing 4ee baseline turn-144 captures against that pair.

No route, fixture membership, selection rule or outcome was changed. The
initial attempt produced no pool or candidate file. The repaired
preparation still fails closed if the asserted affected coverage differs.

The next assertion correctly detected archived/counterfactual shop
differences. `COVERAGE_CORRECTION.md` records the correction and the
208 completed source prefixes; that issue is resolved before pool creation.

The first full screen recorded two clean original-main control games, then
its progress formatter attempted to print a partial-plant counter absent
from original main. The process exited with KeyError after its submitted
batch finished. The two written results are preserved; other unconsumed
batch results are not counted. The formatter now displays zero for the
counter absent in this unmodified control. Policy code, pool, jobs, fixture
hashes and selection gates are unchanged. Resume the same checkpoint after
the verified terminal exit; any repeated jobs remain development games.
