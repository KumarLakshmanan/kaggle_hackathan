# Prospective win-rate reassessment — 2026-09-27

The competition's documented rating objective is match outcome, not the
magnitude of terminal cash differences (README.md, Ranking System). Earlier
Shunki experiments rejected positive win-rate results at an absolute
negative-cash-tail floor. Those experiments and their rejection decisions
remain intact. This new experiment explicitly changes the decision objective
and uses untouched seeds and several reacting policies. It does not reinterpret
the already observed seed blocks as a new validation sample.

Candidate: unchanged `exp_shunki_later_lookup_20260927.py`, SHA-256
`68aad0908c38884aba856373088f1a6ba4a0423df2ee00edbec4c796f8e45fac`.
Incumbent: `main.py`, SHA-256
`489fe8e4e80b03e7e6485b5969f3bec1861fa8389473f361969f064e484f6c7b`.

Freeze 32 fresh native seeds **2631000–2631031**, both seats, 720 turns,
engine 1.32.7, original endogenous shops. Run both candidate and incumbent
against four complete reacting agents: incumbent, previous submitted main
(`08aa268a...`), public Ahmed V35 and public C95. Reload modules per game.
No shop preselection and no fixed future shops. There are 512 games.

Primary outcomes: a seat win = 1, draw = 0.5, loss = 0. A seed block is the
average of both seat outcomes. Compare candidate and incumbent within the
same opponent/seed; never substitute cash-margin size for game outcome.
Report both per-opponent and pooled win points, plus paired seed-block
bootstrap uncertainty for the pooled difference (resample whole seeds).

Further promotion requirements, frozen before new outcomes:

- All games finish DONE/DONE and candidate calls stay under the one-second
  local screening threshold (Kaggle file-loader parity is already verified
  for these exact bytes and will be checked for the final promoted bytes).
- Candidate earns at least 22/32 seed-block win points against each of the
  two submitted-main policies.
- Pooled candidate win points exceed incumbent's, and the 95% paired
  whole-seed bootstrap lower bound for the difference is positive.
- Against each public policy, candidate loses no more than 4/32 seed-block
  win points relative to incumbent.

Cash margins, own/rival cash changes, shop changes and large losses remain
diagnostics. They cannot independently overturn the primary win-rate gate.
Passing earns consideration for promotion as a measured incremental
improvement; it does not demonstrate top-10 or all-100 attainment.

The same exact candidate has already completed the frozen saved top-100
panel: 80/100 paired route wins, 160/200 seats versus incumbent 66/100 and
132/200. Those fixed-tape results are regression evidence, not independent
live-policy validation. Do not rerun or count them as fresh data.

Preserve root-folder backup before replacing main. The user's latest fresh
explicit request conditionally authorizes one upload if this new independent
evaluation earns promotion. Refresh live status and record the latest-two
submission consequences before uploading. Never report a predicted rank
as an observed result.
