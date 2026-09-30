# Retry: full saved 30-loss and top20 panel for isolated pasture candidate

## Retry reason

The first attempt is preserved at `../goalpanel_100/`. It completed 93 rows,
then its progress print failed on a non-ASCII fixture name under the Windows
cp1252 console. The row was already flushed; the attempt has no final receipt
and is labeled interrupted by its missing completion receipt. This fresh,
one-shot attempt keeps the same candidate and frozen panel and uses
ASCII-escaped progress output. No prior outputs are imported or resumed.

## Scope and baseline

Run the frozen 100 seat panel (30 loss fixtures and 20 top20 fixtures, both
seats) against candidate
`6a0a3b38782ba21a4933827888b503dae00fe73182599bc8c801302f959372dc`.
Compare to the direct V5 parent receipt for exact candidate
`8f939ada634f8c1ab57991a6903c731f86551a5bd1e22766987abab752db0c62`.
The two `live-114274897` seats are the only expected new trigger rows.

## Frozen gates

- All 100 candidate games are DONE/DONE at 720 frames with zero policy or
  telemetry errors.
- All 98 rows outside the two THIRD seats exactly match the direct V5 parent
  on result, rewards, margin, statuses, frames, and prior-policy telemetry.
- Both THIRD seats select the source branch, activate route `113332529`, and
  win with positive margin.
- Top20 reaches at least 18/20 both-seat sweeps; the requested loss gate is
  at least 27/30 both-seat sweeps.
- Report each threshold separately. Fixed replay action tapes do not count as
  reactive validation and do not qualify promotion.

The one-shot runner binds the parent receipt and panel, candidate, frozen
static census, replay inputs, engine helpers, and all scripts. It takes the
shared simulator lock and a package-local lock. Kaggle and root `main.py` are
outside this run.
