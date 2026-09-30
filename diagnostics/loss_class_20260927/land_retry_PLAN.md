# Funded retry of an already scheduled land purchase — 2026-09-27

## Scope and evidence

This is a separate candidate experiment layered on the exact current
`main.py` hash `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
It does not edit `main.py` or `agent.md` and does not upload to Kaggle.
The built candidate is
`diagnostics/loss_class_20260927/exp_land_retry_current_4ee.py`, SHA-256
`675893edc7ff07517dc57f60d322341b131ecd0d5286d9728d98d423cdc35e51`.

The current DECEM top-20 source episode is a high-value trace target. Its
scheduled third-land purchase fails at step 240 with 1,120 coins left after
market spending. At step 242 the incumbent observation has 2,902 coins; at
step 264 it has 3,401 and at step 265 it has 4,328. Through the terminal trace, 722 non-pass worker actions have
no state change because their tile is locked; 716 target southwest land and
six target southeast. The 17:47 live-loss no-op ledger shows only one
`locked_tile` failure across 26 losses, a single `PICKUP` in Junliang Ye.
This evidence motivates a branch-specific retry experiment, not a general
worker-no-op rule. The older retry layer improved one DECEM saved-action
tape from -82,192 to -3,104, but failed its frozen top-50 sweep gate. That
rejection remains valid; this is a new current-4ee native test.

## Frozen candidate rule

Start from current `main.py` and append the saved retry layer from
`diagnostics/shunki_land_retry_20260927/layer.py` without changing its
conservative commitments, 500-coin reserve, ten-order limit, route-intent
check, retry cap, or exception behavior. The layer can append one `BUY_LAND`
only after the incumbent route's recorded land intent is ahead of owned
land, no `BUY_LAND` is already in this turn's market list, and current cash
covers the price, its conservative existing-order commitments, and reserve.
Unit tasks and the incumbent's existing orders remain otherwise intact.
This tests a later funded retry after a failed scheduled order; it does not
reorder the incumbent's same-turn land order.

## Outcome-blind seed selection

Two disjoint ascending seed pools are frozen before candidate outcomes:

- Development scan: 2730000–2731999.
- Confirmation scan: 2732000–2733999.

The selection implementation is frozen at SHA-256
`533f0554d1cc7ef0280b38924538dffeaa0f723aef12058c6e6958e6d6a2e38e` (`select_land_retry_seeds.py`). It evaluates seeds in ascending 8-seed
chunks and stops each native game at the first funded retry trigger or step
600, whichever comes first. It does not run selected candidate outcomes.

For each pool, run incumbent `main.py` in seat 0 against the previous
submitted reacting agent
`main_uploaded_shunki_schedule_20260927_3cc0f69f.py`, with native endogenous
shops. Record each observation and incumbent action. A seed is eligible
when the incumbent requests a route-intended `BUY_LAND`, its unlocked-land
count does not increase in the next observation, and a later incumbent
observation before step 600 is one at which the frozen retry layer would
append a funded `BUY_LAND` after applying its reserve and commitment checks.
The eligibility calculation reads only incumbent observations/actions and
the frozen candidate rule. It does not use rewards, margins, candidate-run
states, or candidate outcomes. Select the first 16 eligible seed IDs in
ascending order from each pool. If either pool contains fewer than 16
eligible seeds, stop without candidate testing and report the shortfall.

Freeze both selected ID lists before running any candidate game.

## Native evaluation

For each selected seed, compare unchanged current `main.py` and the frozen
candidate in both seats against each of these reacting references:

1. Current `main.py` (`4eeac9c3…f783ed`).
2. Previous submitted `main_uploaded_shunki_schedule_20260927_3cc0f69f.py`
   (`3cc0f69f…a603`).

All games use original endogenous shops, native step order, and 720 turns.
Run both candidate and incumbent arms for every seed/reference/seat cell.
Report win points (win 1, draw 0.5, loss 0), paired seed deltas, margins,
own and rival cash changes, actual retry count, statuses, and maximum
candidate call time. Cash margin diagnoses the mechanism; win points are
the decision metric.

## Frozen gates

### Development

- All games finish `DONE/DONE` at 720 steps, with no retry-layer exceptions
  and candidate maximum call time below 1 second.
- The candidate actually retries land in at least 12 of the 32
  seed/reference/seat cells against the previous-submission reference.
- Across the 16 paired seed blocks, pooled candidate-minus-incumbent win
  points are positive; the candidate-minus-incumbent total is nonnegative
  separately against each reference; at least 8 seeds have a positive
  average paired delta across the two references.

Only a development pass proceeds to confirmation.

### Confirmation

- The same completion, exception, timing, and activation requirements hold.
- Pooled candidate-minus-incumbent win points are positive across the 16
  fresh selected seeds and nonnegative against each reference.
- In 10,000 paired bootstrap resamples (whole seed IDs sampled with
  replacement, with both seats and both references kept together), the
  2.5th percentile of the pooled candidate-minus-incumbent win-point
  difference is above zero. The bootstrap PRNG seed is 20260927.
- At least 8 of 16 fresh seeds have a positive average paired delta across
  the two references.

Failure of a gate rejects the candidate. A pass supports promotion
consideration only; no main edit, upload, or all-opponent claim is included
in this experiment.
