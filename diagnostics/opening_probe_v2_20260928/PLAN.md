# Common opening with incumbent market parity — 2026-09-28 IST

The full objective remains all 30 saved public losses and all current saved
top-20 replies in both seats. The first common-opening experiment exposed
a concrete defect: preserving only farm and inventory state at turn 3 did
not preserve the incumbent's shared market and cash. Two previously won
top-20 fixtures became losses under both arms. This revision addresses that
mechanism before any new complete-game outcome is read.

## Frozen revision

Use exact 4ee `main.py` SHA
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`
and V43 SHA
`69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3`.
Preserve the incumbent's step-0 gross WHEAT order quantities and their queue
indices. Defer its private COW/SHEEP purchases with NOOP slots, and buy one
WHEAT seed in the original STRAWBERRY seed slot. Retain all four hires in
their original positions. Both complete arms share that action.

For the 4ee arm, supply its parent at turns 1 and 2 with the exactly
reconstructed incumbent observation: account for the deferred animals and
seed cash, and commute the farmer's WHEAT planting with its COW pickup.
Keep the parent's WHEAT trade slots intact; replace the advanced WHEAT seed
purchase by NOOP and append the deferred fixed-price purchases. At turn 3
resume the unchanged parent on the actual state. V43 uses the previously
specified pickup swap and offsets its two advanced WHEAT units and seed.

## Gates and evaluation, set before revised outcomes

1. Verify the 4ee arm against its exact parent on all 50 saved entries in
   both seats, stopping each run after four turns with 720-turn configuration.
   At observation 3 require the entire observation to match, including both
   farms' cash, the shared market and town, own inventory, seeds and crops;
   ignore only runtime's remainingOverageTime. Require common step-1
   observations between arms on the five frozen DECEM/Boey/Vadim/DSM/Majkel
   cases, both seats, and V43 physical parity except its two idle extra hands.
   Any mismatch stops full-game testing and must be diagnosed first.
2. If the stronger parity gate passes, run each exact arm against all 50
   fixed replies in both seats (200 games) using the same original-shop
   native runner, with eight workers. Verify 4ee arm outcomes equal the
   incumbent baseline as well as reporting V43 changes.
3. The same bounded visible-state rule family from the first experiment is
   used: at most two decisions on rival cash, hands or initial net WHEAT
   buying, with the same predeclared cutoffs. Select by both-seat sweeps,
   then win points. A qualifying rule must preserve every incumbent winning
   seat and add both-seat wins. All 50 fixtures remain development data.
4. Freeze any resulting selector bytes, integration checks and fresh native
   reacting-reference gates before those outcomes. A fixed-reply gain does
   not authorize promotion. Keep main.py and its backups intact, and do not
   check Kaggle, download or upload.

Harness recovery note, 2026-09-28 00:58 UTC: the initial prefix process no
longer exists and wrote no complete output; its partial console results do
not count as a pass. The runner retained dynamic policy modules in
sys.modules, causing excessive memory use. It now removes those modules,
collects them between paired prefixes, checkpoints every result, and uses
four workers with bounded worker lifetimes. Candidate bytes and the gates
are unchanged. The full-game batch will also use four workers.

At the next check, the coordinator was live with no child workers after
exactly 32 completed checks; automatic worker recycling had stopped task
dispatch. Its verified coordinator PID was stopped, and all 32 checkpoints
were retained. Explicit finite process-pool batches now replace automatic
worker recycling. Candidate files, fixtures, gate and completed checks are
unchanged.
