# Actual live near-mirror cash audit — 2026-09-25

Source: the 24 downloaded public episodes of user-authorized Kaggle submission
56530281, analyzed without changing `main.py` or submitting again. Frozen
agent SHA-256: `04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.
The unfinished analysis worker stopped at a usage limit after producing its
script and evidence JSON; this report independently summarizes those saved
artifacts. The script itself is read-only on source replays.

The market model reconstructed each premium-product SELL from recorded
pre/post shed, market inventory and actual per-unit lockstep prices. On
**4,627 eligible single-item, no-buy receipt checks**, its predicted cash
exactly matched observed cash within one coin on **4,627/4,627** (zero total
absolute residual). This validates that restricted attribution, not every
mixed buy/sell or end-of-day transaction. `summarize_evidence.py` aggregates
the restricted model by product for all 11 losses.

Findings:

- Seven of 11 live losses sold fewer CARROT units than the rival. The largest
  carrot shortfalls were 53, 52 and 28 units, with modeled carrot receipt
  deficits of 2,688, 3,115 and 1,556 coins respectively. A separate action
  count verified that all seven also requested fewer CARROT seeds and plants;
  this is a portfolio/allocation difference, not merely a failed sale or
  empty-stock queue. These are quantity deficits, so queue reordering alone
  cannot fix them.
- Ten of 11 losses had lower *gross modeled sale cash* than the rival, but this
  is **not** the terminal-margin explanation by itself: product purchases,
  seeds, hires and land costs must be netted separately. In episode 113135718
  the rival sold about 5,407 wheat units through repeated large wheat
  buy/sell cycles while our agent sold 397; its roughly 223,000-coin gross
  wheat receipt lead mostly reflects purchased wheat, not farm production.
  The actual terminal loss was only 351 coins. Do not use gross SELL receipts
  as an optimization target without subtracting acquisition cost.
- One close loss, 113174622, had nearly equal modeled net *gross* sale
  receipts across products (+4 for us) but still lost 525 terminal coins.
  More gross sales would not diagnose its spending or acquisition difference.
- On equal-unit products, timing/price differences remain real; for example,
  113123301 sold 237 WOOL units on each side but received 735 fewer coins.
  That is smaller than some production gaps and does not establish that a
  specific timing rule improves *net terminal* score.
- In three losses, the first CARROT planting divergence was very late: turn
  647 or 657. On two of them our turns 657–659 requested five WHEAT plants
  while the near-mirror rival requested CARROT in those positions. The
  `late_carrot_trace.py` audit records the paired actions and seed state.
  This motivated a predeclared late crop-swap candidate under the live
  submission audit directory, but the observation alone is not evidence
  that the swap pays after harvest and market saturation.

Across all seven CARROT-unit-shortfall losses, the first divergent CARROT
request was a rival CARROT in a slot where our agent requested WHEAT. The
divergence occurred at replay action rows 299, 381, 453, 477, 647 (twice),
or 657. This is a recurrent portfolio choice, but the late five-slot swap
screen failed to flip a loss and produced mixed cash deltas; see
`diagnostics/live_submission_56530281_20260925/LATE_CARROT_SWAP_SCREEN.md`.

Consequence: separate the next hypotheses. Investigate recurring carrot
quantity shortfalls through observation-legal farm-task/crop allocation,
and investigate close-loss net cash ledgers (including purchases and hires)
before changing market logic. The 24 public replays and 100 historical routes
are development data; independent reactive tests are needed before promotion.

Artifacts: `analyze_live_clone_margin.py`, `live_clone_margin_evidence.json`,
`summarize_evidence.py`, `carrot_shortfall_diagnostic.py`, and
`late_carrot_trace.py`. Reproduce the compact per-loss table:

```powershell
python -X utf8 diagnostics\live_clone_margin_20260925\summarize_evidence.py
```
