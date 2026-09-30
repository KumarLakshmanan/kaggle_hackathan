# Same-item protected-sale exception — 2026-09-26

## Hypothesis

In a fresh live loss, a rival sold two strawberry batches two turns before
our equal-unit sales. The local sale-advance layer excludes the first future
sale to protect a possible cash-funding dependency. I tested a narrower
exception: when the inherited action **already sells that same item now**,
allow the layer to add held units from that protected future sale to the
existing current sale. All other code, including the public physical-mirror
gate and four/eight-turn horizons, is unchanged. The candidate is
`exp_sale_sameitem_unprotect_20260926.py`, SHA-256
`6044b121bba42491c7dff51423e83a2a2c4acaa237dd2df2991520d02c144142`.
The build script asserts the exact local baseline hash and replaces one
specific source line. It uses no replay identity, seed, or future shop in the
agent.

## Matched tests

All saved routes were run in both seats under the original simulator and all
games finished `DONE`.

| Check | Local `main.py` | Candidate | Cash effect versus local |
| --- | ---: | ---: | --- |
| Predeclared seven close live-opponent development tapes | 3/7 paired wins | 4/7 | Own -22, fixed rivals -1,072 across 14 seats |
| Full fresh 40 live-opponent **fixed tapes** | 11/40 paired, 21/80 seats | 12/40 paired, 23/80 seats | Own -118, fixed rivals -4,575 across 80 seats |
| Current top-100 **fixed tapes** | 59/100 paired, 118/200 seats | 59/100 paired, 118/200 seats | Own -2,283, fixed rivals -3,705 across 200 seats |
| Fresh reactive self-play, seeds 2610100–2610107, both seats | 0/16 control wins | 14/16 | Own -966, reacting rival -1,646 across 16 games |

The 40-route treatment rescued the paired loss to Roland Luethy but did not
reverse a paired win. The original targeted Squirrel route **remained a loss**;
own cash fell 116 across its two seats even as the fixed rival lost 184.
The older top-100 panel had **zero rescues and zero reversals**. Its routes
have been reused for development and are a regression screen, not an
independent live win-rate estimate.

On the fresh native reactive block, the candidate won seven of eight seeds
in both seats. It lost seed 2610101 in both seats by 641 coins each: own cash
fell 607 while the reacting rival gained 34 per game. The 14 wins yielded
only +680 aggregate margin across all 16 games. Maximum candidate call was
294.5 ms. This is evidence against one reacting near-clone, not diverse
leaderboard opponents. The own-cash decrease and same-seed failure matter
because the candidate already failed to improve the 100-route screen.

Exact outputs and join scripts: `sameitem_7routes.json`,
`sameitem_7routes_comparison.json`, `sameitem_live40_routes.json`,
`sameitem_live40_comparison.json`, `sameitem_top100_routes.json`,
`sameitem_top100_comparison.json`, `reactive_sameitem_fresh.json`,
`compare_sameitem_pilot.py`, and `compare_sameitem_top100.py`.

## Decision

**Reject.** The exception is a small market-race perturbation, not an
improvement across the 100 saved top-player routes. Its reactive near-clone
advantage is inconsistent and comes with lower own cash. Local `main.py`
remains SHA-256
`6b5529feb131cc1689c41c91ff1416c33ed1bbb90b6fbb1feba8b5b36d2d6076`;
no Kaggle upload occurred.
