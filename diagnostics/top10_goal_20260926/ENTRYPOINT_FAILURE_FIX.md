# Kaggle entrypoint failure and local fix — 2026-09-26

## Live failure

User-requested submission **56568576** uploaded local SHA-256
`0e2c30f44ca7a6e0181e38a8d378af1f266ffacaaef33983a1673061797d647a`.
Its validation replay ended 3,000–3,000 with both agents issuing only `PASS`.
Its first public replay, episode 113552915, lost 3,000–101,825 against
Jurgen Sinjari; both status values were `DONE`, but all our 719 recorded
actions were `PASS` and we made no market orders. The 04:13 UTC displayed
public score was 478.3 after that one public episode. This is a submission
execution failure, not evidence that the intended policy lost by strategy.

## Cause and exact source change

The installed Kaggle environment's `get_last_callable` executes the *last
callable inserted into the file's global namespace*. The old uploaded source
ended with `_frontier_h6_clip_rescue_agent` as that callable. The new
44-line mirror gate added `_clone_physical_match` after the global `agent`
and `kaggle_submission_agent` keys had already been inserted. Reassigning
those existing keys did not move their namespace order. Thus Kaggle selected
`_clone_physical_match`, which returns a Boolean, and the game treated it as
an empty action. The direct test harness imported `module.agent` explicitly,
so it had missed the file-loader behavior.

`build_entrypoint_fix.py` made a separate candidate by appending one unique
final callable, `kaggle_main_entrypoint`, which delegates to the unchanged
`agent`. It changed no strategy logic. Candidate SHA-256:
`08aa268af0885f54fb515f801ec49c2022c8e0073870bbd3d48dda03ce142863`.

## Verification and decision

`entrypoint_parity.py` confirmed the loader selected
`_clone_physical_match` from the uploaded source and
`kaggle_main_entrypoint` from the candidate. On new native seed 2610901,
both seats, the candidate loaded by **file path** produced the same exact
terminal cash as the direct-callable harness: 92,681 versus 92,097, both
`DONE`. The first market action was nonempty. The uploaded source loaded by
file path remained at 3,000 coins and issued `PASS`, reproducing the live
failure locally.

**Promote the exact entrypoint candidate locally.** Before replacement,
the uploaded source was backed up byte-for-byte as
`main_before_entrypoint_fix_20260926_0e2c30f4.py`; the earlier
`main_uploaded_mirror12_20260926_0e2c30f4.py` is another exact backup.
Promoted `main.py` SHA-256 matches the candidate `08aa268a...`.
`entrypoint_promoted_smoke.py` parsed the final source, checked the selected
callable and tested the final `main.py` **filename** under Kaggle file-path
loading on a second new native seed 2610902, both seats. Results exactly
matched the candidate path, 97,689 versus 97,395, both `DONE`, with a
nonempty first market action.

The previously completed 100-route and reactive strategy tests still apply
to the unchanged delegated `agent` logic. The local fix has **not** been
uploaded to Kaggle. `AGENTS.md` requires a fresh explicit user request for
each upload. Raw evidence: `entrypoint_parity.json`,
`entrypoint_promoted_smoke.json`, and the downloaded validation and first
public replays in `diagnostics/live_submission_56568576_20260926/`.
