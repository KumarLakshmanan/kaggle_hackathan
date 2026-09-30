# Pet Cafe route 113517834 on the exact 6a pasture candidate

## Question and candidate

Compose the public step-72 Pet Cafe gate for route 113517834 on exact pasture candidate `6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`. The change is isolated in an appended layer; it does not use root main.py.

The gate is exactly leaf `PET_CAFE|M8+|C>S|G0`, rival visible MELON count 12, and public market WHEAT inventory 9975. It selects route 113517834 at step 72.

## Frozen baseline and panel

The full baseline is the completed 100-seat fixed-tape receipt for exact 6a: 60 loss30 seats plus 40 top20 seats. The planned panel runs the composed candidate once on each of those 100 seats. For the two public-win-114192390 control seats, no direct 6a result is saved, so run exact 6a parent and candidate against the same archived 719-action opponent tape in each seat. This makes 104 native fixed-tape game runs: 100 panel candidate runs, plus two parent and two candidate control runs.

The archive’s source public result is historical metadata only. Control margins and cash will be reported, but only control wins gate this experiment.

## Static gates before any game

- Candidate bytes equal exact 6a parent bytes followed by the bound Pet gate layer.
- Route 113517834 matches the bound public route schedule.
- Recompute the public gate from all 208 saved seat traces with exact 6a’s public leaf helper. Require only the two 114260122 targets and two public-win-114192390 controls to trigger; require zero triggers across all 40 top20 seats.
- Verify every saved trace, source replay, opponent action tape, exact 6a baseline row, route, runner, and preflight file by hash.
- Compare parent and candidate policy actions at steps 0 through 71 on all 208 traces. Require identical actions; this is a static policy check without engine transitions.
- Freeze the game objectives and output paths below before any run.

## Predeclared outcomes

Require all 100 full-panel candidate games and all four parent/candidate control games to finish DONE/DONE at 720 frames, with zero policy or telemetry errors. Candidate telemetry must report the gate’s public features and route correctly; the active-call count is **647**, because the harness invokes steps 0 through 718.

On the 100 seats, require both 114260122 target seats to win, at least 27/30 loss fixtures to be both-seat sweeps, at least 18/20 top20 fixtures to be both-seat sweeps, and no seat-level W/D/L regression versus the exact 6a receipt (win > draw > loss). For the two controls, require the direct 6a parent and composed candidate to both win in each seat. Report margins and cash changes, but do not gate on control margins.

## Evidence limit and execution boundary

This is fixed-tape diagnostic evidence, not reacting-opponent validation or promotion evidence. The 114260122 full panel uses its archived opponent action tape. The public-win control’s saved observations are historical prefixes, not new 6a episodes; the full 719-action fixed tape is verified against the archived replay, and runtime telemetry must confirm the gate on each direct-parent and candidate run. This package is staged for review only. Do not run native transitions until the root task owner coordinates and releases the simulator.
