# Fresh top-50 replay panel — 2026-09-27

Downloaded the latest completed public replay from each of the 50 teams
in the frozen leaderboard snapshot. The 50 distinct action hashes cover
43 public episodes; no download failed. Selection used the team's higher
scored active submission and was not conditioned on replay outcome.

| Policy | Seat wins | Both-seat matchup wins |
| --- | ---: | ---: |
| Current main, `489fe8e4...` | 64/100 | 31/50 |
| ICE/BRUNCH schedule candidate, `3cc0f69f...` | 84/100 | 42/50 |

All 200 games completed DONE/DONE with original, endogenous shops. The
candidate gained 15 sweeps and lost four incumbent sweeps. Eight matchups
remain losses in both seats: DECEM, Majkel1337, seek inspiration, We wanna
be tomatos, ymg_aq, marwar22, Snorlax, and Breaking1800. Exact seeds,
hashes, margins, and artifact paths are in `comparison.json`.

Decision: the candidate passes this regression comparison and its separate
native reactive validation, but the user's all-50 target is NOT complete.
Keep investigating the eight failures before choosing the next upload.
These are fixed recorded actions, not executable top-team opponent policies
and not evidence of a guaranteed live leaderboard rank.

The DECEM trace identifies 24 FEED commands with no carried wheat and 13
animal escapes. Follow-up worker tracing shows scheduled wheat harvests
on LOCKED southern land. This points upstream to failed land expansion,
not merely late market wheat purchases. See `decem_fulltrace.json.gz` and
`decem_feed_worker_trace.json` for native observations.
