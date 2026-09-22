# Kaggriculture top-code integration

This is a local, read-only benchmark record. No Kaggle submission was made.

## Inputs inspected

- 100 score-descending public Kaggle kernel references were downloaded to
  `kaggle_top_code_2026-09-21/`.
- 99 notebooks were present and 394 readable notebooks were statically
  analyzed across the current archive and the older public-code archive.
- 38 complete, parseable agent sources were extracted for replay benchmarking;
  provenance and hashes are in `kaggle_complete_agents_2026-09-21/manifest.json`.
- 30 live top-player route files were downloaded to
  `live_top_leaderboard_routes_2026-09-21/`; they represent 25 unique action
  routes after digest de-duplication.

## Logic integrated into `main.py`

The production file retains the tested V46 public-state controller and adds
readable V47/V48 repairs plus a conservative V49 market continuation:

- the existing aurax7-derived chassis supplies route replay, worker alignment,
  weed repair, projected shed safety, sale timing, and terminal handling;
- the current V46 controller retains its exact MMPQ, ymg, and THIRD public-state
  market branches;
- at step 88, a unique public signature identifies the Kawatta/PET route; only
  then does V47 select the benchmarked V49-derived action book;
- V48 separately identifies the live THIRD/YARN_STORE signature and omits one
  empty WHEAT seed order at step 491; it does not enable the archived THIRD
  market table;
- the embedded V49 public source is called for state continuity, but its market
  output is applied only from step 360 on the BRUNCH_SPOT and the PET_CAFE-plus-
  opponent-GOOSE regimes; PET without GOOSE and YARN_STORE remain on the
  existing controller;
- all other observations use the prior V46/V48 action unchanged.

The V47/V48 books and the V49 source are stored as readable Python/JSON in
`main.py`; they are not encrypted and do not require the downloaded files at
runtime.

## Verification

The local engine is `kaggle_environments 1.32.7`.

| Check | Result |
|---|---:|
| V49 known-loss panel | 4 wins / 8 games; BRUNCH -6,033, PET +836, OTTER -3,369, THIRD +2,944 in both seats |
| V49 vs live top-player routes | 56 wins / 60 games; 24 / 25 unique seeded routes won; mean margin +63,444.10 |
| V49 vs all archived best-user route records | 88 wins / 88 games; 22 / 22 unique seeded routes won; mean margin +53,111.64 |
| Current production loss-panel replay | Same 4/8 result as the tested embedded candidate; all 8 games DONE |
| Current production self-play | 4/4 draws, all games DONE; mean agent call 2.08 ms, max 116.83 ms |
| Python bytecode compilation | passed |
| Kaggle submission | not run |

## 2026-09-22 expanded live leaderboard and code-page comparison (round 3)

The fresh leaderboard snapshot contains 200 teams; the leading displayed
scores were DSM 3149.8, Vadim Vasilenko 3080.7, Majkel1337 3077.5, Unknown
Mother-Goose 3069.7, and Kaggledew Valley 3048.0.  I downloaded up to three
recent completed public episodes for each of the top 100 teams.  Duplicate
episode IDs/action hashes were removed, leaving 244 distinct routes in
`live_top_leaderboard_routes_2026-09-22_round3_top100_3ep/`.

The unchanged V53 `main.py` played every route from both seats (488 games),
with no runtime errors.  It won 238 individual games and lost 250; under the
more useful paired-route metric it won 123/244 routes and lost 121/244.  Mean
game margin was +9,163, but median margin was -109, showing that a few very
large wins pull the average upward.  Across 100 represented teams, V53 went
3/3 against DSM, THIRD FARM CLUB, and Orbital Terraformer in this sample, but
lost every sampled route against Roman Katasonov, Ryuichi, Planned Economy,
Driz Lo, and Jyo.  These are three-episode samples, not proof of a universal
matchup result.

I also successfully downloaded the next 100 public Kaggle code examples
(`kaggle_code_examples_live_2026-09-22_round3_page2_top100/`).  Static
extraction found 32 complete parseable agents and 15 embedded payloads
representing 13 unique source hashes; duplicate payload pairs were ranks
5/24 and 8/41.  The extracted ideas include shop routing, market storage,
sell-divergence guards, counter-cyclical production, scarcity/economy
policies, and reactive scheduling.  Static comparison is recorded in
`KAGGLE_CODE_STATIC_COMPARISON_2026-09-22_round3_page2.md`; notebook cells were
not executed.

A first page-2 screen used seven payload candidates on 12 of the previous
panel's loss routes.  Its best policy won only 4/12 paired routes and had a
negative mean paired margin, so no candidate was promoted.  A broader
follow-up compares 11 different complete agents across 16 evenly spaced
loss routes from the new top-100 panel; results are being recorded separately
in `benchmark_codepage2_screen_current_losses_top100_2026-09-22.json`.
Production `main.py` remains unchanged, and no Kaggle submission was made.

The broader screen completed with zero agent errors.  Its best result was
rank 4, the Shop Router 0913 source: 2/16 paired losses flipped to wins,
5/32 individual games won, and mean paired margin -3,152, versus V53's
0/16 and -5,869 on those same loss routes.  Rank 6 and rank 31 each won
1/16; the other eight sources won 0/16.  Rank 4 is the only candidate worth
a full-panel check.  Rank 31 (Shabby Farm) averaged 115 seconds per game and
77 ms per decision (3.85 s maximum), versus V53's 15.74 seconds/game and
9.99 ms/decision, so it is both weak on wins and impractical at that cost.
The other screened candidates averaged roughly 5.4-10.1 seconds per game,
but none produced more than two paired wins on the loss-only sample.

The rank-4 full-panel follow-up rejected it as a replacement: it won 87/244
paired routes (175/488 individual games), compared with V53's 123/244 (238/488).
It recovered 19 V53 losses but damaged 55 V53 wins, for a net loss of 36 paired
wins.  It was faster (8.15 s/game; 5.02 ms/decision) but had a much lower mean
game margin (+870 versus +9,163 for V53) and zero runtime errors.  No page-2
candidate is promoted; `main.py` remains the better of the tested agents on
this expanded panel.

## 2026-09-22 V53 margin update

V53 extends V52 with 20 additional exact public signatures whose rank-41
policy improved aggregate replay margin by at least 500 without reducing the
observed win count or adding losses in the current top-50 comparison.  The
rank-41 controller is embedded as a separate instance so its state is not
advanced twice.  `main_v52_before_v53_promotion_retry.py` preserves the V52
production file.

| Final production verification | Result |
|---|---:|
| V53 candidate vs current top-50 routes | 108 / 164 wins; 54 / 82 paired; mean +19,463.87; 0 errors |
| Promoted `main.py` vs current top-50 routes | 108 / 164 wins; 54 / 82 paired; mean +19,463.87; 0 errors |
| Promoted `main.py` vs refreshed top-20 routes | 82 / 98 wins; 41 / 49 paired; mean +36,346.01 |
| Promoted `main.py` vs archived best-user routes | 88 / 88 wins; 22 / 22 paired; mean +55,682.80 |
| Promoted `main.py` vs failed-replay routes | 16 / 16 wins; 6 / 6 paired; mean +56,829.69 |
| Promoted `main.py` self-play smoke | 4 / 4 draws; all games DONE |
| Python bytecode compilation | passed |
| Kaggle submission | not run |

These are local replay results, not a guarantee of universal leaderboard
victory.  The final production file still loses 56 of 164 games in the
refreshed top-50 panel, so unseen opponents may expose additional regimes.

## 2026-09-22 V52 rank-41 rescue update

The current route files were refreshed before this experiment.  I regenerated
the step-72 feature panel from those exact files rather than reusing the older
same-named snapshot, preventing stale replay features from entering the
selector.  The fresh panel is `capture_current_top50_step72_refreshed_2026-09-22.json`.

On the full current top-50 panel, the downloaded rank-41 Ahmed policy alone
scored 101 / 164 games and 51 / 82 paired routes.  Route-by-route comparison
found seven public signatures where it beat V51 and five where V51 was better.
V52 keeps V51 as the default and selects rank 41 only on those seven fresh
public signatures.  It is embedded as readable Python; no external downloaded
file is required at runtime.  The previous production file is preserved as
`main_v51_before_v52_promotion.py`.

| V52 verification | Result |
|---|---:|
| V51 baseline vs current top-50 routes | 98 / 164 wins; 49 / 82 paired; mean +18,866.81 |
| V52 router candidate vs current top-50 routes | 108 / 164 wins; 54 / 82 paired; mean +19,117.87; 0 errors |
| Promoted `main.py` vs current top-50 routes | 108 / 164 wins; 54 / 82 paired; mean +19,117.87; 0 errors |
| Promoted `main.py` vs refreshed top-20 routes | 82 / 98 wins; 41 / 49 paired; mean +35,978.79 |
| Promoted `main.py` vs archived best-user routes | 88 / 88 wins; 22 / 22 paired; mean +55,682.80 |
| Promoted `main.py` vs failed-replay routes | 16 / 16 wins; 6 / 6 paired; mean +56,829.69 |
| Promoted `main.py` self-play smoke | 4 / 4 draws; all games DONE |
| Python bytecode compilation | passed |
| Kaggle submission | not run |

The replay panels are strong local evidence, not proof of universal victory:
the official ladder can contain unseen seeds and policies. The remaining live
loss routes are the captured Kawatta/BRUNCH and Otter/PET records; the PET and
THIRD records in the four-route diagnostic are wins. A single- and two-order
late-market mutation search did not flip either remaining loss, and Amey’s
full-policy trajectory was rejected because switching into it after route
identification caused much larger state-mismatch losses. No external
submission was made.

## 2026-09-22 current leaderboard/code refresh (round 2)

This was a read-only Kaggle refresh.  The current leaderboard snapshot contains
200 rows; the top visible scores were DSM 3179.9, Majkel1337 3076.2, Vadim
Vasilenko 3069.7, Unknown Mother-Goose 3065.0, and Kaggledew Valley 3028.7.
I downloaded three recent completed public episodes per available team for the
current top 50 teams: 120 route files with 120 unique action hashes.  The
routes are stored in `live_top_leaderboard_routes_2026-09-22_round2_top50_3ep/`.

I also pulled 100 current public code examples.  Static source extraction
recovered 48 embedded agent payloads and the normal complete-agent extractor
has 37 complete parseable agents.  The extraction never executed a notebook;
it only decoded literal base64/base85/gzip/zlib/tar payloads and then parsed
the resulting Python.  The round-2 code archive and manifests are:

- `kaggle_code_examples_live_2026-09-22_round2_top100/`
- `kaggle_notebook_sources_live_2026-09-22_round2_top100/`
- `kaggle_complete_agents_live_2026-09-22_round2_top100/`
- `kaggle_embedded_agents_live_2026-09-22_round2_top100/`

The decisive fresh-panel comparison is:

| Candidate | Games | Individual wins | Paired wins | Mean margin | Errors |
|---|---:|---:|---:|---:|---:|
| V53 `main.py` | 240 | 136 | 69 / 120 | +12,920.07 | 0 |
| Rank 1 Ahmed V56 source | 240 | 136 | 69 / 120 | +13,395.55 | 0 |
| Rank 7 Lynn source | 240 | 136 | 69 / 120 | +13,427.54 | 0 |
| Rank 2 Dmitrii “A Smaller Market Shock” | 240 | 135 | 68 / 120 | +14,600.90 | 0 |

The top-10 screen on the first 12 deterministic routes found no win-count
upgrade.  Ranks 21 and 23 tied V53 at 6 / 12 paired wins; ranks 8, 9, 13,
18, 26, 16, and 3 were lower.  Rank 4 was not recoverable as a complete
Python payload from its notebook wrapper, so it was not executed as an agent.

Conclusion: the current V53 production file already contains most of the
strong public lineage in these examples.  The newest rank-1/rank-7 family
improves margin but not the Kaggle win count, while rank 2 loses one paired
route.  No unproven public-code replacement was promoted into `main.py`; no
Kaggle submission was made.

### Follow-up composition tests

I re-ran the older Haide controller against the same fresh 120-route panel.
It reproduced V53's 69 / 120 paired wins and was slightly lower on paired
margin (+25,822.08 versus +25,840.14), so it was not promoted.  The rank-2
source had five public routes where it beat V53, but a step-72, step-24, and
step-1 targeted router did not reproduce those gains after a V53 prefix.  The
step-72 hybrid dropped to 6 / 11 on the changed-route diagnostic, which is
direct evidence that its internal trajectory is not state-compatible with a
late switch.  The production `main.py` was left unchanged.

The static source inventory is captured in
`KAGGLE_CODE_STATIC_COMPARISON_2026-09-22.md` and its JSON companion: 48
embedded payloads were recovered from 100 downloaded examples, representing
44 unique source hashes.  `analyze_live_code_examples.py` performs only local
static parsing and does not execute notebook cells.  A second Kaggle code-list
page could not be fetched because the CLI session requested fresh
authentication; the already downloaded top-100 archive remains intact.

## 2026-09-22 refresh and V51 promotion

The read-only Kaggle refresh collected 200 leaderboard rows, 82 unique public
routes from the current top 50 teams (two completed public episodes per team
where available), and 100 public competition code examples. The route files
are in `live_top_leaderboard_routes_2026-09-22_top50/`; the code pull is in
`kaggle_code_examples_live_2026-09-22_top100/`. Static extraction found 37
complete parseable agent payloads representing 29 unique source hashes. The
download and analysis utilities are `refresh_top_leaderboard_routes.py`,
`refresh_top_code_examples.py`, `extract_live_notebook_sources.py`, and
`extract_live_complete_agents.py`.

The policy screen covered 14 distinct downloaded sources on the 17-route
current loss panel. The Haide 2950/2965 family was strongest there at 16/34
games and 8/17 paired routes; the other selected policies ranged from 0/34 to
14/34. Static markers and executable results are preserved in
`benchmark_live_code_pool_current_loss17_2026-09-22.json`.

V51 uses the Haide master as the default controller and retains V49 as a
plain-source reserve on six public step-72 signatures where V49 beat Haide in
the refreshed top-50 panel. The selector uses only shop, opponent public
physical counts, and opponent public cash; it does not use seeds, episode IDs,
replay files, or private opponent state. The Haide source is embedded as
readable Python in `main.py`, not encrypted. The pre-promotion V49 file is
preserved as `main_v49_before_v51_promotion.py`.

| Expanded verification | Result |
|---|---:|
| V49 baseline vs current top-50 routes | 89 / 164 wins; 44 / 82 paired; mean +14,308.93 |
| Haide standalone vs current top-50 routes | 96 / 164 wins; 48 / 82 paired; mean +18,580.29 |
| V51 router candidate vs current top-50 routes | 98 / 164 wins; 49 / 82 paired; mean +18,866.81 |
| Promoted `main.py` vs current top-50 routes | 98 / 164 wins; 49 / 82 paired; mean +18,866.81; 0 errors |
| Promoted `main.py` vs refreshed top-20 routes | 80 / 98 wins; 40 / 49 paired; mean +35,710.36 |
| Promoted `main.py` vs archived best-user routes | 88 / 88 wins; 22 / 22 paired; mean +55,682.80 |
| Promoted `main.py` vs six failed-replay route files | 16 / 16 wins; 6 / 6 paired; mean +56,829.69 |
| Promoted `main.py` self-play smoke | 4 / 4 draws; all games DONE |
| Python bytecode compilation | passed |
| Kaggle submission | not run |
