# Kaggriculture workspace notes

Read [agent.md](agent.md) before changing the competition agent. It is the
living research memory: current submitted hash, simulator parity, benchmark
panels, failed and promising experiments, and reproduction commands. Add a
dated finding with evidence and a clear promotion/rejection decision after
each completed experiment; update the current-state section if `main.py` or
the Kaggle status changes. Do not treat fixed replay tapes as independent
validation of a policy change.

`main.py` is the Kaggle submission artifact. Prefer testing changes in a
separate experimental candidate first, then verify both seats, original-shop
and reactive behavior before promotion. Preserve existing worktree edits.
Never submit to Kaggle without a fresh explicit user request for that upload.
No strategy can be guaranteed to beat every possible opponent.
