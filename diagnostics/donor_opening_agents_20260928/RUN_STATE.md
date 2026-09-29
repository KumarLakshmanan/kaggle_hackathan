# Whole donor opening pilot — 28 September 2026

All three candidate files, donor mappings/defaults, the60-game gate and helper code were frozen before outcomes. Preflight confirms the reused raw/recovery schedule references resolve to the donor and no incompatible old route controller is present.

Pilot execution is checkpointed in pilot.jsonl. Unified session98872 terminated after22 completed games because gzip decompression could not allocate the next replay buffer, before that policy/game started. An unchanged runner restart completed games23–25, then terminated for the same pre-game MemoryError. The runner, candidates and gate were not edited. No finished game was repeated and no partial outcome was recorded.

The root reported critically low machine memory and requested holding further launches until headroom returns or its competing animal full-panel job ends. The pilot is incomplete at25/60; no terminal candidate decision is claimed. Current completed shared15120-game subset meets the numerical pilot conditions, while other arms remain incomplete. Preserve its exact bytes for later full testing or use as a varied reacting reference, subject to native compatibility verification.

No unrelated process or user application was closed. Resume the same frozen command when memory permits:

```powershell
python -X utf8 diagnostics/donor_opening_agents_20260928/screen.py pilot
```

The root subsequently stopped only its own independent-pilot coordinator/workers at199 checkpoint rows, restoring virtual-memory headroom. It explicitly asked donor execution to remain waiting until the animal full panel finishes (last reported73/100), then resume unchanged with one worker. The completed25 donor rows and all frozen hashes were revalidated. This is an infrastructure wait, not a strategy rejection.

No full target stage or independent strength game has started.

The animal full-panel worker completed at17:01:42 UTC. Its agent notified us that both coordinator and worker were released. The donor pilot resumed from the exact25/60 checkpoint in session93359, still one worker and with unchanged hashes/gates. The shared151 and shared150 arms now each have20 completed games; shared166 is in progress. shared150 loses all three top controls and cannot satisfy its frozen pilot gate. shared151 retains Majkel but loses Boey/Vadim, so its completed subset satisfies the permissive pilot retention bound. Final decisions will use the completed60-game receipt.

Pilot completed at 2026-09-28T17:03:29.059921+00:00 with all 60 unique games clean. Session 93359 exited 0. shared151 and shared166 pass the frozen pilot gate; shared150 rejects after losing all three top controls. PILOT_RESULTS.md records every lost source-winning seat. The unchanged full-stage command will run the two survivors on all 50 targets/both seats, reuse their 40 pilot rows, and execute 160 missing games sequentially. Pilot receipt SHA-256: `3cd290b6e3fb446ec707d550e65ec17ce8363bc06e1b29d30fe18a93a10357b7`.

Full target stage completed at 2026-09-28T17:14:45.383632+00:00; session 70981 exited 0 and its single worker is released. All200 full-stage rows are unique and clean; 40 exact pilot rows were reused, making220 distinct outcomes across the complete study. shared151 rejects at11/20 top and9/30 public; shared166 rejects at9/20 top and12/30 public. Both fail both predeclared full-stage thresholds (18/20 top,14/30 public). Each loses36 source-winning seats. shared150 was already rejected at pilot. No native/reacting validation or promotion follows. Exact policies remain preserved as prospective varied references, pending native/file-loader checks. See RESULTS.md for every fixture and paired own/rival changes. Full receipt SHA-256: `97d1df983a9f4121c0563704346a9a61a26cd2acdb8033a985c3d60768073a99`.
