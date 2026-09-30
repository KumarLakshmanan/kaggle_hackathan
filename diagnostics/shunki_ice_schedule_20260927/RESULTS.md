# Complete ICE/BRUNCH schedule repair — 2026-09-27

Candidate SHA-256:
`3cc0f69fcb9f6a8bee17bf6789f0f321a17f0d47324c462def1e783d6921a603`.
The change replaces seven route-map entries pointing at episode 113445495
with episode 113383763, already embedded in the candidate. The first 241
actions match exactly, and all nine affected route transitions pass prefix
compatibility checks. No other source schedule was replaced.

## Development

Both seats of all five known ICE/BRUNCH top-100 replay routes completed
DONE/DONE. Four losses became wins; the existing win stayed unchanged.
This is familiar replay development evidence, not independent validation.

## Independent native confirmation

The outcome-blind scan examined only the first 144 turns on sequential
fresh seeds starting at 2632000. It found the first eight qualifying
ICE/BRUNCH seeds within 160 scans. The prefix-only scanner reproduced a
previously measured native seed before being used for selection.

| Reacting rival | Original candidate | Repaired candidate |
| --- | ---: | ---: |
| Current submitted main | 6/16 seat wins | **16/16** |
| Previous submitted main | 6/16 seat wins | **16/16** |

All 80 games including controls were DONE/DONE. Five of eight pairs against
current main exposed the changed branch; the three Pizza third-shop cases
already used the healthy schedule. First-three-shop sequences matched in
all 16 old/new paired comparisons across the two rivals. Summed own cash
increased 1,038,552 coins and paired margin increased 1,617,948, reported as
diagnostics rather than the primary outcome. Maximum new-candidate call
was 7.67 ms on this panel. Every prospectively recorded confirmation gate
passed; its rule clarification happened before any confirmation-seed scan.

## Kaggle loader

The file loader chose `kaggle_shunki_ice_schedule_entrypoint`. On selected
native seed 2632020, file-path and direct-call games matched exactly in
both seats: own 125,160, rival 119,974, DONE/DONE. The source hash matched
the build manifest. See `candidate_parity.json`.

**Decision: candidate passes native branch confirmation and loader checks.**
The user's newly requested fresh top-50 comparison is running separately.
No current claim of 50/50 replay wins or live top-10 rank. No main edit or
upload yet. Evidence: `PLAN.md`, `build_manifest.json`, `development.json`,
`seed_selection.json`, `confirmation.json`, `candidate_parity.json`.
