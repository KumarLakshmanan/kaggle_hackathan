# Economic model, first runnable version

The main agent implemented the model after taking over the economics write
scope. `economics.py` exposes exact `price`, exact current `demand_per_day`, and
approximate `investment_values`. Everything uses current observations and
configuration; there is no seed, replay identity, future-shop access, or
opponent private inventory access.

Price parity covers all nine products across scarcity, both hinge regions,
equilibrium, gluts and floors, including sparse configuration overrides.
Production tests compare daily profiles directly with engine refresh and
unit-action functions for all three animals, all three one-time crops and
both ongoing crops. CARE enters its bonus bank after a production event.
Melons cannot be harvested before age 10, even with an early six-unit yield.

The investment model accounts for the candidate's marginal effect on prices
received by already-owned assets. It projects the publicly visible plants
and animals on both farms, subtracts wheat feed and fertilizer inputs, and
subtracts capital and estimated labor expense. Two scenarios vary competing
production and future demand. Future shops are an explicit expectation over
possible random draws; their actual identities are never consulted.

Approximations requiring empirical validation:

- Successful future feeding, watering, care, harvest and delivery are assumed.
- Daily market flow is valued at a midpoint price rather than every actual
  interleaved per-turn trade; this can misprice rapid price changes.
- The rival's future investments and private stored inventory are unknown.
- Existing ongoing plants use only observed fertilizer; new projects assume
  feasible future fertilizer applications.
- Labor cost and crop/animal duration estimates are heuristics. The scheduler
  must still demonstrate that its promised work can be completed.

The actual engine runs, not these value estimates, decide promotion.
