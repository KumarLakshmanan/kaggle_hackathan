# Pet Cafe route 113517834 four seat diagnostic

## Frozen question

On exact 8f parent `8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`, does the public step-72 gate select route 113517834 on both seats of live-114260122 and both seats of historical public-win-114192390, rescue both target seats, and preserve exact-parent outcomes on both control seats?

The gate is exactly:

- leaf `PET_CAFE|M8+|C>S|G0`
- rival visible MELON count 12
- public WHEAT inventory 9975
- action route 113517834

This is a fixed-action-tape diagnostic. It is not a promotion panel, reacting-opponent validation, or Kaggle candidate.

## Frozen static conditions

- Exact 8f parent and the route layer are byte-bound.
- Route 113517834 matches the named public route schedule.
- The 208-seat saved trace census has exactly four gate hits: the two requested target seats and the two requested control seats. No other seat matches, including zero triggers across all 40 top20 seats.
- The exact 8f 100-seat panel binds the live-114260122 source tape and shows both direct-parent seats as clean 720-frame losses at 90,989 versus 123,017, margin -32,028.
- The full public-win-114192390 action tape is extracted from the archived public replay and its 719 actions exactly match the source opponent's recorded actions.
- Target and control observation traces, source replays, action tapes, route source, 8f panels, this plan, and the runner/preflight code are hash-bound.

## Historical input caveat

The target full traces and control prefix traces in the 208-row selector census were produced by earlier research runs, not fresh episodes of the exact 8f parent. The public-win-114192390 control traces cover only steps 0 through 144. They are not complete replay tapes and are not claimed to be new 8f episodes. The control's fixed opponent tape is independently defensible: it contains 719 actions copied from seat 1 of the archived 720-frame source replay, whose decompressed SHA-256 is bound below. The source public episode's rewards are historical metadata only; they are not the exact-8f control baseline.

At execution time, the candidate's own telemetry must confirm the exact gate inputs and route on all four candidate runs. The parent and candidate will be run from the same cached initial state, seed, and fixed opponent action tape in each seat. Parent target runs must reproduce the bound 8f panel result exactly.

## Eight-game frozen matrix

For each of four fixture-seat pairs, run exact parent and candidate against the same 719-action tape and seed: target seats 0 and 1, then control seats 0 and 1. Use one worker, the existing exclusive game lock, and the bound native diagnostic harness. Do not resume or append partial outputs.

All eight runs must finish DONE/DONE at frame 720 with no policy errors or collisions. Candidate telemetry must report the leaf, MELON count 12, WHEAT inventory 9975, active gate, route 113517834, 648 active calls, and zero gate errors on all four seats.

Pass only if the candidate wins both target seats, the direct-parent target runs exactly reproduce the recorded 8f panel results, and each candidate control exactly preserves its paired direct-parent result, both rewards, margin, statuses, and frame count. Any input, telemetry, clean-run, or result mismatch rejects this diagnostic. Even a pass is fixed-tape evidence only and does not authorize promotion or upload.
