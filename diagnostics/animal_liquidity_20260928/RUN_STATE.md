# Animal liquidity experiment state

2026-09-28 16:24 UTC: exact candidate `32e299fe047a79290d5025b4e2be455ae13d948020beae2d77cb44a7c17dc31e`
was built by appending the pre-existing frozen `layer.py` to exact parent
367d2e76. No policy or gate corrections were needed before outcomes.

The within-day forecast passed 12 comparisons against the native
interpreter (252 transitions), with the explicitly excluded midnight
transition disabled in that comparison. The check covers both seats,
idle and mirrored rivals, and zero/one/two wool sales from the already
saved Yaroslav step-195 state. See `transition_check.json`.

The 12-game frozen development screen completed and passed at 16:25:09 UTC.
Yaroslav is newly won in both seats (+902), with no regressed winning
seats. Root backup of exact 32e299fe is saved. See `RESULTS.md`.

Original-native parity completed and passed all twelve games at 16:30:59
UTC. Rewards and full telemetry match the development games exactly;
all games finish clean DONE/DONE/720. Receipt SHA:
`a71c23a809fee6d19ee15aaccbb2f6c6d2dd82375fb83caeb2a301234a418962`.

The complete 100-game saved-target native regression finished and passed
at 17:01:42 UTC. Unified exec session 81725 is terminal with exit 0 and its
worker/coordinator are released. All 100 games are clean; all parent wins
are retained. Results: **14/30 public-loss sweeps +19/20 top-team sweeps
=33/50**, 66W/0D/34L. These are diagnostic fixed-tape results; no research
promotion is claimed.

The separate 298xxxx independent protocol and helper are prepared with
eleven passing synthetic gate checks, but no reacting game has been
launched. Per root's resource coordination, no new benchmark was launched;
`decem_repair` was notified directly that this worker slot is free. Root
will decide when to launch the prepared independent pilot. No Kaggle
access. Root main and source artifacts are untouched.

Reproduction (each phase writes immutable evidence and rejects an existing
final output):

```powershell
python -X utf8 diagnostics/animal_liquidity_20260928/screen.py prepare
python -X utf8 diagnostics/animal_liquidity_20260928/screen.py transition-check
python -X utf8 diagnostics/animal_liquidity_20260928/screen.py screen
python -X utf8 diagnostics/animal_liquidity_20260928/mechanism.py
python -X utf8 diagnostics/animal_liquidity_20260928/qualify.py parity
python -X utf8 diagnostics/animal_liquidity_20260928/qualify.py full
```
