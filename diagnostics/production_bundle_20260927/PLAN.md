# Predeclared funded land execution bundle — 2026-09-27

## Question and mechanism

Can the incumbent's already scheduled third-quadrant purchase be made executable by placing that existing `BUY_LAND` order immediately after the same turn's existing sales, before wheat, animal, or hire spending? The worker tape must already be scheduled to use the third quadrant. The candidate adds no purchase or worker command. It activates only when the farm owns exactly two quadrants, an existing land order is present, every `SELL` order precedes that land order, and the installed 1.32.7 market simulator projects at least 2,500 coins after those sales with the current actions' deposits included. The 500-coin reserve is intended to reduce false funding from quote uncertainty; rival orders remain endogenous in actual tests.

The motivating diagnostic is the fresh DECEM source replay: the pre-existing land order at step 240 failed at 1,373 coins after the route's sales had raised cash above 2,500, because the schedule then spent on wheat and sheep. The same route sends later workers toward newly opened lower quadrants and accumulated 375 non-PASS/no-change worker commands through day 18. The fresh Majkel replay also has a failed pre-scheduled land order at step 241. These fixed tapes motivate the rule only; they are not strength evidence.

## Frozen artifacts and policy

- Base policy: current `main.py`, SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- Candidate path: `exp_production_bundle_landfund_20260927.py`.
- Reacting references: current `main.py`; uploaded c68 reference `main_uploaded_disjoint_integrated_20260927_c68fa46f.py` (SHA-256 `c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad`); and `public_market_smart_f6a756cf_20260927.py` (SHA-256 `f6a756cfb900b9d5f49905d596b63f1fde2445342ac4b1ae04e353739bd62d2`).
- Engine: installed Kaggle native engine 1.32.7; original generated shops; both candidate seats; all opponents react normally.
- Development seeds, frozen before native outcomes: 2719000–2719015.
- Conditional untouched confirmation seeds: 2719100–2719115. Do not use unless every development gate passes.
- Saved DECEM and Majkel top-20 tapes may be replayed only as mechanism diagnostics; exclude all fixed-tape results from candidate gates.

## Measurements and gates

Record for each seed/ref both-seat wins, draws, losses, final cash, paired margin, candidate activation, successful land purchases, land count at day 18, and worker non-PASS/no-change actions through day 18. Run current-main self-controls against each external reference on the same seeds, so compare candidate changes in paired points and `delta_own - delta_rival`, not candidate cash alone.

Development: all games must finish `DONE`/`DONE` at 720 with zero agent errors; the candidate must activate on at least four distinct seed pairs; against current main it must score at least the incumbent self-control's paired points (16/16) and have positive aggregate paired margin; against each external reference its paired points must be no lower than current main's and pooled paired-margin change must be positive. A saved-panel improvement without these reacting results does not pass.

Only if development passes, confirmation: repeat candidate and current-main controls on all three reacting references over seeds 2719100–2719115. Require clean completion, at least four activated seed pairs, candidate paired points no lower than the baseline against each reference, positive pooled paired-margin change, positive candidate-minus-main paired margin, and no base both-seat sweep converted to a candidate two-seat loss. A pass only justifies a larger separately frozen evaluation; this pilot cannot authorize promotion or upload.

## Rejection rules

Reject if activation is below four pairs, if any clean-run requirement fails, if candidate paired points are lower than current main on any reference, or if pooled paired margin does not improve. Do not adjust the trigger or reserve after outcomes. No `main.py` edit, `agent.md` edit, Kaggle promotion, or upload is part of this experiment.

## Supplemental diagnostic source

A 2026-09-27 17:23–17:25 UTC official top-20 refresh became available before candidate implementation. Its current saved-action losses are DECEM rank 1 (−62,163), Boey rank 3 (−20,873), and Vadim rank 5 (−400); Majkel's newest episode is now a win. Use `diagnostics/current_top20_20260927_172258/{RESULTS.md,manifest.json,assessment.json}` only as a supplemental mechanism diagnostic. It does not replace or widen the predeclared native gates, and its fixed tapes never count as confirmation.
