# Missing-pair coverage addition — development rejection

2026-09-27 02:20 UTC. Candidate a4d0a896 adds newly downloaded episode
113940892 to the otherwise frozen a2 market-order candidate. Both seats of
all three affected saved opponents finished DONE/DONE, with zero queue errors.

| Team | Parent a2 margins | Coverage candidate margins |
| --- | ---: | ---: |
| Arda Ceylan | +68,654 / +70,934 | +19,355 / +19,355 |
| ymg_aq | -4,997 / -4,176 | -7,459 / -7,459 |
| Breaking1800 | -12,806 / -12,806 | -3,758 / -3,758 |

Decision: reject the exact coverage addition. The existing Arda wins hold,
but neither loss becomes a both-seat win, so the development gate fails.
No wider regression or conditional native tests were run for this addition.
The parent a2 qualification continues unchanged.

The source fills a missing shop label, but that is not evidence of a stronger
policy for all continuations. Its third shop is YARN. A follow-up static audit
found 71/72 unit-command differences versus the parent's route during turns
144–215, preventing a late splice after observing the third shop. It has only
one new sheep purchase after turn 216; a broad late sheep-to-cow expansion is
not supplied by that tape. Keep the raw source and prefix audit for research.

Evidence: development.json; parent top50.json; source manifest and
pizza_ice_prefix_audit.json in shunki_source_refresh_20260927_0213.
Root backup: main_candidate_pizza_ice_coverage_20260927_a4d0a896.py.
