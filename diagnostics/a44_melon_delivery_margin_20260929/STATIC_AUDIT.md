# Static feasibility audit — a44 melon delivery margin

**Status:** refreshed 2026-09-29. Candidate and streaming action-transform check passed. This remains outcome-blind: no native game, simulation, reward/margin outcome, or Kaggle call was run.

## Hash bindings

- a44 incumbent source: `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`
- isolated candidate: `dbf54f4d89d0c56d89959e858bde7ffd02a160c1c4013c6cf7c80b25b522313e`
- deterministic candidate builder: `52fd610e8a6578369e7feaf81412dbbd944a045af04dbdaa257775ecfb914e83`
- streaming action-transform checker: `afb0effbb285e345175a070ddfc762fc096fa031738b108bf372c35286887d9b`
- frozen plan: `e7c2b704a7dca092f8e760ba89df326bb283f44e89053d6c6cf2d88a9567b300`
- final manifest: `15599920d47d783c127f392460a6b2eeefb7540418ce94a0a9bc6db0af8c0f24`
- action-transform receipt: `0ee2187efb7bc046b6f234351c284bbbbba6f831b716e247288a1c26522bff67`
- full results: `ea74d2be3b852acf83885a35ce55296b391eff8b33b1bd5f556fa6242fa1d732`; 100 bound target seat traces
- selector semantic SHA: `33a813c56bc0c913a445508523288e6ebebbad5b1cf437e610074eb46507af52`; predicate file SHA: `cf67647b77a2b870d7a7841dc32c5709f2c51ccac8043054e882193d1a388593`

The manifest binds the plan, candidate, builder, checker, incumbent evidence and selector. The receipt binds the final manifest and candidate. Candidate regeneration was deterministic and reproduced the bound candidate SHA.

## Frozen selector and activation receipt

The v2 predicate activates at step 713/day 29/hour 17 only for exactly one own hand at `[1,4]` with incumbent action `WATER`, MELON inventory at least 12, public MELON quote at least 100 (no ceiling), and shed-access distance at most 3. It reads no rival-private fields or rival policy actions.

Across all 100 individually bound seat traces it has exactly four activations: offhand `live-114271958` seats 0/1 and top20 Unknown Mother-Goose `top20-08-Unknown Mother-Goose-114272024` seats 0/1. The activation quotes are 133 and 158, respectively. Baseline margins are +670 and +4,471 per seat. The higher quote case remains included; no ex-ante economic basis supports a ceiling.

## Delivery path and known cost

At steps 713–718, the saved offhand hand state/action sequence is:

| Step | Baseline position | Inventory | Baseline action |
|---|---|---|---|
| 713 | `[1,4]` | MELON 12 + FERTILIZER 1 | WATER |
| 714 | `[1,4]` | MELON 12 + FERTILIZER 1 | HARVEST |
| 715 | `[1,4]` | MELON 18 + FERTILIZER 1 | EAST |
| 716 | `[2,4]` | MELON 18 + FERTILIZER 1 | EAST |
| 717 | `[3,4]` | MELON 18 + FERTILIZER 1 | EAST |
| 718 | `[4,4]` | MELON 18 + FERTILIZER 1 | DROP |

The candidate instead commands EAST at 713, 714 and 715, so its projected step716 state is `[4,4]` with MELON 12 + FERTILIZER 1. Step716 then DROPs the full 13-unit inventory and appends one `SELL MELON 12`. This gives up the observed six-unit melon harvest. Step716 baseline MELON quote is 91 for offhand and 158 for UMG; the quote floor applies only at selector activation, not during continuation. No realized cash or paired-margin benefit is inferred.

Trace rows omit per-game configuration. Runtime activation requires actual supplied `boardSize=10`, shed capacity sufficient for existing shed plus the full carried stack, and an order slot. At step716 the wrapper rechecks capacity, duplicate MELON orders, order slots and competing own DROP/PLACE actions. Unsafe full deposit falls back to PASS; safe deposit with unsafe sale uses DROP only. A fallback PASS at projected `[4,4]` relies on the saved step717 EAST/step718 DROP path to stay shed-adjacent, but this is only a tape-based expectation until native prefix validation.

## Static checker result and limits

The checker streamed all 100 tapes with bounded memory. It verified exact output parity on all 96 nonactivation rows at every step (`69,024/69,024`), and the four projected target-seat action transforms (12 action changes total). It also checked the player-keyed step0 reset, no cross-player latch clearing, trigger-only continuation, out-of-order and projected-state mismatch clearing, board size at steps 713–716, config fail-closed behavior, step716 fallbacks, and candidate loader/entrypoint presence. It did not call the final agent entrypoint or parent policy on counterfactual observations and did not evaluate rewards/margins.

Native step-by-step prefix validation in both seats of offhand and UMG is mandatory before any outcome run. Frozen outcome gates are in `PLAN.md` and `manifest.json`. Saved tapes are regression controls, not independent validation.
