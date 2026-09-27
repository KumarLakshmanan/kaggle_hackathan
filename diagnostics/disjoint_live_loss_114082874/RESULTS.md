# First c68 live loss — reproduced, no successful candidate repair

Completed 2026-09-27 08:53 UTC.
Source public episode 114082874, seed 1751033306, versus Paarthpowa.
All six diagnostic games complete DONE/DONE/720 with zero reported errors.

| Unchanged policy | Seat 0 margin | Seat 1 margin |
|---|---:|---:|
| c68 | -13 | -13 |
| purchase | -24 | -24 |
| funding | -13 | -13 |

The original seat-1 c68 cash pair exactly matches the real downloaded game:
155399 versus 155412. Original native shops and the public opposing tape
were used. Candidate 43d makes the margin 11 coins worse; 31ce is unchanged.

**Decision: reject a repair claim on this case.** These two candidates
remain rejected under their original gates. No promotion or upload; main
stays c68. A fixed opposing tape does not provide independent validation
of a reacting policy or prove future live performance. Preserve the verified
remote reproduction and counterfactuals for a later mechanism audit.

Evidence: PLAN.md, results.json, opponent.json.gz; public replay with hash
receipt in ../disjoint_live_audit_20260927/raw/.

## Passive mechanism audit

The final 13-coin difference is the end of a much larger cash trajectory: c68
trails by 16,588 at frame 264 and recovers late. Physical command dictionaries
differ on all 719 action turns, public noncash farm state differs on all
719 post-initial frames, and market queues differ on 581 turns. Different
commands include worker-count differences; this is not a claim that every
command is productive or that the cash gap has one cause.

At the final frame, own shed, worker inventories, seeds and all field yield
are zero. **Reject a terminal-leftover explanation for this loss.** No new
liquidation candidate or strength experiment was run. Evidence:
passive_action_comparison.json and terminal_inventory.json.
