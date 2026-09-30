# Opponent-agnostic execution review of ae349d83

## Decision: no-go for another candidate from the present evidence

This was a local source and evidence review. No strategy was changed, no new
game was run, and Kaggle was not accessed. The decision means there is no
evidence-supported bounded implementation to launch now; it does not establish
that a different architecture cannot improve the agent.

Exact candidate: `main_candidate_improved_20260929.py`, SHA-256
`ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb`.

## What the current source supports

The base agent at lines 18-41 selects stored actions by step and observed shop
prefix. Its worker schedule is largely predetermined, but a general scheduler
being absent is not proof that one would improve results. Existing guards
already address specific execution failures:

- Lines 569-599 keep executable planting requests when seed supply is partial.
- Lines 716-793 recover a narrowly specified failed hire, delay its worker
  commands, and require a bounded catch-up point.
- Lines 833-930 simulate remaining same-day commitments before funding a
  scheduled animal purchase; they check existing tiles, seeds, land, worker
  positions, feed and physical acquisition.
- Lines 1074-1128 enforce physical compatibility for the opening bridge.
- The existing market layers already simulate order effects. A new name for
  order tuning or another donor splice would repeat prior work.

The source therefore does not justify a generic extra-worker, spare-cash,
missing-supply, or idle-action patch without identifying an unhandled physical
event and its complete execution obligations.

## Why the available outcomes do not support a material new execution patch

1. **Exact current reactive evidence:** 24 matched scenarios against three
   reacting policies, with both seats grouped by seed, give ae349 and its
   previous uploaded parent identical 8W/14D/2L outcomes and zero margin delta.
   The new Pizza guard activates in none. This is not evidence for broad
   adaptive strength or for a particular missing resource repair.
2. **Exact current DECEM audit:** the full final inventory path is accounted
   for, leaving only 44 coins of additional liquidation against a 9,085-coin
   loss. This closes terminal cleanup as a rescue, not all earlier strategy.
3. **Prior funded delivery repair:** a different ancestor candidate repaired
   a missing strawberry physically and preserved its ten winning controls.
   Its own cash rose 24,746, but the rival rose 24,342, leaving only +404 in
   paired margin and both losses intact. This is causal warning evidence on
   an ancestor, not an exact-ae349 counterfactual result.
4. **Earlier broad physical audit:** on older hash 489fe8e4, the last hired
   worker did actual work on all 90 analyzed days; clipped production had
   only 457 coins of instantaneous quote exposure. These observations reject
   that earlier generic cleanup argument. They cannot substitute for a new
   event census on exact ae349.

## Evidence required to reopen this direction

First identify a repeated, material execution failure on the exact current
agent: an already funded production task missed because of actor position,
inventory ownership, or timing. Account for the entire existing commitment,
including travel, feed, fertilizer, delivery, and the next worker task. The
event must have an executable repair, not merely an optimistic output price.

Only then freeze one opponent-independent rule and its activation criterion.
An exact-prefix native check must show the intended physical change without
unintended loss of existing work. Saved tapes may supply mechanism and
regression controls; promotion requires a separate original-shop comparison
against multiple reacting policies in both seats, with frozen win/draw/loss
criteria and paired own-minus-rival margin reporting. No such new event or
repair was established by this review, so no candidate or outcome screen is
recommended now.

## Evidence inspected

- `main_candidate_improved_20260929.py`
- `diagnostics/combined_agent_257f_20260929/reactive/assessment.json`
- `diagnostics/ae349_decem_trace_audit_20260929/RESULTS.md`
- `diagnostics/ae349_decem_trace_audit_20260929/trace_receipt.json`
- `diagnostics/ae349_decem_trace_audit_20260929/REMAINING_MARGIN_REVIEW.md`
- `diagnostics/decem_90_research_20260928/delivery/RESULTS.md`
- `diagnostics/physical_gap_20260927/RESULTS.md`

These are source observations and previously completed results. No new outcome
or guarantee is inferred from them.
