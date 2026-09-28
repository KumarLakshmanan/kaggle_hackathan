# Main vs new candidate — local upload review

Updated 2026-09-28 01:56 UTC. Strategy research used saved local data. Only the requested upload and its submission-list verification accessed Kaggle; no leaderboard or replay refresh.

## Verdict

**Research verdict: not qualified for promotion. Uploaded experimentally by explicit user request.** It improves the fixed-reply development panel, but it has not met the full 30-loss / top-20 objective. The native pilot was stopped after 68 distinct games because its frozen reference-specific nonregression gate became impossible. Against the public market policy, main won all ten completed games while the candidate lost all ten. Even winning all six remaining games would not pass. **Reject this exact candidate for research promotion.**

The user explicitly requested upload after the review. The exact candidate was uploaded as **submission 56625741**, dated **2026-09-28T01:54:52.393000 UTC**; status was **SubmissionStatus.PENDING** at verification. This is an experimental submission by request, not a qualified promotion. Current `main.py` remains unchanged. No leaderboard score or rank can be inferred from these replay counts.

## Files

- [New standalone candidate](H:/hackathan/main_candidate_observable_opening_20260928_fb6c5413.py) — SHA-256 `fb6c54136017eccc9df2652d2826a14346520c6c0d51ce855321ff51be6693f2`.
- [Current main.py](H:/hackathan/main.py) — SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`; exact previously uploaded 4ee artifact, submission 56609430.
- [Research memory](H:/hackathan/agent.md) — the detailed version history, decisions and reproduction references.
- [Readable candidate builder](H:/hackathan/diagnostics/opening_probe_v2_20260928/build_selector.py) and [opening changes](H:/hackathan/diagnostics/opening_probe_v2_20260928/build.py).

The candidate is 1,946,837 bytes versus 1,859,787 for main. Its root-folder copy is byte-identical to the tested candidate in the diagnostics directory.

## What changed

| Area | Current main | New candidate |
|---|---|---|
| Farming plan | 145 saved complete schedules selected by revealed shops, with compatible special branches | Chooses either the existing schedule policy or the V43 early-MELON / SHEEP policy |
| Initial investment | Commits at turn 0 to the incumbent animals and seed | Uses a common first action, then commits after observing the rival's first action through public state |
| Opening choice | No V43 opening choice | V43 when rival cash is over 1,000 and inferred net initial WHEAT buying is at most eight; incumbent otherwise |
| Information used | Current observations and revealed shops | Also uses first-turn public rival cash and shared market inventory; no rival private inventory, identity or future shops |
| Incumbent market behavior | Sale ordering, purchase ordering, two-pass queue search and guarded quantities | Preserved inside the incumbent branch; V43 retains its own policy |
| First three turns | Original schedule | Reorders two farmer actions and defers fixed-price purchases; verifies exact incumbent state at turn 3 |
| Error reporting | Existing market-layer counters | Adds selected-arm telemetry and detection of V43's otherwise hidden fallback exceptions |

Both complete arms share their turn-0 action. The rule was selected using all 50 saved fixtures, so its replay improvements are development results. The preservation of incumbent state has been verified against fixed replies; the reacting tests check whether a rival responds differently to the changed opening.

## Same saved replies, both seats

| Test | main.py | New candidate |
|---|---:|---:|
| 30 saved public-loss replies won in both seats | 0/30 | **7/30** |
| Saved top-20 replies won in both seats | 17/20 | **17/20** |
| Total fixtures won in both seats | 17/50 | **24/50** |
| Individual seat games, wins / draws / losses | 34 / 0 / 66 | **49 / 0 / 51** |
| Incumbent winning seats lost | — | **0** |
| Packaged games completed | Baseline verified | **100/100 DONE/DONE/720** |
| Packaged results equal selected development arms | — | **100/100** |

Recovered loss replies: high frequency farming, Dieter, Vlas Veles, two distinct Ghost Rule episodes, leave you and Navier-stokes. offhand wins only one seat and is not counted as a repaired fixture. DECEM, Boey and Vadim Vasilenko still lose both seats in the selected candidate.

The summed cash-margin change is **-258,954 coins**, despite 15 additional seat wins. This is reported as diagnostic evidence; the frozen promotion objective prioritizes wins/draws/losses. The 50 fixtures cover 48 unique source episodes and should not be treated as 100 independent samples.

Evidence: [integration results](H:/hackathan/diagnostics/opening_probe_v2_20260928/integration.json), [arm screen and selection](H:/hackathan/diagnostics/opening_probe_v2_20260928/RESULTS.md), and [frozen local corpus](H:/hackathan/diagnostics/loss_class_20260927/local_target_manifest_180951.json).

## Independent local comparison

The native pilot was stopped after 68 distinct games because its frozen reference-specific nonregression gate became impossible. Against the public market policy, main won all ten completed games while the candidate lost all ten. Even winning all six remaining games would not pass. **Reject this exact candidate for research promotion.**

| Reacting reference | Main W/D/L | Candidate W/D/L | Completed per file |
|---|---:|---:|---:|
| 4ee | 1/10/1 | 1/10/1 | 12 |
| v43 | 12/0/0 | 12/0/0 | 12 |
| market | 10/0/0 | 0/0/10 | 10 |

All 68 distinct completed games finished DONE/DONE/720 with no recorded errors. Repeated checkpoint keys receive no extra weight.

The references are current 4ee, standalone V43, and the distinct public market policy. The exact hashes, seeds and gates were frozen in [NATIVE_PLAN.md](H:/hackathan/diagnostics/opening_probe_v2_20260928/NATIVE_PLAN.md) before native outcomes. Cash gains alone cannot substitute for a paired win-point improvement.

## Research considered, and what was retained

| Research direction | Evidence and decision |
|---|---|
| Existing 4ee market optimizers | Kept intact in the incumbent branch; this is the known submission artifact. |
| Standalone V43 | Won 13/30 saved loss replies in both seats, but regressed top-team controls. Retained as an optional opening basis, not a universal replacement. |
| First common-opening experiment | Farm-state checks missed shared-market and cash differences; both arms lost old top-team wins. Rejected. |
| Revised common opening | 110/110 prefix checks and exact incumbent parity in all 100 arm games. Its conservative visible-state selector earns the current 24/50 development result. |
| More aggressive selector | Reached 29/50 development sweeps but lost two incumbent winning seats. Rejected by the frozen preservation gate. |
| Three complete route replacements | Ten clean games; DECEM deficit shrank from 62,163 to 5,114 per seat, but none of DECEM/Boey/Vadim became wins. Rejected, not merged. |
| Broader compatible-route pool | An existing research run is testing 32 complete compatible schedules. Its 128-game development search is incomplete and contributes no qualified changes to this file. |
| Land funding, early workers and terminal cleanup | Earlier tests failed reacting or rescue gates, or found too little recoverable production. Not merged into this candidate. |
| Broad wheat cap / earlier product sales | Saved event audits did not justify a repeatable competitive gain. Not merged. |
| Independent search / commitment controllers | Prior reacting tests exposed funding, travel, feed and execution gaps. Preserved as research; not merged into the upload candidate. |

Detailed evidence is retained in [agent.md](H:/hackathan/agent.md), [opening v1](H:/hackathan/diagnostics/opening_probe_20260928/RESULTS.md), [V43 loss screen](H:/hackathan/diagnostics/v43_loss_screen_20260928/RESULTS.md), [route reassessment](H:/hackathan/diagnostics/compatible_route_reassessment_20260928/RESULTS.md), and [search-agent findings](H:/hackathan/diagnostics/search_agent_20260926/RESULTS.md).

The native pilot was briefly launched by two chats using the same candidate and seeds. The duplicate launch was stopped. Raw checkpoint lines are retained, but repeated job identities count once, and matching non-timing fields are required. A positive strength pass requires the full planned block; this pilot was rejected early only because the frozen gate had become mathematically impossible.

## Upload checks

- Python compilation and local Kaggle callable selection passed: `kaggle_observable_portfolio_entrypoint` is selected, avoiding the previous helper-function entrypoint failure.
- Full direct-call integration passed in both seats with zero recorded errors.
- Independent strength qualification is reported above; a failed pilot rejects the current bytes.
- The untouched confirmation panel, regression against the 54 saved public wins, and full both-seat file-loader games have not passed for this candidate.
- The full requested endpoint remains **30/30 saved losses and 20/20 top-team replies won in both seats**. This candidate does not meet it.

Keep the new file for research and keep current main in place. Upload only a separately qualified version following a fresh explicit upload request.
