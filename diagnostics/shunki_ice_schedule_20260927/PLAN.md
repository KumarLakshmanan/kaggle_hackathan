# Replace an incomplete ICE/BRUNCH action schedule — 2026-09-27

The frozen later-shop candidate's ICE_CREAM_SHOP/BRUNCH_SPOT fallback uses
public episode 113445495. It buys 112 wheat seeds after turn 216 but issues
only 54 wheat planting actions; it buys ten strawberry seeds but plants two.
Episode 113383763 from the same public policy has an **exact 241-action
common prefix**, buys the same quantities and schedules all 112 wheat and
ten strawberry plantings. Its worker schedule diverges at turn 243. This
supports testing a complete schedule replacement, not an isolated seed swap.

New artifact: `exp_shunki_ice_schedule_20260927.py`, based on frozen source
`68aad090...`; change only the seven route-map entries selecting 113445495
to select 113383763. The healthy schedule is already embedded. Keep the
other existing routes, including the compatible third-shop Yarn route.
Audit all affected incoming/outgoing route transitions for exact prefix
compatibility; unrelated existing prefix mismatches must be recorded rather
than claimed fixed. Freeze candidate bytes before outcome tests.

Development: both seats against every saved top-100 tape whose original
candidate opens ICE/BRUNCH, on its original seed. Compare with the stored
original-candidate result, diagnose cash and outcome changes. Require no
lost existing route wins and at least one newly won route before escalation.
These familiar replay tapes are development data only.

Independent confirmation: select the first eight native ICE/BRUNCH seeds
from 2632000–2633023 using only the first 144 turns of original candidate
versus reacting unchanged main, seat 0. Selection reads shops, never final
scores. The candidate variants have identical actions through turn 240 in
this branch, so selection precedes treatment. Then run original candidate,
new candidate and incumbent versus reacting main on each selected seed,
both seats, original shops. Also compare the two candidates against reacting
previous main on these seeds. Before scanning any confirmation seed, the
confirmation rule is clarified to avoid requiring six additional wins when
fewer than six losses are available: require DONE/DONE throughout, at least
six of eight seed-block win points against each submitted main, no fewer
win points than the original candidate against either, at least one
additional seed-block win point pooled across both, and no new double-seat
loss on a previously double-seat win. Require at least four of the eight
seed pairs against current main to expose the changed schedule (third shop
other than Yarn/Pizza); report activation frequency and any changed shops.

If these gates pass, run the new candidate against the full saved panel
and verify the final Kaggle loader in both seats before considering
promotion. The broader pending win-rate review evaluates the unchanged
original candidate and cannot be labeled validation of these changed bytes.
No upload until a candidate earns promotion and the latest user upload
authorization is still available.

**User scope update, before this final panel run:** the user changed the
target to the current top 50 and explicitly requested a fresh download.
`diagnostics/top50_refresh_20260927_2303/PLAN.md` supersedes the older
top-100 rerun requirement. Test every one of those 50 in both seats.
