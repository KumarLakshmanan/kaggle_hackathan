# Reviewed upload candidate — 2026-09-29

Candidate: `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55`.
The package's `main.py` and root backup
`main_candidate_pet_source_guard_20260929_257f941d.py` contain the same bytes.
The older research `H:/hackathan/main.py` remains 4ee and is backed up as
`main_before_candidate_4eeac9c3_20260929.py`.

## Comparison with the last uploaded file

The previous upload is a44, submission **56649310**. The older research file
4ee is submission **56609430**; these are different versions.

| Saved benchmark | Last upload a44 | Corrected candidate 257 |
| --- | ---: | ---: |
| Archived loss fixtures won in both seats | 17/30 | **27/30** |
| Saved top20 fixtures won in both seats | 19/20 | **19/20** |
| Individual seats won out of 100 | 72 | **92** |

All 100 fixture/seat identities match the prior panel. There are 20
loss-to-win changes and zero W/D/L regressions. The average paired cash
margin improves by 2,822.7 coins. This average includes a remaining loss
whose margin worsens by 45,291 coins per seat; every winning margin did not
improve. Two additional public-win control seats also remain wins.

These opponents replay saved actions. The panel was used during development,
so it is not an independent estimate of future Kaggle performance.

## Code review

The candidate retains a44's donor opening, queue/quantity handling, and pair
repair, adding routes selected from public farm and shop observations:
Goose4/Ghost, Smoothie, Kwa, Civitas, isolated pasture, and Pet Cafe. The
pasture selector changes the opening branch when the rival has exactly five
hands and one pasture. Other selectors switch route schedules after public
shop and crop observations become available.

Review found a Pet route ownership issue: donor strategies have separate
route maps. The corrected file enables the Pet route only when the source
strategy owns the moves and records the actual selected branch. It preserves
all 102 checked replay outcomes and prior telemetry. Narrow exact-state
selectors may overfit the saved opponents.

The intended Kaggle callable is `kaggle_a44_pet_market_gate_entrypoint`.

## Fresh reacting comparison

The three-arm native pilot ran 96 games: a44, parent 6a and parent ebf each
played the same 32 scenarios, spanning four fresh seeds, four reacting
opponents and both seats. Each recorded **16 wins, 10 draws and 6 losses**;
all paired rewards and margins were identical. The Pet gate never activated.

The strict improvement gate failed, as did the additional under-one-second
per-call screen. All games still completed without policy errors. The exact
guarded 257 file has separate preservation/loader checks; this parent pilot
does not prove a fresh reactive improvement for it. Research promotion is
rejected and the conditional larger confirmation was not started.

## Operational review and upload

The corrected file passed all 102 saved-replay preservation checks and all
**12 native direct/file-loader games**. The Pet target, pasture target and
inactive top20 control passed in both seats: correct callable, DONE/DONE at
720 frames, 719 calls per player, every two-player action and reward matching,
zero policy/native errors, and at least **59.770622 seconds** of remaining
overage. Two verifier implementation defects were corrected with their
original versions preserved under `revisions/`; candidate code and checks of
game behavior were unchanged. Final operational receipt SHA-256:
`a90a5adf1a943f0434e61ef63cbcbc4985783679c00eb2609e762cbeb6c1f1d5`.

The user explicitly requested one new upload. The upload is experimental;
neither a higher score nor a top-10 finish is established by these results.
Kaggle accepted one upload as **submission 56662188**, file **main.py**, at
**2026-09-29 09:39:22 IST**. The listing still showed **Pending** at 09:41:25
IST, with no score; the episode endpoint subsequently reported no episodes
yet. `status_20260929T041125Z.json` records that check. `upload_receipt.json` records the exact submitted
hash, one successful attempt, user authorization and evidence. That upload
authorization has been used. Root research `main.py` remains the backed-up
4ee file; this package's `main.py` is the file uploaded to Kaggle.
