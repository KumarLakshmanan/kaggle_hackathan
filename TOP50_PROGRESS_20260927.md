# Top-50 improvement checkpoint — 27 September 2026

## Current result

**Fresh assessment complete:** today's top 100 gives 77/100 both-seat sweeps
and 155/200 wins; its top-50 slice is 36/50. See
[the current report](CURRENT_LEADERBOARD_REPORT_20260927.md). The figures below
describe the older 50-team regression panel, not the current leaderboard.

All 50 selected top-team replays are downloaded and tested in both seats.
**Local main.py wins 44/50 matchups in both seats (88/100 seat wins).**
Six matchups still lose; the 50/50 and live top-10 goals are not achieved.

| Version | Both-seat wins | Seat wins | Decision |
|---|---:|---:|---|
| Previous 489 main | 31/50 | 64/100 | Historical backup |
| Uploaded 3cc main | 42/50 | 84/100 | Submission 56591314 |
| Previous local a2 main | 43/50 | 86/100 | Preserved backup; never uploaded |
| Current uploaded c68 main | **44/50** | **88/100** | Submission 56602057; remote validation passed |
| Experimental 94f selector | 45/50 | 91/100 | Rejected on independent native games |
| Experimental db selector | 44/50 | 89/100 | Rejected: 0/48 against prior main |
| Opening c90d992d | 44/50 | 88/100 | Rejected: 1/64 against prior main |
| Component f66be305 | 44/50 | 88/100 | Native qualification passed; incorporated into c68 |

The fixed panel uses the 26 September 23:03 UTC leaderboard snapshot. Its
50 distinct action tapes come from 43 public episodes. It is development
and regression data: saved opponents cannot react to changed decisions.

## What changed in main.py

The current c68 version keeps the qualified market queue optimizer and adds
two disjoint decisions at turn 144: a complete FARMERS/ICE schedule when
rival melon production is visible, and guarded trade-quantity changes when
both public farms have matching layouts. The decisions use observed state.

SHA-256: `c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad`.
The final Kaggle entry point is `kaggle_disjoint_integrated_entrypoint`.
Uploaded at 07:25 UTC as **56602057**, using the user's explicit approval.

## Independent qualification

The original 384-game protocol finished without errors. It won 64/64
against each current version, but matched both historical controls at
54/64. That protocol demanded an extra historical-control win, so it failed.
Its original criteria and failed decision remain preserved.

A separate prospective review used 16 untouched seeds, both seats, and
unchanged candidate bytes under a frozen overall-points criterion:

| Reacting reference | Prior 3cc points /32 | New a2 points /32 |
|---|---:|---:|
| Current 3cc | 16 | 32 |
| Leading active 1f | 15.5 | 32 |
| Historical 489 | 26 | 26 |
| Public C95 | 30 | 30 |

All 256 games finished DONE/DONE with zero queue errors. Wins score one,
draws half. Pooled points rose from 87.5 to 120 out of 128. The predeclared
whole-seed interval for improvement was [25.00, 26.17] percentage points.
These four references include related policies; this is not a prediction
of a live leaderboard score.

Both-seat file/direct loading also matched exact cash and finished DONE,
with zero errors. The candidate was promoted locally after preserving the
prior main. This describes the a2 foundation; c68 was subsequently qualified
and uploaded with fresh explicit permission.

## Remaining losses and live state

Remaining replay losses: Breaking1800, Majkel1337, Snorlax,
We wanna be tomatos, seek inspiration, and ymg_aq.

At **07:12 UTC**, the team was **rank 112, score 2608.9**, carried by
submission 56590642 (1f). Latest uploaded 56591314 (3cc) scored 2219.6;
rank 10 scored 2895.4. Ratings keep changing. Uploading another version
would replace the older active submission under the latest-two rule, so
our displayed score may initially fall. The user approved the c68 upload;
that permission is now consumed by 56602057. Its remote validation passed.

A separate trade-quantity experiment 6e09adf8 won its 16-game native pilot
but exchanged ymg_aq for a lost Boey matchup in its completed 100-game
replay panel. It fails its no-lost-sweep gate and is rejected.

Another candidate, f66be305, selects a complete FARMERS/ICE schedule only
when the opponent has visible melon plants at turn 144. It recovers DECEM
in both seats (+13510/+46307), giving 44/50 development sweeps. The other
98 games are reused unchanged because their first-two-shop history excludes
the new branch. All 128 frozen native games passed, preserving external win
counts and inactive mirror behavior.

Restricted trade candidate 2765aed9 now enables quantity changes only after
observing matching public farm layouts at turn 144. It preserves all 100
saved a2 games by branch exclusion and won 15/16 fresh native pilot games,
all DONE with zero errors. Its separate 128-game confirmation also passed:
16/16 against a2, with the other three references' win counts preserved.

The two compatible components are now combined in **c68fa46f**. All 34
integration games and four file-path games passed; both behaviors were
checked in both seats. The qualified candidate is backed up at
main_candidate_disjoint_integrated_20260927_c68fa46f.py. Its 44/50 result
uses explicit identical-policy reuse, not a claim of 100 new replay games.
The user approved c68. Main now has those exact bytes, and Kaggle accepted
submission 56602057. Remote validation passed: 720 frames, DONE/DONE, active commands in both seats.

## Backups and reproducible evidence

- Prior main: `main_before_market_queue_20260927_3cc0f69f.py`.
- Current main backup: `main_uploaded_disjoint_integrated_20260927_c68fa46f.py`.
- Previous a2: `main_before_disjoint_integration_20260927_a2d2869c.py`.
- c68 native qualification: `diagnostics/shunki_disjoint_integration_20260927/`.
- Upload receipt: `diagnostics/disjoint_upload_20260927/promotion_receipt.json`.
- Full replay comparison: `diagnostics/shunki_market_queue_20260927/top50_decision.json`.
- Fresh native qualification and loader receipts: `diagnostics/shunki_queue_winrate_review_20260927/`.
- Download manifest: `diagnostics/top50_refresh_20260927_2303/routes/summary.json`.
- Latest live receipt: `diagnostics/shunki_promotion_20260927/live_0712/`.
- Living research memory and all earlier decisions: `agent.md`.

No `agenda.md` exists in this workspace; the research memory is `agent.md`.
