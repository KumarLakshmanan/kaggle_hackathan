# Observable-history queue experiment — frozen 2026-09-28

## Mechanism

Keep current 4ee source and its full route/worker/purchase quantities. Add a
single queue-reordering layer after the incumbent. It stores only our prior
legal observation/action and the certified past rival net-flow feature.
Skip censored products and midnight observations; unknown is never zero.

At each turn, use nonempty inferred net-trade queues from the same hour one
and two days earlier. Forecast both product order and reversed product order,
along with idle and mirror-incumbent scenarios. These are hypotheses, not
known rival actions or private stock. Historical SELL stock is a synthetic
forecast, capped to the shed capacity. The mirror forecast is explicit too.

Compare at most 24 distinct single-order moves earlier in the existing queue,
plus its unoptimized original ordering only when the order multiset matches.
Quantities and market order contents remain unchanged. Use exact own
post-worker private stock from the physical core. Require own cash and own
resources not to regress against the incumbent queue in every forecast,
unchanged rival resources in non-idle forecasts, and no relative-cash
regression in any forecast. Require a positive aggregate history-scenario
gain. Rank by minimum history gain, total history gain, total forecast gain,
then minimum own gain. Keep the incumbent on ties. Stop the extra optimizer
when reported remaining overage is below five seconds. Record errors and
activation. No fitted thresholds or candidate variants in this experiment.

Source main SHA-256:
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Embed exact native_core SHA
`5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795`
and corrected observable_flow SHA
`5b84b59edd362b31696e1941a607fcb60aaf6c8084d5f35e985991c1d9af0c0d`.
Never embed any episode seed, future action, rival private state or fixture
identity. Freeze standalone bytes and plan hash before outcomes.

## Development and native parity

Use the three closest public losses by mean paired deficit: Yaroslav
live-114283577, Kucing Garong live-114236633, and leave you live-114279280;
add top20 Vadim Vasilenko. Winning controls: top20 Majkel1337 and Kaggledew
Valley. All fixtures come from target manifest SHA
`524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.
Run both seats in the validated fast diagnostic harness: 12 games. Require
all complete/error-free, both controls still won in both seats and at least
one new both-seat target win. Otherwise reject the exact candidate.

If that passes, repeat all 12 with full native engine 1.32.7, original shops,
hidden configuration seed, 720 turns. Require identical rewards/telemetry,
DONE/DONE and no recorded errors. Then run all 50 saved fixtures in both
seats, requiring every incumbent winning seat retained and at least one
new both-seat win. These are development/regression, not independent strength.

## Fresh reacting qualification, conditional on development pass

References: current 4ee and public_market_smart_f6a756cf_20260927.py, SHA
`f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.
Pilot seeds 2914000–2914003; confirmation only on pass, 2914100–2914107.
These ranges had no prior local research occurrence when frozen. Run old and
new against each reference in both seats: 32 pilot / 64 confirmation games.
All native original shops, seed hidden, policies reloaded, DONE/DONE/720,
zero recorded errors. Require activation on at least two distinct pilot
seeds and four confirmation seeds, no reference-specific win-point regression
and positive pooled win-point difference in both stages. Wins=1, draws=0.5.
Confirmation also requires positive lower 95% percentile bootstrap endpoint:
10,000 whole-seed resamples, keeping seats/references together, RNG 2914199,
win-point delta divided by candidate seat-game count. No cash-only veto.

Before promotion, preserve all 54 saved public wins and pass local file-loader
checks in both seats. Back up main and update research memory. No Kaggle
access or upload. Do not combine with another unqualified candidate.
