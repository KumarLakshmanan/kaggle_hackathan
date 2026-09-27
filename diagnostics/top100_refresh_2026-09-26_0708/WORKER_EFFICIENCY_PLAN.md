# Worker-action efficiency diagnostic — 2026-09-26

Question: do failed unit commands provide a broad, recoverable explanation for
the 34 paired-route losses of current `main.py`?

Freeze `main.py` SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
Replay each of the 34 lost public routes on its original seed in candidate
seat 0 with native shops. Include ten paired-route wins chosen deterministically:
the five closest positive margins and five evenly spaced through the other
wins. Verify both terminal cash totals against the saved panel. Count exact
native `unit_action` events by operation and whether the engine changed state;
exclude `PASS` from failed-command counts. Report time windows and both players.

Decision gate, before reading output: consider a generic invalid-command
repair only if at least ten lost routes have 100 or more failed non-`PASS`
commands, or if failed non-`PASS` commands exceed 2% of attempted non-`PASS`
worker commands aggregated over the 34 losses. Otherwise reject this broad
mechanism. `PASS` frequency is a separate capacity diagnostic, not proof that
another legal task existed. Fixed rival tapes are diagnostic and not independent
policy validation. No candidate, `main.py` change, or Kaggle upload follows
from this diagnostic alone.
