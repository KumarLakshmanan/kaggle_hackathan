# Public Step1009 independent pilot — 27 September 2026

Official read-only Kaggle refresh found the same new exact source in
tetsutani/demand-preserving-turn-sale-timing and the Guru Master Engine V4
notebook. Treat these as one policy, not two independent sources or trials.
Exact main hash: 55be5d5f124c8daaaa63c1a29ba4aab096004909666f04748007603c67b7d2a8.
The archive, Apache-2.0 LICENSE and NOTICE are preserved. Only literal
archive extraction was used; notebook cells were not executed. Both embedded
exec strings were statically inspected; the only file-read call is behind
a local path=None guard, and there are no network imports. The production
agent and Kaggle's final callable are the same Step1009 function.

Freeze exact unchanged source plus root candidate and backup before games.
Do not infer current strength from notebook titles, reported ratings or
comparisons with older public policies. Main remains uploaded c68.

Run fresh seeds 2697000–2697007, both seats, against exact reacting c68:
16 games, engine 1.32.7, 720 turns, original native shop generation. Feed
both agents a configuration copy with seed=None, matching remote competition
configuration; the native environment still receives the real seed. The
public source's active opening mode is HybridOpening; its dormant Mixed
mode must not receive a hidden native seed either. Record both-seat results,
full completion, timing, final-entry telemetry, and errors in all report dicts.

Pass only at >=12/16 win points (draw=0.5), all DONE/DONE over 720 frames,
zero runtime/strategy errors. Run all 16 pilot games and preserve every loss.

Only if passed, run both recorded panels: today's 100 current teams and the
older 50 regression teams, both seats. Require >77 current100 sweeps, >36
current50 sweeps, and >=44 older50 sweeps. Report gains and regressions. Stop
remaining work for early rejection when a fully completed required cohort
fails a gate; do not claim a complete larger panel in that case.

If passed, predeclared fresh native confirmation uses seeds 2698000–2698015:
old c68 and unchanged Step1009 versus c68, 1f221922, historical 489fe8e4,
and public C95, both seats (256 games). Mask configuration.seed for all
agents. Require >=24/32 new points versus c68, no per-reference point
regression, all DONE and zero errors, and positive lower 95% percentile
bootstrap bound on pooled paired-seed win-point gain (10,000 resamples,
random seed 2698099; each sample retains both seats and all references).

Require both-seat file-path parity before promotion and preserve attribution.
Any subsequent Kaggle upload requires new explicit authorization. This pilot
and its intermediate gates do not redefine the full all-top50/live-top10 goal.
