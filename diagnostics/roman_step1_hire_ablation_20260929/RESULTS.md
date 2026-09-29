# 6a step-1 hire-only ablation: stopped at the native prefix gate

Date: 2026-09-29

## Decision

Reject this candidate as a productive-worker intervention. No full games ran,
so the test produced no outcome, win-rate, or margin evidence. Do not waive the
prefix failure or count the hire as added labor.

## Frozen inputs

- Candidate: `b78f593938db50bb5118fc8af4b0736f3bb20ad7da01c80e7a6a96f982a95cbf`
- Parent: `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`
- Panel: `c4e6aaec18177882142509a8b6cd5885626348774e69940dd4747123d73b49e1`
- Runner: `8459d5034fa135163c5b490c3bf18d915502b8e73bab679d64cab5f68c74a02c`
- Frozen manifest: `8fef8cad1d193d9014891f48ddbe88c91b7e1f52875c43c5a45a62987a0b0508`

## What happened

The source-bound two-seat prefix for `live-114270587` confirmed the step-1
parent action plus one trailing HIRE, a $5 charge, one appended hand, and no
other observation-state changes. It also confirmed the wrapper returned the
parent's actions unchanged on steps 2 and 3. At those steps each observation
had five own hands, while the parent action had only four hand commands. The
required five-command check failed in both seats and the one-shot runner
stopped before all six baselines and six candidate games (`game_count=0`).

The native transition code accepts variable-length `hands` arrays and loops
only over supplied commands. The bound installed Kaggle engine follows the
same behavior. Therefore the fifth hand receives no command; it is idle until
the day reset clears the hand. This is valid action input, but it does not test
productive capacity. Adding an explicit PASS would leave the worker idle and
would only measure paying $5 for an unused hand.

## Follow-up gate

A future productive-hire experiment needs a separate candidate with an
explicit, source-bound fifth-hand task schedule. Verify both seats in a new
native prefix, preserve the original four hand commands, and check resource
and state effects before scheduling full games. Do not infer a gain from this
stopped run.

Root `main.py` was not changed; its SHA-256 remains
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. No
Kaggle checks or uploads were made.

## Receipts

- `outcome_receipt.json`: stop phase, zero games, and failed checks
- `prefix_results.json`: both seat-level prefix check summaries
- `prefix_candidate_target0.jsonl.gz` and `prefix_candidate_target1.jsonl.gz`:
  candidate observation/action traces
- `PLAN.md`: frozen pre-run gates
