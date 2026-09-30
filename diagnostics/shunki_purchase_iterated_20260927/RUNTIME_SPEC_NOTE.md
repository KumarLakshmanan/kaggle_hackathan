# Native timing semantics checked before file-loader outcomes

2026-09-27. Some pilot actions exceed one second while four native games
run concurrently; all48 games nevertheless finish DONE. The installed
kaggle-environments1.32.7 Agent.act rejects an action only when its duration
minus configuration.actTimeout exceeds observation.remainingOverageTime
(agent.py lines220–222). Environment.step subtracts max(0,duration minus
actTimeout) from that budget (core.py lines629–632).

The frozen plan requires the native action-time limit. The loader script's
initial draft incorrectly treated the one-second base allowance as an
absolute per-action ceiling. Before any file-loader tests, correct it to
check the actual base-plus-remaining budget and nonnegative remaining
overage throughout both file/direct games. Record peak duration, native
budget at that step and minimum remaining time; retain the mandatory
DONE/DONE status and exact action/cash parity checks. Candidate bytes,
strength gates and seed cohorts are unchanged. This is a specification
correction to an unrun harness, not a runtime pass or a strength result.

The host has12 logical processors. The completed pilot and running replay
panel use four workers. Before confirmation starts, configure that next
stage to use six workers to reduce elapsed time. The plan does not constrain
worker count; policy bytes, seeds, gates and native timeouts are unchanged.
Each result records the exact harness hash and worker count. File-loader
parity runs sequentially after the native worker pool exits.
