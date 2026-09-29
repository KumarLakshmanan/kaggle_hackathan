# Pet source-branch guard (2026-09-29)

## Artifact and scope

This is an isolated derivative of the exact ebf candidate. It adds only a
step-72 `bridge_branch` telemetry field and requires `_BRIDGE_SELECTED ==
'source'` before the Pet route splice activates. The gate still uses the same
public shop leaf, rival melon count, and public WHEAT inventory. No game,
transition, Kaggle operation, or pilot edit was made.

| Item | Path | SHA-256 |
|---|---|---|
| Source ebf | `diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/candidate.py` | `ebfbe6e91008cf39d1929d52a60e3cb140d2b1cffdd3fac8e06c122eb9876bbe` |
| Guarded candidate | `diagnostics/pet_source_guard_20260929/candidate.py` | `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55` |
| Frozen 96-job pilot manifest (unchanged) | `diagnostics/a44_ghost_kwa_piice_petmarket114260_reactive_20260929/frozen_manifest.json` | `f615612d6dfd6d2208f8615d56d8d5f702bbfa6da108be99f70ff661ff5e899f` |
| Saved feature census | `diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/feature_census.json` | `becf475a6fbfff891aa278dff51e742f3b52d96860e0f47a436273ef9472afe8` |
| Saved outcome receipt | `diagnostics/a44_ghost_kwa_piice_petmarket114260_on6a_20260929/outcome_receipt.json` | `ec2f45acfa6a7988868bb13e657a639e546ced46d148c15456e78679b0d7dcb5` |

## Why the guard is correct

The Pet layer commits through `_a44_goose4_commit`, which edits the candidate
module's `_DATA['route_map']` (lines 1214–23, 1714–18). The opening bridge
builds `shared150` and `shared151` agents in separate namespaces (lines
968–96); after selection it dispatches to that donor namespace's `agent`
(lines 1120–23). Therefore a route committed to the candidate's root map is
not consumed when a donor branch is selected. The old predicate could report
647 active calls in that case even though it changed no played route. Other
route splices already require the source branch.

The guarded field records the actual selected bridge at step 72. A donor
branch now records its name, reports the Pet gate inactive, leaves the source
route map untouched for this gate, and counts zero Pet calls. A source branch
with the same public feature values behaves as before.

## Saved Pet activations

The static census has four feature hits, zero in the top-20 rows: both seats
of `live-114260122` and both seats of `public-win-114192390`. All four saved
observations have leaf `PET_CAFE|M8+|C>S|G0`, 12 rival melons, and public WHEAT
stock 9,975. Census `source_selector: false` means the isolated-pasture
override did not fire; it does **not** mean the selected branch was a donor.
The archived step-1 traces show zero rival hands and zero pastures in all four,
which implies the existing bridge falls through to `source`.

For the two target seats, the completed receipt records `bridge_selected:
source`, Pet active, route `113517834`, 647 calls, and zero Pet errors. Both
change from a 6a loss at -32,028 to a win at +22,524. The two public-win
controls also pass the saved feature/route/call telemetry checks and stay
wins, with margins lower by 21,106 and 21,699. Their compact receipt stores
only telemetry-check booleans, not raw `bridge_selected`; source is inferred
from their saved step-1 observations, not asserted by the receipt. These are
historical-prefix/fixed-tape results, not independent policy validation.

## Focused checks after the reactive pilot

Root decides whether and how to run these after reviewing the frozen pilot;
this plan does not authorize another run or an upload.

1. Keep the frozen pilot's existing all-arm timing and outcome gates unchanged.
2. If a follow-up is approved, verify the guarded candidate in both seats with
   the standard file loader and native runner. Confirm that a source-branch
   Pet hit reports branch `source`, route `113517834`, and 647 calls; an
   otherwise matching donor-branch hit reports its donor name, inactive gate,
   blank route, and zero calls.
3. Compare guarded candidate versus exact ebf on the four saved hit fixtures
   and paired non-hit controls. These historical replays check the narrow
   code change only; require fresh reactive evidence for promotion.
