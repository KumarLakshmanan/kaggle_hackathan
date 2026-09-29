# Reactive pilot results — 2026-09-29

All 96 predeclared games completed DONE/DONE at 720 frames with no policy
errors. The three policies (last upload a44, parent 6a, and ebf candidate)
each scored **16 wins, 10 draws, and 6 losses** over the same 32 scenarios.
All paired results, own rewards, rival rewards, and margins were identical.

| Reacting opponent | Per-policy wins / draws / losses |
| --- | --- |
| Current root main 4ee | 1 / 4 / 3 |
| Parent 6a | 1 / 6 / 1 |
| Public Ahmed V35 | 6 / 0 / 2 |
| Public C95 | 8 / 0 / 0 |

The candidate's Pet gate activated in zero games. The incremental Pet result
is `inconclusive_no_activation`. Each whole-seed point delta was zero. The
primary requirement for strictly more pooled points failed (21 versus 21).
The separate frozen requirement that every tested call take less than one
second also failed. The largest recorded call was 16,369 ms in the old a44
arm; slower calls occurred in the candidate arms as well. This is a failure
of the deliberately stricter screen, not an observed native timeout: all
games finished and Kaggle also provides a cumulative overage budget.

**Decision:** reject research promotion and do not start the conditional
256-game confirmation. Keep this receipt and its gates unchanged. This
pilot provides no evidence of a rating gain or top-10 probability. A
separate user-requested experimental upload requires the corrected guarded
artifact's preservation and native/file-loader checks, and must be reported
as experimental. Root research `main.py` stays 4ee.

Evidence: `outcome_receipt.json`, SHA-256
`86d70abbf809baf29c6227141036624131856bed40b7f04664f13ba7093693c9`;
frozen manifest SHA-256
`f615612d6dfd6d2208f8615d56d8d5f702bbfa6da108be99f70ff661ff5e899f`.
