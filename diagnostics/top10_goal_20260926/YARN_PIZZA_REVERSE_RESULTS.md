# Complete route alternatives for Yarn Store then Pizza Shop — 2026-09-26

## Selection and hypothesis

In the new September 26 top-100 saved-route panel, three large losses share
the original first two shops `YARN_STORE,PIZZA_SHOP`: mtmr_s1, YumeNeko and
Lucas Boesen. The incumbent route selector forces the sheep-heavy route 9
for all Yarn Store pairs. I froze those three losses and two older wins with
the same first-shop order (RS Turley and 吃白饭的大肥鱼) before testing complete
route schedules 100, 123 and 125. The previous route-125 experiment covered
the *reverse* `PIZZA_SHOP,YARN_STORE` order; this is a separate observation.
The candidates route only on the public first two shops, never episode/seed
identity or unrevealed future shops.

All 40 baseline-plus-candidate original-shop seat-games ended `DONE`:

| Saved route | Current paired margin | Route 100 | Route 123 | Route 125 |
| --- | ---: | ---: | ---: | ---: |
| mtmr_s1 | -50,044 | -43,754 | -44,946 | -44,968 |
| YumeNeko | -41,408 | -24,622 | -38,060 | -38,106 |
| Lucas Boesen | -40,088 | -26,676 | -33,378 | -33,306 |
| RS Turley, control | +270,144 | +272,818 | +270,920 | +273,484 |
| 吃白饭的大肥鱼, control | +123,554 | +114,982 | +116,444 | +116,404 |

Route 100 improved all three losses most, but rescued none and lowered the
second control by 8,572 paired-margin coins. On Lucas, own cash fell 2,422
across both seats; the 13,412 margin gain came from a 15,834 fall in the
fixed rival's cash. This is particularly vulnerable to rival adaptation.

## Native reactive follow-up for route 100

`scan_yarn_pizza_reverse_seeds.py` selected the first eight seeds with exactly
the public `YARN_STORE,PIZZA_SHOP` order from seed 2610400 onward. It examined
197 seeds using only the current `main.py` through turn 144, without looking
at future shops or treatment outcomes. The matched A/B then played baseline
main-versus-main controls and route-100 treatments versus reacting `main.py`,
both seats, 32 complete games. All ended `DONE`.

The treatment won **3/8 distinct seeds** and lost **5/8**; counting seats,
6/16 wins. Worst treatment margin was -6,670 coins per seat. Its aggregate
margin was +7,762 across 16 treatment games, but own cash was 12,377 lower
than controls, while reacting-rival cash was 20,139 lower. One control seed
had a +68/-68 seat asymmetry; total control margin was zero. The positive
aggregate was driven by three wins and does not offset the five distinct
losses as a reliability claim.

**Decision: reject all three switches for local `main.py`.** Routes 123 and
125 offered smaller original-shop improvements than 100 and no rescued
loss. Route 100 failed the fresh native win-count check and materially lost
on multiple seeds. The current `main.py` remains SHA-256
`0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a`;
no Kaggle upload occurred.

Evidence: `yarn_pizza_5routes_summary.json`, the four
`yarn_pizza_*_5routes.json` outputs,
`native_yarn_pizza_reverse_seeds.json`,
`reactive_yarn_pizza_reverse.json`, and the associated builder/scanner scripts.
