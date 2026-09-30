# Day-10 third-land response feasibility — 2026-09-27

## Verdict

**No concrete day-10 third-land intervention is ready for an independent
experiment.** The submitted `main.py` remains SHA-256
`4eeac9c3ded6682d42213ad22242ebe3dbe294faecbee7a33a6543a1f1f783ed`.
No candidate, `main.py` edit, native A/B game, or Kaggle upload was made. This
is a diagnosis of actual public games, not policy-strength validation.

The exploratory observation-legal warning is measured at frame 240: rival
crop/animal installations exceed ours by at least eight, while our public
cash is at least the rival's. It fires in **8 losses and 4 wins** among the
61 complete public replays of submission 56609430. All 12 have our two
quadrants and the rival's three at that instant. The incumbent already buys
our third land successfully at frame **241 in 3**, **242 in 5**, and **266 in
4**. It sends daily hires, seed/animal purchases and worker tasks into that
investment. Adding a land order at frame 240 would duplicate an existing
commitment; moving the order earlier without moving its supporting schedule
does not create an earlier harvest.

| Live episode | Outcome/margin | Shops | Own/rival cash at 240 | Our land #3 | SW installed at 264 / 288 / 312 | Peak hands days 10/11/12 |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 114193811 Chris Tu | win +8,353 | ICE/YARN/BRUNCH | 7,351 / 144 | 242 | 20 / 25 / 25 | 10/10/11 |
| 114195269 Jack Burley | win +21,035 | BAKERY/YARN/BAKERY | 2,125 / 1,108 | 266 | 0 / 21 / 25 | 8/10/11 |
| 114218866 pensukesan | loss −8,665 | PIZZA/PIZZA/PIZZA | 3,261 / 2,287 | 241 | 18 / 25 / 25 | 8/10/12 |
| 114220354 Nakano | win +5,909 | BAKERY/BRUNCH/PET | 1,974 / 145 | 266 | 0 / 21 / 25 | 7/10/10 |
| 114227779 kwa | loss −3,858 | BRUNCH/ICE/ICE | 2,436 / 251 | 242 | 23 / 25 / 25 | 8/9/10 |
| 114235177 mhw | loss −21,260 | BAKERY/PIZZA/FARMERS | 1,642 / 220 | 266 | 0 / 24 / 25 | 8/10/10 |
| 114236633 Kucing Garong | loss −2,857 | BRUNCH/SMOOTHIE/YARN | 2,250 / 227 | 241 | 10 / 11 / 11 | 7/7/9 |
| 114239616 kwa | win +4,217 | FARMERS/SMOOTHIE/FARMERS | 450 / 164 | 242 | 21 / 23 / 23 | 8/8/10 |
| 114243994 high frequency farming | loss −7,539 | BAKERY/PIZZA/BRUNCH | 1,541 / 422 | 266 | 0 / 24 / 25 | 8/10/10 |
| 114249897 Dieter | loss −5,454 | PIZZA/FARMERS/PET | 2,387 / 989 | 242 | 22 / 25 / 25 | 9/9/11 |
| 114254310 Junliang Ye | loss −12,934 | BRUNCH/ICE/ICE | 2,443 / 580 | 242 | 19 / 21 / 23 | 8/9/10 |
| 114257327 pensukesan | loss −19,196 | BRUNCH/PIZZA/PET | 2,236 / 2,000 | 241 | 10 / 11 / 11 | 7/7/9 |

The SW installed counts are actual crop or animal tiles in the newly
unlocked southwest quadrant, not requested actions. The two 11-tile losses
share route 113784024: at frame 312 each has 8 WHEAT, 2 STRAWBERRY and 1
SHEEP there, with **14 still-unbuilt tiles**. This is a real unused-land
observation but not a funded production proposal. The route also sends
FEED, CARE, WATER, harvest, fertilizer and delivery work, and its worker
allocation is below the more densely planted routes. Filling the 14 tiles
would need seeds, hired labor, travel, harvest, storage and sales alongside
those obligations. The warning also fires on two wins against rank-100/105
opponents (Nakano and kwa), so automatic expansion has meaningful controls.

## Complete-route compatibility and timing

The uploaded selector at `main.py` lines 28–41 chooses saved action tapes
from observed shop prefixes. I scanned all **145** embedded route tapes
against each flagged live game's exact first 240 observed farmer/hand commands
and all `HIRE`, `BUY_LAND`, `BUY_ANIMAL`, `BUY_SEED` order multisets. The
selected route matches all 24 worker turns of day 9 in every case. Every
saved tape matching the observed prefix is either the incumbent route or an
ID with an identical **719-turn** tape; there is **no distinct continuation**
which preserves the already executed commitments. This is a strict
compatibility screen, not proof that every conceivable route with a different
past could fail. A new switch would require an independently constructed
complete continuation and native execution checks.

The four frame-266 third-land acquisitions split **two wins and two losses**.
In the two losing BAKERY/PIZZA cases, frame-240 cash is only 1,642/1,541.
The existing first action on day 10 sells 15 FERTILIZER, buys 9 WHEAT and
requests eight hires; cash after it is 2,395/2,224. A 2,000-coin land order
at that point would leave only 395/224 before the next turn's substantial
WHEAT buys and other obligations. The current worker tape does no SW
installation on day 10; after its land order at frame 266 it reaches 24/25
SW installations by frame 288. Paying one day earlier without changing
labor and purchase timing therefore has no demonstrated production benefit
and risks starving the existing schedule. The two winning frame-266 games
follow the same broad timing pattern.

The signal itself arrives after the rival has already acquired its third
land in all 12 games. Its day-10 value diagnoses a lag, but cannot recover
the rival's earlier production day by itself. Any earlier response needs an
earlier observable gate and a complete replacement schedule.

## Prior experiments and decision

This screen does not reopen the rejected day-11 sheep overlay: that candidate
duplicated incumbent land, sheep, feed and worker obligations and lost all
three activated native paired seeds. The day-six complete-route switch
avoided duplication but raised rival cash more than ours, lowered paired
margin by 12,294 and increased ineffective worker actions. A one-day
earlier terminal route switch improved only two of four paired seeds; a
day-18 compatible route switch activated once in 16 seeds and lost cash.
The older land retry and fertilizer prefund cases repaired a *different*
failed frame-217 purchase but still did not rescue a both-seat loss. These
results are recorded in `agent.md` and the linked diagnostics; none supplies
a state-compatible day-10 third-land executor for the current 12 cases.

**Decision: reject a day-10 third-land order, generic route splice, or
partial worker overlay as an experiment candidate.** No independent PLAN.md
is frozen because there is no specified complete alternative bundle whose
funding and tasks can be executed from the observed frame-240 state. A future
candidate would first need to preserve/replace the incumbent's whole land,
hire, seed, animal, feed and worker schedule, demonstrate changed successful
SW production, and then freeze activation and both-seat reactive win gates
before looking at its outcomes.

Evidence: `audit.py` and `route_and_execution.json` in this directory;
`../new_live_56609430_20260927/structural_audit/rule_scan.json`,
`bundle_cases.json`, `features.json`, and the 61 verified raw live replays.
Only the submitted local `main.py` was imported to inspect its embedded
tapes; no downloaded opponent code was executed.
