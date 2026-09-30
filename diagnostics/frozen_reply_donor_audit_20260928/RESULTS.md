# Frozen reply donor audit — 28 September 2026

**The corpus contains omitted production schedules, but none can replace the current source after its existing opening.** All 50 frozen opponent action tapes are novel relative to all 145 routes in exact source 367d2e76. Neither exact actions nor physical commands match a source/library prefix through turn 72 or 144. This remains true after removing harmless trailing PASS hand padding and normalizing default unit arguments. Reject direct insertion of these donors into the existing source route pools on the available evidence.

## Provenance and coverage

- Audited 30 public-loss fixtures and 20 top-team fixtures: 48 episodes and 50 distinct full action tapes. The duplicated episode IDs contain distinct selected opponent tapes.
- Every donor has 719 actions, valid object/list/string/integer shapes, matching manifest action hashes and exact equality to the specified player's 719 recorded replay actions. All replay decompressed hashes match the manifest.
- All 145 library routes also contain 719 typed actions. They represent 91 distinct complete action schedules and 81 strict physical-command schedules, but only **one physical opening through turn 72**.
- All 7,250 donor/library comparisons are retained. All 50 donor full action and physical-command schedules are novel.
- Literal physical prefixes initially differ at turn 0 because the library pads PASS commands for future hands. The separate semantic audit removes this representation difference: 46 donors then diverge at turn 1 and four still diverge at turn 0. No donor reaches turn 72 against any library route.
- Donors contain **43 distinct normalized physical openings** and **46 distinct exact action openings** through turn 72.
- Empty market arrays and recorded PASS/NOOP market entries are separately counted as typed no-ops. This audit does not claim every scheduled request was economically executable.

Exact source SHA:
`367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0`.
Exact target manifest SHA:
`524bc1bfa2f852b3865b94c4d7a37c67be9cc56690b56d2ed0a9a201e4412e20`.

## Actionable separate opening families

Although none matches the current source, three donor groups share exact actions with one another beyond turn 144. They could support a separately built whole policy using their common opening from turn 0 and later public shop selection. State/funding and native validation are still required; this is not approval to splice or promote them.

| Common donor opening | Exact shared prefix | Recorded public shop pairs after 144 |
| --- | ---: | --- |
| boominginging 114232208, mhw 114235177, boominginging 114279308 | 151 actions across all three; first pair 153 | BAKERY/BAKERY; BAKERY/PIZZA_SHOP; FARMERS_MARKET/ICE_CREAM_SHOP |
| carbonapi 114215872, leave you 114289228 | 150 actions | BAKERY/BAKERY; BRUNCH_SPOT/BRUNCH_SPOT |
| Ghost Rule 114260122 and 114288168 | 166 actions | PET_CAFE/FARMERS_MARKET; ICE_CREAM_SHOP/PET_CAFE |

These splits happen after both shops are publicly visible, so the branch condition could use observed shops rather than opponent identity or episode seed. Recorded shop paths describe the donor archives; changing the opening or opponent can change the future shop path. Uncovered shop families require a coherent fallback within the new opening, not a jump back into an incompatible source schedule.

The broader five-member physical-only group contains carbonapi, Civitasmass, fasith 007, offhand and leave you across BAKERY, PIZZA_SHOP, ICE_CREAM_SHOP and BRUNCH_SPOT. Only carbonapi/leave you share the exact opening; other market prefixes differ, so their state/funding compatibility remains unproven. Do not treat shared worker commands as an automatic admissibility pass.

**Decision:** accept this audit as provenance and architecture evidence. Direct source-compatible donor shortlist is empty. The three exact cross-donor opening groups are actionable candidates for a newly frozen whole-opening study, with no outcome or strength claim. No strategy variants, outcome games, source/main modifications, or Kaggle calls were made.

## Artifacts

- `inventory.json`: all donor/library action hashes, strict prefixes, type checks, source first-shop family comparisons, replay provenance.
- `all_route_comparisons.json`: all 7,250 exact and strict physical comparisons.
- `semantic_physical_inventory.json`: explicit normalization and all 7,250 normalized physical comparisons.
- `compatible_donor_inventory.json`: empty admissible source-opening shortlist.
- `opening_family_catalog.json`: 43 normalized donor opening groups.
- `cross_donor_openings.json`: three repeated exact donor openings, full route hashes and pairwise prefix lengths.
- `DONORS.md`: all 50 donors with recorded first shop and earliest physical mismatch.

Reproduction scripts only read source/manifest-referenced local input files. `audit.py` and `semantic_audit.py` intentionally refuse to overwrite completed primary receipts.
