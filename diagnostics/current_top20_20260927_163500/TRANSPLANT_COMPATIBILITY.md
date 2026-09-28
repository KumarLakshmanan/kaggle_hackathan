# Shop-reveal transplant feasibility — 2026-09-27

The DECEM and Majkel1337 full public action tapes lost all 12 fresh original-shop
pilot games against a reacting 4ee incumbent. Their source seeds *do* reproduce
the first two recorded shops, so I compared the incumbent's farm with each
recorded tape farm and the same tape replayed as a native opponent on that
source seed. The observations agree on the physical target layout. This check
does not run downloaded code.

| Tape | Reveal | Public shops | Our cash / tape cash | Our occupied sites matching tape coordinates | Our crop / animals | Tape crop / animals |
| --- | ---: | --- | ---: | ---: | --- | --- |
| DECEM | 72 | BRUNCH_SPOT | 402 / 50 | 9 / 25 | wheat 18, strawberry 2; cow 2, sheep 3 | wheat 9, strawberry 2, melon 8; cow 3, sheep 3 |
| DECEM | 144 | BRUNCH_SPOT, BRUNCH_SPOT | 860 / 661 | 8 / 25 | wheat 7, strawberry 10; cow 4, sheep 4 | strawberry 9, melon 8; cow 5, sheep 3 |
| Majkel1337 | 72 | PIZZA_SHOP | 399 / 7 | 11 / 25 | wheat 18, strawberry 2; cow 2, sheep 3 | wheat 9, melon 10; cow 3, sheep 3 |
| Majkel1337 | 144 | PIZZA_SHOP, SMOOTHIE_SHOP | 811 / 570 | 5 / 25 | wheat 6, strawberry 11; cow 4, sheep 4 | melon 14, strawberry 3; cow 5, sheep 3 |

Cash is from the native 4ee-vs-tape games immediately before the reveal
action. The recorded source-tape cash is within 0–5 coins of the native tape
cash at these checkpoints, with identical crop/animal coordinate layouts.
All three farms hold only NW land at both reveals. Cash being higher for the
incumbent cannot create the missing melon plots or reposition existing
pastures, and later taped worker commands use those coordinates.

At step 72/144 the day reset leaves zero hands and farmer `[4,4]` on both
sides, which masks the different physical schedule. In the preceding final
hours (steps 71/143), DECEM's tape has five hands versus our four/two, with
**zero** matching hand positions at both checkpoints. Majkel has four/five
hands versus our four/three, with two/zero matching positions. At step 71
our farmer is `[2,4]`, DECEM's is `[1,2]`, and Majkel's is `[0,0]`.
At step 143 our farmer is `[0,1]` versus DECEM `[0,0]`; in the Majkel
match both farmers are `[0,0]` and `[4,4]` respectively. One turn after the
second reveal (step 145), DECEM has nine hands versus our three, Majkel has
five versus our four, and the taped farmer is already `[4,3]` versus our
`[4,4]` in both matches. Their day-six market actions hire against the taped
farm's prior investment and production schedule.

The incumbent and each tape have different actions at **every one of the
first 144 steps**, beginning at step 0. The shop reveal is too late to
choose this complete schedule: its first six days commit to a distinct
melon/cow layout and worker route before the first shop is known. A direct
step-72 or step-144 suffix splice would start from the wrong tile graph,
inventory, worker count and positions, even on the tape's own source seed.
No executable shop-conditional transplant follows from these two public
tapes. **Reject the splice and stop this line; no candidate or activation
seed panel was made.** A future coherent opening-to-terminal policy would
be a new experiment, requiring a frozen reactive native gate.

Machine-readable checkpoint profiles, coordinate sets and comparison counts:
`transplant_compatibility.json`; extraction code:
`audit_transplant_compatibility.py`. Source identities and action hashes:
`manifest.json`. Native full-tape pilot: `FULL_TAPE_PILOT_RESULTS.md`.
