# Public live audit: submitted `main.py` (56530281)

Frozen agent SHA-256:
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
This is byte-identical to submission 56529771. The two Kaggle submissions
were explicitly user-authorized; **this audit made no new submission**.

At the 2026-09-25 06:19 UTC Kaggle CLI check, 56530281 was `COMPLETE` and
its displayed rating was 2393.8. The rating is dynamic; it is not a final
rank, and the newest 24 episodes are not a random or independent tournament
sample.

## Fixed audit sample and actual outcomes

The sample is the 24 latest completed public episodes returned by the CLI at
the beginning of this audit. All 24 have both players `DONE`: **13 wins and
11 losses**. Eight losses were below 1,100 coins. The raw public replay JSONs
are `episode-*-replay.json`; `audit_latest_24.json` contains each episode's
seed, actual cash, seat, daily cash, action-count, and order-count summary.
The losing episodes were:

| Episode | Own minus rival final cash |
| ---: | ---: |
| 113174622 | −525 |
| 113170773 | −1,427 |
| 113166794 | −4,003 |
| 113161648 | −317 |
| 113160599 | −1,048 |
| 113152821 | −631 |
| 113151063 | −332 |
| 113135718 | −351 |
| 113130332 | −360 |
| 113123301 | −658 |
| 113116545 | −1,290 |

In 21/24 episodes the rival's main-farmer action exactly matched ours on at
least 718/720 turns. In 19/24, hand-action arrays matched on at least 690
turns; in 22/24, market-order arrays matched on at least 500 turns. These are
**near-mirror action patterns**, not proof of identical code or identical
executed transactions. Requested SELL counts can include zero-stock no-ops or
padded empty orders, so do not treat emitted quantities as realized revenue.

## Local simulator parity and development panel

`extract_routes.py` produced one 719-action opponent tape per replay in
`routes/`, plus `routes/summary.json`. The unchanged `main.py` was rerun
against each captured tape under the installed Kaggriculture 1.32.7 simulator
on its original seed and seat. **All 24/24 reproduced both players' final cash
and `DONE` statuses exactly.** A both-seat expansion of this same panel gave
**13/24 route-pair wins, 26/48 seat wins**, all `DONE`; the output is
`baseline_24routes_both_seats.json`. One winning route has a different cash
margin in the opposite seat because native episode RNG can diverge by seat.

This validates the local simulator/harness for those actual games and provides
a powerful regression panel. It remains a **fixed-action replay**: opponents
do not adapt their future commands when the candidate changes. These routes
are now development data, not untouched validation.

Reproduce from the repository root:

```powershell
python -X utf8 .\diagnostics\live_submission_56530281_20260925\audit_live.py --limit 24 --workers 3
python -X utf8 .\diagnostics\live_submission_56530281_20260925\extract_routes.py
python .\route_panel_benchmark.py --candidate main.py --summary .\diagnostics\live_submission_56530281_20260925\routes\summary.json --workers 8 --json-out .\diagnostics\live_submission_56530281_20260925\baseline_24routes_both_seats.json
```

## Next diagnostic

An independent actual-cash divergence analysis is underway on these near-
mirror games. The predeclared no-roundtrip opening queue screen is in
`OPENING_NET5_SCREEN.md`; it did not improve wins and was rejected. Extending
the sale-advance lookahead from four to eight turns is documented in
`SALE_ADVANCE_LOOK8_SCREEN.md`: it gained two fixed-tape route wins but failed
the predeclared own-cash rescue gate. A user-approved aggregate-only GPT-6 Pro
consultation suggested a strictly independent adjacent sale swap. The
read-only `market_swap_exposure.py` scan found zero strictly eligible events
in the 24 actual games, so this intervention was stopped before coding. See
`PRO_MARKET_SWAP_PLAN.md`. No source code, credentials, or opponent names
were sent to ChatGPT.com. No new Kaggle submission was made.
