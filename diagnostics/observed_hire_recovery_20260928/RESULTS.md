# Observed-hire recovery — development pass

## 2026-09-29 00:47 IST — independent pilot rejected

The frozen reacting pilot stopped at **499/512** under the preregistered
early-rejection rule. All499 rows are unique and clean (DONE/DONE/720, no
policy errors). Both repair arms recorded zero recovery activations. At most
one distinct active seed remained possible, below the required two, so the
runner cancelled the remaining13 games. The terminal summary correctly has
`terminal: true`, `complete: false`, and `passed_any: false`; this is an
intentional early rejection, not a completed 512-game panel.

| Arm | Candidate W/D/L | Control W/D/L | Candidate points | Control points | Paired margin delta | Decision |
|---|---:|---:|---:|---:|---:|---|
| `repair_main` 467a9dfe vs4ee | 65/48/11 (124) | 65/50/11 (126) | 89 | 90 | 0 (124 matched) | Reject: no activation, no pooled win improvement |
| `repair_integrated` 367d2e76 vs4ee | 65/44/15 (124) | 65/50/11 (126) | 87 | 90 | -83,918 (124 matched) | Reject: no activation, fewer wins and worse market-reference result |

For `repair_main`, the 4ee-reference points are31 versus32, while the
market-reference arm ties at58 points apiece. For `repair_integrated`, the
4ee-reference points are31 versus32 and the market-reference points are56
versus58. Its matched cash changes are+21,561 for us and+105,479 for the
rival, so the paired margin falls by83,918 coins. Neither candidate advances
to confirmation, public preservation, or loader checks. No source or upload
file changed.

Summary JSON SHA-256:
`016d7b42da754471a824c13d792e748a23e872c5081f755bc574f882f5f8c86b`.
Unique game ledger SHA-256:
`1c1ea7249f0d705e4e1b0d28d52bff3b3c92f6f11cff741601ad44b56d76d450`.
Frozen plan SHA-256:
`7acdd22977fe7377f67858893f26e2cfa6bc07df0d6718ae22837aaca7387959`.

**Decision: reject both exact repair arms.** This old recovery layer does not
advance the current a44 saved-loss objective. Continue with the separately
frozen a44-bound replay candidates.

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
were subsequently implemented in `diagnostics/native_preservation_20260928/`;
they require passing independent confirmation before use.

## 2026-09-28 07:35 UTC — full saved panels and upload checks pass

All **200/200** original-native games finish cleanly, DONE/DONE/720, with
exact development parity and zero prior winning-seat regressions.

| Exact candidate | Saved public-loss sweeps | Saved top-team sweeps | Combined sweeps | Seat W/D/L |
|---|---:|---:|---:|---:|
| 467a9dfe, main parent | 1/30 | 17/20 | 18/50 | 36/0/64 |
| 367d2e76, integrated parent | 13/30 | 19/20 | 32/50 | 64/0/36 |

Each sweep requires wins in both seats. Both arms add Junliang Ye and
retain every parent winning seat. The integrated file still loses 17
public-loss fixtures and DECEM. **Advance both exact arms to the frozen
independent pilot; do not promote the research baseline.** Full session
13956 is terminal. Receipt SHA:
`1cd02ac25079a1df229ad528c51a94ec467181a4adcd1e6ab13248ff4fd82545`.

The user freshly requested uploading the combined new main.py. Separate
operational loader checks on Junliang and Boey passed in both seats:
eight clean direct/file games, all 719 actions for both players and rewards
identical, correct final callable and no time-budget breach. Loader SHA:
`caa82e5b35e4b6cadb5eeb8bd4694a5f5082e64f8a926ba0fa16599a7f468e33`.

Exact **367d2e76** was uploaded as **main.py**, submission **56633591**, at
**07:35:56 UTC / 13:05:56 IST**. Kaggle listed it as PENDING at 07:35:59 UTC,
without a score. The one authorization is consumed. This is an experimental
upload with independent reacting qualification incomplete. Root main stays
4ee; the exact candidate backup remains at the root. No leaderboard or
replay refresh occurred. Upload evidence is in
`diagnostics/upload_hire_recovery_20260928_367d2e76/upload_receipt.json`.
