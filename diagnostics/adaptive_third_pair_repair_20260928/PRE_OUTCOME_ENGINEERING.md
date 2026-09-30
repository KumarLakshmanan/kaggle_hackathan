# Pre-outcome execution correction

Before starting any discovery prefixes or route games, inspection found
the discovery-proof and final affected-combined executors lacked the
plan's eight-job worker recycle. Add `max_tasks_per_child=8` to those two
single-worker executors. The discovery/member loops already recycle after
each eight-job batch. Candidates, routes, scopes and gates are unchanged.

Preserve the initial pool as pool_before_worker_recycle.json and bind the
corrected helper plus this note in a new pool.json before any outcomes.
Initial pool SHA-256:
ee42cbf576941311aac3ec5bfba1981f1dfd2f89b5db08c54c59348d6f0cc429.
