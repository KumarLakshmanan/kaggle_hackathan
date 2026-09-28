# Funded land-order bundle results — 2026-09-27

## Decision

**Reject; do not promote.** The candidate failed the predeclared current-main gate and the public-market reference gate. No confirmation block was run. This was a research-only candidate; `main.py` and `agent.md` were not changed, and no Kaggle upload was attempted.

## Frozen artifacts and method

- Plan and gates: [PLAN.md](PLAN.md).
- Base `main.py` SHA-256: `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed` (unchanged at completion).
- Candidate SHA-256: `28e6b95be70823cb131938e1fbb0d791e94e572f722b9ecb274f86bb43681cdc`.
- Reacting reference hashes match the plan: c68 `c68fa46f6f0c52b9779a2f135bee8024b8f56310934a17b3683e5023686fbdad`; public-market `f6a756cfb900b9d5f49905d596b63f1fde2445342ac4b1ae04e353739bd62d2`.
- Engine 1.32.7, generated original shops, normal reactive play, both candidate seats, development seeds 2719000–2719015.
- Each of the five native blocks has 32/32 games at 720 frames, both seats `DONE`, and zero candidate projection errors.
- Candidate action: move only an already scheduled third-quadrant `BUY_LAND` order immediately after the turn's existing sells, when the installed queue simulator projects at least 2,500 coins. No purchase or worker action is added.

## Fresh native development results

Paired points below use 2/1/0 for each paired seed outcome (win/draw/loss); 16 paired draws in a self-control would score 16 points.

| Opponent | Candidate seat W/D/L (32 games) | Candidate paired W/D/L (16 seeds) | Candidate paired points | Main-control paired W/D/L | Candidate-minus-main paired-margin delta |
|---|---:|---:|---:|---:|---:|
| Current `main.py` | 1 / 14 / 17 | 0 / 8 / 8 | 8/32 (self-control: 16/32) | self-control expectation: 0 / 16 / 0 | −250 |
| c68 uploaded reference | 32 / 0 / 0 | 16 / 0 / 0 | 32/32 | 16 / 0 / 0 | +28 |
| Public-market reference | 28 / 0 / 4 | 14 / 0 / 2 | 28/32 | 16 / 0 / 0 | −225,318 |

Against current main, candidate mean seat margin was −7.8125 coins; summed paired margin was −250. It activated on 12/16 distinct seed pairs. This misses both the minimum paired-points gate and the positive-margin gate.

Against c68, candidate and main each swept all 16 paired seeds. Candidate paired margin was +124,916 versus main +124,888, a +28 delta (candidate own reward +14, rival reward −14). This reference alone passed its paired-points and margin-delta checks. Candidate activated on 11/16 seed pairs.

Against the public-market reference, candidate paired margin was +233,054 versus main +458,372, a −225,318 delta. Candidate own reward changed by −126,870 total while the reference's reward changed by +98,448. Candidate scored 14 paired wins and 2 losses, compared with main's 16 wins. All nonzero seedwise margin deltas were losses for the candidate: seed 2719006 −89,552; 2719009 −4,734; 2719014 −131,032. Other seedwise deltas were zero. Candidate activated on 14/16 seed pairs. This fails both the paired-points and paired-margin gates.

## Files

- Candidate: [exp_production_bundle_landfund_20260927.py](../../exp_production_bundle_landfund_20260927.py).
- Candidate vs current main: [candidate_vs_main_dev16.json](candidate_vs_main_dev16.json).
- Candidate and main vs c68: [candidate_vs_c68_dev16.json](candidate_vs_c68_dev16.json), [main_vs_c68_dev16.json](main_vs_c68_dev16.json).
- Candidate and main vs public-market reference: [candidate_vs_market_dev16.json](candidate_vs_market_dev16.json), [main_vs_market_dev16.json](main_vs_market_dev16.json).
- Supplemental saved top-20 fixed-action diagnostics only: [DECEM](top20_decem_diagnostic.json), [Boey](top20_boey_diagnostic.json), [Vadim](top20_vadim_diagnostic.json). These are not native-strength evidence or confirmation.

The fixed-action DECEM diagnostic did not activate: projected same-turn sale cash was 2,400 at step 240, below the frozen 2,500 cutoff; its terminal loss remained −62,163. Boey did not activate and retained its −20,873 loss. Vadim activated once at projected cash 3,235 at step 240, but its terminal margin remained −400. These replays did not count toward any gate.

## Limits and promotion decision

The paired benchmark records terminal rewards, activation telemetry, frame count, status, and runtime. It does not retain per-day tile/worker traces, so successful third-land completion, day-18 land count, and non-PASS/no-change worker counts were not measured in these native blocks. The trigger count is not evidence that land purchase or production succeeded. The large public-market regression is sufficient to reject the candidate without a confirmation run. Keep the incumbent; do not promote or upload this candidate.
