# Near-margin market and terminal conversion feasibility — 2026-09-28

## Decision

**Reject a market or terminal-conversion candidate at feasibility.** The saved
Vadim loss has no marketable terminal stock or failed sale to recover. The 20
live losses below 10,000 coins have mixed product gaps and no recurring missed
sale defect that also applies to Vadim. No candidate was created and no
candidate outcomes were run.

## Scope and controls

This read-only audit used the frozen current top-20 panel
`diagnostics/current_top20_20260927_172258/`, the target manifest and live-loss
ledgers/traces under `diagnostics/loss_class_20260927/`, and the installed
native engine traces. The current `main.py` SHA-256 was confirmed as
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
No Kaggle access, download, upload, `main.py` edit, or `agent.md` edit occurred.

## Vadim Vasilenko, current top-20 panel

The frozen panel records a loss of **400 coins in both seats**. The detailed
native trace reproduces that margin (candidate 127,979; opponent 128,379).
The final market observation at step 718 shows 9 strawberries, 23 melons, 3
eggs, and 2 fertilizer. The action queues eight sell orders covering all
marketable products; after the market phase, every marketable shed quantity is
zero. There are no own failed sale attempts in that final market phase, and
the live event ledger records zero own worker no-ops for Vadim.

The product net-cash difference is only **−337 coins**. Its components are
mixed: our milk is +15,096, wool +3,301, fertilizer +763 and tomato +612,
while carrot is −4,169, egg −5,093, wheat −8,069, strawberry −1,221 and melon
−1,557. There is no single unsold item or missed transaction behind the
400-coin result. Terminal liquidation cannot flip this game because the
marketable terminal balance is zero.

## The 20 live losses under 10,000 coins

The exact native traces show marketable terminal stock in only **2 of 20**
losses:

| Opponent | Loss | Terminal stock | Step-718 posted prices | Maximum gross liquidation |
|---|---:|---|---|---:|
| Yaroslav | 324 | 2 wheat, 1 milk | 35, 1 | 71 |
| Vlas Veles | 3,023 | 3 wheat, 1 fertilizer | 43, 32 | 161 |

Even selling every residual unit at the posted step-718 price would not flip
either game. The other 18 traces end with no marketable stock. Five of the 20
show at least one `SELL:empty_shed` event (Yaroslav, Vlas Veles, Ghost Rule,
leave you, and keiz); only Yaroslav and Vlas also end with any marketable
stock, in different items and quantities. The failures therefore do not
identify a shared recoverable terminal sale.

Product results are heterogeneous across these close losses. The all-30
ledger does show recurrent negative melon and milk net-cash gaps (melon in
26/30, totaling −284,681; milk in 25/30, totaling −105,438). The close-loss
traces also show lower average melon sale prices for us than for the recorded
opponent in each matchup where both sold melon. This is a repeated market
outcome, but the underlying sale volumes and other product gaps vary, and the
trace evidence does not identify a queue or liquidation error. The current
agent already reorders market queues against native market forecasts. A
change that shifts crop production or harvest timing would be a broader route
experiment and would need its own independent reactive evaluation.

## Reproduction and evidence

- Vadim both-seat baseline: `diagnostics/current_top20_20260927_172258/assessment.json`
- Vadim item cash, sale units, and worker actions: `diagnostics/loss_class_20260927/current_top20_ledgers.json`
- Vadim native event trace: `diagnostics/loss_class_20260927/top20_traces/Vadim_Vasilenko-episode-114265033-seat0.json.gz`
- All 30 live-loss mechanism summaries: `diagnostics/loss_class_20260927/live_loss_ledgers_180951.json`
- Live close-loss event traces: paths recorded per row in that ledger
- Frozen episode/action selection and hashes: `diagnostics/loss_class_20260927/local_target_manifest_180951.json`

Fixed opponent tapes are mechanism diagnostics only. **Promotion decision:
reject this market/terminal-conversion direction for the present target; no
separate candidate or frozen outcome plan is warranted.**
