# Observable-history balanced quantity experiment — frozen 2026-09-28

Separate hypothesis after the observable queue-order candidate failed its
development rescue gate. Its source/results and rejection remain unchanged.
These six saved fixtures are reused development data, not a holdout.

Keep current 4ee main, its route/worker actions and market order sequence.
Use the already verified legal-observation history feature and the same
explicit idle, mirror, prior-day and two-days-prior same-hour net-flow
forecasts (including reversed historical product order). Unknown price-floor
or midnight flow values remain unknown. Historical private stocks are
hypothetical forecasts capped to shed capacity, never actual rival data.

For WHEAT and FERTILIZER only, find the first existing positive-quantity
BUY_PRODUCT and SELL orders. Add the same delta to both quantities, from
the fixed set +4,+12,+24,-4,-12,-24, retaining quantities in 1..100. At most
12 proposals; do not add orders, alter their order or change worker actions.
Thus net intended product commitment is unchanged. Accept only when the
exact forecast simulator preserves own resources and non-idle rival
resources, never lowers own cash or relative cash in any scenario, and
improves aggregate historical-scenario relative cash. Rank by minimum
history gain, summed history gain, summed all-scenario gain, minimum own
gain; keep incumbent on ties. Stop extra search below five seconds of
reported overage. This is a single frozen candidate, no parameter search.

Input source hashes are the same as the preceding queue experiment:
main `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`,
native_core `5f0c0551ed330129e9211044b8417eaf3bcb90aabfa82ecd480d59564a340795`,
observable_flow `5b84b59edd362b31696e1941a607fcb60aaf6c8084d5f35e985991c1d9af0c0d`.
Freeze generated standalone bytes before any outcome. No episode identity,
configuration seed, future action or rival private state enters the agent.

## Development, parity and regression gates

Target manifest SHA
`524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.
Four targets: public Yaroslav 114283577, Kucing Garong 114236633, leave you
114279280, and current top20 Vadim. Controls: current top20 Majkel1337 and
Kaggledew Valley. Test both seats in the validated fast harness (12 games).
Require no recorded errors, all DONE/DONE/720, both controls preserved, and
at least one new both-seat target win. Reject if any condition fails.

Only on pass, reproduce all 12 with native engine 1.32.7, original shops,
hidden configuration seed and full 720-turn configuration; require exact
rewards and telemetry and no errors. Then complete all 50 saved fixtures in
both seats, preserving every incumbent winning seat and adding at least
one both-seat win. Fixed tapes remain development/regression evidence.

## Fresh reacting qualification, conditional on earlier gates

References: exact main above and public market policy
`f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.
Pilot seeds 2914200–2914203; confirmation 2914300–2914307, used only after
pilot pass. Run old/new × two references × both seats: 32 / 64 native games.
Original shops, seed hidden, policies reloaded, all DONE/DONE/720 and zero
recorded errors. Require activation on at least two distinct pilot seeds
and four confirmation seeds, no reference-specific win-point regression
and positive pooled gain at each stage. Wins=1/draws=0.5. Confirmation also
requires positive lower 95% bootstrap endpoint, 10,000 whole-seed resamples
retaining both seats and references, RNG 2914399; normalize summed point
delta by candidate game count. No added cash-only veto.

Before promotion, preserve the 54 saved public wins and pass local file-loader
checks in both seats. Back up main, update memory, no Kaggle access/upload.
Do not combine unqualified candidates or claim the full 50/50 goal complete.
