# Observed-hire recovery — development pass

## 2026-09-28 06:59 UTC

All **24/24** fast diagnostic games complete cleanly. Both separately
backed-up arms rescue Junliang Ye in both seats and preserve every tested
parent winning seat. The other five matchups retain their parent outcomes.
Each rescue finishes at **135,794 vs 132,837**, a **+2,957** margin.

| Arm | Parent margin | New margin | Own cash change | Rival cash change | Margin change |
|---|---:|---:|---:|---:|---:|
| 467a9dfe, main parent | -12,934 | +2,957 | +12,778 | -3,113 | +15,891 |
| 367d2e76, 8dde parent | -16,055 | +2,957 | +20,897 | +1,885 | +19,012 |

Values are per seat and match in both seats. Each run retries two actual
missing hires at step 193, delays eleven worker commands in total and
catches both workers up by omitting one CARE each. No recovery remains
unfilled, crosses the day boundary, or records a policy error. Full traces
and mechanism.json preserve the feeding and plant-survival comparison.

**Pass development and advance to original-native parity; no promotion.**
The 24-game native stage runs in session 35044, two workers. Both full
50-target panels and new independent reacting gates remain required.
These are fixed-replay results, not independent strength or a rank forecast.

- Main-parent candidate SHA:
  `467a9dfec81b0b05a8c80f0b61b3876339cd307fad481af8b571187d72fb7073`.
- Integrated-parent candidate SHA:
  `367d2e7683472af526bdaee5af80c9e7fe59dfb2136475555a2970ef8beccaa0`.
- Screen SHA:
  `22d14914b8aeab81fadb255c58832f08ee1c5b7c9eb3ed65229908342d40badc`.
- Pool SHA:
  `7b89aaeecc54125116021b7271b2195cfea47438ecb35d99ffa51c0b90f8e83d`.
- Native helper SHA:
  `cfdcc03b6bee6f93d9523df871bf6d76949e31ce2b2cfbd5e7306d8d3fa0ca87`.

Root main remains 4ee. The 8dde parent's native pilot remains a separate
experiment. No Kaggle access or new upload occurred.

## 2026-09-28 07:05 UTC — original-native parity passes

All 24 games exactly reproduce fast rewards and full telemetry, with clean
DONE/DONE/720 and no errors. Both arms retain their development rescue and
controls. **Advance to the full 50-target panels, not promotion.** Parity
session 35044 is terminal. Full session **13956** reuses those 24 games and
evaluates the remaining 176 (200 total across two policies), two workers.
Parity receipt SHA:
`190e408a0537811d349c5bdcf3e92e39ead130c6f4609122faf619275f888a3a`.

Mechanism traces confirm all 15 animals are fed on day 8 instead of 11,
and all eight additional strawberries survive (29 plants instead of 21 at
day 9), in both seats. The two omitted CARE actions remain a recorded cost.
No claim about general win rate follows from this replay.

NATIVE_PLAN.md and the fresh 296xxxx panels were frozen at 07:03 UTC, before
any new independent game. The separate four-arm pilot has 512 planned games;
each recovery policy has its own required controls and failure decision.
Ten synthetic stop/gate checks passed. Neither these checks nor native
parity are independent strength evidence. Public-win and loader runners
still need wiring if a candidate reaches those later gates.
