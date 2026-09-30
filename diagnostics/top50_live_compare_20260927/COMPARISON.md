# Current Kaggriculture top-50 route comparison

Leaderboard snapshot: 2026-09-26T22:35:00.407907+00:00. Engine: 1.32.7.
One completed public action history per displayed top-50 team, replayed on its
original seed in both seats. Both files faced the same fixed opponent tape.
The source submission for each team was the recent one whose public score
was closest to the frozen leaderboard score. Ratings moved during collection:
median selection gap 4.2,
maximum 52.0 leaderboard points.
The opponent does not react to our changed actions, and this is not a Kaggle rating.

`main.py` SHA-256 `489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`;
new file SHA-256 `1f22192297821ab5205b8cdcbd22bd1fab30d546860f3c61e8096a2a4355446b`.

## Summary

| Measure | main.py | New Python file |
| --- | ---: | ---: |
| Paired wins / 50 | 40 | 42 |
| Paired draws / 50 | 0 | 0 |
| Paired losses / 50 | 10 | 8 |
| Total paired coin margin | +3,537,706 | +4,051,180 |

The new file flips 6 losses to wins and
4 wins to losses. Its total paired-margin change is
+513,474 coins; own-cash change
+675,602, rival-cash change
+162,128.
First-two shops matched between policies in 65/100 seat comparisons.
The new file recorded 11 idle weed DIG repairs,
0 blocked-work DIG repairs and
0 repair errors across its 100 games.
The aggregate gain cannot be assigned to those repairs without a same-route ablation.

## Every top-50 team

W/L/D use the sum of margins from the two seat-swapped games.
A positive change favors the new file.

| Rank | Team | LB score | main.py | New file | Margin change |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Boey | 3061.0 | L -42,050 | W +38,472 | +80,522 |
| 2 | DSM | 3054.4 | W +71,224 | W +113,912 | +42,688 |
| 3 | Fourth Quadrant | 3040.7 | L -11,720 | W +39,619 | +51,339 |
| 4 | M & M & P & Q | 2985.9 | W +169,057 | W +379,846 | +210,789 |
| 5 | DECEM | 2972.5 | W +159,878 | W +207,302 | +47,424 |
| 6 | Vadim Vasilenko | 2961.5 | L -57,024 | W +68,242 | +125,266 |
| 7 | Majkel1337 | 2947.7 | W +35,774 | W +54,246 | +18,472 |
| 8 | Unknown Mother-Goose | 2939.9 | W +141,842 | W +220,562 | +78,720 |
| 9 | Yizhou | 2917.4 | W +60,584 | W +71,947 | +11,363 |
| 10 | Pii | 2902.0 | W +146,468 | W +137,734 | -8,734 |
| 11 | Russell Kirk | 2887.2 | W +170,520 | W +108,460 | -62,060 |
| 12 | TheEggman | 2877.2 | W +70,916 | W +103,079 | +32,163 |
| 13 | Azat Akhtyamov | 2874.9 | W +74,550 | W +88,533 | +13,983 |
| 14 | mtmr_s1 | 2871.2 | W +179,710 | W +219,874 | +40,164 |
| 15 | Anton Tikhonov | 2868.7 | W +184,252 | L -27,542 | -211,794 |
| 16 | THIRD FARM CLUB | 2865.5 | W +64,178 | W +84,018 | +19,840 |
| 17 | 🐚seek inspiration🐚 | 2864.2 | W +37,364 | W +9,926 | -27,438 |
| 18 | 吃白饭的大肥鱼 | 2861.1 | W +44,644 | W +224,724 | +180,080 |
| 19 | tetsuya & yuanzhe & guoqin | 2848.0 | W +91,584 | W +70,484 | -21,100 |
| 20 | We wanna be tomatos | 2846.4 | L -25,710 | L -1,134 | +24,576 |
| 21 | Arda Ceylan | 2835.5 | W +68,719 | W +93,996 | +25,277 |
| 22 | My second life | 2829.1 | L -8,492 | W +628 | +9,120 |
| 23 | kigasudayooo | 2828.1 | W +115,918 | W +184,910 | +68,992 |
| 24 | Kaggledew Valley 🏆 | 2813.2 | L -35,908 | L -51,935 | -16,027 |
| 25 | Victor @ Tufa Labs | 2807.9 | W +53,686 | L -29,790 | -83,476 |
| 26 | ymg_aq | 2804.0 | W +70,404 | W +93,608 | +23,204 |
| 27 | Otter Vibe | 2802.6 | W +31,664 | L -8,142 | -39,806 |
| 28 | sekai013 | 2801.1 | W +71,144 | W +105,192 | +34,048 |
| 29 | Artem The Farmer 🍅 | 2796.9 | L -26,666 | L -114,014 | -87,348 |
| 30 | IsaiahP | 2793.1 | W +17,690 | W +43,460 | +25,770 |
| 31 | flg | 2782.3 | W +202,422 | W +193,161 | -9,261 |
| 32 | Aaweg | 2774.1 | L -1,358 | W +27,320 | +28,678 |
| 33 | arutyunoff | 2773.4 | W +81,070 | W +84,754 | +3,684 |
| 34 | Densike | 2770.9 | W +161,612 | W +179,648 | +18,036 |
| 35 | Yannik Schiffner | 2769.6 | W +56,344 | W +56,166 | -178 |
| 36 | feel the agi | 2762.1 | W +146,490 | W +3,288 | -143,202 |
| 37 | SpaTaro | 2759.3 | W +141,848 | W +169,800 | +27,952 |
| 38 | marwar22 | 2757.9 | L -4,476 | L -19,866 | -15,390 |
| 39 | akmr | 2755.9 | W +250,054 | W +244,044 | -6,010 |
| 40 | Ryo Hasegawa | 2752.9 | W +444 | W +7,522 | +7,078 |
| 41 | yuto083 | 2746.7 | W +235,730 | W +174,203 | -61,527 |
| 42 | YumeNeko | 2745.0 | W +46,346 | W +34,486 | -11,860 |
| 43 | 摆烂小分队 🏆 | 2744.8 | W +63,342 | W +67,672 | +4,330 |
| 44 | KawattaTaido | 2743.5 | W +20,700 | W +38,784 | +18,084 |
| 45 | forever young | 2742.6 | W +26,508 | W +39,162 | +12,654 |
| 46 | WarRusher | 2736.3 | W +48,596 | W +111,464 | +62,868 |
| 47 | Snorlax | 2735.7 | W +54,080 | W +12,236 | -41,844 |
| 48 | by | 2729.7 | W +3,452 | L -9,744 | -13,196 |
| 49 | feles99 | 2726.4 | W +105,196 | W +99,663 | -5,533 |
| 50 | Excluding | 2717.9 | L -24,894 | W +7,200 | +32,094 |

## Evidence

`leaderboard_snapshot.json`, `snapshot_meta.json`,
`routes/summary.json`, `main_50routes.json`, `new_50routes.json`,
`comparison.json`, and `comparison.csv` are the frozen evidence.
Every one of the 200 games finished DONE/DONE.
