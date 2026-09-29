# 28 September 2026 — joint market candidate rejected

All twelve frozen development games completed DONE/DONE/720, with zero recorded errors. Candidate `b78fc7fbb3e84a42082c6a156dcd8855be51f44578e31fc12febb5db038b48a7` fails the frozen gate: DECEM remains lost and both Boey control seats regress. No native escalation, combined candidate, promotion or upload follows.

| Fixture | Source margin | Candidate margin, each seat | Own cash change | Rival cash change |
| --- | ---: | ---: | ---: | ---: |
| DECEM | -9,085 | -6,881 | +248 | -1,956 |
| leave you 114289228 | +3,256 | +3,402 | +76 | -70 |
| Boey | +4,935 | -8,058 | -27,869 | -14,876 |
| Vadim | +16,140 | +16,078 | -33 | +29 |
| Majkel1337 | +13,889 | +14,021 | +48 | -84 |
| Junliang Ye | +2,957 | +3,071 | -1,521 | -1,635 |

DECEM activates 54 turns, including 23 depth-two choices, in each seat. The shop path and partial planting shortage remain unchanged. The +2,204 relative gain comes largely from reducing the rival's receipts; it is not a rescued fixture.

The Boey failure illustrates why hypothetical mirror resource preservation does not establish actual preservation. It enters step 248 with three fewer coins (1,256 versus 1,259), then the unchanged queue buys only two of three WHEAT seeds. First seed divergence is observation 249, first tile divergence is 250, and first shop divergence is 288. Root source remains intact. Full exact rows, traces and immutable input hashes are in `screen.json`, `screen.jsonl`, `candidate.json`.

## Distinct next mechanism under inspection

DECEM's source trace at step 188 has a farmer at (4,3) carrying three fertilizer units, scheduled COLLECT_FERTILIZER, then SOUTH at 189 and DROP at 190. The current two-STRAWBERRY seed buy can afford only one; at189 the partial guard removes one worker's planting at (8,3). That worker remains there for WATER190/PASS191. A bounded physical repair could skip the fertilizer collection, move/drop one turn earlier, fund the missing seed at189, then PLANT190/WATER191. This costs the skipped fertilizer unit and the added seed. It is distinct from queue-quantity tuning and the rejected early-sale-only wrapper. It requires its own frozen plan and measurements before any conclusion.

## 28 September 2026 — separate physical repair completed and rejected

The separately frozen delivery experiment now completes all twelve games. Candidate 6a933a6e executes one successful seed/plant/water recovery in each DECEM seat and leaves all ten winning control seats exactly unchanged. DECEM still loses -8,681, improving paired margin only 404 although own cash rises 24,746 and rival cash rises 24,342. Its shop path changes at 288. Reject at the frozen rescue gate. See delivery/RESULTS.md and its immutable receipts. Neither experiment earns native escalation or promotion.
