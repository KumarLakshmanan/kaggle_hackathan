# Static audit of three latest-submission public losses

## Scope and provenance

This audit covers the three public losses in submission 56680167: episodes 115319884 (Maher el Ouahabi), 115315638 (coolin666), and 115302829 (Tomohiro Nagai). The uploaded agent was the exact local `main_candidate_minimal_repair_20260929_cb76fbc4.py`, SHA-256 `cb76fbc462c66380ce3effc3ec2b8d3b888ccae4bccde1d7b7faa5c991e6dd74`.

I used the rival-correct episode metadata in `diagnostics/fresh90_refresh_20260929/routes/current_submission_56680167_opponents/summary.json` (SHA-256 `13379d1947786d129da8a6b38ab6f3aed97a2a5f1d3ce4740418f1d699166a89`) and the matching complete archived replays. I paired observation `steps[i]` with the action in `steps[i+1]`, matching the collection verifier's 719-action convention. For all three episodes, recomputing the uploaded agent's canonical 719-action tape from the archived frames exactly matched the action SHA in the episode metadata.

| Rival / episode | Seed | Candidate seat | Candidate vs. rival reward | Margin | Compressed replay SHA-256 | Candidate action SHA-256 |
|---|---:|---:|---:|---:|---|---|
| Maher el Ouahabi / 115319884 | 893137680 | 1 | 106,410 vs. 111,854 | −5,444 | `a774264b768698b9bb165a3e43518155efe503c2d65f036fafebc0a2d50b7ed1` | `9cf923f87733c745af854deb151957fd34b8692356148aa202b5e6eabf7d04e4` |
| coolin666 / 115315638 | 1013451854 | 1 | 122,881 vs. 128,043 | −5,162 | `edcaff8f361a7eeac17df30d13e5fec723adc6346ff978b6ae06ae7e123d1e59` | `d1918463ab0f058113b1e8157fc4f28e49d3e7a8f459a3118529b7dfe906c742` |
| Tomohiro Nagai / 115302829 | 1425934727 | 0 | 81,723 vs. 94,344 | −12,621 | `6f91356e9ac33b5cbf684e5a8f82c3bd6efc56adc0c235bccdc28dd4550f5acb` | `54f301cb41006a0051b81e6fc9c7e427e5d3745a9c063cee6eb0abef019b0cf6` |

Raw uncompressed replay SHA-256 values, respectively, are `755e5addd2346e2d9fda34eedeb31e3e6955e2ff82e49e254bf9b6bc8fbdee6f`, `8f9c7504f91b9859f5a7beb4e516e38260876dd6f90728ab79ecb7f6493717ec`, and `b7df4076317cd82cae2eeffd389d3e1607c0dafef1d2591ef75c99579f08e0ae`.

## Findings

### No observed missed-land or funded-opening failure

The static `_funded_land_apply` census, using each actual observation and the exact submitted action, changed no action in any of the three replays (zero activations). All six submitted land purchases succeeded: each candidate acquired NE on day 7; Maher and coolin666 acquired SW on day 10; Tomohiro acquired SW on day 11. Each next observation shows the expected additional unlocked quadrant.

The common step-0 market bundle also executed: 2 COW, 3 SHEEP, one STRAWBERRY seed, and four hires appear in the next observation. After the full step-0 market sequence, remaining cash was $429 for Maher, $424 for coolin666, and $443 for Tomohiro. The opening did spend most of the $3,000 starting cash, but these transactions were funded and completed. The plant-action audit found no PLANT attempt with zero seed.

There was one later planting miss: in coolin666's episode, at step 426 (day 17, hour 18), hand slot 10 attempted to plant MELON at `[0,9]`, where the tile remained `WEED`. The MELON seed count was 1 both before and after, so this lost a scheduled action but did not consume the seed. Maher and Tomohiro had no failed PLANT placements in the archived transitions. This isolated miss occurs well after the early cash reversal and is not evidence that the missed-land repair addresses these losses.

### The repeated gap is early crop and sale timing

All three candidates followed the same opening allocation. At the end of day 0 each had one STRAWBERRY and 19 WHEAT plants; the visible rival had 12 MELON and 8 WHEAT plants in Maher's and coolin666's episodes, and 6 MELON and 9 WHEAT in Tomohiro's. The rivals' first MELON planting occurred at step 7 (day 0, hour 7) against Maher and coolin666, and step 10 (day 0, hour 10) against Tomohiro. The candidate's first MELON planting was later:

| Episode | Rival first MELON plant | Candidate first MELON plant | Rival MELON sell-order quantity, days 10–12 | Candidate quantity, days 10–12 | Candidate first MELON sell order |
|---|---|---|---:|---:|---|
| Maher | step 7, day 0 hour 7 | step 323, day 13 hour 11 | 72 | 0 | step 577, day 24 hour 1, qty 6 |
| coolin666 | step 7, day 0 hour 7 | step 391, day 16 hour 7 | 72 | 0 | step 671, day 27 hour 23, qty 12 |
| Tomohiro | step 10, day 0 hour 10 | step 223, day 9 hour 7 | 54 | 0 | step 481, day 20 hour 1, qty 6 |

These are quantities in recorded market actions; they are not a counterfactual estimate of the orders' realized value. The timing is consistent with the cash reversal: at day 9, candidate/rival cash was $5,244/$4,128 for Maher, $2,340/$2,377 for coolin666, and $2,396/$1,008 for Tomohiro. By day 10 it was $1,777/$19,142, $757/$18,063, and $2,509/$2,738, respectively. By day 12, candidate/rival cash was $4,906/$16,858, $8,535/$22,114, and $7,658/$13,500. The replays show the rivals submitting large MELON sale orders during this interval while candidates submitted none; other sales and shared-market price movements also affect cash.

## Assessment and limits

These losses are best classified from the available traces as an early production and sale-timing deficit, rather than a failed land order or an unfunded opening commitment. The repeated observable difference is that the submitted candidate spends the opening schedule on WHEAT, livestock, and STRAWBERRY while each rival starts MELON much earlier and submits MELON sales from day 10. The candidate's first MELON sale comes between days 20 and 27.

This is a mechanism diagnosis, not evidence that an earlier MELON route would win. The archived games do not reveal the outcome of changing the candidate's schedule: earlier output could alter prices for both farms, and the cash delta includes other production and sales. No counterfactual games were run for this audit. Root's separately planned native candidate comparison is needed to measure whether a broad schedule change improves wins against reacting opponents. The missed-land helper has no actual activation in these three loss traces.

## Reproduction artifacts

- Static census script: `diagnostics/fresh90_loss_audit_20260929/audit_latest_submission_losses.py`
- Machine-readable census: `diagnostics/fresh90_loss_audit_20260929/latest_public_losses_56680167_static.json`
- Episode metadata: `diagnostics/fresh90_refresh_20260929/routes/current_submission_56680167_opponents/summary.json`
- Full replays: `diagnostics/fresh90_refresh_20260929/raw_archive/episode-{115319884,115315638,115302829}-replay.json.gz`
- Funded-land helper evaluated statically: `diagnostics/fresh90_improvement_20260929/candidate_funded_land_v1.py`, SHA-256 `2a4d093a4824c0fac824b292dfa4a93c2403214d74f31b703bfd913daf136eb8`

No game runs, network access, Kaggle operations, or shared agent edits were used for this audit.
