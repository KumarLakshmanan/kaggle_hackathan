# Observable day-6/day-10 structure in the 4ee live games

**2026-09-27, final 16:53 UTC public cutoff.** This is a read-only,
post-outcome diagnosis of all 61 completed submission-56609430 public games:
42 wins and 19 losses. The raw replay SHA-256 in `cohort_165306.json` was
verified for each game before extraction; all are engine 1.32.7,
DONE/DONE, 720 frames. `features.json` records the source cohort hash and
every episode's snapshots. Steps 144 and 240 are the starts of game days 7
and 11, after the day-6 and day-10 work, respectively. Only own/current
observation fields are eligible for a future trigger. Rival private stock
and historical rival action requests in the extraction are diagnostic only.

The opponent ranks below are those in the 16:53 UTC leaderboard snapshot,
not ratings assigned at game time. All 19 losses but only 10/42 wins were
against snapshot-rank-200-or-better teams. This strength imbalance makes a
pooled loss/win contrast particularly easy to misread; the smaller strong
opponent comparison remains descriptive.

## Observable progression

| At start of day | Measure, median | 19 losses | 42 wins | 10 rank≤200 wins |
|---|---|---:|---:|---:|
| 7 | Own/rival installed tiles | 25/25 | 25/25 | 25/25 |
| 7 | Own cash | 899 | 852.5 | 807 |
| 7 | Rival melon plots | 12 | 12 | 12 |
| 11 | Own/rival installed tiles | 50/61 | 50/50 | 50/50 |
| 11 | Own cash | 2,236 | 2,144 | 2,009.5 |
| 11 | Own cows/sheep | 8/4 | 8/4 | 8/4 |
| 11 | Own prior-day productive hand **requests** | 78 | 77 | 76 |
| 11 | Own prior-day HIRE **requests** | 7 | 7 | 7 |

The installed-tile gap arises mainly on the rival side. Own day-10 land,
cash, cows, sheep, and attempted labor are not broadly deficient in the
losses. Requested worker commands alone do not prove successful execution;
the installed plot count is direct evidence of physical deployment. Rival
prior-day HIRE requests have median 10 in losses and 8 in wins, but their
saved action history cannot be a current-observation trigger.

The shared TOMATO market inventory changed from day 6 to day 10 by median
−28 in losses versus −10 in all wins and −4 in rank≤200 wins; its price
changed +3 versus +1 and 0. These are market states accessible to the agent,
but the snapshots do not attribute the change to a particular player's
executed sales, nor do they prove that an extra tomato commitment would
improve final relative cash. Day-6 rival melon≥12 covers 11/19 losses but
also 31/42 wins. A generic melon response fails specificity.

## Exploratory observable rules

The finite scan is in `rule_scan.py` and `rule_scan.json`. The frozen audit
plan required ≥4/19 loss coverage and ≤4/42 false positives to highlight a
narrow signal. These thresholds were applied to this cohort only; rules and
cutoffs were inspected against these same outcomes, so all reported
precision is in-sample.

| Rule at start of day 11 | Losses caught | Wins flagged | Rank≤200 wins flagged |
|---|---:|---:|---:|
| Rival installed ≥ own+8 | 11/19 | 6/42 | 3/10 |
| Rival installed ≥ own+8 and rival cash ≤ own | 8/19 | 4/42 | 2/10 |
| Pizza among three visible shops, rival owns ≥3 land parcels, own ≤2 | 6/19 | 0/42 | 0/10 |
| Pizza among three shops and rival installed ≥ own+8 | 7/19 | 1/42 | 0/10 |

The broad 8L/4W rule's four false-positive wins include rank-100 and
rank-105 opponents. They acquire and mostly fill the same third land:

| Win episode; opponent (rank) | Three shops | Day-10 cash own/rival | Our third land | Southwest installed at step 312 | Final margin |
|---|---|---:|---:|---:|---:|
| 114193811; Chris Tu (3359) | ICE_CREAM_SHOP/YARN_STORE/BRUNCH_SPOT | 7,351/144 | 242 | 25/25 | +8,353 |
| 114195269; Jack Burley (3166) | BAKERY/YARN_STORE/BAKERY | 2,125/1,108 | 266 | 25/25 | +21,035 |
| 114220354; Nakano (100) | BAKERY/BRUNCH_SPOT/PET_CAFE | 1,974/145 | 266 | 25/25 | +5,909 |
| 114239616; kwa (105) | FARMERS_MARKET/SMOOTHIE_SHOP/FARMERS_MARKET | 450/164 | 242 | 23/25 | +4,217 |

The same early rival footprint can therefore be overcome by the
incumbent's already scheduled production. The wide range in own day-10
cash also argues against a single fixed cash threshold as a funding
instruction.

The narrower Pizza/land marker occurs in six losses against five distinct
teams: pensukesan twice (114218866 and 114257327), 吃白饭的大肥鱼 (114223292),
mhw (114235177), high frequency farming (114243994), and Dieter
(114249897). It has no wins **in this 61-game cohort**, but the repeated
team and post-hoc selection limit that observation. Pizza visible at day 6
by itself flags 8 losses and 6 wins. The day-10 marker first catches a
rival third-land investment that happened at steps 217–220; our same land
is already scheduled and is acquired at step 241, 242, or 266 in every one
of these six losses. Five of six have all 25 southwest plots installed by
step 312; the second pensukesan episode has 11. This is a timing and
productivity divergence after rival expansion, not evidence that the agent
forgot to buy its third parcel.

Across all 12 broad-rule cases, own third land is acquired by step 266,
and 10/12 have at least 23 southwest installations by step 312, including
all four wins. Only two losses have 11 at that point: Kucing Garong
(114236633) and pensukesan (114257327). Those exceptions warrant a
case-specific execution audit, but cover only 2/19 losses. The incumbent
already issues substantial land, seed/product, animal, and HIRE orders in
the same window. Moving the land order earlier or adding another parcel
would compete with those obligations and needs a funded worker-to-sale
schedule and a forecast of rival market response. The six Pizza losses do
not share an established executed-revenue shortfall in one product.

## Later five-game appendix — 17:12 UTC

The next official listing added five completed public games (three wins,
two losses) after this 61-game audit was frozen. `check_later_delta.py`
applied the same recorded day-10 rules without refitting and verified all
five replay hashes; see `later_delta_171158.json`. The Pizza/land marker
flagged the new kibuna loss (114267572), no new wins, and missed the Roman
Svet loss. Combined descriptive counts at the 66-game cutoff are 7/21
losses covered and 0/45 wins flagged. This tiny later sample does not
establish a reliable win-rate effect or qualify a policy change.

Kibuna repeats the feasibility problem: rival third land at step 220,
our third land at 242, all 25 southwest plots installed by step 312,
then a 6,383-coin loss. The signal still has no funded replacement
schedule or measured reacting-market benefit.

## Decision

**Reject a policy change from this audit.** The day-10 Pizza/land marker is
a useful exploratory warning for future research, but no executable
replacement bundle has been identified. The incumbent already buys and
mostly fills the third land. The marker requires confirmation on fresh
reacting games, in both seats with original shops, and any proposed full
schedule must improve wins and paired relative cash without losing winning
controls. No candidate, `main.py` edit, or Kaggle upload was made.

Reproduce from `extract.py` (fresh destination required because it protects
the frozen `features.json`), then `analyze.py`, `rule_scan.py`,
`bundle_audit.py`, and `pizza_timing.py`. Machine-readable evidence:
`features.json`, `flat.csv`, `feature_summary.json`, `rule_scan.json`,
`bundle_cases.json`, `pizza_timing.json`, and `later_delta_171158.json`.
