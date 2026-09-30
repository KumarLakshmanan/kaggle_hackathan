# Observable first-investment opening fork — 2026-09-28 IST

## Objective and mechanism

The active objective remains both-seat wins on all 30 saved public losses
and all 20 current downloaded top-team replies. V43's completed full-loss
screen won 13/30 both-seat pairs; current 4ee wins 0/30 and 17/20 top teams.
V43 cannot replace 4ee outright because its prior top-20 pilot loses all
three target teams and regresses Majkel. Investigate a new common opening
that permits choosing either complete farming schedule after observing the
rival's first public investment. No team identity, episode ID, seed, future
shop, or rival private inventory may be used by a selector.

Both arms first buy six WHEAT, one WHEAT seed, and four hires. All units
PASS on step 0. On step 1 the 4ee arm plants its farmer's WHEAT one turn
earlier and buys the deferred cows, sheep and strawberry seed. On step 2
that farmer picks up the cow it normally picked up on step 1. Its watering
and all later work keep their original times. The V43 arm instead swaps
its step-1 sheep pickup with its step-2 WHEAT pickup, buys its melon seeds
and sheep on step 1, and reduces step-2 WHEAT buying by the two units bought
in advance. Two extra V43 hands remain idle until the normal daily expiry.

This is a new complete opening experiment, not a promotion of V43 or a late
suffix transplant. Keep original main.py and its existing backups intact.
No Kaggle access, downloads, or upload.

## Frozen sources

- 4ee main.py SHA-256:
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- V43 main_v43_current.py SHA-256:
  `69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3`.
- Unified fixture manifest SHA-256:
  `524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.

## Sequence and gates, frozen before candidate outcomes

1. Build both standalone arms and record their hashes. Verify first-three-
   turn transitions against each unchanged parent on DECEM, Boey, Vadim,
   DSM, and Majkel in both seats. At observation step 3, crop/animal state,
   existing unit positions and inventories, seeds, and shed must agree with
   the parent, except the two explicitly inert extra V43 hands and their
   hire count. Cash and shared-market outcomes may differ and are recorded.
   Do not read whole-game candidate outcomes before this physical gate.
2. If physical verification passes, run both exact arms on all 50 saved
   entries in both seats (200 games), original fixture seeds and generated
   shops, engine 1.32.7. Capture the step-1 public rival cash, hired hands,
   farm state and shared market; the two arms must have the same step-1
   observations for a given seed/seat/opponent. Report actual both-seat wins,
   lost current wins, margins, completion and timing. These are development
   action-tape results; they are not independent reacting-policy validation.
3. Only propose an observable selector if the arm results contain a real
   win tradeoff and visible early features explain a reproducible rule.
   Freeze its exact rule and new candidate hash before its outcome tests.
   A full 50-entry regression run and fresh local native games in both seats
   against current 4ee and a distinct reacting reference are required before
   any promotion. Select fresh seed blocks before outcomes. No promotion is
   authorized merely by the arm screen or an oracle choosing after rewards.

Before all arm outcomes are available, the selector search is limited to
at most two threshold decisions (three leaves). Allowed features are
rival hired-hand count with cutoffs 0/2/4/6/8, rival cash with cutoffs
500/1000/1500/2000/2500, and rival net initial WHEAT purchase with cutoffs
0/4/8/16/32, inferred from shared inventory after subtracting our known six
units. Fit for both-seat sweeps first, seat win points second, and cash
margin only as a tie-breaker. Report separately the best rule preserving
every incumbent winning seat; if none exists, it cannot qualify as a repair
of the incumbent. All 50 saved fixtures remain development data.

Record a dated rejection or continuation decision at each completed stage.
