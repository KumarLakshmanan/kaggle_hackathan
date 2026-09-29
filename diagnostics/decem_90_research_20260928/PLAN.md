# Joint current-market search — frozen 28 September 2026

Source is exact uploaded experimental 367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0. Root main and all older studies are preserved. This folder owns its candidate and receipts only. No Kaggle access.

DECEM episode 114267880 loses by 9,085 in both seats under this source. The source retains 19/20 top-team and 13/30 public-loss sweeps. The 91 earlier-BRUNCH schedule family all lost, best -5,114; those rejected routes will not be retested here. The existing source optimizes order insertions separately from balanced quantities; quantity optimization is disabled on DECEM because the farms differ at turn 144. The source's native telemetry records zero quantity turns but 90 queue turns and 45 iterated queue turns. Its small localized empty-plant command gap does not imply 9,085 of recoverable production.

## Single fixed candidate

Append one generic current-observation market wrapper after the source. From turn 144, when overage is at least ten seconds, jointly consider balanced WHEAT/FERTILIZER quantity edits and moving existing SELL/BUY_PRODUCT orders to any queue position. Quantity deltas are +4,+12,+24,-4,-12,-24, both first existing buy and first existing sell remain within 1..100. No orders, farming commitments, land, workers, seeds or future information are added. The source schedule remains the fallback.

Use depth two and width two; evaluate at most 32 distinct proposals at each depth (64 per turn), in deterministic generation order: quantity edits, then order moves by original index/destination. Score against the original completed source queue under explicit idle, current-queue mirror and raw-queue mirror forecasts. Require exact own resource signature, own cash nonregression in all scenarios, and exact rival signature plus relative cash nonregression in non-idle scenarios. Rank by minimum relative gain, summed relative gain, minimum own gain; keep incumbent on ties. Each retained node must meet those constraints. Stop if no improving node is found. These are hypothetical opponent models and do not prove actual market preservation.

## Development gate

Freeze standalone bytes before running outcomes. Six fixtures, both seats, one worker: DECEM, leave you 114289228, Boey 114266440, Vadim Vasilenko 114265033, Majkel1337 114263239 and Junliang Ye 114254310. Controls are exact integrated rows in observed_hire_recovery_20260928/native_full.json. Require DONE/DONE/720, zero errors, all source winning seats preserved, and DECEM newly won in both seats. Report own/rival/relative changes separately. Reject if any condition fails; do not tune this family or expand its gate after results.

On pass only, validate the same twelve games in original native framework, all 50 saved targets both seats, and all 54 public wins. A separately frozen fresh reacting protocol and both-seat file loader remain mandatory for research promotion. Saved action tapes are diagnostic development, not independent strength. No upload is authorized.
