# Ghost Ice wheat gate — frozen 12-game plan

## Status

Separate experimental derivative of exact accepted candidate `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`. Static candidate and action-equivalence preflight only; **no outcome games have been run**. The accepted 6d source/result files and root `main.py` are unchanged. Do not promote this derivative based on the saved-tape panel.

## Candidate change

At step 72, require the current Goose4 `source` branch and key `ICE_CREAM_SHOP|M8+|C>S|G0`. Read only public `observation.market.inventory.WHEAT`; when it is `<= 9975`, choose route `113360743` instead of existing route `113470868` before `_a44_goose4_commit`. The candidate reports branch, key, inventory, activation, and selected route through `a44_ghost_wheat_*` telemetry. No identity, cash, seed, coordinate, or private selector is added.

The derivative is exactly the accepted 6d candidate plus the four frozen replacements in `patch_spec.json`. Its SHA-256 is `228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767`. The parent is bound at `6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9`.

## Frozen panel

Run both seats of these six matched Ice-key fixtures, 12 games total:

- `live-114255779`
- `live-114258293`
- `live-114288168`
- `public-win-114209881`
- `public-win-114221853`
- `public-win-114245470`

`panel.json` binds every seat to the accepted 6d result, exact a44 control, source trace SHA, step72 public key/inventory, expected route, and candidate/source/panel hashes. Expected activations are exactly the two `live-114288168` seats. The other ten seats matching the coarse key must select the existing route. The other 196 feature rows may be reused only after this preflight and an independent review of its receipts.

Pass the 12-seat screen only if both Ghost seats win, all ten false-trigger controls preserve their exact accepted 6d decisions and outcomes, and all games finish DONE/DONE/720 with zero candidate errors and expected activation telemetry. This is a fixed-tape diagnostic; reactive validation remains a separate gate.

## Static preflight

Run:

```powershell
python -X utf8 diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/preflight.py
```

The preflight rechecks all parent evidence hashes and the byte-exact patch. It recomputes public features and trigger coverage for all 208 rows, replays stored observations through each policy without advancing the game engine, and checks action equality on every available observation for all 206 nontrigger seats. On the two trigger seats it requires identical actions through step 71 and exact activation/route telemetry at step 72. It also checks source/shared151 isolation, all 155 Ice route-map descendants, donor-map stability, and the step-0 map reset. It writes only `preflight.json` in this new folder.

No game runner is included or invoked in this package. Root will independently review candidate and receipts before any outcome run.
