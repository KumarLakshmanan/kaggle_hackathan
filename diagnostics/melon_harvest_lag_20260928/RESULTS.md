# Melon harvest-lag feasibility — 2026-09-28

## Decision

**No-go for a single-day harvest planner.** The saved traces show a sparse
maturity-to-harvest backlog, and the cases where an earlier harvest plus shed
trip fits a contiguous PASS-only schedule are isolated. There is no common,
non-displacing execution opportunity across the 30 losses or the four current
top20 diagnostic traces. No candidate or win-outcome test was justified.

## Evidence

Scope: the 30 rows in
`diagnostics/loss_class_20260927/live_loss_ledgers_180951.json` plus the four
traces in `diagnostics/loss_class_20260927/current_top20_ledgers.json`.
MELON was treated as harvestable at age 10 days, with a strict backlog defined
as more than 24 turns after its first mature observation. The detailed
trace-level extraction is in `lag_audit.json`; the extraction script is
`audit_lags.py`.

- There were 492 mature crop batches and 2,321 units at first maturity.
- Nineteen batches (114 eventual units) remained unharvested for more than a
  day, spread across 9 of 30 loss traces. None appeared in the four top20
  traces. At the >24-turn threshold, 84 units were still on crop tiles.
- A geometric route check found 259 batches where some worker could reach,
  harvest, and reach the shed before the incumbent harvest action. This ignores
  the worker's scheduled crop, feed, watering, and other tasks, so it is not an
  executable opportunity count.
- Requiring one contiguous PASS-only window long enough to travel, harvest,
  reach the shed, drop, and return reduced the count to **2 batches in 34
  traces** (`fasith 007` and `Ghost Rule`, both loss traces; zero of four top20
  traces). Their crops contain at most 12 units total. These isolated cases do
  not support a common planner trigger.
- The audit's harvest-to-shed ledger reports 2,328 delivered MELON units, no
  delivery lag over 24 turns, and a maximum observed lag of 19 turns. Treat the
  cohort-linked sale-price estimates as unusable: the FIFO diagnostic left 691
  sale units unmatched, showing that pooled shed timing prevents reliable
  attribution in this extraction.

The backlog's 114 harvested units are an upper bound on units a hypothetical
one-day shift could affect; that is not an incremental-cash estimate. The
available FIFO price diagnostic tentatively assigns only 30 delayed units and
reports +123 coins against the prior-day quote peak (+126 if negative unit
deltas are discarded), but its 691 unmatched sale units invalidate that
attribution. Therefore this audit makes **no positive cash-margin claim** for
earlier harvesting. The only trustworthy economics conclusion is that the
proposed timing gain has not been established.

## Limits and follow-up

The strict PASS-only test is intentionally conservative; workers might be
reassigned by a policy. But 259 geometric possibilities are not enough to
justify that change without an executable scheduler that preserves displaced
work. Fixed saved traces are diagnostics, not independent validation. Any
future planner should first replay a declared single-day schedule in the native
engine and verify movement, harvest inventory, shed deposit, and the displaced
worker task before considering policy outcomes.

This subtask did not edit `main.py` or `agent.md` and used no Kaggle access.
