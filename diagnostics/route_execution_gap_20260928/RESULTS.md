# Complete-route execution audit — 2026-09-28

All six already-known games reproduce their native terminal cash and
DONE/DONE/720 status exactly. DECEM remains -10,636 per seat on route
113373693; Boey -1,577 and Kaggledew +4,877 on route 113349962. This is
diagnostic repetition, not new strength evidence. The source control
correction and retained unreceipted trace are described in
`IMPLEMENTATION_NOTE.md`.

DECEM's two scheduled land purchases succeed. At step 189, it requests two
STRAWBERRY plants with only one seed: the previous purchase could afford
only one. Boey has nine atomically blocked plant commands across five
turns, and a separate missed SHEEP commitment. At step 195 it has 495
coins and attempts BUY_ANIMAL SHEEP before selling its remaining WHEAT.
The purchase fails; after the market queue it has 527 coins. A worker
requests the missing sheep at step 196 and attempts to place it at 206.
The subsequent route contains 22 ineffective FEED, 18 CARE and 17
COLLECT_FERTILIZER commands on an empty pasture.

The Kaggledew control also misses that sheep, but has only 462 coins and
no WHEAT at step 195; a simple sale-first repair cannot fund it. Neither
case establishes a profit from buying the sheep. The Boey route still
needs cash for later seed/feed commitments, and physical changes can alter
future shops and the rival's prices.

**Accept the concrete missed-purchase diagnosis.** A separate, prospectively
frozen experiment may move an existing scheduled animal purchase behind
an existing sale when modeled funds and resources permit it. Preserve the
rejected route-pool composite and the previous seed/purchase studies;
this audit changes no policy or main file.

Evidence: `audit.json`, six hash-receipted compressed traces, and the
previous route pool's `corrected_screen.json`.
