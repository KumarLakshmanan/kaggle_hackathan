# Untouched robustness check of the frozen coarse lookup — 2026-09-26

The coarse lookup failed its original tail-risk gate by 7,906 paired
margin coins but had broad positive development performance. Do not
change its SHA-256 `371ab5db...`, mapping, or decision rules. Run new,
sequential, untouched native seeds **2630100–2630131** with original shops,
both seats, versus reacting unchanged `main.py` and matched main-vs-main
controls. Record all statuses, same-shop checks, per-seed margin and
own-cash deltas, aggregate and worst deltas, and the number of positive
seed pairs. This is a descriptive robustness check, not a second chance
at the original gate and not an authorization to promote or upload.

If gains persist but the negative tail remains, investigate state-aware
corrections or shop-specific fallback as a new candidate, with another
fresh predeclared test. If gains do not persist, stop work on this lookup.
