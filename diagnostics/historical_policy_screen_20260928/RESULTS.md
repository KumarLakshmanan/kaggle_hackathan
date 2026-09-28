# Historical alternative policy screen — 2026-09-28

## Decision

**Reject all three alternatives as fixes for the current DECEM, Boey, and
Vadim top-20 losses.** On the frozen saved-action tapes, none won even one of
the six target seat games. V43 and V48 also lost both Majkel control seats;
search-v2 lost both seats on both controls. No first-two-shop/state selector
was evaluated because the predeclared target-flip condition did not occur.
These are fixed-tape diagnostics only and do not test reacting opponents.

## Protocol and integrity

The run followed the pre-results plan in `PLAN.md`: three unchanged standalone
files, five fixed fixtures (three failures, two winning controls), both seats,
engine 1.32.7, original fixture seeds, endogenous seeded shops, and exact
saved 719-action opponent tapes. The screen completed all **30/30 games** at
720 frames with both agents `DONE`. Candidate file hashes and current `main.py`
hash matched before and after; the incumbent stayed at
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
Replay and action hashes matched the frozen top-20 panel manifest.

V43 is the saved standalone decoded file `main_v43_current.py` (SHA-256
`69f06a802b62aa08f28705dab5728eb924bb6a7c23ffe0164f65b104cc3dadf3`). The
distinct Ahmed V43 source used by the earlier physical-gap pilot (hash prefix
`919fc1d6`) is unavailable in this workspace; its old result is not attributed
to this file. The V48 fixture is the complete saved policy, not its earlier
route-data proxy. Search-v2 is the retained search variant with the best
completed holdout mean among its saved versions, though its prior reacting
holdout still lost all four paired seeds.

## Results

Margins are candidate minus frozen-tape opponent, seats 0/1. Baseline 4ee
lost both seats on each target and won both seats on each control.

| Candidate | DECEM target | Boey target | Vadim target | DSM control | Majkel control |
| --- | --- | --- | --- | --- | --- |
| V43 decoded | −14,744 / −14,744 (L/L) | −42,599 / −27,555 (L/L) | −35,559 / −35,559 (L/L) | +22,708 / +22,708 (W/W) | −20,324 / −24,075 (L/L) |
| V48 full | −14,744 / −14,744 (L/L) | −42,599 / −27,555 (L/L) | −35,559 / −35,559 (L/L) | +22,708 / +22,708 (W/W) | −20,324 / −24,075 (L/L) |
| Search v2 | −32,250 / −32,250 (L/L) | −50,211 / −50,249 (L/L) | −93,879 / −106,308 (L/L) | −43,546 / −43,546 (L/L) | −62,567 / −56,875 (L/L) |

Every candidate scored losses on all three target fixtures in both seats:
**0/18 target seat wins, 0/18 draws, 18/18 losses**. V43 and V48 had identical
outcome and margin pairs on all five fixtures, while still failing to reverse
any target; both regressed two control seats. Search-v2 regressed all four
control seats. V43/V48 improve DECEM's loss margin from −62,163 to −14,744,
but remain losses and worsen the Boey and Vadim margins. Search-v2 narrows
DECEM's gap to −32,250 but performs worse on the other two targets.

Since no target seat flipped, the plan's trigger-feasibility audit was not
activated. This screen provides no evidence for a shop/state-triggered policy
change, and it does not justify a reacting-reference follow-up for these
artifacts. No candidate was tuned, `main.py` was not edited, and there was no
Kaggle access or upload.

## Artifacts

- `PLAN.md` — frozen candidate hashes, fixture/action hashes, and gate.
- `screen.py` — hash-checked local runner; captures candidate state at turn 48.
- `screen.json` — all 30 outcomes, fixture provenance, integrity checks, and
  target/control summaries.

Reproduce with:

```powershell
python -X utf8 diagnostics/historical_policy_screen_20260928/screen.py --workers 4
```
