# GPT-6 Pro consultation — 2026-09-25

The user requested a GPT-6 Pro strategy consultation. I sent aggregate local
results and the relevant game-mechanics description to ChatGPT.com in a new
GPT-6 Pro chat. No source code, credentials, opponent names or personal data
were sent. Conversation:
https://chatgpt.com/c/6ab6276e-54b4-83ee-a238-f2f1530c9d90

## Proposal, not a verified result

The recommendation was **rollout-distilled, commitment-aware policy
iteration**. Generate complete funded bundles—purchase, worker travel/care,
harvest, delivery and sale—with time-indexed cash, worker, land and storage
requirements. Compare a proposed bundle, a feasible alternative, and making
no new commitment by continuing the *reactive* game to terminal cash.
Train a small observation-only selector on terminal **paired margin**, then
retain the tested worker scheduler as executor. Do not use simulator hidden
state, future shops, seeds, identities, or future actions as deployed inputs.

The first proposed ablation is one replacement at the first genuinely
contested investment decision, with a control wrapper that reproduces the
original decision exactly. A conflict must be backed by a real budget,
deadline, land or storage constraint. The alternative must offer an earlier
feasible sale and include its funding/work obligations. If no qualifying
conflict occurs, report non-activation rather than move the trigger. Use
complete reactive continuations for all three choices on development states;
freeze the resulting low-capacity selector before evaluating on untouched
seeds. The suggested pilot budget was 16 development seeds (both seats),
four held-out seed blocks (both seats), and both matched-shop and native
evaluation. Match exogenous shops, not market prices or opponent actions.

Predeclared materiality suggestion: roughly 6,200 additional own coins per
game (10% of the v1 mean-margin gap) or an actual loss-to-win flip, with
positive paired-margin changes in at least three of four held-out blocks,
no operational failures, and no control-win reversal. This is a gate for
more research, **not** a claim that the proposal works or that a four-seed
screen would justify replacing `main.py`.

## Local mechanical caveat before implementing

In this engine, a newly placed animal may produce saleable fertilizer before
its principal milk/wool/egg product, so an “earliest sale” criterion must count
*all* products and a complete actual sale path. At opening, a cow may have an
earlier first receipt than a melon despite a worse later capital cycle; do
not label a melon as an earlier-sale alternative by inspecting only the
principal crop/product. The complete-bundle, resource-conflict trigger has
not been implemented or tested in this turn. The present v1–v5 candidates
remain rejected.

## Implemented measurement step — 2026-09-25

`terminal_rollout.py` is a runnable, local A/B harness for the next policy
candidate. It runs both agents reactively in both seats and reports terminal
own-cash, rival-cash and paired-margin differences separately. It can pin
only the exogenous observed shop sequence from one native audit while leaving
market stock/prices, weeds, and the opponent's subsequent actions endogenous.
It hashes the source artifacts and records statuses and maximum agent-call
latency. This is **experimental measurement code**, not a Kaggle agent and
not the complete-bundle selector itself.

The seed-0 matched-shop identity control (`standalone_v1.py` versus itself)
gave exactly zero own, rival and margin differences in both seats;
`rollout_identity_seed0.json`. In a demonstration with the previously
rejected v5 throughput policy, own cash changed by −20,651 and −21,289;
rival cash changed by +22,007 and +20,890. Paired margins fell 42,658 and
42,179, respectively; `rollout_v1_v5_matched_seed0.json`. This is not new
strength evidence for either agent, but it validates the causal accounting
and confirms that future bundle policies must measure both sides' cash.
