# Corrected entrypoint live audit — 2026-09-26 04:44 UTC

Submission 56569042 is the user-authorized `main.py` upload with SHA-256
`08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863`.
Its single validation episode exactly matched local Kaggle file-path self-play
on terminal coins and opening action (72,078 / 72,747, both `DONE`).

The first two completed public replays were downloaded read-only and summarized
in `audit_latest_2.json`:

| Episode | Opponent | Our cash | Rival cash | Margin | Status |
| --- | --- | ---: | ---: | ---: | --- |
| 113561004 | Shivam Kushwaha | 162,326 | 84,961 | +77,365 | DONE / DONE |
| 113562187 | smileMAN13912339850 | 124,993 | 16,407 | +108,586 | DONE / DONE |

Our agent issued 6,346 and 6,278 non-`PASS` unit commands, respectively,
and hundreds of market orders in each game. Its displayed public score was
753.2 at 04:44 UTC. **Decision: retain current submitted source.** These
two games confirm Kaggle execution, but provide too little evidence about
the top 10 or the saved top-100 losses. No code promotion or new upload.

At 04:58 UTC, the same read-only audit expanded to five completed public
episodes (`audit_latest_5.json`). The three new opponents were Ryan Adams
(+67,011), Mouad AIT HA (+82,055), and Armanzhan Ayan (+28,938). All five
episodes were wins and both sides were `DONE` in each; displayed score rose
to 1013.2. The source and promotion decision remain unchanged.

At 05:15 UTC, `audit_latest_10.json` covered ten completed public games:
**10 wins, zero losses, all agents `DONE`**. The five newer wins were versus
Moo Point (+31,776), AdarshAleti (+26,151), シュークリーム (+3,581), Baen
(+37,168), and Kaichi Morimoto (+11,848). The displayed score was 1381.8.
This is still an early rating trajectory rather than proof of top-10 rank.

At 05:20 UTC, `audit_latest_11.json` added a `DONE`/`DONE` win by 8,014 coins
versus yurunougyou!, making the available public sample 11/11 wins. The
displayed score was 1475.9. The closest win remains +3,581 against
シュークリーム. **Retain current source; no new upload.**

At 05:28 UTC, `audit_latest_13.json` added two more `DONE`/`DONE` wins:
+2,958 against Juste Me (●'◡'●) and +3,656 against Gorgulu Fried Chicken
Wings. All thirteen available public games were wins; displayed score was
1707.8. These narrower margins warrant continued monitoring as opponent
ratings rise. **Retain current source; no new upload.**

At 05:42 UTC, `audit_latest_16.json` covered sixteen completed public games,
all wins with both agents `DONE`. The three newest were +1,184 versus Toshiki
Narushima, +1,376 versus Yuta Eiki, and +19,687 versus Lin. Displayed score
was 1981.5. The 05:42 UTC public leaderboard export ranked Lakshmanan R
1569, while rank 10 scored 2904.1. The earlier broken submission had reset
the rating; this remains an early upward trajectory, not a top-10 result.
**Retain current source; no new upload.**

At 05:46 UTC, `audit_latest_17.json` added a +20,489 `DONE`/`DONE` win versus
jasonyoung. The available sample was 17/17 wins; displayed score reached
2110.9. The 05:46 UTC leaderboard export ranked Lakshmanan R 1256, while
rank 10 scored 2904.5. **Retain current source; no new upload.**

At approximately 06:10 UTC, `audit_latest_24.json` covered 24 completed
public episodes: **21 wins and 3 losses**, with both players `DONE` throughout.
The three losses were -277 versus Igor V, -276 versus Atakan Aldemir, and
-131 versus GanadorPlusUltra. The newest wins included +396 versus Nagahama
and +15,349 versus Sankalp Wanjari. A 06:11 UTC leaderboard export ranked
Lakshmanan R **869 / 2269.0**, versus rank 10 at 2902.4; the prior 05:46
snapshot was rank 1256 / 2110.9. See
`diagnostics/leaderboard_20260926_0611/kaggriculture.zip`.

All three close losses used near-identical physical farms. Our farmer commands
matched Igor V on all 720 replay frames, Atakan Aldemir on 719, and
GanadorPlusUltra on 711; their market orders differed on 174, 195, and 168
frames respectively. The opponents' saved action routes reproduced the exact
live terminal cash on the original seed and seat, so they are useful
diagnostics. They are fixed routes and cannot independently validate a policy
change. See `live_losses_24_diagnosis.json` and the three route summaries.

The previous eight-turn sale policy and isolated 14-turn sale candidate were
screened against these three captured routes in both seats. Neither rescued
any loss. The submitted 12-turn baseline margins were -277, -276, and -131
on the original seats. Eight turns produced -837, -530, and -127;
14 turns produced -192, -228, and -101. All six candidate games per variant
ended `DONE`. The 14-turn variant already reversed the separate saved
`len8487` win and therefore remains rejected. **Retain the current 12-turn
source; no policy promotion or new Kaggle upload.**

`cash_ledger_losses.py` replayed each original seed and seat with the submitted
`main.py` and instrumented successful native market transactions. It exactly
reproduced all six terminal cash totals, with zero unexplained cash remainder.
Our net strawberry cash was lower in all three losses: -668, -131, and -281
coins versus Igor, Atakan, and Ganador respectively. Igor and Atakan sold the
same number of strawberry units as us; we sold ten *more* than Ganador. The
other item and purchase differences partly offset those gaps. This supports
further price and timing research, but no single strawberry intervention has
yet passed the route and reactive gates. Raw ledger:
`cash_ledger_losses_24.json`.

At 06:32 UTC, `audit_latest_29.json` covered 29 public episodes: **23 wins
and 6 losses**, all `DONE`/`DONE`. Five new games were +102 versus Apa, +40
versus Olympus, -65 versus K.Piro, -690 versus wei chang, and -4,666 versus
datatuu. The corresponding leaderboard snapshot ranked Lakshmanan R
**994 / 2211.4** against rank 10 at 2907.1. It is in
`diagnostics/leaderboard_20260926_0632/kaggriculture.zip`.
The score decreased from the 24-game snapshot; the initial rise was not a
stable estimate of final strength. The K.Piro farms were physically identical
throughout all 720 replay frames; wei chang matched 403 frames, and datatuu
matched 239, though datatuu still shared our day-six and day-twelve farm
counts. These are policy and market differences worth diagnosing, not an
entrypoint execution failure. See `live_losses_29_diagnosis.json`.

At approximately 06:53 UTC, `audit_latest_36.json` covered 36 completed
public episodes: **28 wins and 8 losses**, all `DONE`/`DONE`. Seven newly
available games were -1,006 versus Konstantin Zorin, +166 versus
HirokiTaniai, +714 versus Weifenhuan, +11 versus wei chang, -767 versus
kaggle Osaka, +2,499 versus RuiFSPinto, and +857 versus
𝕯𝖊𝖔𝖉𝖎𝖒𝖘 & 𝕮𝖔. On a 06:58 UTC leaderboard export, Lakshmanan R
ranked **837 / 2278.6**, versus rank 10 at 2900.9. Snapshot:
`diagnostics/leaderboard_20260926_0658/kaggriculture.zip`.
The seven new fixed-action routes were checked against the locally promoted
strawberry-only mirror-horizon candidate. It preserved all five wins and
both losses in both seats, increasing aggregate margin by 1,110 coins.
This does not establish a live win-rate gain because the opponents' actions
were held fixed. **Retain submission 56569042 as the current Kaggle upload;
the new local `main.py` has not been uploaded.** See
`diagnostics/top10_goal_20260926/MIRROR_STRAW24_RESULTS.md`.
