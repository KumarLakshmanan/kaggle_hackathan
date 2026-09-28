# Finite compatible-route development search — 2026-09-28

This separate experiment follows the rejected `61a1dcd6` pilot. Its three
complete replacements did not rescue any top-20 failure, but the BRUNCH
replacement moved DECEM's margin by +57,049 per seat. The finite source
inventory contains 10/10/12 distinct complete schedules with the same
first 144 actions as the three relevant incumbents. Test that whole bounded
set as development before concluding that this compatible route family
cannot rescue these fixtures. Do not alter the earlier rejection.

## Sources and mechanism

Incumbent main SHA-256:
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Frozen 30-loss plus top-20 fixture manifest SHA:
`524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.

Group A: first shops BRUNCH_SPOT / BRUNCH_SPOT, original 113371344.
Group B: YARN_STORE / FARMERS_MARKET, original 113661901.
Group C: SMOOTHIE_SHOP / ICE_CREAM_SHOP, original 113441389.

Enumerate every route already embedded in main with exactly the same
action dictionaries through step 143 as its group's original. Deduplicate
by entire 719-action content, retaining the lexicographically lowest route
ID as its representative. Freeze the resulting pool and source hashes
before running outcomes. Each variant changes only one public shop-pair
branch and every descendant mapping under it, committing to that whole
route from step 144. Current market layers are retained. No current-game
seed, team identity, private rival state or future shop appears in a policy.

## Development fixtures and choice

Use all affected frozen fixtures known from the original-seat loss replay
state and the exact top-20 baseline turn-144 captures:

- A: DECEM, Yizhou, and public loss `live-114289228` (leave you).
- B: Boey.
- C: Vadim Vasilenko and Kaggledew Valley.

Both seats, native engine 1.32.7, original shops, 720 turns, hidden
configuration seed. All 32 variants × their group's fixture seats give
128 games. Every game must finish DONE/DONE/720 with no recorded errors.
Checkpoint exact jobs; no parameter changes or outcome-filtered exclusions.

The unchanged incumbent mapping is an explicit option in each group.
Eligible choices must preserve every incumbent winning seat in that group.
Select per group by: most both-seat wins, then most win points (win=1,
draw=0.5), then largest summed paired margin delta, then lowest route ID.
If neither wins nor win points improves on the incumbent, retain the
incumbent regardless of cash. Freeze the three resulting choices before
any wider outcome. Passing development requires at least one of the three
top-20 failures to become a both-seat win and no affected winning control
to regress. If none qualifies, reject this entire route pool for these
targets rather than tune another trigger on the same results.

If a candidate qualifies, package its chosen public shop-pair mappings and
test all 50 frozen fixtures in both seats, requiring at least one new
both-seat win and no lost incumbent winning seat. These remain development
and regression results, not independent validation. Freeze fresh native
activation-scan ranges, reacting references, win-point gates and seed-paired
uncertainty before reading any reacting outcome. Only native-qualified
candidates can proceed toward promotion; combine with the opening selector
only as a separate checked candidate. Main, backups and Kaggle stay intact.
