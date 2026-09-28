# Frozen local target and promotion rules — 2026-09-28 IST

## Scope

Use only the already downloaded 30 public-loss replies from submission
56609430 and the 20 entries in the saved 17:25 UTC top-20 panel. The user
requested no further Kaggle checks or downloads. These are recorded action
tapes; they do not react to a candidate and cannot establish live strength.
No upload is authorized by this plan.

Exact incumbent `main.py` SHA-256:
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Frozen local fixture manifest:
`diagnostics/loss_class_20260927/local_target_manifest_180951.json`, SHA-256
`524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.
Both-seat 30-loss baseline:
`diagnostics/loss_class_20260927/live_loss_tape_baseline_180951.json`, SHA-256
`e1a5f93dbf093115f8587a81b22d8a81372d02fc665c75c6023242d430466828`.
Top-20 baseline:
`diagnostics/current_top20_20260927_172258/assessment.json`, SHA-256
`9d328af8115e27acb45fd4251a1bbc1fde5fda8c793c027b46792a54c04cbeb7`.
The 50 entries cover 48 unique source episodes and have no overlap between
the 30-loss and top-20 groups.

## Baseline and target

The incumbent loses all 60 seat games against the 30 public-loss tapes:
0 wins, 0 draws, 60 losses. All 30 original-seat runs exactly reproduce the
saved public rewards and margins. On the top-20 panel it wins 34 of 40 seat
games and sweeps 17 of 20 teams. The three two-seat losses are DECEM, Boey,
and Vadim Vasilenko. All games finish DONE/DONE at 720 frames.

The user's requested local endpoint is **50 of 50 both-seat sweeps** on this
frozen set, including all 30 public-loss replies and all 20 top-team entries.
No strategy can be guaranteed to beat every possible opponent or a private
reacting policy from these tapes.

## Candidate sequence

1. Build changes in a separate candidate file and freeze that candidate's
   mechanism, trigger, reference hashes, seeds, and pass/fail criteria before
   reading candidate outcomes. Preserve the current file and its backup.
2. Check both seats, original shop generation, full 720-turn completion,
   worker execution, market fills, and `delta_own - delta_rival` on any
   targeted saved traces. Evaluate the entire 50-entry frozen set before
   promotion. Report wins/draws/losses, both-seat sweeps, cash margins, and
   any incumbent win that turns into a candidate loss. Fixed tapes are
   regression and mechanism diagnostics only.
3. Require separate fresh local native games with original shops and at
   least two reacting references. Keep both seats of a seed together when
   estimating uncertainty. Compare win points first; cash and production
   ledgers explain the mechanism. A candidate should improve paired win
   points without a reference-specific regression before promotion.
4. Promote only a candidate that passes its own predeclared local and
   reacting gates. Back up `main.py` first, verify the Kaggle file loader
   in both seats, and update `agent.md` with the new local state. Do not
   upload without a separate fresh explicit user request.

Record a dated evidence-based rejection when a mechanism fails feasibility
or a frozen gate. Do not retune on the same supposedly confirming seeds.
