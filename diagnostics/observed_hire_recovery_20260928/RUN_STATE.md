# Observed-hire recovery — independent pilot

## Terminal checkpoint — 2026-09-29 00:47 IST

The latest frozen pilot result is in `native_pilot.json`: terminal at499/512
by the planned early-rejection rule. All499 unique games are clean. Both
repair candidates have zero distinct activation seeds, while only one
possible seed remains against the required two. The main-parent candidate
467a9dfe has89/124 win points versus the 4ee control's90/126 and zero paired
margin change; integrated candidate367d2e76 has87/124 and loses83,918 paired
margin coins over124 matched games. Both are rejected. The remaining13 jobs
were cancelled by the frozen runner; do not resume them. No worker or native
lock remains. See the dated decision and hashes in `RESULTS.md`.

Root main remains the exact4ee baseline. The latest uploaded a44 artifact is
not changed by this experiment. The separate a44-bound Goose and pasture
candidate studies are staged in their own directories.

## Resumed checkpoint — 2026-09-28 16:22 UTC

Session 82809 no longer exists, its recorded coordinator PID 31648 is
absent, and no matching Python process is running. The interrupted run
preserved **61 unique games** without a terminal native_pilot.json.
The stale lock was archived only after these checks. See
`resume_20260928T162201Z.json` and `stale_native_lock_20260928T162201Z.json`.

Exact-checkpoint resume is now unified session **31417**, two workers:

```powershell
python -X utf8 diagnostics\observed_hire_recovery_20260928\native.py pilot --workers 2
```

It validated frozen hashes and loaded 61/512 rows. Keep this live run;
do not restart from zero or modify the plans/helper/candidates. Research
gates and experiment scope are unchanged. The user's new 90% priorities
are documented separately in `diagnostics/goal90_20260928/BASELINE.md`.

## Authoritative checkpoint — 2026-09-28 07:38 UTC

Full session **13956** is terminal/pass: 200/200 clean native games,
exact affected-case parity and no prior winning-seat regressions.
Main-parent 467a9dfe has **18/50** sweeps (1/30 losses +17/20 top teams).
Integrated 367d2e76 has **32/50** (13/30 +19/20), 64W/0D/36L.

Operational file-loader session **47717** is terminal/pass: eight games,
Junliang and Boey in both seats, every action/reward exactly reproduced.
The explicit upload request was consumed by **56633591**, exact 367d2e76
named main.py, at **13:05:56 IST / 07:35:56 UTC**. Kaggle verified PENDING
at 07:35:59 UTC, no score. One attempt, return code zero, receipt saved in
`diagnostics/upload_hire_recovery_20260928_367d2e76/`. Do not repeat.

Independent observed-recovery qualification now runs in unified session
**82809**, three workers:

```powershell
python -X utf8 diagnostics\observed_hire_recovery_20260928\native.py pilot --workers 3
```

512 initial jobs; keep the frozen per-candidate early-stop, activation and
win-point gates. Do not duplicate the run or change hash-bound inputs.
Only complete passing candidates may enter confirmation, then the separate
54-public-win and final loader research gates. No strength pass is inherited
from the operational upload checks. The parent's separate pilot 82556
stopped/rejected at 368/384 games: 8dde cannot pass nonregression versus
reacting 4ee even if all its remaining games win. Keep this source rejection
distinct from the new recovery study and do not alter the frozen gates.
Root main stays 4ee. Seventeen public-loss fixtures and DECEM remain
unresolved by the combined upload; the overall goal is still incomplete.
All running/pending statements below are historical.

## Superseding upload instruction — 2026-09-28 07:22 UTC

The user freshly requested one upload of the new combined main.py. Stage
exact **367d2e76** as main.py in
`diagnostics/upload_hire_recovery_20260928_367d2e76/`, retaining the root
backup and 4ee research main. Full saved-panel session 13956 and separate
operational loader session 47717 must pass before that one experimental
upload. Reacting qualification is pending. The frozen research plan is
unchanged; its old no-upload statement is superseded only by this request.

Final research preservation helpers are now implemented in
`diagnostics/native_preservation_20260928/`. They require the exact passing
independent confirmation receipt before all 54 public wins, then loader
checks; these gates have not run or passed. The upload-specific loader
does not replace those research requirements.

## Superseding checkpoint — 2026-09-28 07:05 UTC

Native parity **35044** is terminal/pass: all 24 games clean, exact reward
and telemetry parity, both rescue/control gates passed. Full panels now
run in session **13956** via `qualify.py full --workers 2`: 200 games
across both candidates, reusing the 24 completed parity rows. Do not report
expected 18/50 and 32/50 counts as completed results until native_full.json
passes.

The independent NATIVE_PLAN.md, seed manifest and native.py are frozen;
ten synthetic checks passed. After full validation, run `native.py pilot
--workers 3` (512 initial jobs, early rejection tracked per candidate).
Never inherit the parent's native outcome. Public-win and loader runners
remain to be wired if any candidate reaches those stages. Main unchanged.

Both frozen arms pass the 24-game fast screen: Junliang Ye is newly won
in both seats (+2,957 each), and no tested parent win is lost. Both files
are backed up in the root: 467a9dfe (main parent), 367d2e76 (8dde parent).

Screen session 79912 is terminal. Active native parity session **35044**:

```powershell
python -X utf8 diagnostics\observed_hire_recovery_20260928\qualify.py parity --workers 2
```

After a complete passing receipt, run `qualify.py full --workers 2` for
both full panels (200 native games, reusing the 24 parity rows). No new
combined full-panel total is confirmed yet. A separate reacting plan and
runner still need freezing before new independent outcomes. No existing
native component/parent gate transfers to these exact files.

Independent parent 8dde pilot continues separately in **82556**. The
preemptive hire-funding rule is terminal/rejected (zero activations);
this is a distinct observed-failure and delayed-worker feedback rule.
Main stays 4ee; no Kaggle access or upload is authorized.
