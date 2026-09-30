# Fresh-replay improvement results

Research snapshot: official leaderboard of **2026-09-29 17:04:23 UTC (22:34:23 IST)**. Downloaded the latest three eligible completed public episodes per top 100 team, plus all 27 then-available completed episodes for uploaded submission 56680167. There are 267 unique replay archives (240 top 100 episodes and 27 submission episodes), with provenance and hashes in [collection folder](H:/hackathan/diagnostics/fresh90_refresh_20260929).

The comparison baseline is the exact uploaded **cb76fbc4** source. The retained latest-panel development candidate is **4802aa95**, kept as a separate experimental file. Root main.py remains **4eeac9c3**. No upload was made in this research task.

## Measured replay results

| Panel | Baseline wins | Candidate wins | Candidate both-seat teams | Added / lost winning seats |
|---|---:|---:|---:|---:|
| Newest top 100 | 132/200 (66.0%) | 156/200 (78.0%) | 78/100 | +24 / -0 |
| Newest top 20 subset | 32/40 (80.0%) | 36/40 (90.0%) | 18/20 | +4 / -0 |
| All 27 uploaded-submission opponent tapes | 48/54 (88.9%) | 48/54 (88.9%) | 24/27 | +0 / -0 |
| Reserved second-latest top 100 | 126/200 (63.0%) | 126/200 (63.0%) | 63/100 | +4 / -4 |
| Reserved second-latest top 100: top 20 subset | 28/40 (70.0%) | 26/40 (65.0%) | 13/20 | +0 / -2 |
| Reserved third-latest top 100 | 137/200 (68.5%) | 143/200 (71.5%) | 71/100 | +6 / -0 |
| Reserved third-latest top 100: top 20 subset | 28/40 (70.0%) | 30/40 (75.0%) | 15/20 | +2 / -0 |

**The requested more than 90% target is not met.** The newest top 100 result is 78%; the newest top 20 subset is exactly 90%. These are fixed-action replay diagnostics, not an estimated online win rate or a top 10 probability. The newest 100 includes 84 distinct episodes; the top 20 subset includes 15. The reserved sets have 92 and 96 distinct episodes, with 9 and 7 episode IDs also present in development.

The 27 original uploaded seats reproduce all 719 submitted actions and both final rewards exactly; this verifies baseline provenance and replay mechanics. Online at the collection snapshot, the submission had 24 wins and 3 losses. Playing both seats locally produces 48/54 baseline wins. The new combined candidate retains those wins but does not rescue the three losses.

## Changes in the combined candidate

- Reorders an existing land purchase after same-turn sales only when guarded market forecasts fund the next quadrant and preserve other resources. This rescues both latest Majkel seats.
- Uses eight whole, prefix-compatible schedules after observing the second shop. These preserve the existing opening and match worker and investment commitments.
- Removes the Yarn/Smoothie rule that initially lost four public-control wins. The repeated public 27 panel is development evidence after this correction.

## Experiment record

| Experiment | Result | Decision |
|---|---|---|
| Forecast rollout V1 | Two-seed reacting pilot tied baseline; no activation | Rejected |
| Forecast rollout V2 | 32/40 top 20, no added win; mean margin decreased | Rejected |
| Whole-route searches | 33 then 232 variants; selected rules checked against affected winners | Development only |
| Funded-land repair | 134/200 vs 132/200, no lost winning seats | Retained for combination |
| Combined V1 | 158/200, but public 27 fell 48/54 to 44/54 | Rejected |
| Combined V2 | 156/200; public 27 restored 48/54 | Qualification below |
| Three current melon-opening families | 15W/31L,8W/2D/36L,23W/23L vs 32W/14L | All rejected |

The opening families rescued one or two public losses but sacrificed too many top 20 wins. Earlier melon output alone did not establish a stronger policy.

## Qualification

Reserved replay gate: **PASS**, combined point change +6.0. Individual gained/lost seats are in the case reports.

Reacting screen: baseline 34W/30D/0L; candidate 34W/26D/4L. Frozen gate: **FAIL**. Whole-seed bootstrap 95% interval for paired point-rate change: [-0.09375, 0.0].

The four new losses replace baseline draws at seed 22929006 against cb76 and ae349, both seats. All activate Farmers Market/Smoothie route 113410114, with zero funded-land repair activations; each loses 6114 margin. Conditional operational verification and the untouched 32-seed confirmation were stopped at the failed performance gate. The prepared verifier was statically checked, but its game suite was never run.

Native framework/file-loader qualification for these exact bytes has not been completed.

**Decision: rejected for promotion; preserve the experimental file and retain the incumbent.**

## Files and every-case results

- [Experimental candidate 4802aa95](H:/hackathan/diagnostics/fresh90_improvement_20260929/candidate_fresh_combined_v2.py)
- [Exact uploaded baseline cb76fbc4](H:/hackathan/diagnostics/fresh90_improvement_20260929/baseline_cb76fbc4.py)
- [Frozen overall plan](H:/hackathan/diagnostics/fresh90_improvement_20260929/PLAN.md)
- [Frozen combined V2 plan](H:/hackathan/diagnostics/fresh90_improvement_20260929/COMBINATION_V2_PLAN.md)
- [Public-loss diagnosis](H:/hackathan/diagnostics/fresh90_loss_audit_20260929/LATEST_PUBLIC_LOSSES_56680167_AUDIT.md)
- [Byte-identical experimental candidate in the workspace root](H:/hackathan/main_candidate_fresh_replay_20260930_4802aa95.py)
- [top 100: every seat, rewards, margins, changes and hashes (CSV)](H:/hackathan/diagnostics/fresh90_improvement_20260929/combined_v2_top100_comparison.csv)
- [public 27: every seat, rewards, margins, changes and hashes (CSV)](H:/hackathan/diagnostics/fresh90_improvement_20260929/combined_v2_public27_comparison.csv)
- [reserved2: every seat, rewards, margins, changes and hashes (CSV)](H:/hackathan/diagnostics/fresh90_improvement_20260929/combined_v2_reserved2_comparison.csv)
- [reserved3: every seat, rewards, margins, changes and hashes (CSV)](H:/hackathan/diagnostics/fresh90_improvement_20260929/combined_v2_reserved3_comparison.csv)
- [Opening family 1: every pilot case](H:/hackathan/diagnostics/fresh90_improvement_20260929/opening_family1_pilot_comparison.csv)
- [Opening family 2: every pilot case](H:/hackathan/diagnostics/fresh90_improvement_20260929/opening_family2_pilot_comparison.csv)
- [Opening family 3: every pilot case](H:/hackathan/diagnostics/fresh90_improvement_20260929/opening_family3_pilot_comparison.csv)
- [All logged case rows across experiments (includes exact reused rows)](H:/hackathan/diagnostics/fresh90_improvement_20260929/ALL_CASE_ROWS.csv)
- [Case ledger provenance and hashes](H:/hackathan/diagnostics/fresh90_improvement_20260929/ALL_CASE_ROWS_INDEX.json)
- [Reacting screen: every paired case](H:/hackathan/diagnostics/fresh90_improvement_20260929/combined_v2_screen_paired_cases.csv)

## Final alternative: highest-ranked single-tape controls

The complete recorded schedules from ranks 1,2,3 were selected and frozen before their pilot. They score 12W/2D/32L,12W/0D/34L and 22W/0D/24L versus baseline 32W/0D/14L. All 138 cases are clean, but all three controls fail the frozen improvement criteria. No further source-tape search was made in this bounded experiment.

- [Rank 1 control: every pilot case](H:/hackathan/diagnostics/fresh90_improvement_20260929/leading_rank1_pilot_comparison.csv)
- [Rank 2 control: every pilot case](H:/hackathan/diagnostics/fresh90_improvement_20260929/leading_rank2_pilot_comparison.csv)
- [Rank 3 control: every pilot case](H:/hackathan/diagnostics/fresh90_improvement_20260929/leading_rank3_pilot_comparison.csv)

Candidate SHA-256: `4802aa95c1b960f6bdba3ac313870a847dba8e93dce7d22edfeaca4cee7c19f4`.
Report generated: 2026-09-29T18:56:17.062197+00:00.
