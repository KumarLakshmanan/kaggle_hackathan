# Loss30 mechanism proposal: Smoothie second-shop continuation

**Status (2026-09-29):** read-only audit complete. No candidate was built, no game or simulator was launched, no experiment was completed, and no promotion is recommended. This proposal uses frozen replay evidence only.

## Finding

The best separate follow-up is a public-state Smoothie continuation for `live-114223338` (forever young). Exact a44 loses both seats by 10,466 coins. The completed Smoothie route-member screen, based on production-leaf candidate SHA `5eb6f5c15d23eb24123bb1c869eb65efbe9ddcebee784a9c1c372317c7bd4219` and frozen replay-opponent tapes, yields +313 in both seats. Its selected routes keep all ten previously winning seats across the same six fixtures. The consolidated selector has not been run as an exact-a44 integration, so this would add one possible loss30 sweep only if the result transfers when composed onto the exact a44 source bridge.

Among all 104 fixtures / 208 seats in the exact-a44 frozen feature rows, the proposed step72 key appears in exactly six fixtures / 12 seats: two loss30 fixtures and four public-win controls. It appears on zero top20 fixtures. One of the two loss30 fixtures (`live-114211346`) is already an a44 win and remains a win in the selected screen; the remaining loss is `live-114223338`.

## Falsifiable public rule

On the **a44 source bridge only**, at observation72, when the first unlocked shop is `SMOOTHIE_SHOP`, the public rival tiles show at least 8 melons, more cows than sheep, and zero geese, choose route `113470868` and mark the continuation active. At observation144, read the public first two `town.unlocked_shops`; choose the listed continuation route for that pair. Keep `113470868` for a pair absent from the frozen map. Do not activate this rule on donor branches.

| Public pair at step144 | Route |
|---|---:|
| `SMOOTHIE_SHOP|BAKERY` | 113639519 |
| `SMOOTHIE_SHOP|BRUNCH_SPOT` | 113340658 |
| `SMOOTHIE_SHOP|FARMERS_MARKET` | 113639519 |
| `SMOOTHIE_SHOP|ICE_CREAM_SHOP` | 113340658 |
| `SMOOTHIE_SHOP|PIZZA_SHOP` | 113618016 |
| `SMOOTHIE_SHOP|SMOOTHIE_SHOP` | 113639519 |

The selector uses only the publicly visible shop list and rival crop / animal tiles. It does not use fixture or opponent identity, cash, coordinates, seed, or private observation data.

## Fixture evidence

| Fixture | Pair | Exact a44 margin, seats 0/1 | Selected route-member screen margin, seats 0/1 |
|---|---|---:|---:|
| `live-114211346` (chocolat) | `SMOOTHIE_SHOP|BAKERY` → 113639519 | +6,019 win/+6,019 win | +11,582 win/+11,582 win |
| `live-114223338` (forever young) | `SMOOTHIE_SHOP|SMOOTHIE_SHOP` → 113639519 | -10,466 loss/-10,466 loss | +313 win/+313 win |
| `public-win-114216671` (yfy) | `SMOOTHIE_SHOP|BRUNCH_SPOT` → 113340658 | +10,562 win/+10,562 win | +1,245 win/+1,245 win |
| `public-win-114217947` (c_fxy) | `SMOOTHIE_SHOP|FARMERS_MARKET` → 113639519 | +872 win/+872 win | +14,384 win/+14,384 win |
| `public-win-114248439` (Rio) | `SMOOTHIE_SHOP|ICE_CREAM_SHOP` → 113340658 | +1,472 win/+1,472 win | +330 win/+330 win |
| `public-win-114258739` (Argyris Anastopoulos) | `SMOOTHIE_SHOP|PIZZA_SHOP` → 113618016 | +9,814 win/+9,814 win | +16,184 win/+16,184 win |

Seat-specific exact a44 trace SHA-256 values, source receipt hashes, selected route candidate hashes, and clean status/telemetry are in [`evidence.json`](evidence.json). Exact a44 target outcomes are bound to `adaptive_donor_pair_repair_20260928/full_results.json`; the four public controls are bound to `a44_source_bridge_goose_4leaf_20260929/source_public.json`.

## Why it is separate from the queued work

The running Goose4 rules start with `FARMERS_MARKET`, `ICE_CREAM_SHOP`, or `PIZZA_SHOP`; this proposal starts with `SMOOTHIE_SHOP`, so the first-shop rule keys do not collide. Each of the 12 eligible seats is on the `source` bridge. The pasture guard’s step1 condition is false for all 12: rival hands = 0 and rival pasture count = 0. These are static feature checks; the composed candidate still needs reset / route-map / helper isolation checks.

## Smallest useful frozen test after Goose finishes

First freeze a new isolated integration on the exact a44 bytes plus the completed Goose4 candidate, then add this source-only rule at steps72/144. Bind candidate, helpers, engine, pool, source traces, and all panels. Static checks must prove exact 12/208 trigger coverage, the six pair keys, the source-only branch, no Goose4/pasture overlap, and that the downstream schedule helpers use the selected route. The Smoothie screen proved the 11 route schedules share the same first144 actions, but that proof must be repeated for the exact composed wrapper.

After that preflight, run only the six affected fixtures in both seats (12 new native fixed-replay games). Join those rows with the completed Goose panel’s other 196 rows only after confirming byte / decision equivalence outside these triggers. Pass only if `live-114223338` wins both seats, the ten previously winning seats among the other five fixtures remain wins, and every game is DONE/DONE/720 with zero candidate errors and the expected route telemetry. This remains a development replay gate; run separate reacting-opponent checks before any promotion.

## Evidence limits and bindings

The source result is exact a44, but the selected continuation outcomes come from the 132-row Smoothie route-member screen on frozen replay-opponent tapes. The generated consolidated `candidate_selected_family0.py` has not been run as an exact-a44 integration. Therefore +313 is a falsifiable prediction for the new integration, not a completed rescue. No second mechanism met this preservation standard in this static pass.

`evidence.json` binds the exact baseline, feature rows, source traces, Goose4 / pasture candidates and preflights, Smoothie pool, route candidates, preflight, result ledger, and selection receipt by SHA-256. The global `agent.md`, frozen candidates, source files, and panels were not changed.
