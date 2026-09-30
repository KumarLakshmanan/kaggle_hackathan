# Complete rival-tape mechanical pilot — 27 September 2026

The entire fresh DECEM and Majkel 719-action tapes were replayed unchanged
as native candidates against **reacting exact 4eeac9c3** on predeclared
fresh seeds 2716200–2716202, both seats and original shop generation. No
opponent code was executed. All **12/12** games finished DONE/DONE/720.

| Tape | Seed 2716200 margins | Seed 2716201 margins | Seed 2716202 margins | Wins |
|---|---:|---:|---:|---:|
| DECEM | −25,480 / −25,589 | −8,145 / −8,145 | −8,393 / −8,393 | 0/6 |
| Majkel1337 | −23,135 / −23,135 | −22,272 / −22,272 | −10,907 / −10,907 | 0/6 |

All three seeds' first two shops differ from each tape's source shops.
DECEM's tape still reaches three land quadrants and 12 workers by the last
hour of day 18 in all six games. In the instrumented seed-2716201 seat-0
game it has only **10** non-PASS worker commands with no state change, versus
43 in its original source game. It is physically executable, but the market
does not pay for its product mix: 292 strawberries sell for 9,173 coins,
whereas 295 sell for 57,015 in its source game. Milk receipts fall from
26,677 for 134 units to 13,508 for 136 units. The direct comparison also
includes different seeds and a different reacting rival, so it diagnoses
shop/market sensitivity rather than isolating one price cause.

Majkel's tape reaches only two land quadrants by day 18 in four of six
games; it reaches three only on seed 2716202. The audited seed-2716201
seat-0 run has **1,027** non-PASS worker commands with no state change,
versus 65 in its source game. Milk receipts fall from 55,731 to 11,687 and
WOOL receipts from 31,295 to 4,577; milk sale units also fall from 254 to
233 and wool from 198 to 103. This schedule is both physically and
commercially sensitive to the new game state.

**Decision:** Reject either full fixed tape as a robust standalone candidate
for promotion. DECEM's executable schedule could inform a new funded
portfolio, but it needs observable shop and market adaptation. Majkel's
schedule additionally needs a compatible land/funding/worker plan. These
12 games are a small mechanical screen, not independent validation of a
reacting transplant. No policy edit or Kaggle upload was made.

Evidence: `FULL_TAPE_PILOT_PLAN.md`, `full_tape_pilot.json`,
`full_tape_pilot_summary.json`,
`decem_full_tape_seed2716201_events.json.gz`, and
`majkel_full_tape_seed2716201_events.json.gz`.
