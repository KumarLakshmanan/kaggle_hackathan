# Portfolio feasibility screen — 2026-09-28

## Decision

**No-go; no candidate or native outcome block.** A rival MELON/MILK revenue edge is frequent in the 30 saved live losses, but the only route-switch trigger that covers the three fresh top-20 losses fires on just 1/30 live losses and also 3 live wins. A broader visible-MELON trigger covers every live loss and almost every win. Existing exact-prefix-compatible route alternatives add only 1–4 post-day-six MELON planting requests. This does not support a high-frequency, materially different, funded production candidate.

`main.py` and `agent.md` were not changed. No Kaggle access, downloads, or upload occurred. Fixed-tape results below are diagnostic evidence only.

## Frozen evidence

- Current submission artifact: `main.py`, SHA-256 `4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
- Full saved live corpus: [cohort_180951.json](../new_live_56609430_20260927/cohort_180951.json), SHA-256 `2e37cf158c4e28edcc3e044c6b7d3fd84d4bfc5a983b31e1aeeee5a2986f0116`: 84 episodes, 54 wins and 30 losses; all archived raw hashes verify.
- All-loss event ledger: [live_loss_ledgers_180951.json](../loss_class_20260927/live_loss_ledgers_180951.json): all 30 loss replays were traced with the exact 4ee artifact, engine 1.32.7, and terminal cash parity.
- Fresh current top-20 replay corpus and native assessment: [manifest.json](../current_top20_20260927_172258/manifest.json), SHA-256 `4cf340e5ac28eec35dc202a459c3910cee8da1c692324b41ebd3f619f70230ea`; [assessment.json](../current_top20_20260927_172258/assessment.json), SHA-256 `9d328af8115e27acb45fd4251a1bbc1fde5fda8c793c027b46792a54c04cbeb7`.
- The older 61-game day-six feature panel is [features.json](../new_live_56609430_20260927/structural_audit/features.json), SHA-256 `0b608492da8038f147cea29c3dbc994782d8386c088ddfe2ed76e1761339ad18`. I combined its 61 observed step-144 states with step-144 states from the remaining 23 archived replays in `cohort_180951.json` for the 84-game trigger counts below.

## Repeated loss channel

Across the 30 losses, own-minus-rival net product trade is **−383,434 coins**, against **−353,424 coins** in final cash margin. Product gaps sum to MELON **−284,681** (negative in 26/30 losses), MILK **−105,438** (25/30), and CARROT **−67,032**; STRAWBERRY **+39,101** and WOOL **+35,458** offset part of those losses. Changed HARVEST requests average 448 per game for us and 483 for the rival.

This identifies a frequent production and market outcome, but not an executable low-risk fix. Net trade is not production attribution: purchases, sale prices, and shared inventory effects are included. Increasing MELON or dairy commitments can change the rival's receipts and the later shop sequence.

## Route-trigger screen

The three shop pairs observed at turn 144 in the latest fixed top-20 losses are:

| Current top-20 team | Margin per seat | First two shops | Incumbent route → compatible alternative | Post-turn-144 MELON plant requests | Total plant requests, incumbent → alternative | HARVEST requests, incumbent → alternative |
|---|---:|---|---|---:|---:|---:|
| DECEM | −62,163 | BRUNCH_SPOT / BRUNCH_SPOT | 113371344 → 113365392 | 14 → 15 | 183 → 200 | 423 → 464 |
| Boey | −20,873 | YARN_STORE / FARMERS_MARKET | 113661901 → 113660799 | 13 → 17 | 219 → 232 | 439 → 439 |
| Vadim Vasilenko | −400 | SMOOTHIE_SHOP / ICE_CREAM_SHOP | 113441389 → 113772818 | 13 → 16 | 177 → 199 | 413 → 412 |

Each alternative route has exactly the same action dictionaries as the incumbent's selected first-shop route through step 143, so the proposed switch could preserve the full day-six action prefix. The remaining route is a complete scheduled route, not a single crop overlay, but its MELON change is modest and it also changes other planting and worker actions. The screen did not run the candidate or claim native state parity from a switched game.

Across all 84 saved live games, these three pairs appear in **1 loss and 3 wins**: loss 114289228 (leave you), wins 114188105, 114206899, and 114248439. Thus the route-family trigger covers **1/30 live losses** and fires on **3/54 live wins**. In the current top-20 assessment, it fires on 5/20 teams: the three failures above plus winning controls Yizhou and Kaggledew Valley. A generic visible condition `rival MELON count ≥ own MELON count + 8` covers **30/30 losses and 53/54 wins** in the live corpus. Neither trigger meets a useful combination of loss coverage and protection of winning controls.

The alternate sources are not a materially new melon portfolio: they add only one to four MELON plant requests after turn 144. They do add 13–22 total planting requests in two branches, while changed harvest requests range from −1 to +41. That is insufficient evidence to attribute a gain to MELON, and it would be unsafe to cherry-pick route changes on the three losing tapes.

## Prior route and market overlap

- [route_portfolio_20260927/RESULTS.md](../route_portfolio_20260927/RESULTS.md) tested four first-two-shop route substitutions; target fixed-tape margin changes were +447 to +2,688 per seat, all below its frozen +5,000 gate. The proposed branch is the same route-swap mechanism, now with lower live-loss activation.
- [commitment_controller_20260926/ROUTE_RESULTS.md](../commitment_controller_20260926/ROUTE_RESULTS.md) found that a day-six full-route switch raised our cash by 5,392 but raised rival cash by 17,686, reducing paired margin by 12,294. This directly cautions against treating added output or own cash as competitive gain.
- The current 4ee top-20 assessment already activates its market queue optimizer 62, 91, and 68 turns against DECEM, Boey, and Vadim, with predicted relative gains of 2,824, 4,223, and 8,298 coins and zero optimizer errors. It still loses all three fixed-tape matchups. The separate [perfect-information market audit](../market_oracle_diagnostic_20260927/RESULTS.md) found only 530–4,197 coins of local relative-cash improvement per selected game while using the recorded rival queues and private stock, neither of which is available to a deployed policy.

**Rejection:** do not build or run the melon route variant from these data. Reopen only when a funded whole schedule has a predeclared observable trigger that activates on multiple live losses without broad activation on wins, and its measured `delta_own - delta_rival` can be tested against at least two reacting references with winning controls preserved.
