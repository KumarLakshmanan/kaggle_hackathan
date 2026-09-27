# Two-pass ordering of existing market trades

Frozen 2026-09-27 before candidate games. Parent: uploaded c68fa46f.
Purchase-only43d and planned-funding31ce remain rejected; combined7673's
separate rare-funding gate is still running. This is a different search
over existing orders, not a reinstatement of those candidates.

## Intervention

After the complete c68 action, make at most two best-improvement passes.
Each pass enumerates at most 48 distinct permutations moving an existing
SELL or BUY_PRODUCT earlier. Evaluate all proposals relative to the
unchanged post-c68 action against a passive rival, a rival using that
post-c68 queue, and (when different) a rival using the original schedule
queue. Use c68's embedded native market simulator and hypothetical mirror
stock, never hidden opponent information. Keep the rival scenarios fixed
through both passes.

Every proposal must preserve own resource signature and own cash under
the passive forecast; preserve both players' resource signatures and not
reduce own cash in every non-passive forecast. Require nonnegative
relative-cash gain in every non-passive forecast and positive total gain.
Rank by minimum relative gain, then summed relative gain, then minimum own
cash gain. The second pass must improve this same score over the first.
Never add, remove or resize orders, change physical commands, or modify
the existing turn-144 gates. Record first/second-pass activations and errors.
These are hypothetical guards; native tests decide empirical strength.

Freeze the source hash and root backup before outcomes. Keep main.py c68.

## Native development pilot

Seeds **2708000–2708007**, both seats versus reacting c68 and reacting
purchase-only43d: 32 full native games, original shops, agent-visible seed
masked. Require >=12/16 win points versus c68 and >=9/16 versus43d;
at least six paired seeds with an actual new queue against each reference;
and at least four paired seeds against each reference with a second-pass
improvement in both seats. All games DONE/DONE/720 and zero agent errors.
Complete the frozen cohort and reject on any failed gate; no extension.

## Conditional panels and confirmation

If the pilot passes, test all fresh current100 and original50 recorded
matchups in both seats. Require >77 current100 sweeps, >36 current50
sweeps, >=44 original50 sweeps, no lost incumbent winning seat, all DONE
and zero errors. These are regression/development tapes, not private
reacting agents; do not redefine the user's all50/top10 goal.

After passed panels, use untouched **2709000–2709015**, old c68/new candidate
versus c68,1f221922,489fe8e4,C95, both seats (256 games). Require >=24/32
new points versus c68, no per-reference point regression, and positive
lower95% percentile bootstrap bound on pooled paired-seed point gain
(10,000 resamples, seed2709099, keeping both seats and all references
together). All DONE/720 and zero errors. Margins diagnose mechanisms.

Both-seat Kaggle file-loader parity on the first pilot seed with two-pass
activation in both seats, including exact all-action/native-cash agreement,
is required before promotion. Any upload requires fresh explicit approval.
