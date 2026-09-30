# Public-movement sale model

Parent: frozen experimental selector 94f0602f, still unpromoted. Passive
development audit found 5–24 sale-race opportunities in each remaining
loss trace. Source models use only the past eight public worker-position
states at the current turn. At least three distinct states are required;
all models matching that history must agree on a positive sale quantity.
Do not use team identity, seed, future observations, or replay outcomes.

Compile the 50 downloaded public position/action histories into a compact
consensus-sale map keyed by a hash of (turn, eight past/current position
states). This is explicitly replay-trained data. Runtime physical actions
stay identical to the parent. Only advance held cash products that the
parent already plans to sell within 24 turns, before the next shop unlock.
Exclude wheat, fertilizer, animals and seeds. Reserve any planned pickup
of the product. Act only when predicted rival sales exceed known town
consumption before the original sale, and the current price is above one.
Respect ten order slots and deduct advanced quantities from their original
scheduled sale; no new production or borrowed inventory is assumed.

Freeze one candidate. Development is the five remaining matchups, both
seats (ten games). Require a strict increase in both-seat wins, no prior
seat win lost, all DONE, and nonzero activation. If it passes, run all 50
both seats, requiring more than 45 sweeps and no prior sweep lost. These
results remain training/regression, never independent validation. A fresh
native protocol with meaningful reactive activation must pass before any
promotion. Main and the ongoing 94f confirmation remain unchanged.
