# Early worker watering feasibility — 2026-09-27

## Decision

**Reject at the mechanism-feasibility gate. Do not spend reserved native seeds 2721000–2721031.** The added crew can reach and water every selected crop, but the proposed day-1 WATER bundle does not increase the incumbent's day-2 wheat delivery. It adds no wheat sale at the first planned sale and costs 7 coins in hire fees. Fixed source-tape diagnostics then show no margin gain against either saved reacting opponent tape. This is not a promotion test: fixed tapes do not adapt to the candidate.

`main.py` was not edited. Its SHA-256 remains `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`. The isolated candidate is `exp_early_workers_20260927.py` (SHA-256 `cea5fd736f260258df4ec3b132800ce0c652772e72cd85842e137b4db2c84a29`). No Kaggle upload, API call, replay download, or reserved-seed game was run.

## Frozen intervention

At turn 24, the candidate appends four HIRE orders to the incumbent's existing market queue only when there are no current hands, `hires_today == 0`, at least 16 unwatered owned wheat/strawberry tiles, enough cash for all four hires (7 coins), and four spare queue slots. On turns 25–47, it assigns hands to unwatered owned WHEAT/STRAWBERRY tiles, moves each hand one grid step toward its target, and emits WATER only while standing on that tile. It does not change the farmer command or the incumbent's planned day-2 HIRE/harvest/replant orders.

## Mechanism evidence

The local Kaggriculture 1.32.7 engine was used to replay the downloaded, saved action tapes for DECEM (seed `1699455618`) and Majkel1337 (seed `1254482898`). The incumbent replays reproduce the saved source rewards and margins exactly. For the candidate, the replay recorder compared each command against its input observation and the next observation:

- The candidate bought four day-1 hands for 7 coins. They started on the shed-access tiles.
- It issued 58 one-tile movements; all 58 moved the corresponding hand to the expected adjacent tile on the next observation.
- It issued 20 WATER commands: 19 on owned WHEAT tiles and 1 on an owned STRAWBERRY tile. All 20 targets were unwatered PLANTs, and all 20 changes were confirmed in the next observation.
- Day-1 watering occurs at crop age 1; the wheat yield bonus window begins at age 2. These WATER actions reset the daily/unwatered state but do not add wheat yield on day 1.
- At turn 72, the candidate has 21 WHEAT in the shed and requests `SELL WHEAT 18`, leaving 3. The saved incumbent has the same 21 WHEAT and requests the same sale. The day-2 route still harvests and replants its planned 12 wheat plots; later day-2/day-3 crop counts and farmer/market actions match the saved incumbent through turn 95. The watered wheat does not block the replacement planting schedule.
- Candidate farm cash is exactly 7 coins below the incumbent from turn 25 through turn 167. Later the state and policy schedule diverge; by the terminal reward the candidate is worse on both fixed tapes. No additional wheat reaches the first planned delivery, and terminal own reward does not improve.

| Saved opposing action tape | Incumbent own / rival / margin | Early-worker own / rival / margin | Candidate margin change |
|---|---:|---:|---:|
| DECEM, seed 1699455618 | 68,153 / 131,304 / −63,151 | 60,616 / 125,009 / −64,393 | −1,242 |
| Majkel1337, seed 1254482898 | 76,125 / 153,498 / −77,373 | 76,118 / 153,498 / −77,380 | −7 |

The DECEM tape has a later cash path divergence (candidate cash is 98 coins lower by turn 191 and 7,000 lower at turn 695), while the day-2/day-3 replacement schedule remains compatible. That downstream change cannot rescue the first-delivery mechanism: the early WATER bundle has not increased delivered wheat, and both fixed-tape terminal margins are non-positive versus the incumbent.

## Reproduction

From the workspace root:

```powershell
python diagnostics/early_workers_20260927/replay_source_tapes.py
```

Machine-readable observations and results are in `source_tape_replay.json`. The script explicitly labels those runs as fixed-tape mechanism diagnostics, not reacting-policy validation.
