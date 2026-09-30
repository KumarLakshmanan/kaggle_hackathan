# Live-loss and worker execution diagnosis — 2026-09-27

## Scope and method

The current 4ee policy hash is
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
The exact native trace ledger covers every loss in the 18:09 UTC public
cohort, `cohort_180951.json`: 30 losses from 84 games (54 wins, 30 losses,
no draws). All old 26 rows were reconciled against the new cohort by
episode, opponent, reward, seat, and seed. All 30 compressed replays were
decompressed and their saved raw SHA-256 values verified; the four new
episodes were replayed on their original seed and seat and matched both
players' cash exactly.

The worker no-change classifier compares the action with that step's native
observation. Its saved traces are exact original-seat/seed replays against
the public opponent's saved action tape. They explain mechanisms but do not
validate policy changes. The refreshed 17:25 current-top-20 panel is kept as
separate evidence: the original 4ee won both seats against 17/20 teams;
DECEM, Boey, and Vadim Vasilenko were the three current two-seat failures.
Majkel1337 is a current winning control, now +17,814 on its newer episode.

## Findings

- No shared locked-land or generic worker-idle defect appears in the live
  losses. Across all 30, our traces contain 359 no-change worker actions
  versus 1,925 for rivals. Only 9/30 losses have any own no-change action,
  and only 5/30 have at least ten. There is just **one** `locked_tile`
  no-op: a single `PICKUP` in Junliang Ye's episode. The largest own counts
  are Vlas Veles (65), Junliang Ye (167), Yaroslav (83), THIRD FARM CLUB
  (27), and the newer Ghost Rule loss (13); their causes are different.
- Fresh top-20 DECEM is the clear exception. It has 722 locked-tile worker
  no-ops, compared with three for Boey, zero for Vadim, and zero for the
  current winning Majkel control. Of DECEM's 722, 716 target southwest land
  and six southeast. Its planned third-land purchase fails at step 240 with
  1,120 coins at the atomic order; 4ee remains at two quadrants through the
  end. The separate frozen retry layer would first append a later funded
  land purchase at step 247 (day 10, 2,729 coins) on this saved trace. This
  proves activation on that tape only; it does not show that the candidate
  wins after changing land, worker production, shops, and rival market
  response.
- The 30 losses have mixed product and market gaps rather than one
  executable bundle. Melon net cash is below the rival in 26/30 and sums to
  -284,681; milk is below in 25/30 and sums to -105,438. Other products have
  mixed signs. This repeats the known non-specific melon/milk signal and
  does not justify a generic trigger. Own failed wheat purchases appear in
  four losses; sell attempts against empty sheds and other market failures
  are scattered.
- The four newest losses do not reveal a common execution failure:
  Yaroslav is -324 with a -439 product-net gap and 83 mostly `not_animal`
  no-ops; Ghost Rule is -4,243 with a -996 product-net gap and 13
  `not_plant`/empty-yield no-ops; the newer `leave you` episode is -7,748
  with one empty-tile dig and a -5,259 product-net gap; Navier-stokes is
  -7,764 with no own no-change actions or market failures and a -7,348
  product-net gap.
- The refreshed top-20 Boey loss has 179 no-ops, only three on locked land;
  its item gaps are led by egg and wheat while wool, tomato, and strawberry
  net cash are positive. Vadim's -400 loss has no own no-change actions.
  These failures do not join DECEM's land mechanism.

## Funded land retry feasibility screen

The isolated candidate was built from current 4ee plus the conservative
retry layer saved in `diagnostics/shunki_land_retry_20260927/layer.py`.
Candidate SHA-256:
`675893edc7ff07517dc57f60d322341b131ecd0d5286d9728d98d423cdc35e51`.
The frozen plan is `land_retry_PLAN.md`; it specified original native shops,
both seats, the current 4ee and previous submitted 3cc as reacting
references, two disjoint 2,000-seed selection ranges, first-16 activation
selection, and paired win-point gates before candidate outcomes.

At the parent's request, the incumbent-only development scan stopped at a
bounded feasibility checkpoint. It scanned the first 64 seeds of
2730000–2731999 and found **0 eligible activations** under the frozen rule.
No candidate games ran; the 2,000-seed scan was not completed, the fresh
confirmation range 2732000–2733999 was not started, and the candidate remains
untested. The sparse prefix does not disprove a benefit on DECEM's branch,
but it makes a representative random native test inefficient. A broader
promotion claim would require a deliberately activation-conditioned panel
with separate native confirmation. The earlier 2026-09-27 retry candidate
on 3cc improved one DECEM tape but failed its frozen top-50 sweep gate; that
rejection remains in force.

Decision: reject a broad worker no-op or locked-land fix from this audit.
Do not promote the current-4ee land-retry artifact based on the fixed DECEM
tape. It remains an untested narrow diagnostic candidate after the
activation feasibility screen. No `main.py` or `agent.md` edit and no Kaggle
access occurred.

## Frozen local regression fixtures

`local_target_manifest_180951.json` contains all 30 live losses and all 20
entries from the downloaded current top-20 panel. It records source replay
and action-tape paths and hashes, seeds, episode IDs, and baseline outcomes
for both seats. All 30 live raw replay hashes and all 20 top-20 replay and
action hashes were verified. These 50 entries cover 48 unique episodes.
Top-20 outcomes are from the existing both-seat assessment against frozen
saved action tapes. They are not native reacting-policy games.

### 4ee live-loss tape baseline completed

The current 4ee `main.py` was run locally in both seats against each of the
30 saved public-opponent action tapes: 60/60 games completed at 720 frames,
with **0 wins, 0 draws, 60 losses**. This is a fixed-tape regression panel,
not an estimate against opponents that react to the candidate. On every
fixture, the candidate's original public-game seat replayed to exactly the
recorded candidate reward, rival reward, and margin (30/30 exact parity).
In the opposite seat, it also lost all 30 games (0W/0D/30L). The two margins
that changed across seat assignment were episode 114252835 (−5,282 original,
−3,023 opposite) and 114274897 (−42,560 original, −41,698 opposite); both
remained losses in both seats. All other seat pairs had identical margins.

This completes the 30-loss both-seat baseline requested for later fixed-tape
candidate comparisons. The separate local reacting-reference gate is still
required for any policy decision. No retry-candidate outcome games were run.

Key files:

- `live_loss_ledgers_180951.json` — exact native event summaries and cash
  parity for all 30 live losses.
- `nochange_classes_180951.json` — no-change reasons for the live losses
  and the four current top-20 cases.
- `local_target_manifest_180951.json` — frozen replay/action fixtures and
  baseline outcomes, including the 30 live-loss both-seat tape runs.
- `live_loss_tape_baseline_180951.json` — 60 current-4ee local games against
  the 30 frozen live-loss action tapes.
- `run_live_tape_baseline.py` — hash-checked runner for rerunning any frozen
  live-loss tape in both seats; supply the candidate SHA explicitly for a
  later candidate.
- `land_retry_PLAN.md` and `land_retry_scan_prefix.json` — frozen test
  design and bounded selection result.

Reproduction:

```powershell
python -X utf8 diagnostics/loss_class_20260927/extend_live_losses_180951.py
python -X utf8 diagnostics/loss_class_20260927/classify_noops.py live_loss_ledgers_180951.json nochange_classes_180951.json
python -X utf8 diagnostics/loss_class_20260927/run_live_tape_baseline.py --workers 4
python -X utf8 diagnostics/loss_class_20260927/build_local_target_manifest.py
```
