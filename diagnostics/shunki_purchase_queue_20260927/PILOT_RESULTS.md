# Purchase queue native pilot — 27 September 2026

Candidate **43d6f448** was built from exact uploaded c68 with a root-folder
backup. It preserves existing sale optimization, then considers moving an
existing product purchase earlier under the frozen resource and cash guards.

All 16 games on fresh seeds 2695000–2695007 finished DONE/DONE with 720
frames and zero queue, quantity, gate, farmice or purchase errors. Result:
**15 wins, 1 loss, no draws**. All eight paired seeds activate purchase
reordering in both seats. Mean seat margin is 1,390.2; all eight summed
paired margins are positive. The single loss is seed 2695006, seat 1,
margin -1146; preserve that outcome.

**Pass the frozen development pilot only.** Run the unchanged candidate on
all 100 fresh current tapes and all 50 older regression tapes, both seats,
as predeclared. These are development panels. Independent multi-reference
native confirmation and file-path checks remain required before promotion.
Main remains c68fa46f; no new upload is authorized or performed.

Evidence: PLAN.md, build_manifest.json and pilot.json.
