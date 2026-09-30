# Observable opening selector: prospective native gate

Frozen 2026-09-28 before a v2 selector is built or any native outcome is read.

The 50 saved fixtures remain development data. Run this gate only if the
bounded selector preserves every incumbent winning seat and improves on
17/50 both-seat sweeps. Freeze its source hash in `selector_manifest.json`.
Instrumentation exposes selected-arm counters and V43's hidden fallback
exceptions without changing returned actions.

## Integration

Run the packaged selector on all 50 saved fixtures in both seats with the
unmodified 1.32.7 native engine, original shops and 720 turns. Its selected
arm, final rewards and result must exactly match the chosen arm from the
completed development screen. Require zero policy exceptions, all games
DONE/DONE/720 and no formerly winning seat lost. Configuration seed is masked
from both agents. A mismatch is a packaging failure, not a reason to refit.

## Reacting references and seeds

Use three distinct complete policies, each reloaded for every game:

- Current uploaded 4ee: `main.py`, SHA-256
  `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- V43: `main_v43_current.py`, SHA-256
  `69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3`.
- Public market policy: `public_market_smart_f6a756cf_20260927.py`, SHA-256
  `f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.

Pilot seeds 2908000 through 2908007 inclusive. If it passes, untouched
confirmation seeds 2908100 through 2908115 inclusive. No previous use of
these seed ranges was found in the local research scripts or plans before
this plan was written. Test both selector and unchanged incumbent against
each reference in both seats for each seed: 96 pilot and 192 confirmation
games. Shops and the full 720-turn horizon are native; agents cannot see
the configuration seed. Four workers in finite checkpointed batches.

## Frozen pass/fail criteria

Wins count 1, draws 0.5, losses 0. Both seats of every seed remain together.

Pilot must complete all games without agent errors, must select V43 in both
seats on at least four reference/seed pairs, must have at least as many win
points as the incumbent against each reference, and must improve pooled
win points strictly. A failed pilot rejects this exact selector for
promotion; do not retune it on these supposedly confirming seeds.

Confirmation must satisfy the same completion, error and reference-specific
nonregression gates, select V43 in both seats on at least eight reference/seed
pairs, and have a strictly positive lower endpoint of the 95% percentile
bootstrap interval of paired win-point improvement. Resample entire seeds,
including both seats and all three references, 10,000 times with RNG seed
2908199. Also require strictly positive pooled win-point improvement.
Cash margins diagnose the mechanism but are not an additional rejection
criterion when the win-rate gates pass.

Any candidate that passes still needs regression against the 54 previously
saved public wins and both-seat file-loader checks before promotion. Freeze
that regression's hashes before running it. Back up main before promotion.
No Kaggle access, download or upload is part of this work. The full requested
endpoint remains all 30 saved losses and all 20 saved top-team replies won
in both seats; a partial improvement does not complete the goal.
