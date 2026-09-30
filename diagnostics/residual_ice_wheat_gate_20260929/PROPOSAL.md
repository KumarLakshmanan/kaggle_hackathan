# Residual Ghost Ice route proposal — 2026-09-29

## Status

Static proposal only. No candidate derivative or runner was created, no games were run, no experiment completed, and no promotion is recommended. The proposal is bound to exact uploaded a44 SHA `a44c8c2cc453d5b2d0f2be105afe5d650f762fe39674d51cb10d7d54e727090f`, Goose4 SHA `c76dc9078b59b400e4facbf0a70969e6da32c395dc6a1a63fd9bb78cb2b56632`, and accepted Goose4+Smoothie candidate SHA `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

## Hypothesis

At observation 72, on the existing `source` bridge branch only, refine the current Goose4 rule key `ICE_CREAM_SHOP|M8+|C>S|G0`: if public `observation.market.inventory.WHEAT <= 9975`, select route `113360743` instead of route `113470868`. This is one refinement of an existing Goose4 rule key, so the expected Goose4 key collision count is one; the Smoothie key is different, and the rule stays outside the shared151/pasture branch. Apply the route choice before `_a44_goose4_commit`, not as a later action wrapper.

The gate reads only the public first shop, rival public tile counts already used by the Goose4 key, bridge branch, step and public market wheat inventory. It does not use fixture identity, opponent identity, cash, coordinates, seed or private state.

This is a replay-trained threshold hypothesis. In the exact 6d-bound rows sharing the coarse Ice key, Ghost has WHEAT stock 9975; the other five fixtures have 9976 or 9977. The one-to-two-unit difference is thin evidence and may encode the saved market history rather than a transferable condition.

## Exact a44 and accepted 6d margins

All 208 exact observation72 feature rows were joined to their compressed trace hashes; all trace hashes and recomputed public shop/rival keys matched. The a44 control margins come from the hash-bound 208-row a44 receipt, and accepted margins come from the exact 6d candidate result receipt.

The predicate triggers 2/208 seats, both seats of `live-114288168`. It matches zero top20 and public-win seats. The coarse key covers 12 seats in six fixtures; ten are no-trigger controls. The other 196 rows do not meet the public key and source-branch guard.

| Fixture | Panel | 6d branch | 6d public WHEAT | Gate fires | Exact a44 margins, seats 0/1 | Accepted 6d margins, seats 0/1 |
|---|---|---|---:|---|---|---|
| `live-114255779` | loss30 | `source` | 9977 | no | +16321, +16321 | +9559, +9559 |
| `live-114258293` | loss30 | `source` | 9977 | no | -9211, -9211 | +7157, +7157 |
| `live-114288168` | loss30 | `source` | 9975 | yes | -2085, -2085 | -2253, +1425 |
| `public-win-114209881` | public-win | `source` | 9977 | no | +23901, +23901 | +1337, +1337 |
| `public-win-114221853` | public-win | `source` | 9976 | no | +4067, +4067 | +2097, +2097 |
| `public-win-114245470` | public-win | `source` | 9977 | no | +6184, +6184 | +10228, +10228 |

The current 6d target result is still a split for Ghost: seat 0 loses by 2,253, and seat 1 wins by 1,425. The earlier route result is not a measured result for the exact 6d derivative.

## Earlier route screen, shown separately

The exact source file for route `113360743` is [faecafbb131c…](../ice_finalist_controls_20260928/candidate_113360743.py) (SHA `faecafbb131c0bd81cbcbea0ea905bb3836e7deefab550037674276fde33fb25`). Its embedded schedule matches the route already present in the 6d candidate, has 719 actions, and first differs from route `113470868` at action index 72.

That screen was run on a frozen exact367 production-selector parent with saved tapes. Every screen row reports the Ice production leaf selected. It reports Ghost +1,298 in both seats and keiz (`live-114258293`) +4,894 in both seats. It also loses both seats on `public-win-114209881` (-8,637/-11,555) and `public-win-114205447` (-16,092 each). Those results are not paired to the 6d feature observations below: notably, the exact 6d feature for `public-win-114205447` is `SMOOTHIE_SHOP|M8+|C>S|G+` on `shared151`, while the exact367 screen reports an Ice key for the same fixture ID. The WHEAT values below come only from the exact 6d-bound traces, not the exact367 screen.

| Fixture | Exact 6d branch / rule key | 6d WHEAT | Exact367 screen key | Prior route margins, seats 0/1 | Key and branch align? |
|---|---|---:|---|---|---|
| `live-114255779` | `source` / `ICE_CREAM_SHOP|M8+|C>S|G0` | 9977 | `ICE_CREAM_SHOP|M8+|C>S` | +4694, +4694 | yes |
| `live-114258293` | `source` / `ICE_CREAM_SHOP|M8+|C>S|G0` | 9977 | `ICE_CREAM_SHOP|M8+|C>S` | +4894, +4894 | yes |
| `live-114288168` | `source` / `ICE_CREAM_SHOP|M8+|C>S|G0` | 9975 | `ICE_CREAM_SHOP|M8+|C>S` | +1298, +1298 | yes |
| `public-win-114205447` | `shared151` / `SMOOTHIE_SHOP|M8+|C>S|G+` | 9975 | `ICE_CREAM_SHOP|M8+|C>S` | -16092, -16092 | no |
| `public-win-114209881` | `source` / `ICE_CREAM_SHOP|M8+|C>S|G0` | 9977 | `ICE_CREAM_SHOP|M8+|C>S` | -8637, -11555 | yes |
| `public-win-114221853` | `source` / `ICE_CREAM_SHOP|M8+|C>S|G0` | 9976 | `ICE_CREAM_SHOP|M8+|C>S` | +5069, +5069 | yes |
| `public-win-114245470` | `source` / `ICE_CREAM_SHOP|M8+|C>S|G0` | 9977 | `ICE_CREAM_SHOP|M8+|C>S` | +152, +152 | yes |

The separate exact367 results are useful as a route lead and a warning about broad Ice selection; they do not establish the conditional rule's result under 6d, nor do they provide reactive validation. The full proposed gate is false for both of those rows in the exact 6d corpus: WHEAT 9977 excludes public-win-114209881, while the public key and bridge branch exclude public-win-114205447. Unseen step72 states remain untested.

## Route-map scope and isolation

The accepted 6d source checks Goose4 activation at step 72 on branch `source`, resets the route map at step 0, then commits the selected route to every route-map entry whose first shop is `ICE_CREAM_SHOP`. The proposed commit would therefore set all **155** ICE-prefixed descendants and the first-shop fallback to `113360743`; the exact key and pre-commit route of every descendant are listed in `evidence.json`. The ICE branch leaves `_FARMICE_TAPE` alone. The Smoothie step72 key begins with a different shop and remains inactive on this Ghost rule. The donor namespaces are not changed by this route-map commit.

On the frozen corpus the guard is false for 206 seats. If implemented as a conditional route-value substitution before the existing Goose4 commit, those rows preserve the exact 6d route choice and policy path. It also excludes all 18 `shared151` rows, including the separate pasture/THIRD work. These are static code-path claims only; a derivative candidate and no-op preflight must verify them before any results can be reused.

## Remaining loss30 context

The accepted 6d result is 22/30 loss30 sweeps, 19/20 top20 sweeps, and 53/54 public-win sweeps. A successful two-seat Ghost repair would add at most one loss30 sweep, to 23/30. The other unswept rows remain:

| Fixture | Accepted 6d seat results and margins |
|---|---|
| `live-114218866` | seat0 loss -53956, seat1 loss -53956 |
| `live-114223292` | seat0 loss -33224, seat1 loss -33224 |
| `live-114227779` | seat0 loss -3858, seat1 loss -3858 |
| `live-114238112` | seat0 loss -8178, seat1 loss -8178 |
| `live-114260122` | seat0 loss -32028, seat1 loss -32028 |
| `live-114270587` | seat0 loss -18815, seat1 loss -18815 |
| `live-114274897` | seat0 loss -17760, seat1 loss -17099 |
| `live-114288168` | seat0 loss -2253, seat1 win +1425 |

`live-114274897` belongs to the separate pasture/Brunch experiment and is intentionally outside this proposal.

## Recommended decision and smallest next test

**Do not promote. Keep this as a replay-trained hypothesis.** If root later approves a derivative, first freeze it against the exact 6d candidate and preflight the route/reset/branch behavior. Then run both seats of only the six fixtures sharing the coarse Ice key: 12 games, with two expected activations and ten no-trigger controls.

Allow the other 196 current results to be reused only after the derivative passes exact hash, trigger-count, shared151-isolation, reset, all-155-route-descendant, and nontrigger decision-equivalence checks. The fixed-tape screen advances only if Ghost wins both seats, all ten no-trigger seats preserve their exact 6d decisions and outcomes, and every game is clean DONE/DONE/720 with expected route telemetry. A pass remains replay evidence; promotion still requires independent both-seat native/reactive validation and all frozen preservation gates.

## Bound artifacts

[`evidence.json`](evidence.json) contains exact input bindings, all 208 feature-row trace hashes, the 12 matching rows with a44 and 6d margins, all 14 exact367 route-screen outcomes and activation keys, the eight remaining loss30 fixtures, key-collision counts, and every one of the 155 route-map descendants. Evidence SHA-256: `eeaaf71d862693ede68a65f3877ef318b3233ab59861f431f3df84e04b25f83b`.
