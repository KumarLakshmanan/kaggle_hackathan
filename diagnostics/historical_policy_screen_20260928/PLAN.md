# Historical alternative policy screen — 2026-09-28

## Frozen scope

Run three previously saved, complete standalone alternatives against five
already downloaded current-top-20 action tapes: the 4ee failures DECEM, Boey,
and Vadim Vasilenko, plus current winning controls DSM and Majkel1337. Run each
alternative in both seats on the source seed: 3 candidates × 5 fixtures × 2
seats = 30 local games. Use installed Kaggriculture engine 1.32.7, the exact
saved 719-action route for each fixture, and the unmodified native shop and
market response from that seeded engine. Capture the candidate's observation
at step 48 for a possible early state-trigger audit.

These are fixed-action replay diagnostics, not games against the opponents'
reacting policies. No candidate tuning, route edits, `main.py` edits, Kaggle
checks, downloads, or uploads are in scope.

## Frozen source hashes

The current incumbent is `main.py`, SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Each candidate must match the recorded digest before and after every game.

| Candidate | Standalone file | SHA-256 | Selection note |
| --- | --- | --- | --- |
| V43 decoded policy | `main_v43_current.py` | `69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3` | Decoded standalone payload produced by `kaitofukami_v43_code.py`; do not execute that build wrapper because it writes `main.py`. This is not the distinct Ahmed V43 file from the older physical-gap pilot (that source path is unavailable in this workspace). |
| V48 complete policy | `diagnostics/public_kaito_v48_20260926/full_policy_local_screen.py` | `dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a` | Full decoded policy used for the prior V48 native pilot, not the route-data-only proxy. |
| Search v2 | `kaggriculture_search_agent_v2_20260926.py` | `5e4023df7b78d62e86df068c4ae54c7c95b2d29a0908be680b3332a3019fa6da` | Retained search version with the best completed fresh holdout mean among the saved search variants (still 0/4 paired wins against reacting incumbent). |

All three files parse as Python and expose a top-level `agent` callable.
The V48 and search sources have previous engine-1.32.7 native pilots. The
older physical-gap pilot identified a different Ahmed V43 file
(source hash prefix `919fc1d6`); that source path is not present here, so its
seed-0 result is not attributed to this chosen V43 decoded payload. Compatibility
for the selected V43 file is checked by the frozen engine-1.32.7 games. The
main file hash will also be checked before and after the complete screen.

## Frozen fixtures and baseline

Source panel: `diagnostics/current_top20_20260927_172258/`, manifest SHA-256
`4cf340e5ac28eec35dc202a459c3910cee8da1c692324b41ebd3f619f70230ea`,
assessment SHA-256
`9d328af8115e27acb45fd4251a1bbc1fde5fda8c793c027b46792a54c04cbeb7`.
Each route and raw replay hash must match that manifest before testing.
Current 4ee baseline outcomes are from the existing assessment, both seats.

| Role | Team | Rank | Episode | Seed | Saved action SHA-256 | 4ee baseline seats |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Target | DECEM | 1 | 114267880 | 1390733823 | `a326e4f9e779ce21762e8cac5a0058884a1676271f296bf4c2291180b0175226` | loss / loss, −62,163 each |
| Control | DSM | 2 | 114267880 | 1390733823 | `f3ef1eb69b43dcb3051235fedbc71b331966972cc92d17f8b877acfd1066bc30` | win / win, +33,114 each |
| Target | Boey | 3 | 114266440 | 1042173125 | `62fff0dbd859fe5cb99d2fff2a126731f740f3345f4d1b7e8c1e3fab43d81c97` | loss / loss, −20,873 each |
| Target | Vadim Vasilenko | 5 | 114265033 | 931842424 | `d7a9a8d5e3b6feab6b21a09796f70972668a1a9d1fc9ba4ae316479efaf8a741` | loss / loss, −400 each |
| Control | Majkel1337 | 6 | 114263239 | 1525050266 | `35753ab4044c3192ef625f780d76a41a6ffe4d4f2658084f64bdfc1289df2282` | win / win, +17,814 each |

DSM is a useful same-episode/seed control for DECEM; Majkel is a separate
current winning control. The exact route paths and replay SHA-256 values are
read from the frozen panel manifest and copied to the screen output.

## Frozen readout and gates

- A game is valid only if both agents finish `DONE` and the engine produces
  720 frames. An invalid game aborts interpretation; do not replace its seed.
- A **target seat flip** is a strict candidate win (`margin > 0`) on any of
  the three target seats where 4ee currently loses. Report draws separately.
  Also report paired sweeps for each target.
- A **control regression** is a draw or loss on any of the four control seats
  where 4ee currently wins. Report candidate control outcomes and margins.
- If a candidate flips at least one target seat, perform the requested
  descriptive trigger-feasibility audit using only its captured step-48
  observation. Freeze the observable key as: first two unlocked shops,
  candidate farm hands and unlocked land, own-cash bucket `floor(money/5000)`,
  counts of WHEAT/CARROT/TOMATO/STRAWBERRY/MELON/GOOSE/COW/SHEEP, and private
  shed counts for those same items. Do not use episode, seed, team, action
  hash, replay outcome, or any later observation. Consider the union of keys
  observed on flipped target seats as a hypothetical state guard. Check
  whether either seat of a control matches one of those keys, and whether the
  alternative remains a strict win on every matching control seat. This is
  only a heuristic on five frozen tapes; no trigger is promoted from this
  sample.
- **No promotion gate exists for this screen.** Even a target flip with no
  observed control regression only justifies a new, separately predeclared
  local reacting-reference experiment. Fixed tapes cannot establish a
  policy gain.
- Check that candidate and `main.py` hashes are unchanged at completion.

## Reproduction

`python -X utf8 diagnostics/historical_policy_screen_20260928/screen.py`

Plan frozen before any candidate-vs-top-20 screen games.
