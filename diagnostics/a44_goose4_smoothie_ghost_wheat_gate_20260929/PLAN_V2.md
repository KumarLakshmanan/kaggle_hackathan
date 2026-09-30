# Ghost Ice wheat gate — superseding static preflight plan

This document supersedes the static-preflight method in `PLAN.md`. The frozen
candidate, 12-game panel, source files, and `PLAN.md` remain unchanged. The
original policy-action replay was stopped after 20 of 208 rows took about two
minutes and used about 1.35 GB of working memory. No game engine was loaded,
and no outcome game ran.

## Bound candidate

Candidate SHA-256:
`228ca9da123ef388b5430d4451020820d7e3854a8dc7ec5fd7ae54e9da1d2767`

The candidate is reconstructed byte-for-byte from accepted parent
`6d3d1c0df1b06566417d8ba204e05e0caad9a115bb84b73513bef68575a70bf9` using
the four frozen replacements in `patch_spec.json`. At step 72, only the
source branch with public key `ICE_CREAM_SHOP|M8+|C>S|G0` and public
`market.inventory.WHEAT <= 9975` selects route `113360743`.

## Static equivalence proof

The preflight hashes all inherited Goose4 and accepted-6d manifest inputs,
then verifies the 208 unique bound step-72 feature rows and trace files. It
recomputes the public key from the saved observation, reads public WHEAT, and
evaluates the frozen predicate. Expected coverage is exactly two Ghost seats,
zero top20 seats, zero public-win seats, and zero shared151 seats.

For every one of the 206 false-predicate rows, the derivative's route
expression falls through to the same `_A44_GOOSE4_RULES.get(leaf)` result as
the accepted parent. The source activation, key, commit, and route lookup
helpers are byte-identical to the parent; all embedded route data are
identical. The reset function adds clears for the new telemetry fields, while
its route-map and FARMICE restoration statements remain byte-identical. The
new telemetry fields are not read by action-selection code. Equal selected
routes therefore enter the same unchanged commit path and preserve the same
route map and later policy decisions. This is a source-level equivalence
proof over the frozen feature rows; it does not replay action streams or claim
direct output hashes.

The route-map check binds all 155 `ICE_CREAM_SHOP` entries, verifies the
113360743 schedule against its separately bound source candidate, confirms
that other route keys and donor namespaces are untouched, and verifies that
the unchanged route-map/FARMICE reset statements restore the exact original
state after the additive telemetry reset.

## Frozen outcome panel

After root review and coordination, run both seats for the six fixtures in
`panel.json`, 12 games total. The two expected activations are
`live-114288168` seats 0 and 1. Ten Ice-key controls must remain on the
accepted parent route. These are fixed-tape diagnostics; reactive validation
is separate, and no promotion is claimed.

Command for this static-only preflight:

```powershell
python -X utf8 diagnostics/a44_goose4_smoothie_ghost_wheat_gate_20260929/preflight.py
```

The preflight writes `preflight.json` and `frozen_manifest.json` only in this
new diagnostic directory. It makes zero agent action calls, runs zero engine
transitions, and runs zero outcome games.

## Preflight attempt record

The initial direct action replay was stopped after 20/208 rows (14,380 saved
observations) because it took about two minutes and reached about 1.35 GB of
working memory. It emitted no receipt or manifest and advanced no engine.
The first structural check then failed an overstrict assertion that the whole
reset helper was byte-identical. Review confirmed the candidate intentionally
adds ghost telemetry clears there; the revised check compares the original
route-map/FARMICE reset statements exactly and validates the additive clears.
