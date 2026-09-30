# Current top-100 live cash audit — 2026-09-27

All four public games against teams ranked in the top 100 of the **10:05
UTC snapshot** were included: three wins and one loss. Selection was by
opponent rank, without filtering outcomes. Their ranks describe that team
snapshot, not necessarily the opposing submission's rating at game time.

The exact uploaded c68 policy reproduced all **719 own actions and both
final cash totals** in every game. Both cash ledgers reconcile with zero
unexplained cash. Every own purchase succeeded in all four games.

| Opponent | Snapshot rank | Our margin |
|---|---:|---:|
| Driz Lo | 75 | +9,617 |
| liminhai | 79 | -38,375 |
| istinetz | 97 | +5,269 |
| Joseph Adamski | 100 | +3,010 |

## Loss mechanism

Against liminhai, the largest net item differences were **tomatoes
-35,542** and **melons -17,409**. Strawberry receipts (+7,646), lower net
hire/land expenditure (+4,405), carrots (+2,756) and other items offset
part of that deficit. Net item figures include the associated seed,
animal and product purchases, so gross wheat round trips do not inflate
the comparison. These are descriptive differences, not intervention gains.

At turn 576 the rival had 27 tomato plots versus our 10. Their final farm
retained 23 tomato plots versus our seven. Our earlier strawberry-heavy
farm therefore did not match their later tomato output in this game.
Neither player had a failed purchase. The visible shop sequence had five
tomato-consuming shops among its first six reveals.

The win over Driz Lo started with the **same first two shops**
(SMOOTHIE_SHOP, FARMERS_MARKET). A change triggered solely by that opening
pair is not supported by this audit. A useful next hypothesis needs a
complete executable continuation and later visible information, followed
by fresh tests against reacting policies.

## Decision and evidence

**Accept the reconciled diagnosis. Reject missing purchases as the cause
of this loss. Do not promote a policy based on this passive audit.**
Main.py remains c68fa46f; no upload was made. This audit does not establish
that any alternate crop allocation would improve wins after rival market
response and native future shop generation.

- `ledger.json`: complete results, raw/trace/helper hashes and parity checks.
- `physical_checkpoints.json`: visible farm and shop checkpoints.
- `traces/`: native reconstructed events; `routes/`: opposing action tapes.
- `PLAN.md`: frozen selection and parity requirements.
