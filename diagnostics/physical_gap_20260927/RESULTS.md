# Physical-execution gap and public-policy screen — 2026-09-26

This is exploratory diagnosis, **not** a promotion panel. Current submission
source `main.py` retained SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.
The purpose was to find a repeatable mechanical defect outside the separate
sale-timing work before building another wrapper.

## Native action traces

Instrumented engine 1.32.7 self-play on familiar seeds 0, 1 and 2, examining
seat 0. The full native 720-turn games ended `DONE` in both seats. Seeds 0–2
had 0 failed `PLANT`, 2/0/0 failed `FEED`, and every attempted `HIRE` and
`BUY_LAND` succeeded. The last hired hand performed 12–23 non-`PASS`
commands on every one of the 90 analyzed days. A simple trailing-hire trim
would delete actual planned work. An isolated `_R148_SEEDS=true` pilot on
seed 0 in both seats completed but reproduced the incumbent's exact terminal
cash pairs, so this switch supplied no local improvement evidence.

Replaying the exact step-23 field actions and installed animal refresh showed
only five production-cap events across the three traces, clipping five goose
units and two cow units. Their instantaneous quote exposure sums to 457 coins
before any worker travel, delivery, sale or rival-price effect. This is too
small and too spatially scattered to justify a broad animal-harvest overlay
from these traces. The exact events are in `animal_clip_audit.json`.

## Terminal tiles in live losses

Read-only scan of the frozen 29 original live losses for submission 56572390
found saleable yield still on our tiles in only **two** games: one milk unit
versus koucha (margin -295), and one milk unit versus Randy (margin -468).
Each opponent also had one milk unit on a tile. This extends the earlier
zero-shed/worker-cargo check: overlooked terminal tile stock does not explain
the other 27 losses. `terminal_tile_inventory.py` and its JSON output retain
the exact episode identities and counts. These saved replays are diagnosis,
not independent evidence for a new policy.

## Complete public policies, screening only

The published v48 artifact had previously contributed only **route data**
to a local experiment. We statically decoded its bundled modules, checked
imports and dynamic calls, and used the exact archived source SHA-256
`dadee25a...` as a full-policy pilot on familiar seed 0, both seats, native
shops and reacting `main.py`. All games ended `DONE`; v48 lost both seats,
61,820–109,858 and 40,601–82,144 (paired margin -89,581). The full v48
policy therefore did not reverse the route-data screen's direction on this
pilot; one seed is not a general ranking.

The archived complete published V43 source SHA-256 `919fc1d6...`, which
shares several safeguards already in `main.py`, also completed both seats on
seed 0 and lost, 65,115–73,818 and 65,764–73,073 (paired margin -16,012).
Both published artifacts remain reference material; no public code was
incorporated into `main.py` here. Raw native results are `v48_full_seed0.json`
and `v43_full_seed0.json`.

## Decision

**Reject a terminal-cargo, generic invalid-action, trailing-hire, seed-prefund
or wholesale public-policy module from these observations.** None has a
demonstrated improvement that could justify promotion. The more material
gap is the *funded production mix and its market response* in the broader
top-100 loss ledgers, which needs a complete executable investment/worker/
sale commitment and a frozen reactive validation gate. `main.py` was not
edited and no Kaggle upload was performed.

Reproduce the traces with `python trace_paired_game_events.py --candidate
main.py --opponent main.py --seed 0 --candidate-seat 0 --json-gz-out
diagnostics/physical_gap_20260927/main_seed0_self_trace.json.gz` (repeat
seeds 1 and 2). Run `python diagnostics/physical_gap_20260927/animal_clip_audit.py`
and `python diagnostics/physical_gap_20260927/terminal_tile_inventory.py` for
the saved analyses. The full-policy pilots use `paired_benchmark.py` with
`--candidate` set to the archived source path and `--opponent main.py
--seeds 0`. Familiar seed 0 was used only for mechanism screening; any future
candidate needs fresh predeclared seeds in both seats.
