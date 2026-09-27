# Kaggriculture decision-architecture reassessment — 2026-09-26

## Verified state and evidence hierarchy

The current submission artifact is `main.py` SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
Its exact uploaded backup is `main_uploaded_mirror_straw24_20260926_489fe8e4.py`;
Kaggle submission 56572390 used these bytes after separate user approval.
The actual Kaggle file entry point is the final `kaggle_main_entrypoint`;
the trusted local harness imports `agent`. Kaggle loader seed-0 self-play
matched local first actions and terminal cash in both seats. The earlier
wrong-callable/PASS submission was fixed before this experiment. Installed
engine is `kaggle-environments==1.32.7`, standard 30-day, 720-turn,
two-player configuration; the game scores terminal bank cash, not unused
inventory. `main.py` remained unchanged by this reassessment.

The authoritative current research memory is `agent.md`. There is no
`agenda.md` anywhere in this repository, including ignored files; this
assessment uses the documented `agent.md`, frozen manifests and native
engine. The working tree was already dirty and was preserved. No worktree,
commit, push, production deployment or Kaggle upload was made here.

Paired route win means the **sum of both seat margins for the same saved
route is positive**. Each route/seed is an independent block; seats within
one block are correlated. Source identity, opponent/replay source, seed,
configuration and seat are kept together in the raw results and joins.

| Artifact | Configuration and panel | Metric and result | Evidence type | Limit |
| --- | --- | --- | --- | --- |
| Current `main.py`, 56572390 | Kaggle public, 100 completed games audited 17:09 UTC | 71 wins, 29 losses, all players DONE; team rank 876/2221.0 at 17:07 UTC versus rank 10/2881.7 | Observed live matches | Different public samples cannot compare two policy versions causally; the team score reflects the older higher-scoring submission. [Audit](../live_submission_56572390_20260926/RESULTS.md) |
| Current `main.py` | Latest frozen top-100 saved routes, 100 action hashes, both seats, engine 1.32.7 | 66/100 paired routes, 132/200 seats, all DONE | Fixed-action regression/diagnosis | Opponent actions do not adapt; [panel](../top100_refresh_2026-09-26_0708/RESULTS.md) |
| Prior September 25/26 top-100 panels | Different frozen 100-route action sets, both seats | 59/100 and 69/100 paired wins, respectively | Reused fixed-action development | Neither is untouched or a live win-rate estimate; [memory](../../agent.md) |
| Day-11 sheep counterfactual B and simpler C | Native seeds 2612000–2612015, both seats versus trusted reacting `main.py` | B and C: 0/16 paired wins, 3 paired losses, 13 ties; B margin −60,686 versus A | Reactive local development | A self-play draws; only three seeds activated; [results](RESULTS.md) |
| Day-6 whole-route controller B and simpler C | Native seeds 2613000–2613015, both seats versus trusted reacting `main.py` | B: 0/16 wins, 16 ties, no switches; C: 0 wins, 2 losses, 14 ties, margin −12,294 | Reactive local development | Only two seeds triggered; [results](ROUTE_RESULTS.md) |
| Sheep matched-shop seed 2612002 seat 0 | Same baseline future shops forced, rival and market still reactive | B margin +8,659 versus native B −9,850 | Causal shop-path diagnostic | One deliberately controlled seed, not deployable or untouched; [ledger](ledger_2612002_s0.json) |

The explicit user goal from the earlier conversation is top-ten leaderboard
placement and all 100 saved top-player routes. The last dated rank snapshot
above is far short of top ten, and the latest fixed panel is 66/100. Neither
one local development block nor a fixed replay win count solves that goal.

## Decision path and diagnosis

`Chassis` selects one of 41 complete action tapes, then repairs or modifies
worker and market actions reactively. Its router commits at step 144 after
the first two shop unlocks and switches to a shared terminal route at step
648. For one-Yarn shop pairs it normally selects route 9, regardless of
the companion shop, except a narrow existing rival-response control. Route
9's full schedule purchases sheep and land, hires workers, serves crops and
animals, moves product to storage, and sells. Market orders are settled by
the engine; final money reflects only executed sales minus purchases and
hires/land. This is a strong hand-constructed continuation library, but the
route choice does not compare full downstream competitive cash outcomes for
the visible state.

The installed engine processes atomic HIRE and BUY_LAND orders in player
order. It then quotes both players' next per-unit market operations before
committing each unit; market inventory and prices update after settlement.
Independent WOOL and FERTILIZER sales commute in a small installed-engine
transition check. A SELL before BUY_SEED can change the seed fill by funding
it. Thus a proposed reordering must be shown to change the exact relevant
state; a generic market-order race is not a valid explanation. See
`market_transition_check.py`. Final ledger comparisons use only successful
market-unit and atomic events and reconcile unexplained cash to zero.

The important diagnoses are:

1. **Execution/parity:** the present file loader and local simulator match
   in checked cases. The previous callable-selection failure was real and
   corrected; it does not explain the current close losses. Normal engine
   no-ops still occur in both routes.
2. **Shared market and endogenous shops:** the sheep challenger lost 9,850
   margin natively on seed 2612002 seat 0 but gained 8,659 with identical
   future shops. In two route-switch controls, shops stayed identical, yet
   rival wool receipts increased 8,046 and 4,005. Price changes can alter
   rival cash even when our own cash improves; sale order alone cannot be
   interpreted as productivity.
3. **Capital and commitments:** the day-11 sheep project charged new land,
   animals, wheat and hires against an incumbent already executing a sheep
   plan. The optimistic three-scenario model selected it on three seeds and
   lost all six seat games. Switching a complete route at day six avoided
   that overlay inconsistency, but the simple route-0 control still lost on
   both activated seeds. On seed 2613002, the first action divergence at
   step 144 changed hires and orders; own cash was 1,069 under route 9 and
   937 under route 0 at the next observation.
4. **Worker/capacity throughput:** in the two activated route controls,
   own non-PASS worker actions with no state change rose from 20 to 59 and
   from 24 to 66. An incumbent worker successfully built a pasture at step
   155 while the corresponding route-0 worker's WATER did nothing. These
   are concrete schedule mismatches, although the traces do not establish
   which one individually caused the terminal loss. The historical
   one-fewer-hire savings bound remains optimistic until a complete feasible
   replacement schedule preserves the task deadlines.
5. **Experiment measurement:** original replay equality validates the
   harness, not the policy. A fixed rival action tape can still have changed
   rival cash through shared prices; it cannot show adaptation. The local
   A/B/C tests used the trusted reacting incumbent, but they cover one rival
   policy and small qualifying blocks. The native shop path must remain
   endogenous in the strength claim.

**What remains even if the code executes exactly as intended?** The
incumbent makes long, irreversible route commitments from two early shops
without a reliable estimate of the market, worker and opponent cash
consequences. Future shops are hidden by the legal API, so any deployable
comparison is uncertain. The two tested approximations either selected a
harmful expansion or stayed at the incumbent without winning new games.

## Architecture experiments, controls and decision

The first challenger represented a complete funded six-sheep project as a
counterfactual against the incumbent at the first eligible day-11 one-Yarn
decision. It reused the existing complete sheep executor, changed no
unrelated route layer and called the incumbent only once. A was the native
continuation, B used a time-indexed forecast and C relaxed the shop gate
without a model. [Predeclaration](PLAN.md), [code](../../exp_sheep_commitment_20260926.py),
[raw A/B/C comparison](abc_fixed_dev16_comparison.json), and
[cash/shops ledger](ledger_2612002_s0.json) preserve the result. An initial
empty-order parser bug caused only fallback; it was fixed before the frozen
effective development run and its zero-change output is not treatment
evidence. B and C then both lost three paired seed blocks. **Rejected.**

The second challenger moved the comparison to step 144 and evaluated full
route-9 versus route-0 commitments, including capital, hires, land,
projected production/delivery/sale time, feed/resource checks, market price
impact and a visible-rival estimate across three hypothetical future Yarn
paths. A was route 9, B made a conservative selection, and C always chose
route 0 at the trigger. The full route tape keeps execution and reservations
coherent after the choice, although the forecast is approximate. OFF parity
matched direct `main.py` on two seeds in both seats. B chose the incumbent
on both qualifying seeds and won nothing; C made own cash rise 5,392 but
rival cash rise 17,686, losing 12,294 paired margin. Engine-event ledgers
reconcile both activated seeds and reveal extra worker no-ops. B's timed
agent maximum was 1.407 seconds under concurrent machine load, beyond the
reported one-second action budget. [Predeclaration](PLAN2.md),
[code](../../exp_route_commitment_20260926.py),
[raw A/B/C comparison](route_abc_dev16_comparison.json), and
[cash ledger](route_ledger_activated_s0.json) preserve the result.
**Rejected.**

No challenger reached the first paired-win gate, so the full top-100
regression panels and untouched 2612100–2612115 / 2613100–2613115 native
blocks were not used for these candidates. No unfamiliar downloaded opponent
source was executed: the workspace has no approved isolated runner for it.
There is no independent validation or leaderboard result for either
candidate. No prototype was integrated into `main.py`; the incumbent stays
the submitted and local policy. In accordance with the two-mechanism stop
rule, no third variant or threshold tuning follows from these results.

The exact reproduction commands, source hashes, status checks, runtime
qualification limits, and full matched-case deltas are in [sheep results](RESULTS.md)
and [route results](ROUTE_RESULTS.md). The dated findings and promotion
decisions are also recorded in [agent.md](../../agent.md).
