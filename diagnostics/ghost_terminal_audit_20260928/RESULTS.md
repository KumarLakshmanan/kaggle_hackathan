# Ghost Rule near-loss audit

Exact ICE_CREAM_SHOP/113332529 against saved114288168 reproduces81,439
versus81,460 (−21) in both seats, with full telemetry matching the prior
320-game receipt. These two repetitions add no independent outcome data.

At the final unit phase all14 bags empty. The shed receives exactly93
units, and each product's complete quantity has a matching scheduled sale.
The shed capacity is100, so no terminal delivery clips in this trace.

The remaining idle suffixes contain only1–4 actions. For every idle unit,
an optimistic scan of all publicly available harvest/fertilizer targets
finds no collect-and-deliver path that finishes by the last action718.
It assumes shortest Manhattan paths and ignores competition from other
workers, making this an optimistic bound. No candidate has been changed.

**Decision: reject extra terminal liquidation or collection in these idle
suffixes as a repair for this particular near-loss.** This does not rule
out earlier scheduling or market changes. The broader91-route search is
separate and retains its frozen scope.

Evidence: audit.json, seat0/seat1 full traces, idle_reach.json. Audit SHA:
`21735e69e1f4e84e327a6e373838ebeba9eef58416b965a9acce9fad4f0ada43`.
