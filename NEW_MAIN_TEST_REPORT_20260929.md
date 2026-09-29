# New standalone competition agent — 29 September 2026

## Result

The new file improves one saved matchup’s cash margin and preserves every saved win. It does not add a win on that panel. The fresh reacting comparison below determines whether there is evidence of a broader win-rate gain.

- New standalone file: [main_candidate_improved_20260929.py](H:/hackathan/main_candidate_improved_20260929.py).
- Exact uploaded-version backup: [main_uploaded_backup_257f941d_20260929.py](H:/hackathan/main_uploaded_backup_257f941d_20260929.py).
- Root research `main.py` remains unchanged. No Kaggle check or upload was performed.

| Version | SHA-256 | Role |
|---|---|---|
| New candidate | `ae349d83276976906626f7b59bc6bd3c41d286bc51854c26a6a8b25caf999abb` | Tested separate file |
| Uploaded257 | `257f941d06fcd6dd9185ca58bc98d1af83dc4c3fafc24e275a1bf057b61bad55` | Exact last uploaded baseline, submission 56662188 |
| Root research main | `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed` | Preserved; also a reacting opponent |

## What changed

The candidate retains the uploaded agent’s market-order adjustments, planting and hiring repairs, animal-cash handling, donor scheduling, and the Ghost, Kwa, Pizza/Ice Cream, pasture and Pet Cafe route repairs. One new guard prevents the optional Goose4 Pizza route when the existing source-branch production category has at least 12 visible rival melon plots at step 72. It leaves the pre-existing route map in place in that case. The same route remains available for the 10-melon Dieter control.

This threshold was fitted to a sparse saved example. It uses public farm observations, not player names, replay IDs or hidden seeds. That does not establish generalization.

## Experiments and decisions

| Experiment | Test | Result / decision |
|---|---|---|
| Public production guard | Static review of 208 stored observation rows | 2 target activations; Dieter and top20/public-win controls excluded from fallback. Proceed to gameplay. |
| Guard target/control pilot | 4 paired scenarios, 8 full games | Both Pensukesan deficits improve by 45,291; both Dieter wins/rewards exact; clean execution. Passed. |
| Guard full saved panel | 102 new games against source-bound prior baseline rows | 94W/0D/8L for both versions; total margin +90,582; no regressions. Passed the saved margin gate. |
| Mirrored Brunch/Pizza route swap | Static state/schedule audit; 0 games | Rejected: matching farm tiles does not establish worker/inventory compatibility; schedules diverge on 575 later turns. |
| Late melon delivery | Separate concurrent experiment | Not included in this frozen file; treatment validation was incomplete at selection time. No benefit attributed to it here. |
| Final fresh reacting comparison | 24 paired scenarios, 48 full games | Uploaded: 8W / 14D / 2L; new: 8W / 14D / 2L; margin change +0. |
| Loader checker preparation | 0 games started | Checker import-path error; archived and fixed before the native run. Candidate unchanged. |
| Actual Kaggle file-loader check | 4 fixture/seat cases × direct/file mode = 8 full games | Correct callable; all 719 two-player actions, rewards and telemetry match; all clean DONE/DONE/720. |

A total of 166 full game executions were run for this candidate. Repeated fixture checks are not independent opponents. The 102 saved baseline outcomes were reused only after four fresh baseline pilot runs exactly reproduced their rewards, status and prior telemetry.

## Saved opponent results

| Group | Uploaded257 | New candidate | Both-seat opponent sweeps |
|---|---|---|---|
| Archived 30-loss set | 54W / 0D / 6L | 54W / 0D / 6L | 27/30 → 27/30 (90%) |
| Saved top20 set | 38W / 0D / 2L | 38W / 0D / 2L | 19/20 → 19/20 (95%) |
| Pet public-win control | 2W / 0D / 0L | 2W / 0D / 0L | 1/1 → 1/1 |

Pensukesan’s own/rival cash changes from 120,144 / 174,100 to 107,828 / 116,493. Our cash falls by 12,316 while the rival’s falls by 57,607, reducing the deficit from 53,956 to 8,665 in each seat. This remains a loss. All other 100 saved seat results and margins are unchanged.

Remaining losses: Pensukesan (−8,665 each seat), 吃白饭的大肥鱼 (−33,224), Roman (−18,815), and top20 DECEM (−9,085). These were not solved by this change.

## Final fresh reacting test

The seeds 2026092981–2026092984 and all three opponent sources were frozen before new outcomes. Each policy played both seats against each opponent with original native shops and hidden seeds. The four complete seed blocks, not individual seats, are the units for the declared consistency check.

| Reacting opponent | Uploaded257 | New candidate | Point change | Margin change |
|---|---|---|---:|---:|
| research4ee | 0W / 6D / 2L | 0W / 6D / 2L | +0 | +0 |
| uploaded257 | 0W / 8D / 0L | 0W / 8D / 0L | +0 | +0 |
| publicAhmedV35 | 8W / 0D / 0L | 8W / 0D / 0L | +0 | +0 |

New guard activations: **0/24 candidate games**.
Whole-seed point changes: `{'2026092981': 0.0, '2026092982': 0.0, '2026092983': 0.0, '2026092984': 0.0}`.
Predeclared strict win-rate improvement gate: **not passed**.

There is no demonstrated fresh win-rate gain. Retain this as a tested experimental margin repair; do not promote it as a stronger general policy.

These local results do not provide a reliable Kaggle score estimate or a probability of reaching top10. Saved action tapes cannot reproduce the full responses of their original opponents.

## Every executed comparison case

### Focused pilot (each row runs both versions)

| Case / seat | Uploaded result | New result | Uploaded own / rival cash | New own / rival cash | Margin: uploaded → new | Margin change | Execution |
|---|---|---|---:|---:|---:|---:|---|
| live-114218866-seat0 | loss | loss | 120,144 / 174,100 | 107,828 / 116,493 | -53,956 → -8,665 | +45,291 | DONE/DONE, 720, no errors |
| live-114218866-seat1 | loss | loss | 120,144 / 174,100 | 107,828 / 116,493 | -53,956 → -8,665 | +45,291 | DONE/DONE, 720, no errors |
| live-114249897-seat0 | win | win | 124,604 / 96,750 | 124,604 / 96,750 | +27,854 → +27,854 | +0 | DONE/DONE, 720, no errors |
| live-114249897-seat1 | win | win | 124,604 / 96,750 | 124,604 / 96,750 | +27,854 → +27,854 | +0 | DONE/DONE, 720, no errors |

### Full saved panel (new candidate run; uploaded reference reproduced and reused)

| Case / seat | Uploaded result | New result | Uploaded own / rival cash | New own / rival cash | Margin: uploaded → new | Margin change | Execution |
|---|---|---|---:|---:|---:|---:|---|
| live-114211346-seat0 | win | win | 111,245 / 99,663 | 111,245 / 99,663 | +11,582 → +11,582 | +0 | DONE/DONE, 720, no errors |
| live-114211346-seat1 | win | win | 111,245 / 99,663 | 111,245 / 99,663 | +11,582 → +11,582 | +0 | DONE/DONE, 720, no errors |
| live-114215872-seat0 | win | win | 79,808 / 70,395 | 79,808 / 70,395 | +9,413 → +9,413 | +0 | DONE/DONE, 720, no errors |
| live-114215872-seat1 | win | win | 79,808 / 70,395 | 79,808 / 70,395 | +9,413 → +9,413 | +0 | DONE/DONE, 720, no errors |
| live-114218866-seat0 | loss | loss | 120,144 / 174,100 | 107,828 / 116,493 | -53,956 → -8,665 | +45,291 | DONE/DONE, 720, no errors |
| live-114218866-seat1 | loss | loss | 120,144 / 174,100 | 107,828 / 116,493 | -53,956 → -8,665 | +45,291 | DONE/DONE, 720, no errors |
| live-114223292-seat0 | loss | loss | 117,404 / 150,628 | 117,404 / 150,628 | -33,224 → -33,224 | +0 | DONE/DONE, 720, no errors |
| live-114223292-seat1 | loss | loss | 117,404 / 150,628 | 117,404 / 150,628 | -33,224 → -33,224 | +0 | DONE/DONE, 720, no errors |
| live-114223338-seat0 | win | win | 155,518 / 155,205 | 155,518 / 155,205 | +313 → +313 | +0 | DONE/DONE, 720, no errors |
| live-114223338-seat1 | win | win | 155,518 / 155,205 | 155,518 / 155,205 | +313 → +313 | +0 | DONE/DONE, 720, no errors |
| live-114227779-seat0 | win | win | 137,711 / 133,593 | 137,711 / 133,593 | +4,118 → +4,118 | +0 | DONE/DONE, 720, no errors |
| live-114227779-seat1 | win | win | 137,711 / 133,593 | 137,711 / 133,593 | +4,118 → +4,118 | +0 | DONE/DONE, 720, no errors |
| live-114229792-seat0 | win | win | 105,779 / 95,507 | 105,779 / 95,507 | +10,272 → +10,272 | +0 | DONE/DONE, 720, no errors |
| live-114229792-seat1 | win | win | 105,779 / 95,507 | 105,779 / 95,507 | +10,272 → +10,272 | +0 | DONE/DONE, 720, no errors |
| live-114232208-seat0 | win | win | 68,351 / 62,812 | 68,351 / 62,812 | +5,539 → +5,539 | +0 | DONE/DONE, 720, no errors |
| live-114232208-seat1 | win | win | 68,351 / 62,812 | 68,351 / 62,812 | +5,539 → +5,539 | +0 | DONE/DONE, 720, no errors |
| live-114235177-seat0 | win | win | 54,659 / 44,665 | 54,659 / 44,665 | +9,994 → +9,994 | +0 | DONE/DONE, 720, no errors |
| live-114235177-seat1 | win | win | 47,689 / 38,544 | 47,689 / 38,544 | +9,145 → +9,145 | +0 | DONE/DONE, 720, no errors |
| live-114236633-seat0 | win | win | 135,491 / 130,131 | 135,491 / 130,131 | +5,360 → +5,360 | +0 | DONE/DONE, 720, no errors |
| live-114236633-seat1 | win | win | 135,491 / 130,131 | 135,491 / 130,131 | +5,360 → +5,360 | +0 | DONE/DONE, 720, no errors |
| live-114238112-seat0 | win | win | 142,268 / 140,729 | 142,268 / 140,729 | +1,539 → +1,539 | +0 | DONE/DONE, 720, no errors |
| live-114238112-seat1 | win | win | 142,268 / 140,729 | 142,268 / 140,729 | +1,539 → +1,539 | +0 | DONE/DONE, 720, no errors |
| live-114243994-seat0 | win | win | 95,487 / 78,317 | 95,487 / 78,317 | +17,170 → +17,170 | +0 | DONE/DONE, 720, no errors |
| live-114243994-seat1 | win | win | 94,968 / 78,329 | 94,968 / 78,329 | +16,639 → +16,639 | +0 | DONE/DONE, 720, no errors |
| live-114249897-seat0 | win | win | 124,604 / 96,750 | 124,604 / 96,750 | +27,854 → +27,854 | +0 | DONE/DONE, 720, no errors |
| live-114249897-seat1 | win | win | 124,604 / 96,750 | 124,604 / 96,750 | +27,854 → +27,854 | +0 | DONE/DONE, 720, no errors |
| live-114252835-seat0 | win | win | 98,003 / 92,344 | 98,003 / 92,344 | +5,659 → +5,659 | +0 | DONE/DONE, 720, no errors |
| live-114252835-seat1 | win | win | 98,003 / 92,344 | 98,003 / 92,344 | +5,659 → +5,659 | +0 | DONE/DONE, 720, no errors |
| live-114254310-seat0 | win | win | 135,794 / 132,837 | 135,794 / 132,837 | +2,957 → +2,957 | +0 | DONE/DONE, 720, no errors |
| live-114254310-seat1 | win | win | 135,794 / 132,837 | 135,794 / 132,837 | +2,957 → +2,957 | +0 | DONE/DONE, 720, no errors |
| live-114255779-seat0 | win | win | 94,821 / 85,262 | 94,821 / 85,262 | +9,559 → +9,559 | +0 | DONE/DONE, 720, no errors |
| live-114255779-seat1 | win | win | 94,821 / 85,262 | 94,821 / 85,262 | +9,559 → +9,559 | +0 | DONE/DONE, 720, no errors |
| live-114257327-seat0 | win | win | 87,967 / 84,975 | 87,967 / 84,975 | +2,992 → +2,992 | +0 | DONE/DONE, 720, no errors |
| live-114257327-seat1 | win | win | 87,967 / 84,975 | 87,967 / 84,975 | +2,992 → +2,992 | +0 | DONE/DONE, 720, no errors |
| live-114258293-seat0 | win | win | 120,985 / 113,828 | 120,985 / 113,828 | +7,157 → +7,157 | +0 | DONE/DONE, 720, no errors |
| live-114258293-seat1 | win | win | 120,985 / 113,828 | 120,985 / 113,828 | +7,157 → +7,157 | +0 | DONE/DONE, 720, no errors |
| live-114260122-seat0 | win | win | 120,369 / 97,845 | 120,369 / 97,845 | +22,524 → +22,524 | +0 | DONE/DONE, 720, no errors |
| live-114260122-seat1 | win | win | 120,369 / 97,845 | 120,369 / 97,845 | +22,524 → +22,524 | +0 | DONE/DONE, 720, no errors |
| live-114267572-seat0 | win | win | 100,349 / 100,105 | 100,349 / 100,105 | +244 → +244 | +0 | DONE/DONE, 720, no errors |
| live-114267572-seat1 | win | win | 104,830 / 98,355 | 104,830 / 98,355 | +6,475 → +6,475 | +0 | DONE/DONE, 720, no errors |
| live-114270587-seat0 | loss | loss | 84,377 / 103,192 | 84,377 / 103,192 | -18,815 → -18,815 | +0 | DONE/DONE, 720, no errors |
| live-114270587-seat1 | loss | loss | 84,377 / 103,192 | 84,377 / 103,192 | -18,815 → -18,815 | +0 | DONE/DONE, 720, no errors |
| live-114271958-seat0 | win | win | 125,317 / 124,647 | 125,317 / 124,647 | +670 → +670 | +0 | DONE/DONE, 720, no errors |
| live-114271958-seat1 | win | win | 125,317 / 124,647 | 125,317 / 124,647 | +670 → +670 | +0 | DONE/DONE, 720, no errors |
| live-114274897-seat0 | win | win | 129,916 / 123,933 | 129,916 / 123,933 | +5,983 → +5,983 | +0 | DONE/DONE, 720, no errors |
| live-114274897-seat1 | win | win | 128,532 / 126,297 | 128,532 / 126,297 | +2,235 → +2,235 | +0 | DONE/DONE, 720, no errors |
| live-114279280-seat0 | win | win | 91,106 / 84,042 | 91,106 / 84,042 | +7,064 → +7,064 | +0 | DONE/DONE, 720, no errors |
| live-114279280-seat1 | win | win | 91,106 / 84,042 | 91,106 / 84,042 | +7,064 → +7,064 | +0 | DONE/DONE, 720, no errors |
| live-114279308-seat0 | win | win | 98,282 / 94,984 | 98,282 / 94,984 | +3,298 → +3,298 | +0 | DONE/DONE, 720, no errors |
| live-114279308-seat1 | win | win | 97,904 / 95,362 | 97,904 / 95,362 | +2,542 → +2,542 | +0 | DONE/DONE, 720, no errors |
| live-114282277-seat0 | win | win | 124,128 / 112,818 | 124,128 / 112,818 | +11,310 → +11,310 | +0 | DONE/DONE, 720, no errors |
| live-114282277-seat1 | win | win | 124,128 / 112,818 | 124,128 / 112,818 | +11,310 → +11,310 | +0 | DONE/DONE, 720, no errors |
| live-114283577-seat0 | win | win | 79,661 / 78,759 | 79,661 / 78,759 | +902 → +902 | +0 | DONE/DONE, 720, no errors |
| live-114283577-seat1 | win | win | 79,661 / 78,759 | 79,661 / 78,759 | +902 → +902 | +0 | DONE/DONE, 720, no errors |
| live-114288168-seat0 | win | win | 83,030 / 81,732 | 83,030 / 81,732 | +1,298 → +1,298 | +0 | DONE/DONE, 720, no errors |
| live-114288168-seat1 | win | win | 83,030 / 81,732 | 83,030 / 81,732 | +1,298 → +1,298 | +0 | DONE/DONE, 720, no errors |
| live-114289228-seat0 | win | win | 109,053 / 105,797 | 109,053 / 105,797 | +3,256 → +3,256 | +0 | DONE/DONE, 720, no errors |
| live-114289228-seat1 | win | win | 109,053 / 105,797 | 109,053 / 105,797 | +3,256 → +3,256 | +0 | DONE/DONE, 720, no errors |
| live-114289837-seat0 | win | win | 97,910 / 71,845 | 97,910 / 71,845 | +26,065 → +26,065 | +0 | DONE/DONE, 720, no errors |
| live-114289837-seat1 | win | win | 97,910 / 71,845 | 97,910 / 71,845 | +26,065 → +26,065 | +0 | DONE/DONE, 720, no errors |
| top20-01-DECEM-114267880-seat0 | loss | loss | 86,464 / 95,549 | 86,464 / 95,549 | -9,085 → -9,085 | +0 | DONE/DONE, 720, no errors |
| top20-01-DECEM-114267880-seat1 | loss | loss | 86,464 / 95,549 | 86,464 / 95,549 | -9,085 → -9,085 | +0 | DONE/DONE, 720, no errors |
| top20-02-DSM-114267880-seat0 | win | win | 92,860 / 59,746 | 92,860 / 59,746 | +33,114 → +33,114 | +0 | DONE/DONE, 720, no errors |
| top20-02-DSM-114267880-seat1 | win | win | 92,860 / 59,746 | 92,860 / 59,746 | +33,114 → +33,114 | +0 | DONE/DONE, 720, no errors |
| top20-03-Boey-114266440-seat0 | win | win | 101,949 / 91,235 | 101,949 / 91,235 | +10,714 → +10,714 | +0 | DONE/DONE, 720, no errors |
| top20-03-Boey-114266440-seat1 | win | win | 101,949 / 91,235 | 101,949 / 91,235 | +10,714 → +10,714 | +0 | DONE/DONE, 720, no errors |
| top20-04-M & M & P & Q-114265030-seat0 | win | win | 100,637 / 74,096 | 100,637 / 74,096 | +26,541 → +26,541 | +0 | DONE/DONE, 720, no errors |
| top20-04-M & M & P & Q-114265030-seat1 | win | win | 100,637 / 74,096 | 100,637 / 74,096 | +26,541 → +26,541 | +0 | DONE/DONE, 720, no errors |
| top20-05-Vadim Vasilenko-114265033-seat0 | win | win | 153,922 / 137,782 | 153,922 / 137,782 | +16,140 → +16,140 | +0 | DONE/DONE, 720, no errors |
| top20-05-Vadim Vasilenko-114265033-seat1 | win | win | 153,922 / 137,782 | 153,922 / 137,782 | +16,140 → +16,140 | +0 | DONE/DONE, 720, no errors |
| top20-06-Majkel1337-114263239-seat0 | win | win | 97,257 / 94,390 | 97,257 / 94,390 | +2,867 → +2,867 | +0 | DONE/DONE, 720, no errors |
| top20-06-Majkel1337-114263239-seat1 | win | win | 97,257 / 94,390 | 97,257 / 94,390 | +2,867 → +2,867 | +0 | DONE/DONE, 720, no errors |
| top20-07-Fourth Quadrant-114267646-seat0 | win | win | 117,484 / 112,640 | 117,484 / 112,640 | +4,844 → +4,844 | +0 | DONE/DONE, 720, no errors |
| top20-07-Fourth Quadrant-114267646-seat1 | win | win | 117,484 / 112,640 | 117,484 / 112,640 | +4,844 → +4,844 | +0 | DONE/DONE, 720, no errors |
| top20-08-Unknown Mother-Goose-114272024-seat0 | win | win | 122,930 / 118,459 | 122,930 / 118,459 | +4,471 → +4,471 | +0 | DONE/DONE, 720, no errors |
| top20-08-Unknown Mother-Goose-114272024-seat1 | win | win | 122,930 / 118,459 | 122,930 / 118,459 | +4,471 → +4,471 | +0 | DONE/DONE, 720, no errors |
| top20-09-Just A game on your lips-114259211-seat0 | win | win | 179,188 / 0 | 179,188 / 0 | +179,188 → +179,188 | +0 | DONE/DONE, 720, no errors |
| top20-09-Just A game on your lips-114259211-seat1 | win | win | 179,188 / 0 | 179,188 / 0 | +179,188 → +179,188 | +0 | DONE/DONE, 720, no errors |
| top20-10-Anton Tikhonov-114270638-seat0 | win | win | 104,010 / 67,021 | 104,010 / 67,021 | +36,989 → +36,989 | +0 | DONE/DONE, 720, no errors |
| top20-10-Anton Tikhonov-114270638-seat1 | win | win | 104,010 / 67,021 | 104,010 / 67,021 | +36,989 → +36,989 | +0 | DONE/DONE, 720, no errors |
| top20-11-KawattaTaido-114272232-seat0 | win | win | 136,816 / 61,413 | 136,816 / 61,413 | +75,403 → +75,403 | +0 | DONE/DONE, 720, no errors |
| top20-11-KawattaTaido-114272232-seat1 | win | win | 136,816 / 61,413 | 136,816 / 61,413 | +75,403 → +75,403 | +0 | DONE/DONE, 720, no errors |
| top20-12-kigasudayooo-114273655-seat0 | win | win | 195,167 / 0 | 195,167 / 0 | +195,167 → +195,167 | +0 | DONE/DONE, 720, no errors |
| top20-12-kigasudayooo-114273655-seat1 | win | win | 195,167 / 0 | 195,167 / 0 | +195,167 → +195,167 | +0 | DONE/DONE, 720, no errors |
| top20-13-TheEggman-114273215-seat0 | win | win | 113,289 / 72,167 | 113,289 / 72,167 | +41,122 → +41,122 | +0 | DONE/DONE, 720, no errors |
| top20-13-TheEggman-114273215-seat1 | win | win | 113,289 / 72,167 | 113,289 / 72,167 | +41,122 → +41,122 | +0 | DONE/DONE, 720, no errors |
| top20-14-Azat Akhtyamov-114264626-seat0 | win | win | 155,910 / 94,381 | 155,910 / 94,381 | +61,529 → +61,529 | +0 | DONE/DONE, 720, no errors |
| top20-14-Azat Akhtyamov-114264626-seat1 | win | win | 158,336 / 93,195 | 158,336 / 93,195 | +65,141 → +65,141 | +0 | DONE/DONE, 720, no errors |
| top20-15-Yizhou-114273553-seat0 | win | win | 161,484 / 76,905 | 161,484 / 76,905 | +84,579 → +84,579 | +0 | DONE/DONE, 720, no errors |
| top20-15-Yizhou-114273553-seat1 | win | win | 161,484 / 76,905 | 161,484 / 76,905 | +84,579 → +84,579 | +0 | DONE/DONE, 720, no errors |
| top20-16-atsushi11o7-114273553-seat0 | win | win | 186,413 / 0 | 186,413 / 0 | +186,413 → +186,413 | +0 | DONE/DONE, 720, no errors |
| top20-16-atsushi11o7-114273553-seat1 | win | win | 186,413 / 0 | 186,413 / 0 | +186,413 → +186,413 | +0 | DONE/DONE, 720, no errors |
| top20-17-有辣条有权-114262952-seat0 | win | win | 171,071 / 84,751 | 171,071 / 84,751 | +86,320 → +86,320 | +0 | DONE/DONE, 720, no errors |
| top20-17-有辣条有权-114262952-seat1 | win | win | 171,071 / 84,751 | 171,071 / 84,751 | +86,320 → +86,320 | +0 | DONE/DONE, 720, no errors |
| top20-18-Kaggledew Valley 🏆-114273541-seat0 | win | win | 118,253 / 113,376 | 118,253 / 113,376 | +4,877 → +4,877 | +0 | DONE/DONE, 720, no errors |
| top20-18-Kaggledew Valley 🏆-114273541-seat1 | win | win | 118,253 / 113,376 | 118,253 / 113,376 | +4,877 → +4,877 | +0 | DONE/DONE, 720, no errors |
| top20-19-Arda Ceylan-114271761-seat0 | win | win | 166,030 / 80,205 | 166,030 / 80,205 | +85,825 → +85,825 | +0 | DONE/DONE, 720, no errors |
| top20-19-Arda Ceylan-114271761-seat1 | win | win | 149,089 / 67,789 | 149,089 / 67,789 | +81,300 → +81,300 | +0 | DONE/DONE, 720, no errors |
| top20-20-Densike-114270616-seat0 | win | win | 131,219 / 80,332 | 131,219 / 80,332 | +50,887 → +50,887 | +0 | DONE/DONE, 720, no errors |
| top20-20-Densike-114270616-seat1 | win | win | 131,219 / 80,332 | 131,219 / 80,332 | +50,887 → +50,887 | +0 | DONE/DONE, 720, no errors |
| public-win-114192390-seat0 | win | win | 51,275 / 41,239 | 51,275 / 41,239 | +10,036 → +10,036 | +0 | DONE/DONE, 720, no errors |
| public-win-114192390-seat1 | win | win | 54,519 / 45,076 | 54,519 / 45,076 | +9,443 → +9,443 | +0 | DONE/DONE, 720, no errors |

### Fresh reacting comparison (each row runs both versions)

| Case / seat | Uploaded result | New result | Uploaded own / rival cash | New own / rival cash | Margin: uploaded → new | Margin change | Execution |
|---|---|---|---:|---:|---:|---:|---|
| research4ee-2026092981-seat0 | draw | draw | 133,857 / 133,857 | 133,857 / 133,857 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092981-seat1 | draw | draw | 133,857 / 133,857 | 133,857 / 133,857 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092981-seat0 | draw | draw | 133,857 / 133,857 | 133,857 / 133,857 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092981-seat1 | draw | draw | 133,857 / 133,857 | 133,857 / 133,857 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092981-seat0 | win | win | 149,134 / 146,622 | 149,134 / 146,622 | +2,512 → +2,512 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092981-seat1 | win | win | 149,134 / 146,622 | 149,134 / 146,622 | +2,512 → +2,512 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092982-seat0 | draw | draw | 110,102 / 110,102 | 110,102 / 110,102 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092982-seat1 | draw | draw | 110,102 / 110,102 | 110,102 / 110,102 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092982-seat0 | draw | draw | 110,102 / 110,102 | 110,102 / 110,102 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092982-seat1 | draw | draw | 110,102 / 110,102 | 110,102 / 110,102 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092982-seat0 | win | win | 123,108 / 116,032 | 123,108 / 116,032 | +7,076 → +7,076 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092982-seat1 | win | win | 123,108 / 116,032 | 123,108 / 116,032 | +7,076 → +7,076 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092983-seat0 | loss | loss | 105,299 / 115,945 | 105,299 / 115,945 | -10,646 → -10,646 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092983-seat1 | loss | loss | 105,299 / 115,945 | 105,299 / 115,945 | -10,646 → -10,646 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092983-seat0 | draw | draw | 110,265 / 110,265 | 110,265 / 110,265 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092983-seat1 | draw | draw | 110,265 / 110,265 | 110,265 / 110,265 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092983-seat0 | win | win | 122,005 / 117,053 | 122,005 / 117,053 | +4,952 → +4,952 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092983-seat1 | win | win | 122,005 / 117,053 | 122,005 / 117,053 | +4,952 → +4,952 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092984-seat0 | draw | draw | 129,718 / 129,718 | 129,718 / 129,718 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| research4ee-2026092984-seat1 | draw | draw | 129,718 / 129,718 | 129,718 / 129,718 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092984-seat0 | draw | draw | 129,718 / 129,718 | 129,718 / 129,718 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| uploaded257-2026092984-seat1 | draw | draw | 129,718 / 129,718 | 129,718 / 129,718 | +0 → +0 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092984-seat0 | win | win | 124,002 / 115,231 | 124,002 / 115,231 | +8,771 → +8,771 | +0 | DONE/DONE, 720, no errors |
| publicAhmedV35-2026092984-seat1 | win | win | 124,002 / 115,231 | 124,002 / 115,231 | +8,771 → +8,771 | +0 | DONE/DONE, 720, no errors |

### File-loader test details

| Case / seat | Mode | Result | Own / rival cash | Margin | Minimum overage left | Completion |
|---|---|---|---:|---:|---:|---|
| live-114218866 / 0 | direct | loss | 107,828 / 116,493 | -8,665 | 60.000s | DONE/DONE, 720 |
| live-114218866 / 0 | file | loss | 107,828 / 116,493 | -8,665 | 58.670s | DONE/DONE, 720 |
| live-114218866 / 1 | direct | loss | 107,828 / 116,493 | -8,665 | 60.000s | DONE/DONE, 720 |
| live-114218866 / 1 | file | loss | 107,828 / 116,493 | -8,665 | 59.023s | DONE/DONE, 720 |
| live-114249897 / 0 | direct | win | 124,604 / 96,750 | +27,854 | 60.000s | DONE/DONE, 720 |
| live-114249897 / 0 | file | win | 124,604 / 96,750 | +27,854 | 60.000s | DONE/DONE, 720 |
| live-114249897 / 1 | direct | win | 124,604 / 96,750 | +27,854 | 60.000s | DONE/DONE, 720 |
| live-114249897 / 1 | file | win | 124,604 / 96,750 | +27,854 | 59.025s | DONE/DONE, 720 |

All eight native loader runs also reproduce the saved-panel rewards and complete policy telemetry.

[Eight native run records](H:/hackathan/diagnostics/combined_agent_257f_20260929/loader_pensukesan_dieter_20260929/runs.jsonl)

[Four direct/file parity outcomes](H:/hackathan/diagnostics/combined_agent_257f_20260929/loader_pensukesan_dieter_20260929/outcomes.jsonl)

[Source-bound loader receipt](H:/hackathan/diagnostics/combined_agent_257f_20260929/loader_pensukesan_dieter_20260929/receipt.json)

The final callable must be `kaggle_a44_pet_market_gate_entrypoint`. Actual Kaggle loading is compared with direct `agent` execution, including both players’ complete action sequences. This checks the earlier helper-selection/PASS failure mode.

## Evidence and reproduction

[Frozen research plan](H:/hackathan/diagnostics/combined_agent_257f_20260929/PLAN.md)

[Pilot assessment](H:/hackathan/diagnostics/combined_agent_257f_20260929/pizza_pilot/assessment.json)

[Saved-panel assessment](H:/hackathan/diagnostics/combined_agent_257f_20260929/saved_panel/assessment.json)

[Fresh reacting assessment](H:/hackathan/diagnostics/combined_agent_257f_20260929/reactive/assessment.json)

[Archived loader preparation error](H:/hackathan/diagnostics/combined_agent_257f_20260929/loader_checker_import_fix/failure.json)

Each comparison folder contains its immutable manifest, source hashes, JSONL ledger and receipt. Use `run_comparison.py` for saved cases, `run_reactive_comparison.py` for the native phase, and `check_loader.py` for the operational check. Existing output paths are intentionally refused; make a new manifest/output directory for a reproduction. Both compared policy hashes and all case/seed/opponent bindings must remain unchanged.
