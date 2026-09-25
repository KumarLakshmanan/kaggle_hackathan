# Predeclared sale-advance horizon screen

Date: 2026-09-25. Frozen `main.py` SHA-256:
`04b0bdc3bbe319d969170ddc8007bd6300af254a98151d6ef990c9ed2ebbabc1`.

Hypothesis: many live near-mirror opponents sell the same already-produced
goods close to our schedule. Extending the existing own-plan sale-advance
lookahead from four to eight turns could collect a better quote before their
sell, without changing production or adding unsupported future observations.
It could also sell before town consumption and harm own receipts.

Treatment: override only `_ADV_LOOK=8` in the unchanged `main.py`; retain
existing `_ADV_FROM`, `_ADV_TO`, product set, and price/stock guards. This
consults only our own future route tape, not the opponent's future actions.

Screen: the same 24 recent live public fixed-action routes, both seats. Frozen
baseline is 13/24 route wins, 26/48 seat wins, all `DONE`. Proceed to the full
top-50 panel only if treatment reaches at least 15/24 route wins and 30/48
seat wins, has no previously winning route or seat reversed, and the rescued
losses increase own cash (not only suppress fixed-tape rival cash). A failure
or <10 activated routes means reject/inconclusive, not an invitation to add
route-specific exceptions. Passing still requires a fresh reactive test and
does not authorize a Kaggle upload.

## Result — fails the predeclared own-cash gate

The 48-game screen completed, all `DONE`, max local agent call ~371 ms. The
look-eight treatment reached **15/24 route wins and 30/48 seat wins** versus
13/24 and 26/48, with no previously won route or seat reversed. It rescued
two losses, but attribution is mixed:

| Rescued live episode | Pair margin, baseline → treatment | Own cash change, both seats | Fixed-tape rival cash change |
| ---: | ---: | ---: | ---: |
| 113123301 | −1,316 → +70 | +632 | −754 |
| 113174622 | −1,050 → +498 | **−214** | −1,762 |

The second rescue violates the predeclared requirement that rescued losses
increase **own** cash. Across 48 games, mean own cash changed +79.17 while
the fixed-tape rival changed −298.38, so most of the +377.54 mean paired
margin came from rival-cash suppression. Other regressions include the
113170773 loss worsening from −2,854 to −4,158 paired, with own cash −1,264
across seats; the 113149911 winning margin decreased by 1,302 paired, with
own cash −1,480. Full data:
`sale_advance_look8_24routes_both_seats.json`.

Do **not** promote this treatment to `main.py` on these results. A fixed tape
keeps the rival's future commands despite altered prices/cash; that cannot
establish the same gain against a reactive opponent. Any follow-up needs a
new observation-based causal condition and fresh independent validation,
not a retrospective exception for the two affected episode IDs.
